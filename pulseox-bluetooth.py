#!/usr/bin/env python
#    Author: jaggz.h who is at gmail.com
#      Date: 2021-12-04
# Copyright: GPL 3.0 https://www.gnu.org/licenses/gpl-3.0.en.html

# Inspired by:
# https://anaesthetics.app/blog/posts/2020/bluetooth/

# Currently this only handles the data sent by this PulseOx
# Wellue Fingertip Pulse Oximeter, Blood Oxygen Saturation Monitor
#  with Batteries for Wellness Use Bluetooth, Black 
# https://www.amazon.com/gp/product/B087Q724QM/

#import playsound  # Not using right now
import pysine      # Used for playing an alert tone
import settings
from bansi import * # Yes, that's right, *. Free colors everywhere!
#pysine.sine(frequency=440.0, duration=1.0)

######################################################################3
## Configuration variables:

#pomac='BA:03:C4:2C:4D:60'
alert_bpm_audiofile=""               # not used; only using pysine.sine()
alert_on_disconnect=True             # If sensor gives bpm=255, spo2=127
alert_on_disconnect=False

# bpm and o2 alert limits and time average length
# (At present the plan is: If the avg over this time of data samples
#  exceeds the limits, alert)
bpm_low=52
bpm_high=93  # 4 testing
bpm_high=120
o2_low=92
bpm_alert_sustained_secs=5  # samples averaged over this seconds
alert_bpm_delay_secs=15     # Delay between alarms
last_alert_bpm=0            # don't change. tracks time.

o2_low=96    # 4 testing
o2_low=97
o2_low=93
o2_low=92
o2_alert_sustained_secs=5
alert_o2_delay_secs=15      # Delay between alarms
last_alert_o2=0             # don't change. tracks time.
# Internal logs
bpm_log=[]  # []['time','val']
o2_log=[]
log_hours=6                 # Could be a lot of data points. We keep each sample
                            #  currently.
log_mins=log_hours*60
log_secs=log_mins*60

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

from bluepy import btle  # linux only (no mac)

do_plot=True
do_plot=False
if do_plot:
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation

last_webupd_time=0
if settings.do_web_lcd:
    import remotedisplay as display

import sys # for exit()

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

def avg_log(log=None, dur=None):
    tot=0
    lenny=len(log)-1
    if lenny < 1: return 0
    ctime = time.time()
    count = 0
    for i in range(lenny-1, -1, -1):
        val = log[i]['val']
        tim = log[i]['time']
        if ctime-tim > dur: break
        tot += val
        count += 1
    if count < 1: return 0
    avg = tot / count
    if args.verbose > 1:
        print(f"Total {count} items: {tot}.  Avg: {avg}")
    return avg

def alert_bpm(avg):
    global last_alert_bpm
    pfp(bred, "WARNING. BPM out of range!!! ", avg, rst)
    #import playsound
    #playsound.playsound('sample.mp3')
    if time.time()-last_alert_bpm > alert_bpm_delay_secs:
        if settings.alert_audio:
            pysine.sine(frequency=440.0, duration=1.0)
        last_alert_bpm=time.time()

def alert_o2(avg):
    global last_alert_o2
    pfp(bred, "WARNING. SpO2 out of range!!! ", avg, rst)
    if time.time()-last_alert_o2 > alert_o2_delay_secs:
        if settings.alert_audio:
            pysine.sine(frequency=540.0, duration=1.0)
        last_alert_o2=time.time()

def handle_alerts():
    ret_alert = None  # Return: None, 'bpm', 'spo2'
    if len(bpm_log) < 5: return  # Need more data.

    if not alert_on_disconnect:  # User does not desire disconnection alerts
        if bpm_log[-1] == 255 and o2_log[-1] == 127:
            return None
    bpm_avg = avg_log(log=bpm_log, dur=bpm_alert_sustained_secs)
    o2_avg = avg_log(log=o2_log, dur=o2_alert_sustained_secs)
    if args.verbose > 0:
        print("  BPM avg:", bpm_avg)
        print("   O2 avg:", o2_avg)
    if bpm_avg >= bpm_high or bpm_avg <= bpm_low:
        alert_bpm(bpm_avg)
        ret_alert = 'bpm'
    elif o2_avg <= o2_low:
        alert_o2(o2_avg)
        ret_alert = 'spo2'
    return ret_alert

