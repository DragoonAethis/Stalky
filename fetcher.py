#!/usr/bin/python3
import sys, os, json, time, urllib.parse, urllib.request
# import requests  # We urllib now, fam

try:
    import config  # Place your config stuffs in config.py pls.
except ModuleNotFoundError:
    print("Before running this, try creating a config file with your credentials.")
    exit()

if sys.version_info < (3, 6):
    print("You need at least Python 3.6 for this to work.")
    exit()

SLEEP_TIME = 1
OFFLINE_STATUS_JSON = """{"lat": "offline", "webStatus": "invisible", "fbAppStatus": "invisible", "otherStatus": "invisible", "status": "invisible", "messengerStatus": "invisible"}"""
ACTIVE_STATUS_JSON = """{ "lat": "online", "webStatus": "invisible", "fbAppStatus": "invisible", "otherStatus": "invisible", "status": "active", "messengerStatus": "invisible"}"""


class Fetcher():
    # Headers to send with every request.
    REQUEST_HEADERS = {
        'accept': '*/*',
        # If you leave gzip etc enabled here, urllib will break on decoding :<
        'accept-language': 'en-US,en;q=0.8,en-AU;q=0.6',
        'cookie': config.STALKER_COOKIE,
        'dnt': '1',
        'origin': 'https://www.facebook.com',
        'referer': 'https://www.facebook.com/',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:63.0) Gecko/20100101 Firefox/63.0'
    }

    # Hey hey, Facebook puts this in front of all their JSON to prevent hijacking. But don't worry, we're ~verified secure~.
    JSON_PAYLOAD_PREFIX = "for (;;); "

    def __init__(self):
        if not os.path.exists("log"):
            os.makedirs("log")
        self.reset_params()

    def make_request(self):
        # Load balancing is for chumps. Facebook can take it.
        parsed_args = urllib.parse.urlencode(self.params)
        full_url = "https://6-edge-chat.facebook.com/pull?{}".format(parsed_args)
        request = urllib.request.Request(full_url, headers=self.REQUEST_HEADERS)
        with urllib.request.urlopen(request) as f:
            response_obj = f.read()

        try:
            raw_response = response_obj.decode('utf-8')
            if not raw_response:
                return None
            if raw_response.startswith(self.JSON_PAYLOAD_PREFIX):
                data = raw_response[len(self.JSON_PAYLOAD_PREFIX) - 1:].strip()
                data = json.loads(data)
            else:
                # If it didn't start with for (;;); then something weird is happening.
                # Maybe it's unprotected JSON?
                data = json.loads(raw_response)
        except ValueError as e:
            print(str(e))
            return None
        except UnicodeDecodeError as e:
            print(str(e))
            return None

        return data

    def _log_lat(self, uid, lat_time):
        if uid in config.STALKED_LIST:
            with open("log/{uid}.txt".format(uid=uid), "a") as f:
                # Now add an online status at the user's LAT.
                user_data = []
                user_data.append(lat_time)
                user_data.append(ACTIVE_STATUS_JSON)
                f.write("|".join(user_data))
                f.write("\n")

                # Assume the user is currently offline, since we got a lat for them. (This is guaranteed I think.)
                user_data = []
                user_data.append(str(time.time()))
                user_data.append(OFFLINE_STATUS_JSON)
                f.write("|".join(user_data))
                f.write("\n")

    def start_request(self):
        resp = self.make_request()
        if resp is None:
            print("Got error from request, restarting...")
            self.reset_params()
            return

        # We got info about which pool/sticky we should be using I think??? Something to do with load balancers?
        if "lb_info" in resp:
            self.params["sticky_pool"] = resp["lb_info"]["pool"]
            self.params["sticky_token"] = resp["lb_info"]["sticky"]

        if "seq" in resp:
            self.params["seq"] = resp["seq"]

        if "ms" in resp:
            for item in resp["ms"]: # The online/offline info we're looking for.
                if item["type"] == "buddylist_overlay": # Find the key with all the message details, that one is the UID.
                    for key in item["overlay"]:
                        if type(item["overlay"][key]) == dict:
                            uid = key

                            # Log the LAT in this message.
                            self._log_lat(uid, str(item["overlay"][uid]["la"]))
                            if "p" in item["overlay"][uid]: # Now log their current status.
                                with open("log/{uid}.txt".format(uid=uid), "a") as f:
                                    user_data = []
                                    user_data.append(str(time.time()))
                                    user_data.append(json.dumps(item["overlay"][uid]["p"]))
                                    f.write("|".join(user_data))
                                    f.write("\n")

                # This list contains the last active times (lats) of users.
                if "buddyList" in item:
                    for uid in item["buddyList"]:
                        if "lat" in item["buddyList"][uid]:
                            self._log_lat(uid, str(item["buddyList"][uid]["lat"]))

    def reset_params(self):
        self.params = {
            'cap': '8', # No idea?
            'cb': '2qfi', # No idea? (j6wr for me)
            'channel': 'p_' + config.STALKER_UID, # Internal push notification channel?
            'clientid': config.STALKER_CLIENTID,
            'format': 'json',
            'idle': '0', # Is this my online status? (2 for me)
            'isq': '173180', # No idea? (168989 for me)
            # 'mode': 'stream', # Whether to stream the HTTP GET request. We don't want to!
            'msgs_recv': '0', # How many messages we've got from Facebook in this session so far?
            'partition': '-2', # No idea?
            'qp': 'y', # No idea?
            'seq': '0', # Set starting sequence number to 0. (Not required for /pull, setting to 0 gets everything.)
            'state': 'active',
            'sticky_pool': 'rash0c01_chatproxy-regional',
            'sticky_token': '0',
            'uid': config.STALKER_UID,
            'viewer_uid': config.STALKER_UID,
            'wtc': '171%2C170%2C0.000%2C171%2C171',
            'iris_enabled': 'false'
        }


if __name__ == "__main__":
    f = Fetcher()
    while True:
        try:
            f.start_request()
            time.sleep(SLEEP_TIME)
        except UnicodeDecodeError:
            f.reset_params()
            print("UnicodeDecodeError!")
