"""ffmpeg.exe commands."""

from pmvc.utils import windowspath


def check_path(path):
    if str(path).startswith('/'):
        path = windowspath(path)

    return path


def convert_to_wav(*args):
    args = list(args)
    for i in [0, 1]:
        args[i] = check_path(args[i])

    return (
        'ffmpeg.exe -y -i "{}" -af silenceremove=1:0:-50dB "{}"'
    ).format(*args)


# def make_segments(*args):
#     return (
#         'ffmpeg.exe -y -hwaccel cuvid -i "{}" -ss {} -to {} -vcodec copy -acodec copy'
#         ' -f segment -segment_time {} -reset_timestamps 1 -map 0:0 "{}"'
#     ).format(*args)


# def make_segments_gif(*args):
#     return (
#         'ffmpeg.exe -i {} -movflags faststart -pix_fmt yuv420p -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -r 24 {}.mp4'
#     ).format(*args)


def process_segment(*args):
    args = list(args)
    for i in [2, -1]:
        args[i] = check_path(args[i])

    return (
        'ffmpeg.exe -y -hwaccel cuvid -hwaccel_output_format cuda -c:v h264_cuvid -vsync 0 -ss {} -t {} -i "{}" -vb {} -mbd rd'
        ' -trellis 2 -cmp 2 -subcmp 2 -g 100 -c:v h264_nvenc -f mpeg "{}"'
    ).format(*args)


def join(*args):
    args = list(args)
    for i in [0, 1]:
        args[i] = check_path(args[i])

    return (
        'ffmpeg.exe -hwaccel cuvid -hwaccel_output_format cuda -auto_convert 1 -f concat -safe 0 -i "{}" -y -c:v copy {}'
    ).format(*args)


def join_force(**kwargs):
    for i in ['input_file', 'output_file']:
        kwargs[i] = check_path(kwargs[i])

    return (
        'ffmpeg.exe -y -auto_convert 1 -f concat -safe 0 -i "{input_file}"'
        ' -c:v h264_nvenc -movflags faststart -vf "scale='
        '(iw*sar)*min({width}/(iw*sar)\,'
        '{height}/ih):ih*min({width}/(iw*sar)\,{height}/ih), pad='
        '{width}:{height}:({width}-iw*min({width}/iw\,'
        '{height}/ih))/2:({height}-ih*min({width}/iw\,{height}/ih))/2"'
        ' "{output_file}"'
    ).format(**kwargs)


def join_audio_video(*args):
    args = list(args)
    for i in [1, 2, -1]:
        args[i] = check_path(args[i])

    return (
        'ffmpeg.exe -y -itsoffset {} -i "{}" -i "{}" {} -acodec copy'
        ' -shortest -map 0:v:0 -map {}:a:0 "{}"'
    ).format(*args)


def join_audio_video_mix(*args):
    args = list(args)
    for i in [1, 2, -1]:
        args[i] = check_path(args[i])

    return (
        'ffmpeg.exe -y -itsoffset {} -i "{}" -i "{}" {}'
        ' -shortest -filter_complex amix "{}"'
    ).format(*args)


def get_duration(*args):
    args = list(args)
    for i in [0]:
        args[i] = check_path(args[i])
    return (
        'ffprobe.exe -v error -show_entries format=duration -of'
        ' default=noprint_wrappers=1:nokey=1 "{}"'
    ).format(*args)


def get_bitrate(*args):
    args = list(args)
    for i in [0]:
        args[i] = check_path(args[i])
    return (
        'ffprobe.exe -v error -show_entries format=bit_rate -of '
        'default=noprint_wrappers=1:nokey=1 "{}"'
    ).format(*args)


def get_wslpath(path):
    return f'wslpath "{path}"'


def get_windows_path(path):
    return f'wslpath -m "{path}"'
