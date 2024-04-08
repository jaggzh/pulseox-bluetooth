#!/usr/bin/env python3
#    Author: jaggz.h who is at gmail.com
#      Date: 2021-12-04
# Copyright: GPL 3.0 https://www.gnu.org/licenses/gpl-3.0.en.html

# Currently this only handles the data sent by this PulseOx
# Wellue Fingertip Pulse Oximeter, Blood Oxygen Saturation Monitor
#  with Batteries for Wellness Use Bluetooth, Black 
# https://www.amazon.com/gp/product/B087Q724QM/

#import playsound  # Not using right now
import pysine      # Used for playing an alert tone
import sys
import ovals       # Other values from pulseox (like SpO2 trace)
from threading import Thread
import subprocess
import os
try:
    import volpy
except:
    print("NOT FOUND: volpy module, or one of its dependencies")
    volpy=None

threadlife_warn_time_s = 6  # seconds
threadlife_kill_time_s = 9  # seconds

import settings as stg
import flogging
import alerts
from bansi import * # Color variables. Leave.

######################################################################3
## Configuration variables:

alert_bpm_audiofile=""               # not used; only using pysine.sine()
alert_on_disconnect=False
alert_on_disconnect=True             # If sensor gives bpm=255, spo2=127

# bpm and o2 alert limits and time average length
# (At present If the avg over this time of data samples
#  exceeds the limits, alert)
alert_avg_secs = {  # samples averaged over this seconds
        'o2': 5,
        'bpm': 5,
        'disco': 5,
        }
last_alert = {      # don't change. these track time.
        'o2': 0,
        'bpm': 0,
        'disco': 0,
        }

bpm_low=95   # 4 testing
bpm_low=52
bpm_high=83  # 4 testing
bpm_high=120
o2_low=99    # 4 testing
o2_low=88
# Internal logs
bpm_log=[]  # []['time','val']
o2_log=[]

alert_bpm_low_freq = 260
alert_bpm_high_freq = 440
alert_o2_freq = 540
alert_disco_freq = 199

log_hours=0    # Could be a lot of data points. We keep each sample currently.
log_mins=log_hours*60
log_secs=log_mins*60 + 20

# Internal, probably no reason to modify
bt_reconnect_delay=2
bt_last_connect_try=0

# Internal, definitely.  No need to touch
btdev=None
final_mac=None
args=None

import sys
import time
from argparse import ArgumentParser

#import bluepy
from bluepy import btle  # linux only (no mac)

do_plot=True
do_plot=False
if do_plot:
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation

last_webupd_time=0
last_keepalive_time=0

if stg.do_web_lcd:
    import remotedisplay as display

import sys
import threading
import time

thread_tracking = {}
thread_terminate_signals = {}

def tracked_thread(target, args=(), kwargs=None, life_limit=7):
    if kwargs is None:
        kwargs = {}
    terminate_signal = threading.Event()
    thread_id = f"{target.__name__}-{time.time()}"  # Ensuring unique ID using timestamp
    
    def wrapper():
        start_time = time.time()
        thread_tracking[thread_id] = {
            'start_time': start_time,
            'thread': threading.current_thread(),  # Store the current thread object
            'terminate_signal': terminate_signal
        }
        
        kwargs['terminate_signal'] = terminate_signal

        try:
            target(*args, **kwargs)
        finally:
            # Cleanup after thread termination
            del thread_tracking[thread_id]
    
    t = threading.Thread(target=wrapper)
    t.start()

    return t

import ctypes
import time
import threading

thread_warned_times = {}

def _async_raise(tid, exctype):
    """Raises an exception in the threads with ID tid"""
    if not isinstance(exctype, type):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("Invalid thread ID")
    elif res != 1:
        # "Undo" the effect if more than one thread was affected, which shouldn't happen
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), None)
        raise SystemError("PyThreadState_SetAsyncExc failed")

