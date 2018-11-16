"""Main file."""

import os
import yaml
import datetime
import logging

from pathlib import Path
from pmvc.pmvc import PMVC


LOG = logging.getLogger(__name__)
LOG.handlers = []
LOG.addHandler(logging.StreamHandler())
LOG.setLevel(logging.INFO)


config_path = Path(os.path.dirname(__file__)) / 'config.yaml'
with open(str(config_path), 'r') as stream:
    CONFIG = yaml.load(stream)


def make(
    sources,
    duration,
    audio,
    bpm,
    force,
    offset,
    delete_work_dir,
    segment_duration,
    segment_start,
    segment_end,
    force_segment,
):
    started = datetime.datetime.now()

    if bpm is not None:
        try:
            bpm = float(bpm)
        except ValueError:
            pass

    p = PMVC(
        CONFIG['paths']['raw'],
        CONFIG['paths']['segments'],
        CONFIG['paths']['work']
    )

    p.load_audio(audio, bpm)

    p.generate(
        sources=sources,
        duration=duration,
        force_segment=force_segment,
        segment_duration=segment_duration,
        segment_start=segment_start,
        segment_end=segment_end
    )

    p.make_join_file()

    p.join(force=force)

    p.finalize(
        ready_directory=CONFIG['paths']['ready'],
        offset=offset,
        delete_work_dir=delete_work_dir
    )

    finished = datetime.datetime.now()

    LOG.info('COMPLETED: {}'.format(finished - started))


def parse_args():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--sources', '-s', nargs='*', required=True,
        help='Names of the source folders.'
    )
    parser.add_argument(
        '--duration', '-d', type=int,
        default=CONFIG['default']['work']['duration'],
        help='Beats per scene modifier.'
    )
    parser.add_argument(
        '--audio', default=CONFIG['default']['audio']['file'],
        help='Path to audio file.'
    )
    h = '''
    Audio bpm. Can be either a number (known bpm of audio),
    "auto" (use peak detection for variable bpm),
    path to text file (file containing peak positions, separated by commas),
    or unspecified (auto bpm detection).
    '''
    parser.add_argument('--bpm', help=h)
    parser.add_argument(
        '--delete', type=int, default=CONFIG['default']['work']['delete'],
        help='Delete working directory.'
    )
    parser.add_argument(
        '--offset', type=float, default=0,
        help='Audio offset in the final file.'
    )
    parser.add_argument(
        '--force', type=int, default=CONFIG['default']['work']['force'],
        help='Force width and height for final video.'
    )
    parser.add_argument(
        '--segment_duration', '--sd', type=float,
        default=CONFIG['default']['segments']['duration'],
        help='Duration of the segments.'
    )
    parser.add_argument(
        '--segment_start', '--ss', type=float,
        default=CONFIG['default']['segments']['start'],
        help='Position from beginning of raw video to segment from.'
    )
    parser.add_argument(
        '--segment_end', '--se', type=float,
        default=CONFIG['default']['segments']['end'],
        help='Position from end of raw video to segment to.'
    )
    parser.add_argument(
        '--force_segment', type=int,
        default=CONFIG['default']['segments']['force'],
        help='Force segmentation of raw video.'
    )

    args = parser.parse_args()

    return args


def run():
    args = parse_args()

    make(
        sources=args.sources,
        duration=args.duration,
        audio=args.audio,
        bpm=args.bpm,
        force=args.force,
        offset=args.offset,
        delete_work_dir=args.delete,
        segment_duration=args.segment_duration,
        segment_start=args.segment_start,
        segment_end=args.segment_end,
        force_segment=args.force_segment
    )
