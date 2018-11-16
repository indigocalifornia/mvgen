import argparse
import yaml
import os

from pathlib import Path
from pmvc.main import run

def load_config():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='Path to config file.')
    args, _ = parser.parse_known_args()

    if args.config is None:
        config_path = Path(os.path.dirname(__file__)) / 'config.yaml'

        if not config_path.exists():
            m = 'No config was specified and file does not exist.'
            raise ValueError(m)
    else:
        config_path = args.config

    with open(str(config_path), 'r') as f:
        config = yaml.load(f)

    return config

if __name__ == '__main__':
    config = load_config()
    run(config)
