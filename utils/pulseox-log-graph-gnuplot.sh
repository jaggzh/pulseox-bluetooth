#!/bin/bash
# Final version must have cat *.log comments changed around line ~7
logdir=~/logs/pulseox-patient
if ! cd "$logdir"; then
	echo "Can't change to logdir: $logdir: $!" >&2
	exit
fi

umask 0077
tmpf=/tmp/gp.data

usage() { echo "Usage: $0 [-b] [-o]" 1>&2; exit 1; }

col_bpm=3
col_o2=4

graph_bpm=
graph_o2=

while getopts ":bo" o; do
    case "${o}" in  # May separate lines with \n instead of ;
        o) graph_o2=1;  ;;
        b) graph_bpm=1;  ;;
        h) usage ;;
        *) usage ;;
    esac
done
shift $((OPTIND-1))
if [[ "$graph_o2" != 1 && "$graph_bpm" != 1 ]]; then
	graph_o2=1
fi

if [[ "$graph_o2" = 1 ]]; then
	echo "Graphing O2 column" >&2
	target_col="$col_o2" 
fi
if [[ "$graph_bpm" = 1 ]]; then
	echo "Graphing BPM column" >&2
	target_col="$col_bpm"
fi

if [[ "$#" -gt 0 ]]; then
	logs=("$1")
else
	readarray -t logs < <(ls *.log | tail -1)
fi
# Final version should cat *.log
cat "${logs[@]}" | grep -v '255	127' > "$tmpf"
#cat *.log | grep -v '255	127' > "$tmpf"

# # For testing, just add a few lines of data:
# cat <<EOT > "$tmpf"
# 2022-02-10 07:53:26	74	96	-
# 2022-02-10 07:53:27	76	96	-
# 2022-02-10 07:53:28	73	96	-
# EOT


line1=$(cat "$tmpf" | grep -v '^#' | grep -v $'\t255\t' | head -1)
linen=$(cat "$tmpf" | grep -v '^#' | grep -v $'\t255\t' | tail -1)
printf "Line1: %s\n" "$line1"
printf "LineN: %s\n" "$linen"
fmt1=$(printf "%s" "$line1" | sed -e $'s/\t.*$//')
fmtn=$(printf "%s" "$linen" | sed -e $'s/\t.*$//')
printf "Range: $fmt1 - $fmtn\n"

# 2022-02-10 07:53:26	74	96	-

exec {gp}> >(gnuplot)

cat <<EOT >&"$gp"
set xdata time
set timefmt "%Y-%m-%d %H:%M:%S"
set xrange ["$fmt1":"$fmtn"]
set format x "%m/%d %H:%M"
set timefmt "%Y-%m-%d %H:%M:%S"
set xtics rotate by 75 right
plot "$tmpf" using 1:$target_col with lines
pause -1
EOT
sleep 1
read -p "Enter when done" uinp
printf 'You entered: %s\n' "$uinp"

