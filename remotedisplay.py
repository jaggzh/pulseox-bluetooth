import requests
import settings
import ipdb
import sys
import os
from bansi import * # Yes, that's right, *. Free colors everywhere!

try: import usercallbacks
except: pass

lcd_ip=None # Assigned at init()
initial_clear_done=False
verbose=0

boxw=312
boxh=79
boxx=4
boxy=10
boxrad=5
boxcol='r=0'
boxbordcol='r=200'
tx=10
ty=10
tsize=12
last_alert=False
last_pulseox_strlen=-1

tsize0_xadv=6  # Default Adafruit GFX fixed-width font size 0 glyph pixel width
tsize0_yadv=8

def text_escape(txt):
	txt=txt.replace('\n','%0A')
	txt=txt.replace(' ','+')
	txt=txt.replace(',','')       # Killing commas for now. :(
	return txt

# textbox() draw text in a box
# min size is 1
def textbox(rad=0,
	        padx=0,
	        pady=0,
	        *,
	        size=None,
	        txt=None,
	        x=None,
	        y=None,
	        color=None,
	        bgcolor=None,
	        #bordercolor=None,
	        ):
	txt = txt.strip()
	linecnt = txt.count('\n')+1
	if verbose>1: print("Line count:", linecnt)
	maxlinelen = max([len(s) for s in txt.split('\n')])
	if verbose>1: print("Maxlinelen:", maxlinelen)
	width = maxlinelen * tsize0_xadv * size
	if verbose>1: print("width:", width)
	height = linecnt * tsize0_yadv * size
	if verbose>1: print("height:", height)
	width  += padx*2 # - size  # Remove the glyph-spacing pixel from padding
	if verbose>1: print("width:", width)
	height += pady*2 # - size
	if verbose>1: print("height:", height)
	tx = x + padx
	if verbose>1: print("tx:", tx)
	ty = y + pady
	if verbose>1: print("ty:", ty)
	return f"col={bgcolor}&frect={x},{y},{width},{height},{rad}&" + \
	       f"tfg={color}&" + \
	       f"txt=s={size},x={tx},y={ty},t={text_escape(txt)}", \
				width, height

# textbox_cmd = textbox(
# 		size = 9,
# 		txt = f"88qqq",
# 		x = tx,
# 		y = ty,
# 		color='r=255,g=205,b=255',
# 		bgcolor='r=255',
# 		padx=2,
# 		pady=1,
# 	)
# print("Textbox cmd:")
# print(textbox_cmd)
# import sys
# sys.exit()

def init(ip=None, error=False):
	global lcd_ip
	lcd_ip=ip
	#    ip: IP address of LCD display
	# error: default False: don't crash if the request fails
	#                 True: crash on web failure (raise exception)
	# Used to clears the screen, but now it doesn't
	pass

def initial_clear():
	global initial_clear_done
	if not initial_clear_done:
		try:
			s = f"http://{lcd_ip}/cs?cls=r=0"
			r = requests.get(s)
		except:
			if error: raise
			pass
		initial_clear_done = True

