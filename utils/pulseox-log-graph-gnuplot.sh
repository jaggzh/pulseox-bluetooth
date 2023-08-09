#!/bin/bash

# Function to validate if argument is a directory or file
validate_argument() {
    if [[ -d "$1" ]]; then
        readarray -t logs < <(find "$1" -type f -name "*.log" | tail -120)
    elif [[ -f "$1" ]]; then
        logs+=("$1")
    else
        echo "Invalid argument: $1. Argument must be either a directory or a file." >&2
        exit 1
    fi
}

logdir=~/logs/pulseox-patient

# Validate command-line arguments
if [[ $# -lt 1 ]]; then
    echo "You can provide a directory or list of files on the command line."
    echo "Defaulting to directory: $logdir"
    read -n 1 -t 3 -p "(Proceeding in 5 seconds... q to quit)"
    if [[ $REPLY = q ]]; then echo; echo 'Aborting'; exit; fi
    validate_argument "$logdir"
else
    for arg in "$@"; do
        validate_argument "$arg"
    done
fi

umask 0077
tmpf=/tmp/gp.data

usage() { echo "Usage: $0 [-b] [-o] [directory or list of files]" 1>&2; exit 1; }

col_bpm=3
col_o2=4

graph_bpm=
graph_o2=

while getopts ":bo" o; do
    case "${o}" in
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

# Concatenate logs to temp file, filtering out unwanted lines
cat "${logs[@]}" | grep -a -v '255\t127' > "$tmpf"
echo "Processing files: ${logs[*]}"

line1=$(cat "$tmpf" | grep -av '^#' | grep -av $'\t255\t' | head -1)
linen=$(cat "$tmpf" | grep -av '^#' | grep -av $'\t255\t' | tail -1)
printf "Line1: %s\n" "$line1"
printf "LineN: %s\n" "$linen"
fmt1=$(printf "%s" "$line1" | sed -e $'s/\t.*$//')
fmtn=$(printf "%s" "$linen" | sed -e $'s/\t.*$//')
printf "Range: $fmt1 - $fmtn\n"

exec {gp}> >(gnuplot)

lines=$(wc -l "$tmpf" | sed -e 's/ .*$//')

# # For testing, just add a few lines of data:
# cat <<EOT > "$tmpf"
# 2022-02-10 07:53:26	74	96	-
# 2022-02-10 07:53:27	76	96	-
# 2022-02-10 07:53:28	73	96	-
# EOT


cat <<EOT >&"$gp"
ntics = 2
set xdata time
set timefmt "%Y-%m-%d %H:%M:%S"
set xrange ["$fmt1":"$fmtn"]
set format x "%m/%d %H:%M"
set timefmt "%Y-%m-%d %H:%M:%S"
set xtics $lines/4 rotate by 75 right
plot "$tmpf" using 1:$target_col with lines title "SpO2", "" using 1:$col_bpm with lines title "BPM",
pause -1
EOT
sleep 1
read -p "Enter when done" uinp
printf 'You entered: %s\n' "$uinp"
