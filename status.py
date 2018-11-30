import json, bisect, time

class StatusLevel():
    OFFLINE = 0
    INVISIBLE = 1
    IDLE = 2
    ACTIVE = 3


class Status():
    """The status of a user."""

    value_map = {
        "offline": StatusLevel.OFFLINE,
        "invisible": StatusLevel.INVISIBLE,
        "idle": StatusLevel.IDLE,
        "active": StatusLevel.ACTIVE
    }

    statuses = "status webStatus messengerStatus fbAppStatus otherStatus".split()

    status_type_map = {
        "status": 4,
        "webStatus": 3,
        "messengerStatus": 2,
        "fbAppStatus": 1,
        "otherStatus": 0
    }


    def __init__(self, time, status_json):

        self.time = time
        self._status = {}
        self.lat = False

        fields = json.loads(status_json)

        for status in self.statuses:
            # Map status_name -> status value enum
            self._status[status] = self.value_map[fields[status]]

        # Is this an entry for a last active time?
        if "lat" in fields:
            self.lat = True

    def is_online(self):
        return self._status["status"] == StatusLevel.ACTIVE

    def all_active_status_types(self):
        """Returns all status types which are currently active. If types other than "status" are active, "status" is necessarily also active."""

        return filter(lambda status_type: self._status[status_type] >= StatusLevel.ACTIVE, self._status.keys())

    def highest_active_status_type(self):
        active_status_types = list(self.all_active_status_types())

        if not active_status_types:
            return 0

        return max([self.status_type_map[status] for status in active_status_types])

    # Make these objects sortable by time.
    def __lt__(self, other):
        return self.time < other

    def __gt__(self, other):
        return self.time > other


class StatusHistory():
    """Object representing the history for a particular user. History stored sparse."""


    EPOCH_TIME = 1452556800

    # Save the start time so computation time doesn't offset the measured time.
    START_TIME = int(time.time())

    def __init__(self, uid):
        with open("log/{uid}.txt".format(uid=uid)) as f:
            self.activity = self.parse_status(map(str.strip, f.readlines()))

    def create_time_map(self, status_list):
        status_map = {}
        for item in status_list:
            status_map[int(float(item["time"]))] = item["status"]
        return status_map

    def parse_status(self, lines):
        # A list of status objects.
        activity = []

        # Keep a list of seen times so we can avoid duplicates in the history
        seen_times = set()

        for line in lines:
            time, fields = line.split("|")
            # Only add new times, preferring earlier records in the file. This is probably not optimal since later records seem to be more likely to be LATs, but oh well gotta break a few algorithmic contraints to make a BILLION dollars.
            if time not in seen_times:
                seen_times.add(time)
                status_obj = Status(int(float(time)), fields)
                activity.append(status_obj)
        return activity

    def get_status(self, time):
        """Get the HAST (highest active status type) for the user at a particular time by querying the sparse data."""
        # #ALGORITHMS
        # This index is the index of the item AFTER this item would go if it were inserted.
        idx = bisect.bisect(self.activity, time)

        # Since we treat status data points as valid until the next data point, the "current" status is the one on the left of where the inserted time would go.
        current_status = self.activity[max(0, idx - 1)]

        return current_status


    def normalised(self, max_time_back_seconds=None, resolution=60, status_type=None):
        """Turns a sparse time series into a dense one, with number of seconds per bucket specified by resolution.
        If a status_type (status, webStatus, messengerStatus etc.) is given, returns a generator of the status level (online, offline, idle) for that status type."""

        if max_time_back_seconds is None:
            start_time = self.EPOCH_TIME
        else:
            start_time = self.START_TIME - max_time_back_seconds

        for tick in range(start_time, self.START_TIME, resolution):
            status_obj = self.get_status(tick)
            if status_type is None:
                yield status_obj.highest_active_status_type()
            else:
                yield status_obj._status[status_type]
