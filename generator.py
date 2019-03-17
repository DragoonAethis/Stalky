#!/bin/python3
import glob, datetime

TEMPLATE_HEADER = '''<!DOCTYPE html>
<html>
<head>
    <title>Stalky Heatmaps</title>
    <link rel="stylesheet" type="text/css" href="app.css">
</head>
<body>
    <h1>Stalky Heatmaps</h1>
    <div class="main-container">
        <div class="target-container sticky-header">
            <div class="target-name">Who?</div>
            <div class="target-rows">
                <div class="row">
                    <div class="date">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;When?</div>
                    <div class="heat">0</div>
                    <div class="heat">1</div>
                    <div class="heat">2</div>
                    <div class="heat">3</div>
                    <div class="heat">4</div>
                    <div class="heat">5</div>
                    <div class="heat">6</div>
                    <div class="heat">7</div>
                    <div class="heat">8</div>
                    <div class="heat">9</div>
                    <div class="heat">10</div>
                    <div class="heat">11</div>
                    <div class="heat">12</div>
                    <div class="heat">13</div>
                    <div class="heat">14</div>
                    <div class="heat">15</div>
                    <div class="heat">16</div>
                    <div class="heat">17</div>
                    <div class="heat">18</div>
                    <div class="heat">19</div>
                    <div class="heat">20</div>
                    <div class="heat">21</div>
                    <div class="heat">22</div>
                    <div class="heat">23</div>
                </div>
            </div>
        </div>
'''

TEMPLATE_FOOTER = '''
    </div>
</body>
</html>
'''

# LOGFILE_NAME -> Obviously.
TEMPLATE_LOGFILE_HEADER = '<div class="target-container"><div class="target-name">LOGFILE_NAME</div><div class="target-rows">\n'
TEMPLATE_LOGFILE_FOOTER = '</div></div>\n'

# ROW_CLASS -> extra CSS classes, ROW_DATE -> key from mapped dates.
TEMPLATE_ROW_HEADER = '<div class="row ROW_CLASS"><div class="date">ROW_DATE</div>\n'
TEMPLATE_ROW_FOOTER = '</div>\n'

# HEAT_CLASS -> h0..4, HEAT_MARKERS -> number of timestamps.
TEMPLATE_MARKER = '<div class="heat hHEAT_CLASS">HEAT_MARKERS</div>\n'

def map_dates_to_markers(file):
    with open(file, 'r') as input_file:
        lines = input_file.read().split("\n")

    # Delete outliers first
    if lines[0] == '-1':
        del lines[0]

    if lines[len(lines) - 1] == '':
        del lines[len(lines) - 1]

    timestamps = [int(x) for x in lines]
    dates = {}

    for timestamp in timestamps:
        dt = datetime.datetime.fromtimestamp(timestamp)

        date = str(dt.date())
        if not date in dates:
            # Generate list of hours 0..23 to hit
            dates[date] = [0 for x in range(0, 24)]

        dates[date][dt.hour] += 1

    return dates


def generate_heatmaps_for_all_logs():
    document = TEMPLATE_HEADER

    maps = {}
    for file in glob.glob('*.log'):
        maps[file] = map_dates_to_markers(file)

    for logfile, dates in maps.items():
        document += TEMPLATE_LOGFILE_HEADER.replace("LOGFILE_NAME", logfile)
        for date, values in dates.items():
            weekday = datetime.date.fromisoformat(date).weekday()
            if weekday == 5 or weekday == 6: # Sat/Sun
                extra_class = "weekend"
            else:
                extra_class = ""

            document += TEMPLATE_ROW_HEADER.replace("ROW_CLASS", extra_class).replace("ROW_DATE", date)

            for hour in range(0, 24):
                heat_class = 0
                if values[hour] in range(1, 3):
                    heat_class = 1
                elif values[hour] in range(3, 5):
                    heat_class = 2
                elif values[hour] in range(5, 8):
                    heat_class = 3
                elif values[hour] >= 8:
                    heat_class = 4

                document += TEMPLATE_MARKER.replace("HEAT_CLASS", str(heat_class)).replace("HEAT_MARKERS", str(values[hour]))
            document += TEMPLATE_ROW_FOOTER
        document += TEMPLATE_LOGFILE_FOOTER
    document += TEMPLATE_FOOTER

    with open("generated.html", "w") as output_file:
        output_file.write(document)


if __name__ == "__main__":
    generate_heatmaps_for_all_logs()
