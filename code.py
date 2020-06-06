'''
Example code for using the max6921 library.
Makes a simple stop watch.
'''

import board
import digitalio
import time
from max6921 import VFD

load = digitalio.DigitalInOut(board.D0)
load.direction = digitalio.Direction.OUTPUT
digits = [(load, 19), (load, 18), (load, 17), (load, 16),
  (load, 15), (load, 14), (load, 13), (load, 12),
  (load, 11), (load, 10), (load, 8), (load, 9)]
segments = [(load, 4), (load, 5), (load, 6), (load, 0),
  (load, 1), (load, 3), (load, 2), (load, 7)]

vfd = VFD(digits, segments)

def format_time(time_stamp):
    '''Formats a number of seconds as " HH.MM.SS.ff"'''
    hms = []
    # Hours
    hms.append(str(int(time_stamp) // 3600))
    # Minutes
    hms.append(str(int(time_stamp) // 60 % 60))
    # Seconds
    hms.append(str(int(time_stamp % 60)))
    # Microseconds
    hms.append(str(int((time_stamp % 1) * 100)))
    output = " "
    for unit in hms:
        while len(unit) < 2:
            unit = "0" + unit
        while len(unit) > 2:
            unit = unit[:2]
        output += unit + "."
    return output[:-1]

while True:
    vfd.print(format_time(time.monotonic()))
    vfd.draw()
