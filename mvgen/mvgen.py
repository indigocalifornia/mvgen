"""Main functionality."""
from multiprocessing import Value
import os
import random
import datetime
from typing_extensions import final
import uuid
import shutil
import logging
import numpy as np
import attr
import inspect
import json

from pathlib import Path
from tqdm import tqdm
from tempfile import mkdtemp
from copy import deepcopy

from mvgen import commands as cs
from mvgen.audio import get_bpm, get_beats
from mvgen.utils import (
    natural_keys, mkdir, get_duration, get_bitrate, runcmd, modify_filename,
    str2sec, checkcmd, wslpath
)
from mvgen.variables import WSL, CUDA, GCP_PROJECT_ID

logging.basicConfig(level=logging.INFO)

# logging = logging.getLogger(__name__)
# logging.handlers = []
# logging.addHandler(logging.StreamHandler())
# logging.setLevel(logging.INFO)

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


def convert_path(path, make_directory=True):
    if WSL:
        path = wslpath(path)

    path = Path(path)

    if make_directory:
        mkdir(path)

    return path


def get_random_files(paths, limit):
    segs = np.concatenate([list(i.rglob('*')) for i in paths])
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


class NullNotifier:
    def notify(self, *args, **kwargs):
        pass


@attr.s
class MVGen(object):
    work_directory = attr.ib(converter=convert_path)
    uid = attr.ib(default=None, converter=convert_uid)
    notifier = attr.ib(default=None)

    audio = None
    beats = None
    final_file = None

    def __attrs_post_init__(self):
        self.directory = self.work_directory / self.uid
        self.random_file = self.directory / RANDOM_FILENAME
        self.video = self.directory / VIDEO_FILENAME

        if self.notifier is None:
            self.notifier = NullNotifier()

    def load_audio(self, audio, bpm=None, delete_original_audio=False):
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
        self.notifier.notify({'status': 'processing-audio'})

        mkdir(self.directory)

        self.debug_file = self.directory / DEBUG_FILENAME
        self.audio = self._copy_audio(
            audio, delete_original_audio=delete_original_audio
        )
        self.beats = self._process_audio(self.audio, bpm)

    def _copy_audio(self, audio, delete_original_audio):
        if not os.path.exists(audio):
            with open(str(self.debug_file), 'w', encoding='utf-8') as file:
                file.write(f'Audio: {audio}\n')
            return audio

        audio = convert_path(audio, make_directory=False)

        if os.path.isdir(audio):
            audio = np.random.choice(
                [i for i in audio.iterdir() if os.path.isfile(i)]
            )

        duration = get_duration(audio, raise_error=True)
        logging.info(f'Audio duration: {duration}')

        audio_name = modify_filename(os.path.basename(audio))
        new_audio = self.directory / audio_name

        logging.info(f'AUDIO: Copying {audio} to {new_audio}')
        shutil.copy(str(audio), str(new_audio))

        if delete_original_audio:
            logging.info(f'AUDIO: Deleting original audio {audio}')
            audio.unlink()

        audio = new_audio

        with open(str(self.debug_file), 'w', encoding='utf-8') as file:
            file.write(f'Audio: {audio}\n')

        return audio

    def _process_audio(self, audio, bpm):
        logging.info(f'AUDIO: Processing {audio}')

        if Path(str(bpm)).exists():
            logging.info('AUDIO: Beats file: {}'.format(bpm))

            with open(str(bpm), 'r') as text_file:
                beats = text_file.read()

            beats = [float(i) for i in beats.split(',')]

        elif bpm == 'beats':
            logging.info('AUDIO: Beats mode')

            beats = get_beats(str(audio))
            beats = [0] + beats

        else:
            if bpm is None or bpm == 'auto':
                logging.info('AUDIO: Detecting BPM')

                if not os.path.exists(audio):
                    raise ValueError('Audio is not a file and no bpm is specified')

                if audio.suffix != '.wav':
                    logging.info('AUDIO: Converting to WAV')

                    wav_audio = audio.parent / WAV_FILENAME
                    cmd = cs.convert_to_wav(audio, wav_audio)
                    exit_code = runcmd(cmd)

                    if exit_code != 0:
                        raise ValueError(f'Error converting {audio.name} to WAV')
                else:
                    wav_audio = audio

                bpm = get_bpm(str(wav_audio))
                bpm = np.round(bpm)

            bpm = float(bpm)

            logging.info('AUDIO: {} BPM'.format(bpm))

            diff = 60. / bpm

            if os.path.exists(audio):
                duration = get_duration(audio, raise_error=True)
            else:
                duration = str2sec(str(audio))

            beats = list(np.arange(0, duration, diff))

        self.bpm = bpm

        with open(str(self.debug_file), 'a') as file:
            json.dump({'beats': beats}, file)

        return beats

    def generate(
        self, duration, sources=None, src_directory=None, src_paths=None,
        start=0, end=0, cuda=None, segment_codec=None,
        width=None, height=None, watermark=None
    ):
        self.notifier.notify({'status': 'processing-video'})

        self.random_directory = self.directory / RANDOM_DIRECTORY_NAME
        mkdir(self.random_directory)

        if src_paths is None:
            src_directory = convert_path(src_directory)
            src_paths = [src_directory / i for i in sources]

            logging.info(f'VIDEO: Sources {sources} in {src_directory}')
        else:
            src_paths = deepcopy(src_paths)
            for i, src_path in enumerate(src_paths):
                src_paths[i] = convert_path(src_path)
                logging.info(f'VIDEO: Using source path {src_path}')

        if duration >= 1:
            duration = int(duration)
            beats = self.beats[::duration]
        else:
            beats = np.array(self.beats)
            fracs = np.arange(0, 1, duration)[1:]
            new_beats = [beats]
            for frac in fracs:
                new = (beats[1:] + beats[:-1]) * frac
                new_beats.append(new)
            beats = list(np.sort(np.concatenate(new_beats)))

        limit = len(beats) + 1

        segs = get_random_files(src_paths, limit)

        if segment_codec is not None:
            logging.info(f'VIDEO: Using segment codec {segment_codec}')

        total_dur = 0
        results = []
        for i in tqdm(np.arange(len(beats) - 1)):
            diff = beats[i + 1] - total_dur
            if diff > 0:
                self.notifier.notify({
                    'status': 'processing-video',
                    'progress': i / (len(beats) - 1)
                })

                file = segs[i]
                filename = modify_filename(file.name, prefix=i)
                outfile = self.random_directory / filename

                dur = get_duration(file)

                new_start = start * dur if start < 1 else start
                new_end = end * dur if end < 1 else end

                new_end = dur - end - diff

                if new_end < new_start:
                    logging.warning(f'File {file} duration {dur} with new end {new_end} is shorter than required {new_start}, ignoring')
                    continue

                ss = np.random.uniform(new_start, new_end)

                cmd = cs.process_segment(
                    start=ss,
                    length=diff,
                    input_file=file,
                    output_file=outfile,
                    cuda=cuda,
                    segment_codec=segment_codec,
                    width=width,
                    height=height,
                    watermark=watermark
                )

                runcmd(cmd, timeout=15)

                dur = get_duration(outfile)

                if dur <= 0:
                    if outfile.exists():
                        try:
                            os.remove(str(outfile))
                        except Exception as e:
                            logging.error(e)

                    continue

                results.append((outfile, total_dur, ss, diff))
                total_dur += dur

        if total_dur == 0:
            raise ValueError('Video segments have no length')

        with open(str(self.debug_file), 'a') as tf:
            for file, d, ss, diff in results:
                d = str(datetime.timedelta(seconds=d))
                r = {
                    'time': d,
                    'filename': file.name,
                    'start': ss,
                    'duration': diff
                }
                json.dump(r, tf)

    def make_join_file(self):
        logging.info(f'VIDEO: MAKING JOIN FILE for {self.random_directory}')

        self.random_file = self.directory / RANDOM_FILENAME

        fs = list(self.random_directory.iterdir())
        fs.sort(key=lambda x: natural_keys(x.name))

        with open(str(self.random_file), 'w') as tf:
            for f in fs:
                f = os.path.abspath(f)
                if WSL:
                    f = cs.windowspath(f)
                tf.write("file '{}'\n".format(f))

    def join(self):
        self.notifier.notify({'status': 'encoding-video'})

        if not CUDA:
            logging.info('VIDEO: Not using CUDA')

        self.video = self.directory / VIDEO_FILENAME

        logging.info(f'VIDEO: JOINING {self.random_file} into {self.video}')

        cmd = cs.join(
            input_file=self.random_file,
            output=self.video,
        )

        exit_code = runcmd(cmd, raise_error=True)
        if exit_code != 0:
            raise ValueError('Output video contains no stream')

    def finalize(
        self, ready_directory=None, offset=0, delete_work_dir=True,
        audio_mode='audio'
    ):
        self.notifier.notify({'status': 'finalizing'})

        final_file = self.directory / FINAL_FILENAME

        if os.path.exists(self.audio):
            logging.info(f'FINALIZE: Joining audio and video using audio mode {audio_mode}')

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
            logging.info('FINALIZE: Copying video only')
            shutil.copy(
                str(self.video),
                str(final_file)
            )


        if ready_directory is not None:
            logging.info(f'FINALIZE: Moving results to ready directory {ready_directory}')

            video_suffix = os.path.splitext(FINAL_FILENAME)[-1]
            debug_suffix = os.path.splitext(DEBUG_FILENAME)[-1]

            debug_file = self.directory / DEBUG_FILENAME

            ready_directory = convert_path(ready_directory)
            ready_file = ready_directory / (self.directory.name + video_suffix)
            ready_debug_file = ready_directory / (self.directory.name + debug_suffix)

            logging.info(f'FINALIZE: Moving {final_file} to {ready_file}')
            shutil.copy(str(final_file), str(ready_file))

            logging.info(f'FINALIZE: Moving {debug_file} to {ready_debug_file}')
            shutil.copy(str(debug_file), str(ready_debug_file))

            if delete_work_dir:
                logging.info(f'FINALIZE: Deleting work directory {self.directory}')
                shutil.rmtree(str(self.directory))

            final_file = ready_file

        logging.info(f'FINALIZE: Final file {final_file}')

        self.final_file = final_file

        return final_file

    @staticmethod
    def run(config):
        started = datetime.datetime.now()

        gen = MVGen(**get_args(config, MVGen))

        gen.load_audio(**get_args(config, MVGen.load_audio))

        gen.generate(**get_args(config, MVGen.generate))

        gen.make_join_file(**get_args(config, MVGen.make_join_file))

        gen.join(**get_args(config, MVGen.join))

        gen.finalize(**get_args(config, MVGen.finalize))

        finished = datetime.datetime.now()

        logging.info('COMPLETED: {}'.format(finished - started))

        return gen
