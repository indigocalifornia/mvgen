import argparse
import yaml
import os
import datetime
import inspect
import json

from pathlib import Path
from mvgen.utils import get_logger, wslpath
from mvgen.variables import WSL
from mvgen.mvgen import MVGen

LOG = get_logger(__name__)


def validate_config(config):
    force = config['force']
    if force is not False:
        assert len(force) == 2, '--force must have exactly two elements.'

    config['delete_work_dir'] = int(config['delete_work_dir'])

    return config


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='Path to config file.')

    parser.add_argument(
        '--sources', '-s', nargs='*',
        help='Names of the source folders.'
    )
    parser.add_argument(
        '--duration', '-d', type=int,
        help='Beats per scene modifier.'
    )
    parser.add_argument(
        '--audio',
        help='Path to audio file.'
    )
    parser.add_argument('--bpm', help='Audio BPM variable')
    parser.add_argument(
        '--delete_work_dir',
        help='Delete working directory.'
    )
    parser.add_argument(
        '--start', type=float,
        help='Position from beginning of raw video to process from.'
    )
    parser.add_argument(
        '--end', type=float,
        help='Position from end of raw video to process to.'
    )
    parser.add_argument(
        '--offset', type=float,
        help='Audio offset in the final file.'
    )
    parser.add_argument(
        '--force',
        nargs='*',
        help='Force width and height for final video.'
    )
    parser.add_argument(
        '--raw_directory', type=str,
        help='Directory of original videos.'
    )
    parser.add_argument(
        '--work_directory', type=str,
        help='Directory for storing temporary files.'
    )
    parser.add_argument(
        '--ready_directory', type=str,
        help='Directory for final videos.'
    )
    parser.add_argument(
        '--audio_mode', type=str,
        help='Audio mode. Valid values are "audio", "original" and "mix".'
    )
    parser.add_argument(
        '--convert', type=str,
    )

    args, _ = parser.parse_known_args()

    args = {k: v for k, v in vars(args).items() if v is not None}

    return args

def load_config(path=None):
    if path is None:
        config_path = Path(os.path.dirname(__file__)) / 'config.yaml'

        if not config_path.exists():
            LOG.info('No config was specified and default file does not exist')
            config_path = None
    else:
        config_path = args.config

    if config_path is not None:
        with open(str(config_path), 'r', encoding = "utf-8") as f:
            config = yaml.load(f, Loader=yaml.SafeLoader)
    else:
        config = {}

    return config


def get_args(config, function):
    args = {
        k: v for k, v in config.items()
        if k in inspect.getfullargspec(function).args
    }
    return args


def run(args):
    config = load_config(args.get('config'))

    config.update(args)

    config = validate_config(config)

    LOG.info(f'CONFIG: {json.dumps(config)}')

    started = datetime.datetime.now()

    final_file = MVGen.run(config)

    finished = datetime.datetime.now()

    LOG.info('COMPLETED: {}'.format(finished - started))

    return {
        'filename': final_file.name,
        'filepath': str(final_file)
    }


if __name__ == '__main__':
    args = parse_args()

    run(args)
