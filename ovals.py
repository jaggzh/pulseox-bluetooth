import pyfiglet
import os # get_terminal_size
import sys
from bansi import *
import signal # SIGWINCH

def resize_handler(signum, frame):
    global cols,rows
    if have_term:
        print("Resize happened")
        cols, rows = os.get_terminal_size()
        print(f"New size: {cols} x {rows}")
        set_term_size_dependencies()

# Settings
widthperc = .25   # How much of screen to take up, left-right, with the SpO2 trace
show_every_n_samples = 3  # Maintained by sampctr

# More for internal use
ovals=dict()
ia=3; ib=6; ic=7  # Indexes into integer list of other data
sampctr=0      # Counter. Don't touch me. For show_every_n_samples
show_data_toggle = False # This is NOT an option. It toggles to flip the data output
have_term = False

def bpm_to_color(bpm):
    # Define our color palette
    blue = (0, 0, 255)
    light_pink = (255, 182, 193)
    hot_pink = (255, 105, 180)
    red = (255, 0, 0)

    # Check the bpm and assign the color
    if bpm <= 55:
        color = blue
    elif 55 < bpm < 90:
        color = light_pink
    elif 90 <= bpm < 120:
        # Calculate the gradient between light_pink and hot_pink based on bpm
        t = (bpm - 90) / 30  # This gives a value between 0 and 1
        color = (
            int(light_pink[0] + t * (hot_pink[0] - light_pink[0])),
            int(light_pink[1] + t * (hot_pink[1] - light_pink[1])),
            int(light_pink[2] + t * (hot_pink[2] - light_pink[2])),
        )
    else:
        color = red

    # Convert the RGB value to a terminal escape sequence for 24-bit color
    terminal_sequence = f"\033[38;2;{color[0]};{color[1]};{color[2]}m"
    return terminal_sequence

def setup():
    global have_term
    global ovals
    global cols,rows
    global bpmcola, bpmcolb
    ovals=dict()
    ovals['a']=dict()
    ovals['b']=dict()
    ovals['c']=dict()
    for i in ovals.keys():
        ovals[i]['min'] = 256
        ovals[i]['max'] = -256
    if not sys.stdout.isatty():
        print(bred, "ovals: No TTY found to output plot", rst)
        cols,rows = 2,2
    else:
        cols,rows = os.get_terminal_size()
        have_term = True
    set_term_size_dependencies()
    signal.signal(signal.SIGWINCH, resize_handler)

def set_term_size_dependencies():
    global plotcola, plotcolb
    plotcola = 1
    plotwidth = int(cols * widthperc - 3)
    plotcolb = plotcola+plotwidth

def set_from_ints(ints):
    #  8-value line: {254 8 86} a 0 ? b c  <-- maybe trace
    #                 0   1 2   3 4 5 6 7
    if ints[ia] < ovals['a']['min']: ovals['a']['min'] = ints[ia]
    if ints[ia] > ovals['a']['max']: ovals['a']['max'] = ints[ia]
    if ints[ib] < ovals['b']['min']: ovals['b']['min'] = ints[ib]
    if ints[ib] > ovals['b']['max']: ovals['b']['max'] = ints[ib]
    if ints[ic] < ovals['c']['min']: ovals['c']['min'] = ints[ic]
    if ints[ic] > ovals['c']['max']: ovals['c']['max'] = ints[ic]

def show_data(bpm=None, spo2=None):
    global show_data_toggle
    if not have_term: return
    col=40
    width=cols-col-1
    # fraktur aquaplan char1___ future_7
    fig = pyfiglet.Figlet(font="aquaplan", width=width)
    #tarr = fig.renderText(f"BPM {bpm}, SPO2 {sp02}

    # if not show_data_toggle: tarr = fig.renderText(f"BPM {bpm}")
    # else:                    tarr = fig.renderText(f"OX {spo2}")

    try:
        if not show_data_toggle: tarr = fig.renderText(f"BPM {bpm}")
        else:                    tarr = fig.renderText(f"OX {spo2}")
    except: # ^^ renderText() fails if the width was too small
            #    Let's set some tiny silly text instead:
        if not show_data_toggle: tarr = f"BPM {bpm}"
        else:                    tarr = f"OX {spo2}"
        
    show_data_toggle = not show_data_toggle
    tarr = tarr.replace('#', '▓')
    tarr = tarr.split('\n')
    height = len(tarr)
    print(bpm_to_color(bpm), end='')
    for i,t in zip(range(height), tarr):
        gxy(col, rows-height+i)
        print(t, end='')
    gbottomleft()

def gbottomleft():
    if not have_term: return
    gxy(1,rows)

def plot(ints):
    global sampctr
    if not have_term: return
    sampctr += 1
    if (sampctr % show_every_n_samples) == 0:
        sampreducer = 0
        cola = get_plot_col('a', ints[ia])
        colb = get_plot_col('b', ints[ib])
        colc = get_plot_col('c', ints[ic])
        #set_scroll_region_plot()
        print(f'\033[46m\033[2K\033[;33;1m\033[{cola}C##\033[K\033[;m')
        #gxy(50,30)
        #set_scroll_region_data()
        #print("Yay", sampreducer)
        #gxy(1,rows)
        #gright(cola); print(f"{bcya}##\r", sep='', end='')
        # gright(colb); print(f"{bmag}O\r", sep='', end='')
        # gright(colc); print(f"{yel}X\r", sep='', end='')
        #print(rst, sep='')

def set_scroll_region_plot():
    # [5;130s left margin at column 5 and right at column 130
    # [4;20r   top margin at line 4 and bottom at line 20
    if not have_term: return
    print(f"\033[{plotcola};{plotcolb}s", end='')

def set_scroll_region_data():
    if not have_term: return
    print(f"\033[{plotcolb+1};{cols-1}s", end='')

def get_plot_col(idchar, val):
    if not have_term: return
    amax = ovals[idchar]['max']
    amin = ovals[idchar]['min']
    denom = amax - amin
    if denom == 0: denom=1
    pos = ((val-amin)/denom) * (cols * widthperc - 3)
    return int(pos)

def test_colors():
    print("BPM color test")
    for bpm in range(50,130,2):
        print(f"{bpm:3d} {bpm_to_color(bpm)}▓{rst}")

if __name__ == '__main__':
    test_colors()

# vim: et
