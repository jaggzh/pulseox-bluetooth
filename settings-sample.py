# Many settings are still in the main .py, not here.

# pomac:  (pulseox mac): MAC addr of pulseox/device
#  Can get with:
#   timeout 5 bluetoothctl scan on   # Update cached devices (or something)
#                                    #  ('timeout 5' kills it after 5 seconds)
#   bluetoothctl devices             # List'em
pomac='BA:03:C4:FF:FF:FF'
do_logging=True              # set logdir below
do_logging=False             # set logdir below

# For an extra WiFi LCD display
# (project at: https://github.com/jaggzh/esp8266-wifi-lcd-touch )
do_web_lcd=True              # Hit LCD display with bpm and spo2
do_web_lcd=False
ip_lcd="192.168.3.10"        # Not used if do_web_display is False
lcd_w=320
lcd_h=240

alert_audio=False            # Make a pysine noise when vitals out of range
alert_audio=True


## LOG Settings
# logdir: Will be created, if it doesn't exist, with user-access only (0700)
logdir='/home/me/logs/pulseox-john'
logfreq=60                   # Seconds: Don't log each reading

# Speech synthesis for additional alert info
# (This takes text via stdin)
speech_synth_args=['/usr/bin/festival', '--tts']

# Data format/Model info should eventually be here, if others add
# more models

# vim: set et