def force_terminate_thread(thread):
    """Forcibly terminate a Python thread"""
    _async_raise(thread.ident, SystemExit)

def monitor_threads():
    while True:
        current_time = time.time()
        for thread_id, info in list(thread_tracking.items()):
            thread, start_time = info['thread'], info['start_time']
            if current_time - start_time > threadlife_kill_time_s and thread_id in thread_warned_times:
                # If the thread was previously warned and has exceeded the kill time
                print(f"Forcefully terminating thread {thread_id}")
                force_terminate_thread(thread)
                del thread_tracking[thread_id]  # Remove from tracking
            elif current_time - start_time > threadlife_warn_time_s and thread_id not in thread_warned_times:
                # If the thread exceeds the warn time but hasn't been warned yet
                print(f"Warning thread {thread_id} to terminate")
                thread_terminate_signals[thread_id].set()
                thread_warned_times[thread_id] = current_time  # Mark as warned
        time.sleep(1)

def diff_strings(a, b):
    import difflib
    from wasabi import color
    output = []
    matcher = difflib.SequenceMatcher(None, a, b)
    for opcode, a0, a1, b0, b1 in matcher.get_opcodes():
        if opcode == "equal":
            output.append(a[a0:a1])
        elif opcode == "insert":
            output.append(color(b[b0:b1], fg=16, bg="green"))
        elif opcode == "delete":
            output.append(color(a[a0:a1], fg=16, bg="red"))
        elif opcode == "replace":
            output.append(color(b[b0:b1], fg=16, bg="green"))
            output.append(color(a[a0:a1], fg=16, bg="red"))
    return "".join(output)
    
def plot_setup():
    global fig
    global ax
    #plt.style.use('fivethirtyeight')
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

def avg_log(log=None, dur=None, prune=True):
    tot=0
    ctime = time.time()
    count = 0
    loglen=len(log)-1
    for i in range(loglen-1, -1, -1):
        val = log[i]['val']
        tim = log[i]['time']
        if ctime-tim >= dur: break
        tot += val
        count += 1
    if prune:
        for i in range(i, -1, -1):
            if ctime-tim >= log_secs:
                log.pop(i)

    if len(log) < 5:  # Not enough for averaging really.. I guess
        return 0

    avg = tot / count
    if args.verbose > 1:
        print(f"Total {count} items: {tot}.  Avg: {avg}")
    if avg == 0:
        print(f"Average is 0: ", log)
    return avg

def handle_alerts():
    ret_alert = None  # Return: None, 'bpm', 'spo2'
    if len(bpm_log) < 5: return None  # Need more data.

    # Disconnected
    #print(f"BPMlog: {bpm_log[-1]['val']}  SpO2: {o2_log[-1]['val']}")
    if bpm_log[-1]['val'] == 255 and o2_log[-1]['val'] == 127:
        if alert_on_disconnect:  # User does not desire disconnection alerts
            alerts.alert_disco(last_alert=last_alert)
        ret_alert = 'disco'
    else:
        bpm_avg = avg_log(log=bpm_log, dur=alert_avg_secs['bpm'])
        o2_avg = avg_log(log=o2_log, dur=alert_avg_secs['o2'])
        if args.verbose > 0:
            print("  BPM avg:", bpm_avg)
            print("   O2 avg:", o2_avg)
        if bpm_avg >= bpm_high:
            ret_alert = 'bpm'
            alerts.alert_bpm(bpm_avg, high=True, last_alert=last_alert)
        elif bpm_avg <= bpm_low:
            ret_alert = 'bpm'
            alerts.alert_bpm(bpm_avg, last_alert=last_alert)
        elif o2_avg <= o2_low:
            alerts.alert_o2(o2_avg, last_alert=last_alert)
            ret_alert = 'spo2'
    return ret_alert

dlog = open(stg.raw_dlog_fn, "a")

