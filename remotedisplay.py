import requests
import settings

boxw=312
boxh=79
boxx=4
boxy=10
boxrad=5
boxcol='r=0'
boxbordcol='r=200'
tx=10
ty=10
tsize=9

def display(
		ip=None,
		bpm=None,
		spo2=None,
		verbose=0):
	lenstr=bpm + spo2
	ltsize=tsize
	if lenstr > 5: ltsize -= 1
	if verbose>0: print("  (updating web)")
	# Displays a colored box/strip with the values in it
	#s=f"http://{settings.ip_lcd}/cs?col=r=35&frect=4,47,312,83,1&tfg=r=100,g=255,b=255&txt=x=10,y=10,s=5,t=%0a++BPM&tfg=r=255,g=95,b=95&txt=t=+{bpm}&tfg=r=100,g=255,b=255&txt=t=%0a+SpO2+&tfg=r=150,g=255,b=255&txt=t={spo2}"
	#s=f"http://{ip}/cs?col=r=35&frect=4,47,312,83,1&tfg=r=100,g=255,b=255&txt=x=10,y=10,s=5,t=%0a++BPM&tfg=r=255,g=95,b=95&txt=t=+{bpm}&tfg=r=100,g=255,b=255&txt=t=%0a+SpO2+&tfg=r=150,g=255,b=255&txt=t={spo2}")
	s = f"http://{ip}/cs?" + \
		f"col={boxcol}&frect={boxx},{boxy},{boxw},{boxh},{boxrad}&" + \
		f"col={boxbordcol}&rect={boxx},{boxy},{boxw},{boxh},{boxrad}&" + \
		f"tfg=r=255,g=95,b=95&txt=s={ltsize},x={tx},y={ty},t={bpm}&" + \
		f"tfg=r=150,g=255,b=255&txt=t={spo2}"
	if verbose>1: print(s)
	r = requests.get(s)
