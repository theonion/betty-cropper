import time


# Necessary b/c Python<3.3 doesn't support datetime.timestamp()
def seconds_since_epoch(when):
    return int(time.mktime(when.timetuple()))
