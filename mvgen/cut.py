import os
import numpy as np

from audio import get_bpm

import argparse


def modify_filename(filename, prefix=None, suffix=None):
    fname, fext = os.path.splitext(filename)
    if prefix is not None:
        fname = '{}_{}'.format(prefix, fname)
    if suffix is not None:
        fname = '{}_{}'.format(fname, suffix)
    return '{}{}'.format(fname, fext)


parser = argparse.ArgumentParser()
parser.add_argument('--file', '-f', '-i', required=True)
parser.add_argument('--position', '-p', required=True, type=float)
parser.add_argument('--to', type=float)
parser.add_argument('--number', '-n', type=int, default=1)
parser.add_argument('--duration', '-d', type=int, default=180)
parser.add_argument('--total', type=int)
parser.add_argument('--bpm', type=float)
args = parser.parse_args()

print(args.number)

os.system('ffmpeg -y -i "{}" -vn tmp-audio.wav'.format(args.file))

if args.bpm is None:
    bpm, _ = get_bpm('tmp-audio.wav')
else:
    bpm = args.bpm

print('BPM: {}'.format(bpm))

d = 60. / bpm
if args.to is None:
    dur = 16 * d * args.number
else:
    dur = 16 * d
    dur = np.round((args.to - args.position) / dur) * dur
position = np.round(args.position / d) * d

cmd = 'ffmpeg -y -i "{}" -ss {} -t {} -acodec copy -vn -strict -2 tmp-cut.mp4'
os.system(cmd.format(args.file, position, dur))

if args.total is None:
    number = int(args.duration / dur)
else:
    number = args.total

with open('tmp-join.txt', 'w') as fp:
    for _ in range(number):
        fp.write("file 'tmp-cut.mp4'\n")

new_name = os.path.join('F:\\projects\\video\\video\\audio-cuts',
                        os.path.basename(args.file))

cmd = 'ffmpeg -y -f concat -safe 0 -i tmp-join.txt -c copy "{}"'
print(cmd.format(new_name))
os.system(cmd.format(new_name))

for i in ['tmp-audio.wav', 'tmp-cut.mp4', 'tmp-join.txt']:
    os.system('rm {}'.format(i))


# ffmpeg -y -i c4589891-da32-11e7-8164-3052cb239fde.mp4 -i full.wav -vcodec copy -map 0:v:0 -map 1:a:0 -shortest out.mp4
