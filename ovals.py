import os
from bansi import *

ovals=dict()
ia=3; ib=6; ic=7  # Indexes into integer list of other data

def setup():
    global ovals
    global cols,rows
    ovals=dict()
    ovals['a']=dict()
    ovals['b']=dict()
    ovals['c']=dict()
    for i in ovals.keys():
        ovals[i]['min']=256
        ovals[i]['max']=-256
    cols,rows = os.get_terminal_size()

def set_from_ints(ints):
    #  8-value line: {254 8 86} a 0 ? b c  <-- maybe trace
    #                 0   1 2   3 4 5 6 7
    if ints[ia] < ovals['a']['min']: ovals['a']['min'] = ints[ia]
    if ints[ia] > ovals['a']['max']: ovals['a']['max'] = ints[ia]
    if ints[ib] < ovals['b']['min']: ovals['b']['min'] = ints[ib]
    if ints[ib] > ovals['b']['max']: ovals['b']['max'] = ints[ib]
    if ints[ic] < ovals['c']['min']: ovals['c']['min'] = ints[ic]
    if ints[ic] > ovals['c']['max']: ovals['c']['max'] = ints[ic]

def plot(ints):
	cola = get_plot_col('a', ints[ia])
	colb = get_plot_col('b', ints[ib])
	colc = get_plot_col('c', ints[ic])
	gright(cola); print(f"{bcya}*\r", sep='', end='')
	# gright(colb); print(f"{bmag}O\r", sep='', end='')
	# gright(colc); print(f"{yel}X\r", sep='', end='')
	print(rst, sep='')

def get_plot_col(idchar, val):
	amax = ovals[idchar]['max']
	amin = ovals[idchar]['min']
	denom = amax - amin
	if denom == 0: denom=1
	pos = ((val-amin)/denom) * (cols-1)
	return int(pos)

# vim: et