class MyDelegate(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        # print("Notif: %s" % data)
        global yvs, xvs
        global last_webupd_time
        ints = byte_array_to_int_array(data)
        lenny = len(ints)
        # 10-lines format: 254 10 85 0 <BPM> <SPO2> 6 ? ? ?
        #  8-lines format: {254 8 86} ? 0 ? ? ?

        # [10] 254 10 85 0 92 100 7 116 178 76

        if ints[0] == 254 and ints[1] == 10:
            if len(ints) < 6: 
                print("Invalid data line (type 'BPM/SpO2'):", data)
            else:
                bpm, spo2 = ints[4], ints[5]
                bpm_log.append({'time': time.time(), 'val':bpm})
                o2_log.append({'time': time.time(), 'val':spo2})
                alert_type = handle_alerts() # None, 'bpm', 'spo2'
                print(f"BPM: {bpm}  SpO2: {spo2}")
                if bpm == 255 and spo2 == 127:
                    print("  DISCONNECTED!")
                else:
                    if settings.do_web_lcd and time.time() - last_webupd_time > 5:
                        display.display(ip=settings.ip_lcd, 
                                        bpm=bpm,
                                        spo2=spo2,
                                        alert=alert_type)
                        last_webupd_time = time.time()
        elif ints[0] == 254 and ints[1] == 8:
            if len(ints) < 8: 
                print("Invalid data line (type 'extra data'):", data)
            else:
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
    #btdev = btle.Peripheral(final_mac)
    btdev = btle.Peripheral(args.mac_address)
    print("Connected!")
    btdev.setDelegate(MyDelegate())
    # print("Delegate set")

    # descs=btdev.getDescriptors()
    # for desc in descs:
    #     print(f"Desc {desc.handle}: {desc.uuid.getCommonName()}")
    #     descs

def main():
    # get args
    global bt_last_connect_try
    global args
    global final_mac

    # Clear the screen probably
    if settings.do_web_lcd: display.init(ip=settings.ip_lcd)

    args = get_args()
    final_mac = args.mac_address
    print("Using bluetooth device MAC address:", final_mac)
    bt_connect()

    prev=None
    i=0
    while True:
        try:
            # print("Waiting for notifications:")
            btdev.waitForNotifications(1.0)
        #except BTLEDisconnectedError as e:
        except Exception as e:
            # if type(e) is btle.BTLEDisconnectError:
            #     print("We disconnected.  Ignoring it. Not sure what will happen now")
            # else:
                #sys.exit()
                if time.time() - bt_last_connect_try > bt_reconnect_delay:
                    print("Unknown error (it's not BTLEDisconnectError). Re-connecting:")
                    print(" (Error:", e, ")")
                    bt_last_connect_try = time.time()
                    bt_connect()
                    print("Reconnected!")
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
        '-a', '--mac_address', help="MAC address of PulseOx device",
        default=settings.pomac)
    arg_parser.add_argument(
        '-v', '--verbose', help="Increase verbosity", action='count', default=0)
    args = arg_parser.parse_args()
    return args

