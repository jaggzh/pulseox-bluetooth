import requests
import settings
import ipdb
import sys
from bansi import * # Yes, that's right, *. Free colors everywhere!

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
	print("Line count:", linecnt)
	maxlinelen = max([len(s) for s in txt.split('\n')])
	print("Maxlinelen:", maxlinelen)
	width = maxlinelen * tsize0_xadv * size
	print("width:", width)
	height = linecnt * tsize0_yadv * size
	print("height:", height)
	width  += padx*2 # - size  # Remove the glyph-spacing pixel from padding
	print("width:", width)
	height += pady*2 # - size
	print("height:", height)
	tx = x + padx
	print("tx:", tx)
	ty = y + pady
	print("ty:", ty)
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
	#    ip: IP address of LCD display
	# error: default False: don't crash if the request fails
	#                 True: crash on web failure (raise exception)
    # Just clears the screen
	try:
		s = f"http://{ip}/cs?cls=r=0"
		r = requests.get(s)
	except:
		if error: raise
		pass

def display(
		ip=None,
		bpm=None,
		spo2=None,
		verbose=0,
		alert=False):  # None, 'bpm', 'spo2'
	lenstr=bpm + spo2
	ltsize=tsize
	space=''
	clear=False
	alert_border=False
	global last_alert
	print(bgre, "Last alert:", last_alert, rst)

	# Adjust fonts/layout for length and alert-status
	if alert is not None:  # ALERT is TRUE (not True-true, but some string value)
		print("Sending alert display!");
		space='%0A'
		ltsize += 1
		if not last_alert: clear = True
		last_alert = True
		alert_border = True
	else:
		if lenstr < 5: space='+'
		elif lenstr > 5: ltsize -= 1
		space='%0A'
		if last_alert: clear = True
		last_alert = False

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
			bgcolor='r=100',
			padx=2, pady=1,
		)
	if alert is None:
		curx += bw
	else:
		cury += bh
	textbox_o2, bw, bh = textbox(
			size = ltsize,
			txt = f"{spo2}",
			x = curx,
			y = cury,
			color='r=255,g=255,b=255',
			bgcolor='r=0',
			padx=2, pady=1,
		)
	print("Textbox cmd bpm:", textbox_bpm)
	print("Textbox cmd  o2:", textbox_o2)
	if clear: clear_str = 'cls=r=0&'
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
	if verbose>1: print("Request:", s)
	r = requests.get(s)
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

