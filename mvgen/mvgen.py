"""Main functionality."""
import os
import random
import datetime
import uuid
import shutil
import logging
import numpy as np
import attr
import inspect

from pathlib import Path
from tqdm import tqdm
from tempfile import mkstemp

from mvgen import commands as cs
from mvgen.audio import get_bpm, get_beats
from mvgen.utils import (
    natural_keys, mkdir, get_duration, get_bitrate, runcmd, modify_filename,
    str2sec, checkcmd, wslpath
)
from mvgen.variables import WSL, CUDA


LOG = logging.getLogger(__name__)
LOG.handlers = []
LOG.addHandler(logging.StreamHandler())
LOG.setLevel(logging.INFO)

DEBUG_FILENAME = 'debug.txt'
RANDOM_DIRECTORY_NAME = 'random'
RANDOM_FILENAME = 'random.txt'
WAV_FILENAME = 'audio.wav'
CONVERTED_AUDIO_FILENAME = 'audio3.aac'
VIDEO_FILENAME = 'all.mp4'
FINAL_FILENAME = 'all_music.mp4'


def convert_uid(uid):
    if uid is None:
        uid = str(uuid.uuid1())

    return uid


def convert_path(path):
    if WSL:
        path = wslpath(path)

    path = Path(path)
    mkdir(path)

    return path


def get_random_files(paths, limit):
    segs = np.concatenate([list(i.iterdir()) for i in paths])
    segs = [i for i in segs if os.stat(str(i)).st_size > 0]

    random.shuffle(segs)

    if limit is not None and limit > 0:
        replace = True if limit > len(segs) else False
        segs = np.random.choice(segs, size=limit, replace=replace)

    return segs


def get_args(config, function):
    args = {
        k: v for k, v in config.items()
        if k in inspect.getfullargspec(function).args
    }
    return args


