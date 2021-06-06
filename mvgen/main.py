"""Main file."""

import datetime
import logging

from pathlib import Path
from mvgen.mvgen import MVGen
from mvgen.utils import wslpath


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
    if force is False:
        return

    if force is not None:
        assert len(force) == 2, '--force must have exactly two elements.'


def check_path(path):
    path = Path(path)
    if not path.exists():
        path = wslpath(str(path))

    return path


def make(
    sources,
    duration,
    audio,
    bpm,
    force,
    offset,
    delete_work_dir,
    start,
    end,
    segment_duration,
    segment_start,
    segment_end,
    force_segment,
    raw_directory,
    segments_directory,
    work_directory,
    ready_directory,
    audio_mode,
    convert
):
    started = datetime.datetime.now()

    if not Path(audio).exists():
        raw_directory = wslpath(raw_directory)
        work_directory = wslpath(work_directory)
        ready_directory = wslpath(ready_directory)
        audio = wslpath(audio)

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
        segment_end=segment_end,
        start=start,
        end=end
    )

    p.make_join_file()

    p.join(force=force)

    final_file = p.finalize(
        ready_directory=ready_directory,
        offset=offset,
        delete_work_dir=delete_work_dir,
        audio_mode=audio_mode,
        convert=convert
    )

    finished = datetime.datetime.now()

    LOG.info('COMPLETED: {}'.format(finished - started))

    return {
        'filename': final_file.name,
        'filepath': str(final_file)
    }


def parse_args(config):
    import argparse

    if '__argv' in config:
        import sys
        sys.argv += config['__argv']

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--sources', '-s', nargs='*', required=True,
        help='Names of the source folders.'
    )
    parser.add_argument(
        '--duration', '-d', type=int,
        default=config['duration'],
        help='Beats per scene modifier.'
    )
    parser.add_argument(
        '--audio', default=config['audio'],
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
        '--keep_work_dir', default=config['keep_work_dir'],
        action='store_true',
        help='Delete working directory.'
    )
    parser.add_argument(
        '--start', type=float,
        default=config['start'],
        help='Position from beginning of raw video to process from.'
    )
    parser.add_argument(
        '--end', type=float,
        default=config['end'],
        help='Position from end of raw video to process to.'
    )
    parser.add_argument(
        '--offset', type=float, default=config['offset'],
        help='Audio offset in the final file.'
    )
    parser.add_argument(
        '--force', default=config['force'],
        nargs='*',
        help='Force width and height for final video.'
    )
    parser.add_argument(
        '--segment_duration', '--sd', type=float,
        default=config['segment_duration'],
        help='Duration of the segments.'
    )
    parser.add_argument(
        '--segment_start', '--ss', type=float,
        default=config['segment_start'],
        help='Position from beginning of raw video to segment from.'
    )
    parser.add_argument(
        '--segment_end', '--se', type=float,
        default=config['segment_end'],
        help='Position from end of raw video to segment to.'
    )
    parser.add_argument(
        '--force_segment',
        default=config['force_segment'],
        action='store_true',
        help='Force segmentation of raw video.'
    )
    parser.add_argument(
        '--raw_directory', type=str,
        default=config['raw_directory'],
        help='Directory of original videos.'
    )
    parser.add_argument(
        '--segments_directory', type=str,
        default=config['segments_directory'],
        help='Directory for video segments.'
    )
    parser.add_argument(
        '--work_directory', type=str,
        default=config['work_directory'],
        help='Directory for storing temporary files.'
    )
    parser.add_argument(
        '--ready_directory', type=str,
        default=config['ready_directory'],
        help='Directory for final videos.'
    )
    parser.add_argument(
        '--audio_mode', type=str,
        default=config.get('audio_mode', 'audio'),
        help='Audio mode. Valid values are "audio", "original" and "mix".'
    )
    parser.add_argument(
        '--convert', type=str,
        default=config.get('convert', False)
    )

    args, _ = parser.parse_known_args()

    LOG.info(str(args.__dict__))

    return args


def run(config):
    args = parse_args(config)

    return make(
        sources=args.sources,
        duration=args.duration,
        audio=args.audio,
        bpm=args.bpm,
        force=args.force,
        offset=args.offset,
        delete_work_dir=not args.keep_work_dir,
        start=args.start,
        end=args.end,
        segment_duration=args.segment_duration,
        segment_start=args.segment_start,
        segment_end=args.segment_end,
        force_segment=args.force_segment,
        raw_directory=args.raw_directory,
        segments_directory=args.segments_directory,
        work_directory=args.work_directory,
        ready_directory=args.ready_directory,
        audio_mode=args.audio_mode,
        convert=args.convert
    )
