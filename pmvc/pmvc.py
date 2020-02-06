"""Main functionality."""
import os
import random
import datetime
import uuid
import shutil
import logging
import numpy as np
import pandas as pd
import attr
import yaml

from pathlib import Path
from tqdm import tqdm

from pmvc import commands as cs
from pmvc.audio import get_bpm, get_beats
from pmvc.utils import (
    natural_keys, mkdir, get_duration, get_bitrate, runcmd, modify_filename
)


LOG = logging.getLogger(__name__)
LOG.handlers = []
LOG.addHandler(logging.StreamHandler())
LOG.setLevel(logging.INFO)

DEBUG_FILENAME = 'debug.txt'
RANDOM_DIRECTORY_NAME = 'random'
RANDOM_FILENAME = 'random.txt'
CONVERTED_AUDIO_FILENAME = 'audio3.mp4'
VIDEO_FILENAME = 'all.mp4'
FINAL_FILENAME = 'all_music.mp4'


def convert_uid(uid):
    if uid is None:
        uid = str(uuid.uuid1())

    return uid


def convert_path(path):
    path = Path(path)
    mkdir(path)

    return path


def get_segments(paths, limit):
    LOG.info('VIDEO: Source: {}'.format([i.name for i in paths]))

    segs = np.concatenate([list(i.iterdir()) for i in paths])
    segs = [i for i in segs if os.stat(str(i)).st_size > 0]

    random.shuffle(segs)

    if limit is not None and limit > 0:
        replace = True if limit > len(segs) else False
        segs = np.random.choice(segs, size=limit, replace=replace)

    return segs


def combine_video_and_beats(fs, beats):
    fs = list(fs)
    fs.sort(key=lambda x: natural_keys(x.name))
    beats = list(np.diff(beats)) + [1]
    fs = np.array(list(zip(fs, beats)))

    return fs


def make_segments(src, dest, segtime, cut_start, cut_end):
    LOG.info('{} will be emptied and rewritten!'.format(dest))

    if dest.exists():
        shutil.rmtree(dest)
    mkdir(dest)

    for f in tqdm(list(src.iterdir())):
        duration = get_duration(f)

        names = dest / "{}_%d{}".format(f.stem, f.suffix)

        cmd = cs.make_segments(
            f, cut_start, duration - cut_end, segtime, names)
        runcmd(cmd)