@attr.s
class MVGen(object):
    src_directory = attr.ib(converter=convert_path)
    work_directory = attr.ib(converter=convert_path)
    uid = attr.ib(default=None, converter=convert_uid)

    audio = None
    beats = None
    final_file = None

    def __attrs_post_init__(self):
        self.directory = self.work_directory / self.uid
        self.random_file = self.directory / RANDOM_FILENAME
        self.video = self.directory / VIDEO_FILENAME

    def load_audio(self, audio, bpm=None):
        """Load and process audio.

        Args:
            audio: str
                One of
                    file path: Path to audio file
                    directory path: Random file is chosen in the directory
                    string in in hh:mm:ss format: Duration
            bpm: str or None
                One of
                    None or "auto": BPM is detected automatically
                    integer: BPM value
                    "auto": Audio is analyzed for beats
                    file path: Path to beats file
        """
        mkdir(self.directory)

        self.debug_file = self.directory / DEBUG_FILENAME
        self.audio = self._copy_audio(audio)
        self.beats = self._process_audio(self.audio, bpm)

    def _copy_audio(self, audio):
        audio = convert_path(audio)

        if not audio.exists():
            with open(str(self.debug_file), 'w', encoding='utf-8') as file:
                file.write(f'Audio: {audio}\n')
            return audio

        if os.path.isdir(audio):
            audio = np.random.choice(
                [i for i in audio.iterdir() if os.path.isfile(i)]
            )

        audio_name = modify_filename(audio.name)
        new_audio = self.directory / audio_name
        LOG.info(f'AUDIO: Copying {audio} to {new_audio}')
        shutil.copy(str(audio), str(new_audio))
        audio = new_audio

        with open(str(self.debug_file), 'w', encoding='utf-8') as file:
            file.write(f'Audio: {audio}\n')

        return audio

    def _process_audio(self, audio, bpm):
        LOG.info(f'AUDIO: Processing {audio}')
        if Path(str(bpm)).exists():
            LOG.info('AUDIO: Beats file: {}'.format(bpm))

            with open(str(bpm), 'r') as text_file:
                beats = text_file.read()

            beats = [float(i) for i in beats.split(',')]

        elif bpm == 'beats':
            LOG.info('AUDIO: Beats mode')

            beats = get_beats(str(audio))
            beats = [0] + beats

        else:
            if bpm is None or bpm == 'auto':
                LOG.info('AUDIO: Detecting BPM')

                if audio.suffix != '.wav':
                    LOG.info('AUDIO: Converting to WAV')

                    wav_audio = audio.parent / WAV_FILENAME
                    cmd = cs.convert_to_wav(audio, wav_audio)
                    runcmd(cmd)

                bpm = get_bpm(str(wav_audio))
                bpm = np.round(bpm)

            bpm = float(bpm)

            LOG.info('AUDIO: {} BPM'.format(bpm))

            diff = 60. / bpm

            if audio.exists():
                duration = get_duration(audio)
            else:
                duration = str2sec(str(audio))

            beats = list(np.arange(0, duration, diff))

        return beats

    def generate(
        self, sources, duration, start=0, end=0
    ):

        self.random_directory = self.directory / RANDOM_DIRECTORY_NAME
        mkdir(self.random_directory)

        src_paths = [self.src_directory / i for i in sources]

        beats = self.beats[::duration]
        limit = len(beats) + 1

        LOG.info('VIDEO: Source: {}'.format([i.name for i in src_paths]))
        segs = get_random_files(src_paths, limit)

        total_dur = 0
        results = []
        for i in tqdm(np.arange(len(beats) - 1)):
            diff = beats[i + 1] - total_dur
            if diff > 0:
                file = segs[i]
                filename = modify_filename(file.name, prefix=i)
                outfile = self.random_directory / filename

                dur = get_duration(file)

                new_end = dur - end - diff

                if new_end < start:
                    LOG.warning(f'File {file} is shorter than required, ignoring')
                    continue

                ss = np.random.uniform(start, new_end)

                cmd = cs.process_segment(
                    start=ss,
                    length=diff,
                    input_file=file,
                    bitrate=None,
                    output=outfile
                )

                runcmd(cmd)

                dur = get_duration(outfile)

                if dur <= 0:
                    if outfile.exists():
                        os.remove(str(outfile))

                    continue

                results.append((outfile, total_dur))
                total_dur += dur

        with open(str(self.debug_file), 'a') as tf:
            for file, d in results:
                d = str(datetime.timedelta(seconds=d))
                tf.write("{} : {}\n".format(d, file.name))

    def make_join_file(self):
        LOG.info('VIDEO: MAKING JOIN FILE')

        self.random_file = self.directory / RANDOM_FILENAME

        fs = list(self.random_directory.iterdir())
        fs.sort(key=lambda x: natural_keys(x.name))

        with open(str(self.random_file), 'w') as tf:
            for f in fs:
                f = os.path.abspath(f)
                if WSL:
                    f = cs.windowspath(f)
                tf.write("file '{}'\n".format(f))

    def join(self, force=False, convert=False):
        LOG.info('VIDEO: JOINING')

        if not CUDA:
            LOG.info('VIDEO: Not using CUDA')

        self.video = self.directory / VIDEO_FILENAME

        if force:
            LOG.info('FORCING SIZE: {}'.format(force))

        cmd = cs.join(
            input_file=self.random_file,
            output=self.video,
            force=force,
            convert=convert
        )

        runcmd(cmd)

    def finalize(
        self, ready_directory=None, offset=0, delete_work_dir=True,
        audio_mode='audio'
    ):
        final_file = self.directory / FINAL_FILENAME

        if self.audio.exists():
            new_audio = self.directory / CONVERTED_AUDIO_FILENAME

            if self.audio != new_audio:
                LOG.info('FINALIZE: Converting audio to AAC')
                cmd = cs.convert_audio(self.audio, new_audio, 'aac')
                runcmd(cmd)
                self.audio = new_audio

            LOG.info('FINALIZE: Joining audio and video')

            if audio_mode == 'audio':
                channel = 1
            elif audio_mode == 'original':
                channel = 0
            elif audio_mode == 'mix':
                channel = 'mix'
            else:
                raise ValueError(audio_mode)

            cmd = cs.join_audio_video(
                offset=offset,
                video=self.video,
                audio=self.audio,
                channel=channel,
                output=final_file
            )

            runcmd(cmd)

        else:
            LOG.info('FINALIZE: Copying video only')
            shutil.copy(
                str(self.video),
                str(final_file)
            )


        if ready_directory is not None:
            ready_directory = convert_path(ready_directory)

            video_suffix = os.path.splitext(FINAL_FILENAME)[-1]
            ready_file = ready_directory / (self.directory.name + video_suffix)
            shutil.copy(
                str(final_file),
                str(ready_file)
            )

            debug_suffix = os.path.splitext(DEBUG_FILENAME)[-1]
            debug_file = ready_directory / (self.directory.name + debug_suffix)

            shutil.copy(
                str(self.directory / DEBUG_FILENAME),
                str(debug_file)
            )

            if delete_work_dir:
                shutil.rmtree(str(self.directory))

            return ready_file

        return final_file

    @staticmethod
    def run(config):
        gen = MVGen(**get_args(config, MVGen))

        gen.load_audio(**get_args(config, MVGen.load_audio))

        gen.generate(**get_args(config, MVGen.generate))

        gen.make_join_file(**get_args(config, MVGen.make_join_file))

        gen.join(**get_args(config, MVGen.join))

        final_file = gen.finalize(**get_args(config, MVGen.finalize))

        return final_file