class MyDelegate(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        if args.verbose>1:
            print(f"handleNotification()")
        if args.eval and args.verbose > 0:
            print("Notif: %s" % data)
        global yvs, xvs
        global last_webupd_time
        ints = byte_array_to_int_array(data)
        if args.eval:
            print("Data:", ints)
            return
        lenny = len(ints)
        # 10-value line: 254 10 85 0 <BPM> <SPO2> 6 ? ? ?
        #  8-value line: {254 8 86} a 0 ? b c  <-- maybe trace
        #                 0   1 2   3 4 5 6 7

        # [10] 254 10 85 0 92 100 7 116 178 76
        # dlog.write(' '.join([str(i) for i in ints]) + "\n")

        if ints[0] == 254 and ints[1] == 8:  # 8-line format
            if args.verbose>1:
                print(f"{stg.plot_supp_indent}  0. Received data. ints={ints}", end='\r')
            ovals.set_from_ints(ints)
            ovals.plot(ints)

        elif ints[0] == 254 and ints[1] == 10:
            if len(ints) < 6: 
                print("Invalid data line (type 'BPM/SpO2'):", data)
            else:
                print(f"{stg.plot_supp_indent}  1. Received data. ints={ints}", end='\r')
                bpm, spo2 = ints[4], ints[5]
                bpm_log.append({'time': time.time(), 'val':bpm})
                o2_log.append({'time': time.time(), 'val':spo2})
                ovals.show_data(bpm=bpm, spo2=spo2)
                if stg.do_speech:
                    if time.time()-stg.last_say > 30:
                        # subprocess.run(stg.speech_synth_args, input=("" + str(int(bpm))).encode())
                        subprocess.run(stg.speech_synth_args + [str(int(bpm))])
                        stg.last_say=time.time()
                #print(f"BPM   : {bpm}  SpO2: {spo2}")
                alert_type = handle_alerts() # None, 'disconnected', 'bpm', 'spo2'
                if alert_type is not None:
                    # print(f"Alert type: {alert_type}")
                    # print("Ints:", ints)
                    # print(" BPM Log:", bpm_log)
                    # print("  O2 Log:", o2_log)
                    pass
                flogging.handle_filelog(bpm=bpm, spo2=spo2, time=time.time(), alert=alert_type)
                if alert_type == 'disco':
                    print("  DISCONNECTED!")
                else:
                    if alert_type is not None:
                        print(f"{stg.plot_supp_indent}  Some alert received. alert_type={alert_type}", end='\n')
                    if stg.do_web_lcd and time.time() - last_webupd_time > 3:
                        tracked_thread(target=display.display, 
                                       kwargs={'ip': stg.ip_lcd, 
                                               'bpm': bpm, 
                                               'spo2': spo2, 
                                               'alert': alert_type}, 
                                       life_limit=7)
                        last_webupd_time = time.time()
        elif ints[0] == 254 and ints[1] == 8:
            if len(ints) < 8: 
                print("Invalid data line (type 'extra data'):", data)
            else:
                print(f"  2. Received data. ints={ints}")
                q,r,s,t = ints[3], ints[5], ints[6], ints[7]
                yvs[0].append(q)
                yvs[1].append(r)
                yvs[2].append(s)
                yvs[3].append(t)
                xvs.append(len(xvs))
                # print("Length of plot data: ", len(yvs[0]))
                update_plot()
            # print("Other data")
            # for i in range(0,4):
            #     yvs[i] = yvs[i][-20:]
            cache=20
            if len(xvs) > cache:
                xvs = xvs[-cache:]
                for i in range(len(yvs)):
                    yvs[i] = yvs[i][-cache:]

        # print(f"[{lenny}]", " ".join([str(i) for i in ints]))
        if do_plot:
            plt.pause(0.01)
        if args.verbose>1:
            print("Updating keepalive...")

        update_keepalive()

# wrap display logic
def update_display(ip, bpm, spo2, alert_type):
    display.display(ip=ip, bpm=bpm, spo2=spo2, alert=alert_type)

def update_keepalive():
    # print(f"{bgblu}{bmag}Updating keepalive file: '{yel}{stg.keepalive_filename}{bgblu}{bmag}'{rst}")
    global last_keepalive_time
    if time.time() - last_keepalive_time > stg.keepalive_spacing_s:
        print(bgblu, whi, f"  Updating is due, yay!", rst)
        last_keepalive_time = time.time()
        try:
            pid = os.getpid()  # get current process ID
            print(bgblu, whi, f"    We are writing... supposed to...", rst)
            with open(stg.keepalive_filename, 'w') as file:
                print(bgblu, whi, f"      We really are...", rst)
                file.write(str(pid))
        except Exception as e:
            print(f"An error occurred while writing the PID to the keepalive file!")
            print(f"   File: {stg.keepalive_filename}")
            print(f"  Error: {e}")
    # else:
    #     print(bgblu, bred, f"  Not time for update", rst)

colors=[ '#eeac99', '#e06377', '#c83349', '#5b9aa0', '#d6d4e0',
    '#b8a9c9', '#622569',
    'red', 'gray', 'blue', 'green', 'cyan', 'magenta', 'yellow',
    ]
def animate(i, xs, ys):
    plt.cla()
    # axs[0].plot(xvs[0], yvs[0], color='red')
    # axs[0].plot(xvs[1], yvs[1], color='gray')
    for i in range(0, len(xvs)):
        plt.plot(xvs, yvs[i], color=colors[i])
    plt.xlabel('D')
    plt.ylabel('V')
    plt.title('PulseOx')
    #plt.gcf().autofmt_xdate()
    plt.tight_layout()
    print("ani!")
def update_plot():
    if do_plot:
        print("Updating plot:", yvs)
        plt.cla()
        for i in range(0, len(xvs)):
            for y in range(0, len(yvs)):
                try:
                    plt.plot(xvs, yvs[y], color=colors[y])
                    plt.pause(0.01)
                except:
                    import ipdb
                    ipdb.set_trace()


xvs=[]
yvs=[[], [], [], []]
# fig, axs=plt.subplots(1)
fig, axs=None, None
if do_plot:
    plot_setup()
    #ani = animation.FuncAnimation(fig, animate, fargs=(xvs, yvs), interval=1000)
# plt.ion()
# plt.show()

def bt_connect():
    global btdev
    print("Connecting...")
    #btdev = btle.Peripheral(args.mac_address)
    connected = False
    while connected is False:
        update_keepalive()
        try:
            print(f"Connecting with btle.Peripheral({args.mac_address})")
            btdev = btle.Peripheral(args.mac_address)
            print(f" btdev retrieved {btdev}")
            connected = True
        except btle.BTLEDisconnectError as e:
            print(f"{bgbro}{whi} Couldn't connect to {yel}{args.mac_address}{whi} {rst}")
            print("KNOWN Exception found:", e)
            print("KNOWN Exception type:", type(e))
            print(f"{whi}Trying again in 3 secs...{rst}")
            time.sleep(3)
    #        #import ipdb; ipdb.set_trace();
    #        #pass
        except Exception as e:
            print("Unknown Exception found:", e)
            print("Unknown Exception type:", type(e))
            # import ipdb; ipdb.set_trace();
            # pass
    for svc in btdev.services:
        print(" Service:", str(svc))

    print("Connected!")
    btdev.setDelegate(MyDelegate())
    print("Delegate set")

    # descs=btdev.getDescriptors()
    # for desc in descs:
    #     print(f"Desc {desc.handle}: {desc.uuid.getCommonName()}")
    #     descs

def main():
    # get args
    global bt_last_connect_try
    global args
    global final_mac

    args = get_args()
    if args.test_audio:
        print(f"{bcya}BPM high alert:")
        alerts.alert_bpm(140, high=True, test=True, last_alert=last_alert)
        time.sleep(.5)
        print(f"{bcya}BPM low alert:")
        alerts.alert_bpm(40, high=False, test=True, last_alert=last_alert)
        time.sleep(.5)
        print(f"{bcya}O2 low alert:")
        alerts.alert_o2(80, test=True, last_alert=last_alert)
        time.sleep(.5)
        print(f"{bcya}Disconnect alert:")
        alerts.alert_disco(test=True, last_alert=last_alert)
        time.sleep(.5)
        sys.exit()

    # Clear the screen probably
    if stg.do_web_lcd: display.init(ip=stg.ip_lcd)

    flogging.setup_log()
    ovals.setup()

    final_mac = args.mac_address

    print("Using bluetooth device MAC address:", final_mac)
    bt_connect()
    if stg.do_web_lcd:
        if not args.noclear:
            display.initial_clear()

    prev=None
    i=0
    while True:
        try:
            # print("Waiting for notifications:")
            btdev.waitForNotifications(1.0)
        #except BTLEDisconnectedError as e:
        #  (Error type: <class 'bluepy.btle.BTLEDisconnectError'> )
        except Exception as e:
            # if type(e) is btle.BTLEDisconnectError:
            #     print("We disconnected.  Ignoring it. Not sure what will happen now")
            # else:
                #sys.exit()
                if time.time() - bt_last_connect_try > bt_reconnect_delay:
                    print("Unknown error (it's not BTLEDisconnectError). NOT Re-connecting:")
                    print(" (Error:", e, ")")
                    print(" (Error type:", type(e), ")")
                    print("Disconnecting...", flush=True)
                    btdev.disconnect()
                    print("Setting last connect try to 'right now':", flush=True)
                    bt_last_connect_try = time.time()
                    print("Reconnecting...", flush=True)
                    bt_connect()
                    print("Reconnected!")
                else:
                    print("Error caught:", e)
                pass
                # raise e
    while True:
        cur = "==============================================\n"
        i += 1
        cur += f"{i}\n"
        _ = btdev.getServices()
        for svc in list(btdev.services):
            cur += f"Service: UUID: {svc.uuid}\n"
            print("Cur: ", cur)
            # ipdb.set_trace()
            chars = svc.getCharacteristics()
            for char in chars:
                common = char.uuid.getCommonName()
                try:
                    read = char.read()
                    cur += f" Char[{common}] Handle: {char.valHandle}  Read: {read}\n"
                except KeyboardInterrupt: sys.exit()
                except:
                    # cur += f" Char[{common}] Handle: {char.valHandle}  Read: -\n"
                    print("Some error caught in char.read()")
                    pass
        if prev is None:
            print(cur)
        else:
            diff = diff_strings(prev, cur)
            print(diff)
        prev=cur


def byte_array_to_int_array(value):
    # Raw data is hexstring of int values, as a series of bytes, in little endian byte order
    # values are converted from bytes -> bytearray -> int
    # e.g., b'\xb8\x08\x00\x00' -> bytearray(b'\xb8\x08\x00\x00') -> 2232

    # print(f"{sys._getframe().f_code.co_name}: {value}")

    value = bytearray(value)
    value = [int(i) for i in value]
    return value

def get_args():
    arg_parser = ArgumentParser(description="BLE Pulse Oximeter Monitor")
    arg_parser.add_argument(
        '-a', '--mac_address', help="MAC address of PulseOx device (regex)",
        default=stg.pomac)
    arg_parser.add_argument(
        '-v', '--verbose', help="Increase verbosity", action='count', default=0)
    arg_parser.add_argument(
        '-t', '--test-audio', help="Test the audio alarms", action='store_true')
    arg_parser.add_argument(
        '-C', '--noclear', help="Clear LCD at start", action='store_true')
    arg_parser.add_argument(
        '-e', '--eval', help="Eval bluetooth device data only (use with -a to check out a new device)", action='store_true')
    args = arg_parser.parse_args()
    return args

if __name__ == "__main__":
    monitor_thread = threading.Thread(target=monitor_threads)
    monitor_thread.start()
    main()

# vim: et
