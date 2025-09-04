import time
from pypixxlib._libdpx import DPxOpen, DPxClose, DPxWriteRegCache, DPxUpdateRegCache, DPxGetTime, DPxStopDinLog, DPxGetDinValue
from experiments.psychopy.general.utilities import *

while True:

    selection1 = {
        "right box": ["green", "blue", "yellow"],
        "left box": ["white", "blue", "red"]
    }


    DPxOpen()

    candidates = getbuttonColor(selection1)


    time.sleep(0.5)  # 500 milliseconds

    DPxClose()
    print("candidates", candidates)

