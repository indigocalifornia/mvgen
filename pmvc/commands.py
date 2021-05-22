"""ffmpeg commands."""


def convert_to_wav(*args):
    return (
        'ffmpeg -y -i "{}" -af silenceremove=1:0:-50dB "{}"'
    ).format(*args)


def make_segments(*args):
    return (
        'ffmpeg -y -hwaccel cuvid -i "{}" -ss {} -to {} -vcodec copy -acodec copy'
        ' -f segment -segment_time {} -reset_timestamps 1 -map 0:0 "{}"'
    ).format(*args)


def make_segments_gif(*args):
    return (
        'ffmpeg -i {} -movflags faststart -pix_fmt yuv420p -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -r 24 {}.mp4'
    ).format(*args)


def process_segment(*args):
    return (
        'ffmpeg -y -hwaccel cuvid -c:v h264_cuvid -vsync 0 -ss {} -t {} -i "{}" -vb {} -mbd rd'
        ' -trellis 2 -cmp 2 -subcmp 2 -g 100 -c:v h264_nvenc -f mpeg "{}"'
    ).format(*args)


def join(*args):
    return (
        'ffmpeg -hwaccel cuvid -auto_convert 1 -f concat -safe 0 -i "{}" -y -c:v copy {}'
    ).format(*args)


def join_force(**kwargs):
    return (
        'ffmpeg -y -auto_convert 1 -f concat -safe 0 -i "{input_file}"'
        ' -c:v h264_nvenc -movflags faststart -vf "scale='
        '(iw*sar)*min({width}/(iw*sar)\,'
        '{height}/ih):ih*min({width}/(iw*sar)\,{height}/ih), pad='
        '{width}:{height}:({width}-iw*min({width}/iw\,'
        '{height}/ih))/2:({height}-ih*min({width}/iw\,{height}/ih))/2"'
        ' "{output_file}"'
    ).format(**kwargs)


def join_audio_video(*args):
    return (
        'ffmpeg -y -itsoffset {} -i "{}" -i "{}" -vcodec copy -acodec copy'
        ' -shortest -map 0:v:0 -map 1:a:0 "{}"'
    ).format(*args)


def join_audio_video_mix(*args):
    return (
        'ffmpeg -y -itsoffset {} -i "{}" -i "{}" -vcodec copy'
        ' -shortest -filter_complex amix "{}"'
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
