from enum import Enum

class TelecallerStatus(str, Enum):
    ACTIVE = "Active"
    BUSY = "Busy"
    BREAK = "On Break"
    TRAINING = "Training"
    MEETING = "In a Meeting"
    OFFLINE = "Offline"
    OUT_OF_OFFICE = "Out of Office"