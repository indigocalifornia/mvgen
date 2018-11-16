"""ffmpeg commands."""


def convert_to_wav(*args):
    return (
        'ffmpeg -y -i "{}" -af silenceremove=1:0:-50dB "{}"'
    ).format(*args)


def make_segments(*args):
    return (
        'ffmpeg -y -i "{}" -ss {} -to {} -vcodec copy -acodec copy'
        ' -f segment -segment_time {} -reset_timestamps 1 -map 0 "{}"'
    ).format(*args)


def process_segment(*args):
    return (
        'ffmpeg -y -i "{}" -an -ss 0 -t {} -vb {} -mbd rd'
        ' -trellis 2 -cmp 2 -subcmp 2 -g 100 -f mpeg "{}"'
    ).format(*args)


def join(*args):
    return (
        'ffmpeg -y -auto_convert 1 -f concat -safe 0 -i "{}" -c:v copy {}'
    ).format(*args)


def join_force(*args):
    return (
        'ffmpeg -y -auto_convert 1 -f concat -safe 0 -i "{}" -vcodec libx264'
        ' -movflags faststart -vf "scale=(iw*sar)*min(1280/(iw*sar)\,720/ih):'
        'ih*min(1280/(iw*sar)\,720/ih), pad=1280:720:(1280-iw*min(1280/iw\,'
        '720/ih))/2:(720-ih*min(1280/iw\,720/ih))/2" "{}"'
    ).format(*args)


def join_audio_video(*args):
    return (
        'ffmpeg -y -itsoffset {} -i "{}" -i "{}" -vcodec copy -acodec copy'
        ' -shortest "{}"'
    ).format(*args)


def get_duration(*args):
    return (
        'ffprobe -v error -show_entries format=duration -of'
        ' default=noprint_wrappers=1:nokey=1 "{}"'
    ).format(*args)


def get_bitrate(*args):
    return (
        'ffprobe -v error -show_entries format=bit_rate -of '
        'default=noprint_wrappers=1:nokey=1 "{}"'
    ).format(*args)