# [8] 254 8 86 17 0 3 222 80
# [8] 254 8 86 17 0 3 223 81
# [8] 254 8 86 18 0 3 224 83
# [8] 254 8 86 21 0 3 225 87
# [8] 254 8 86 26 0 4 226 94
# [8] 254 8 86 34 0 5 227 104
# [8] 254 8 86 44 0 7 228 117
# [8] 254 8 86 54 0 8 229 129
# [8] 254 8 86 63 0 9 230 140
# [8] 254 8 86 71 0 11 231 151
# [8] 254 8 86 75 0 11 232 156
# [8] 254 8 86 77 0 12 233 160
# [8] 254 8 86 77 0 12 234 161
# [8] 254 8 86 74 0 11 235 158
# [8] 254 8 86 70 0 11 236 155
# [10] 254 10 85 0 73 98 7 84 230 75
# [8] 254 8 86 65 0 10 237 150
# [8] 254 8 86 60 0 9 238 145
# [8] 254 8 86 55 0 8 239 140
# [8] 254 8 86 50 0 8 240 136
# [8] 254 8 86 46 0 7 241 132
# [8] 254 8 86 43 0 6 242 129
# [8] 254 8 86 40 0 6 243 127
# [8] 254 8 86 38 0 6 244 126
# [8] 254 8 86 37 0 6 245 126
# [8] 254 8 86 37 0 6 246 127
# [8] 254 8 86 36 0 5 247 126
# [8] 254 8 86 36 0 5 248 127
# ...
# [8] 254 8 86 35 0 5 37 171
# [8] 254 8 86 35 0 5 38 172
# [8] 254 8 86 34 0 5 39 172
# [8] 254 8 86 33 0 5 40 172
# [10] 254 10 85 0 74 98 6 199 52 12
# [8] 254 8 86 32 0 5 41 172
# [8] 254 8 86 31 0 5 42 172
# [8] 254 8 86 31 0 5 43 173
# [8] 254 8 86 30 0 5 44 173
# [8] 254 8 86 30 0 5 45 174
# [8] 254 8 86 31 0 5 46 176
# [8] 254 8 86 33 0 5 47 179
# [8] 254 8 86 36 0 5 48 183
# [8] 254 8 86 40 0 6 49 189
# [8] 254 8 86 46 0 7 50 197
# [8] 254 8 86 52 0 8 51 205
# [8] 254 8 86 57 0 9 52 212
# [16] 254 8 86 61 0 9 53 217 254 8 86 64 0 10 54 222
# [8] 254 8 86 65 0 10 55 224
# [8] 254 8 86 64 0 10 56 224
# [8] 254 8 86 63 0 9 57 223
# [8] 254 8 86 60 0 9 58 221
# [8] 254 8 86 57 0 9 59 219
# [8] 254 8 86 54 0 8 60 216
# [8] 254 8 86 51 0 8 61 214
# [8] 254 8 86 48 0 7 62 211
# [8] 254 8 86 46 0 7 63 210
# [8] 254 8 86 44 0 7 64 209
# [8] 254 8 86 42 0 6 65 207
# [8] 254 8 86 41 0 6 66 207

# 10-lines format: 254 10 85 0 <BPM> <SPO2> 6 ? ? ?
#  8-lines format: {254 8 86} ? 0 ? ? ?
# [10] 254 10 85 0 72 97 6 167 44 225
# [10] 254 10 85 0 72 98 6 98 45 158
# [10] 254 10 85 0 72 98 6 7 46 68
# [10] 254 10 85 0 72 98 6 57 47 119
# [10] 254 10 85 0 72 98 6 87 48 150
# [10] 254 10 85 0 72 98 6 87 49 151
# [10] 254 10 85 0 72 98 6 87 50 152
# [10] 254 10 85 0 74 98 6 115 51 183
# [10] 254 10 85 0 74 98 6 199 52 12
# [10] 254 10 85 0 74 98 6 199 53 13
# [10] 254 10 85 0 74 98 6 183 54 254
# [10] 254 10 85 0 75 98 6 181 55 254
# [10] 254 10 85 0 75 98 6 109 56 183
# [10] 254 10 85 0 78 98 6 109 57 187
# [10] 254 10 85 0 78 98 6 59 58 138
# [10] 254 10 85 0 84 97 6 37 59 122
# [10] 254 10 85 0 84 97 6 13 60 99
# [10] 254 10 85 0 89 98 6 36 61 129
# [10] 254 10 85 0 89 98 6 36 62 130
# [10] 254 10 85 0 90 97 6 36 63 131
# [10] 254 10 85 0 90 97 6 36 64 132
# [10] 254 10 85 0 90 97 6 45 65 142
# [10] 254 10 85 0 90 97 6 60 66 158
# [10] 254 10 85 0 87 97 6 60 67 156
# [10] 254 10 85 0 87 97 6 39 68 136

if __name__ == "__main__":
    main()

# vim: et
