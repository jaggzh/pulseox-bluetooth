# Copy this to usercallbacks.py, and edit if you need some events called

def pre_display_normal():
	print("This is called before the BPM/O2 drawing is done")
	#os.system("lcd-notice -s 35 /mnt/shared/decorations/heart-metallic.png -y 20 -x 200 >/dev/null 2>/dev/null");

def post_display_normal():
	#print("This is called after the BPM/O2 drawing is done")
	pass

# vim: set et
