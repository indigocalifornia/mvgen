"""Utility functions."""

import re
import os
import subprocess
import logging
import unidecode

from pmvc import commands as cs

LOG = logging.getLogger(__name__)
LOG.handlers = []
LOG.addHandler(logging.StreamHandler())
LOG.setLevel(logging.INFO)


def natural_keys(text):
    return [
        int(t) if t.isdigit() else t
        for t in re.split('(\d+)', text)
    ]


def mkdir(path):
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)


def get_duration(filename):
    cmd = cs.get_duration(filename)
    duration = os.popen(cmd)
    duration = duration.read().strip('\n')
    try:
        return float(duration)
    except Exception:
        return 0.


def get_bitrate(filename):
    cmd = cs.get_bitrate(filename)
    duration = os.popen(cmd)
    duration = duration.read().strip('\n')
    try:
        return float(duration)
    except Exception:
        return 0.


def runcmd(cmd):
    # LOG.info(cmd)
    # with open(os.devnull, 'w') as stderr:
    #     subprocess.check_output(cmd, stderr=stderr)
    log = os.devnull
    with open(log, 'a') as stdout:
        res = subprocess.Popen(
            cmd, stdout=stdout, stderr=subprocess.STDOUT, shell=True
        )

        out, err = res.communicate()

        if res.returncode != 0:
            LOG.error(cmd)

        # LOG.info(res)
        # os.system(cmd)


def checkcmd(cmd):
    log = os.devnull
    with open(log, 'a') as stdout:
        res = subprocess.Popen(
            cmd, stdout=stdout, stderr=subprocess.STDOUT, shell=True
        )
        res.communicate()

    if res.returncode != 0:
        LOG.error(cmd)

    return res.returncode


def modify_filename(filename, prefix=None, suffix=None):
    filename = unidecode.unidecode_expect_ascii(filename)

    whitelist = '. _-'
    filename = re.sub(r'[^\w' + whitelist + ']', '---', filename)

    fname, fext = os.path.splitext(filename)
    if prefix is not None:
        fname = '{}_{}'.format(prefix, fname)
    if suffix is not None:
        fname = '{}_{}'.format(fname, suffix)
    return '{}{}'.format(fname, fext)


def modify_extension(filename, ext):
    fname, fext = os.path.splitext(filename)
    return '{}.{}'.format(fname, ext)


def str2sec(s):
    if not isinstance(s, str):
        return s

    if ':' not in s:
        return float(s)

    else:
        s = s.rsplit(':')
        return 60. * float(s[0]) + float(s[1])


def wslpath(path):
    path = str(path)
    cmd = cs.get_wslpath(path)
    new_path = os.popen(cmd)
    new_path = new_path.read().strip('\n')

    return new_path


def windowspath(path):
    path = str(path)

    if path.startswith('/mnt'):
        new_path = path.replace('/mnt/', '')
        new_path = new_path[0] + ':/' + new_path[1:]

    else:
        cmd = cs.get_windows_path(path)
        new_path = os.popen(cmd)
        new_path = new_path.read().strip('\n')

    return new_path
