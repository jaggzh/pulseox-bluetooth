import os
import datetime
import time
from pathlib import Path # for Path(logdir).mkdir(parents=True, exist_ok=True)
import settings
import sys

logfile=None
logfile_timefmt = '%Y-%m-%d %H:%M:%S'
last_lognotice=0      # internal (when did we last show logfile name and stuff)
last_loglinewrite=0   # internal (when did we last write a log line)
loglinewrite_period=10 # Write logfile every this many seconds

lognotice_period=60*2 # Show logfile name every this many seconds
lognotice_period=30 # Show logfile name every this many seconds
logfile_fields_str="#Time\tBPM\tO2\tAlertType"

def setup_log():
    if settings.do_logging:
        if not os.path.isdir(settings.logdir):
            Path(settings.logdir).mkdir(0o700, parents=True, exist_ok=True)
        if not os.access(settings.logdir, os.W_OK):
            raise(PermissionError(f"settings.logdir: No write access? {settings.logdir}"))

def make_logfilename():
    datestr = datetime.datetime.now().strftime('%Y-%m-%d')
    filenameonly = datestr + ".log"
    logfilename = os.path.join(settings.logdir, filenameonly)
    return logfilename

def handle_filelog(
        bpm=None, spo2=None, time=None, alert=None):
    global logfile
    global last_lognotice
    global last_loglinewrite
    dt = datetime.datetime.fromtimestamp(time)
    import time                          # time Param changed to import!

    logfilename = make_logfilename()
    print(f"Logfile: {logfilename}")

    # If it's a new file, open it and write the field names
    if not os.path.isfile(logfilename):
        logfile = open(logfilename, 'a')
        logfile.write(logfile_fields_str + "\n")
    # Otherwise, if we just ran and are logging the first time, logfile
    # will be None, but the logfile was created before, so just open it
    # for appending.
    if logfile is None:
        logfile = open(logfilename, 'a')

    if alert is None: alert='-'
    if time.time()-last_lognotice > lognotice_period:
        last_lognotice = time.time()
        print(f"Logfile @ {logfilename}")
        print(logfile_fields_str)
    if time.time()-last_loglinewrite > loglinewrite_period:
        last_loglinewrite = time.time()
        logfile.write(f"{dt.strftime(logfile_timefmt)}\t{bpm}\t{spo2}\t{alert}\n")
        logfile.flush()

# vim: et
