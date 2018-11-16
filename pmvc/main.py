"""Main file."""

import datetime
import logging

from pmvc.pmvc import PMVC


LOG = logging.getLogger(__name__)
LOG.handlers = []
LOG.addHandler(logging.StreamHandler())
LOG.setLevel(logging.INFO)


def check_bpm(bpm):
    if bpm is not None:
        try:
            bpm = float(bpm)
        except ValueError:
            pass

    return bpm


def check_force(force):
    if force is not None:
        assert len(force) == 2, '--force must have exactly two elements.'


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
    raw_directory,
    segments_directory,
    work_directory,
    ready_directory
):
    started = datetime.datetime.now()

    bpm = check_bpm(bpm)
    check_force(force)

    p = PMVC(
        raw_directory,
        segments_directory,
        work_directory
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
        ready_directory=ready_directory,
        offset=offset,
        delete_work_dir=delete_work_dir
    )

    finished = datetime.datetime.now()

    LOG.info('COMPLETED: {}'.format(finished - started))


def parse_args(config):
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--sources', '-s', nargs='*', required=True,
        help='Names of the source folders.'
    )
    parser.add_argument(
        '--duration', '-d', type=int,
        default=config['work']['duration'],
        help='Beats per scene modifier.'
    )
    parser.add_argument(
        '--audio', default=config['audio']['file'],
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
        '--delete', default=config['work']['delete'],
        action='store_true',
        help='Delete working directory.'
    )
    parser.add_argument(
        '--offset', type=float, default=config['audio']['offset'],
        help='Audio offset in the final file.'
    )
    parser.add_argument(
        '--force', default=config['work']['force'],
        nargs='*',
        help='Force width and height for final video.'
    )
    parser.add_argument(
        '--segment_duration', '--sd', type=float,
        default=config['segments']['duration'],
        help='Duration of the segments.'
    )
    parser.add_argument(
        '--segment_start', '--ss', type=float,
        default=config['segments']['start'],
        help='Position from beginning of raw video to segment from.'
    )
    parser.add_argument(
        '--segment_end', '--se', type=float,
        default=config['segments']['end'],
        help='Position from end of raw video to segment to.'
    )
    parser.add_argument(
        '--force_segment',
        default=config['segments']['force'],
        action='store_true',
        help='Force segmentation of raw video.'
    )
    parser.add_argument(
        '--raw_directory', type=str,
        default=config['paths']['raw'],
        help='Directory of original videos.'
    )
    parser.add_argument(
        '--segments_directory', type=str,
        default=config['paths']['segments'],
        help='Directory for video segments.'
    )
    parser.add_argument(
        '--work_directory', type=str,
        default=config['paths']['work'],
        help='Directory for storing temporary files.'
    )
    parser.add_argument(
        '--ready_directory', type=str,
        default=config['paths']['ready'],
        help='Directory for final videos.'
    )

    args, _ = parser.parse_known_args()

    return args


def run(config):
    args = parse_args(config)

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
        force_segment=args.force_segment,
        raw_directory=args.raw_directory,
        segments_directory=args.segments_directory,
        work_directory=args.work_directory,
        ready_directory=args.ready_directory
    )