def display(
		ip=None,
		bpm=None,
		spo2=None,
		verbose=0,
		alert=False,
		terminate_signal=None):  # None, 'bpm', 'spo2'
    # If you do any loops, you should test:
    #     while not terminate_signal.is_set(): to break out
    # OTHERWISE our monitor_threads may kill you
	global last_alert, last_pulseox_strlen
	#import os
	#os.system(f"moztts 'Your heart rate is {bpm}'")
	lenstr_s=str(bpm) + str(spo2)
	lenstr = len(lenstr_s)
	ltsize=tsize
	space=''
	clear=False
	alert_border=False
	double_line=False
	#print(bgre, "Last alert:", last_alert, rst)
	#print(yel, f"Str len: {lenstr}, str: {lenstr_s}", rst)
	#print(f"{yel}BPM: {bred}{bpm}{yel}, SpO2: {bcya}{spo2){rst}")

	# Adjust fonts/layout for length and alert-status
	if last_pulseox_strlen != lenstr:
		clear=True
	if lenstr > 4:
		double_line=True
	if alert is not None:  # ALERT is TRUE (not True-true, but some string value)
		if verbose>0: print("Sending alert display!");
		double_line=True
		ltsize += 1
		if not last_alert: clear = True
		last_alert = True
		alert_border = True
	else:
		double_line=True
		ltsize += 2
		if last_alert: clear = True
		last_alert = False
	if double_line:
		space='%0A'

	if verbose>0: print("  (updating web)")
	# Displays a colored box/strip with the values in it
	#s=f"http://{settings.ip_lcd}/cs?col=r=35&frect=4,47,312,83,1&tfg=r=100,g=255,b=255&txt=x=10,y=10,s=5,t=%0a++BPM&tfg=r=255,g=95,b=95&txt=t=+{bpm}&tfg=r=100,g=255,b=255&txt=t=%0a+SpO2+&tfg=r=150,g=255,b=255&txt=t={spo2}"
	#s=f"http://{ip}/cs?col=r=35&frect=4,47,312,83,1&tfg=r=100,g=255,b=255&txt=x=10,y=10,s=5,t=%0a++BPM&tfg=r=255,g=95,b=95&txt=t=+{bpm}&tfg=r=100,g=255,b=255&txt=t=%0a+SpO2+&tfg=r=150,g=255,b=255&txt=t={spo2}")
	# Returns box width and height too
	curx = tx
	cury = ty
	textbox_bpm, bw, bh = textbox(
			size = ltsize,
			txt = f"{bpm}",
			x = curx,
			y = cury,
			color='r=255,g=255,b=255',
			bgcolor='r=150',
			padx=2, pady=1,
		)

	if not double_line: curx += bw
	else: cury += bh

	textbox_o2, bw, bh = textbox(
			size = ltsize,
			txt = f"{spo2}",
			x = curx,
			y = cury,
			color='r=255,g=255,b=255',
			bgcolor='r=0',
			padx=2, pady=1,
		)
	if verbose>0: print("Textbox cmd bpm:", textbox_bpm)
	if verbose>0: print("Textbox cmd  o2:", textbox_o2)
	if clear:
		clear_str = 'cls=r=0&'
	else: clear_str = ''

	bwidth=30
	alert_border_str=''
	if alert_border:
		pass
		# Red filled box, then an inset black filled box (to make a border)
		alert_border_str= \
				f'col=r=255&frect=0,0,{settings.lcd_w-1},{settings.lcd_h-1},0&' + \
				f'col=r=0&frect={bwidth},{bwidth},{settings.lcd_w-bwidth*2-1},{settings.lcd_h-bwidth*2-1},5&'
	# Make sure clear_str is first \/~~~~~
	s = f"http://{ip}/cs?" + \
			clear_str + \
			alert_border_str + \
			textbox_bpm + "&" + textbox_o2;

	################################################################
	## Actual drawing calls done here
	
	# When not alerting, call an optional user-callback
	# (I draw a heart on our LCD display)
	if not alert_border:
		try: usercallbacks.pre_display_normal()
		except: pass
	if verbose>1: print("Request:", s)
	# Here is the actual web hit to the LCD
	r = requests.get(s)
	# When not alerting, call an optional user-callback
	if not alert_border:
		try: usercallbacks.post_display_normal()
		except: pass
	#os.system("livmsg-txt-box-time");
	## / END of actual drawing calls
	################################################################

	last_pulseox_strlen = lenstr
	# last_alert = <-- we record the last alert, above

	# sys.exit()
	# s = f"http://{ip}/cs?" + \
	# 	f"col={boxcol}&frect={boxx},{boxy},{boxw},{boxh},{boxrad}&" + \
	# 	f"col={boxbordcol}&rect={boxx},{boxy},{boxw},{boxh},{boxrad}&" + \
	# 	f"tfg=r=255,g=95,b=95&" + \
	# 	 f"txt=s={ltsize},x={tx},y={ty},t={bpm}{space}&" + \
	# 	f"tfg=r=150,g=255,b=255&" + \
	# 	 f"txt=t={spo2}"
	# if verbose>1: print(s)
	# r = requests.get(s)