@attr.s
class PMVC(object):
    """PMV creator."""

    raw_directory = attr.ib(converter=convert_path)
    segments_directory = attr.ib(converter=convert_path)
    work_directory = attr.ib(converter=convert_path)
    uid = attr.ib(default=None, converter=convert_uid)

    audio = None
    beats = None
    final_file = None

    @uid.validator
    def validate_uid(self, attribute, value):
        work_directory = Path(self.work_directory)
        self.directory = work_directory / value
        self.random_file = work_directory / value / RANDOM_FILENAME
        self.video = self.random_file.parent / VIDEO_FILENAME


    def load_audio(self, audio, bpm=None):
        self.directory = self._create_directory()

        self.audio = self._copy_audio(audio)

        self.beats = self._process_audio(self.audio, bpm)

        return self.directory

    def _create_directory(self):
        directory = self.work_directory / self.uid
        mkdir(directory)

        return directory

    def _copy_audio(self, audio):
        audio = Path(audio)

        new_audio = self.directory / audio.name
        shutil.copy(str(audio), str(new_audio))
        audio = new_audio

        self.debug_file = self.directory / DEBUG_FILENAME

        with open(str(self.debug_file), 'w') as tf:
            tf.write('{}\n'.format(audio.name))

        if audio.suffix != '.wav':
            LOG.info('AUDIO: Converting to WAV')

            new_audio = audio.parent / (audio.stem + '.wav')
            cmd = cs.convert_to_wav(audio, new_audio)
            runcmd(cmd)

            audio = new_audio

        return audio

    def _process_audio(self, audio, bpm):
        if Path(str(bpm)).exists():
            LOG.info('AUDIO: Beats file: {}'.format(bpm))

            with open(str(bpm), 'r') as text_file:
                f = text_file.read()
            beats = [float(i) for i in f.split(',')]

        elif bpm == 'auto':
            LOG.info('AUDIO: Beats mode')

            beats = get_beats(str(audio))
            beats = [0] + beats

        else:
            if bpm is None:
                LOG.info('Detecting BPM')

                bpm = get_bpm(str(audio))
                bpm = np.round(bpm)

            LOG.info('AUDIO: {} BPM'.format(bpm))

            diff = 60. / bpm
            duration = get_duration(audio)
            beats = list(np.arange(0, duration, diff))

        return beats

    def generate(
        self, sources, duration=2,
        force_segment=False, segment_duration=2,
        segment_start=0, segment_end=0
    ):

        self.random_directory = self.directory / RANDOM_DIRECTORY_NAME
        mkdir(self.random_directory)

        segment_paths = [self.segments_directory / i for i in sources]

        for path in segment_paths:
            segments_exist = path.exists() and len(list(path.iterdir()))

            if not segments_exist:
                LOG.info("Segments for {} don't exist, creating".format(
                    path.name))
                self._make_segments(
                    path, segment_duration, segment_start, segment_end)

            elif force_segment:
                LOG.info('Overwriting segments for {}'.format(path.name))
                self._make_segments(
                    path, segment_duration, segment_start, segment_end)

        beats = self.beats[::duration]
        limit = len(beats) + 1
        segs = get_segments(segment_paths, limit)

        bitrate = [get_bitrate(i) for i in np.random.choice(segs, size=20)]
        bitrate = np.max(bitrate)
        LOG.info('VIDEO: Max bitrate: {}'.format(bitrate))

        total_dur = 0
        for i in tqdm(np.arange(len(beats) - 1)):
            diff = beats[i + 1] - total_dur
            if diff > 0:
                f = segs[i]
                filename = modify_filename(f.name, prefix=i)
                outfile = self.random_directory / filename

                cmd = cs.process_segment(f, diff, bitrate, outfile)
                runcmd(cmd)

                dur = get_duration(outfile)

                if dur > 0:
                    total_dur += dur
                elif outfile.exists():
                    os.remove(str(outfile))

        fs = list(self.random_directory.iterdir())
        fs.sort(key=lambda x: natural_keys(x.name))

        with open(str(self.debug_file), 'a') as tf:
            for f, d in zip(fs, beats):
                d = str(datetime.timedelta(seconds=d))
                tf.write("{} : {}\n".format(d, f.name))

    def _make_segments(
        self, path, segment_duration, segment_start, segment_end
    ):
        src = self.raw_directory / path.name
        make_segments(
            src, path, segment_duration, segment_start, segment_end
        )

    def make_join_file(self):
        LOG.info('MAKING JOIN FILE')

        self.random_file = self.directory / RANDOM_FILENAME

        fs = list(self.random_directory.iterdir())
        fs.sort(key=lambda x: natural_keys(x.name))

        with open(str(self.random_file), 'w') as tf:
            for f in fs:
                f = os.path.relpath(f, self.directory)
                tf.write("file '{}'\n".format(f))

    def join(self, force=None):
        LOG.info('JOINING')

        self.video = self.random_file.parent / VIDEO_FILENAME

        if force is None:
            cmd = cs.join(self.random_file, self.video)

        else:
            width, height = force

            LOG.info('FORCING SIZE: {}x{}'.format(width, height))

            cmd = cs.join_force(
                input_file=self.random_file,
                output_file=self.video,
                width=width,
                height=height
            )

        runcmd(cmd)

    def finalize(self, ready_directory=None, offset=0, delete_work_dir=True):
        audio = self.audio

        LOG.info('FINALIZE: Converting audio to AAC')
        audio = self.directory / CONVERTED_AUDIO_FILENAME
        cmd = 'ffmpeg -y -i "{}" -acodec aac "{}"'.format(self.audio, audio)
        runcmd(cmd)

        final_file = self.directory / FINAL_FILENAME

        LOG.info('FINALIZE: Joining audio and video')
        cmd = cs.join_audio_video(offset, self.video, audio, final_file)
        runcmd(cmd)

        if ready_directory is not None:
            ready_directory = Path(ready_directory)
            mkdir(ready_directory)

            ready_file = ready_directory / '{}.mp4'.format(
                self.directory.name)

            shutil.copy(
                str(final_file),
                str(ready_file)
            )
            shutil.copy(
                str(self.directory / 'debug.txt'),
                str(ready_directory  / '{}.txt'.format(self.directory.name))
            )

            if delete_work_dir:
                shutil.rmtree(str(self.directory))

            return ready_file

        return final_file
