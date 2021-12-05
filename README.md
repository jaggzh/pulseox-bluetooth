## Monitor a Bluetooth PulseOx's Data from Linux

See comments at top of code.

## Screenshots

Default text output (with the alert ranges set low to force it).

![Text console display](img/text-output.png)

It's unlikely you have this LCD project set up. It's a separate
ESP8266 WiFi project I use for notices in our livingroom, and
this project can display the BPM/SpO2 on it. *This project does not
currently display this graphics image*

![External (extra) LCD Display, if Available)](img/lcd-display.jpg)

[https://github.com/jaggzh/esp8266-wifi-lcd-touch](https://github.com/jaggzh/esp8266-wifi-lcd-touch)

## Usage

1. Copy settings-sample.py to settings.py and edit
1. Get a compatible pulseox. It's programmed, currently, to support the data coming from a **"Wellue Fingertip Pulse Oximeter, Blood Oxygen Saturation Monitor with Batteries for Wellness Use Bluetooth, Black"** [https://www.amazon.com/gp/product/B087Q724QM/](https://www.amazon.com/gp/product/B087Q724QM/).  (I have no relation to them.)
1. Set MAC address to the pulseox (see settings file)
1. `pip install bluepy pysine`
1. Run ./pulseox-bluetooth.py

## Dependencies

1. Python module: `bluepy` (required!)
1. Python module: `pysine` (used for audio alert tones, can remove in code)
