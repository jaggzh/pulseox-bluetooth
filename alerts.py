import settings as stg
import volpy
from bansi import *
import time
import pysine      # Used for playing an alert tone

def alert_bpm(avg, high=False, test=False, last_alert=None):
    pfp(bred, "WARNING. BPM out of range!!! ", avg, rst)
    #import playsound
    #playsound.playsound('sample.mp3')
    freq = stg.alert_bpm_low_freq if not high else stg.alert_bpm_high_freq
    if time.time()-last_alert['bpm'] > stg.alert_delay_secs['bpm']:
        if not test:
            last_alert['bpm']=time.time()
        if stg.alert_audio:
            play_freq(freq, dur=1.0)
        # BMP is our default; we don't bother to keep saying "bee pee em "
        # subprocess.run(stg.speech_synth_args, input=("bee pee em " + str(int(avg))).encode())
        if stg.do_speech:
            # subprocess.run(stg.speech_synth_args, input=("" + str(int(avg))).encode())
            subprocess.run(stg.speech_synth_args + [str(int(avg))])

def alert_o2(avg, test=False, last_alert=None):
    pfp(bred, "WARNING. SpO2 out of range!!! ", avg, rst)
    if time.time()-last_alert['o2'] > stg.alert_delay_secs['o2']:
        if not test:
            last_alert['o2']=time.time()
        if stg.alert_audio:
            play_freq(stg.alert_o2_freq)
        if stg.do_speech:
            subprocess.run(stg.speech_synth_args, input=("oxygen " + str(int(avg))).encode())

def alert_disco(test=False, last_alert=None):
    pfp(bmag, "WARNING. Disconnected", rst)
    if time.time()-last_alert['disco'] > stg.alert_delay_secs['disco']:
        if stg.alert_audio:
            play_freq(stg.alert_disco_freq)
        if not test:
            last_alert['disco']=time.time()
        if stg.do_speech:
            subprocess.run(stg.speech_synth_args, input="disconnected".encode())

def play_freq(freq, dur=1.0):
    if volpy is not None:
        print(f"Current volume: {volpy.volget()}")
        volpy.volsave()
        volpy.volset(stg.alert_volume_start)
        print(f"Current volume after set: {volpy.volget()}")
    pysine.sine(frequency=freq, duration=dur)
    if volpy is not None:
        volpy.volrestore()

