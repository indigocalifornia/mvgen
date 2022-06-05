# mvgen

## Description
`mvgen` generates video mixes for you in an automated fashion. Given a set of video sources
and one audio file, it will randomly select clips from those videos, stich them together and overlay the audio file.

## Prerequisites
[Python 3.6.7](https://www.python.org/downloads/)
[ffmpeg](https://www.ffmpeg.org/)

## Installation
`python setup.py install`

## Usage
### As a script

1. Order your video sources by folder. E.g. if you have a collection of videos you want to use in a single mix, put in a location with structure `src_directory/vidz/`, where `vidz` will be name of your mix *source*, e.g. `/home/user/raw/vidz`.

2. Edit `config.yaml` file with your settings. As a bare minimum you will need to change paths to to "raw", "segments", "work" and "ready" directories, and path to audio file.

**src_directory**: Absolute path to video sources. In the example above it would be `/home/user/raw`

**segments_directory**: Absolute path to where video segments will be kept. To speed up the process, each original video will be pre-segmented into small chunks. This is supposed to be a one-time process, so that when you use the same sources later on, the segments can be re-used. Sometimes however, segmentation will need to be re-run, e.g. if your segments turn out to be too short.

**work_directory**: Absolute path to directory where temporary work files will be stored.

**ready_directory**: Absolute path to directory where complete files will be copied to.

**audio**: Path to audio file to use.

**bpm**: Value for audio bpm. Can be either
    - a number: value of bpm to use,
    - "auto": use peak detection (useful when bpm is not constant, e.g. audio mixes),
    - path to file: text file with peak locations in seconds, separated by commas,
    - not used (null): attempt to detect constant bpm automatically.
Default is null.

**duration**: This is a modifier for number of beats per video segment. For example, if `duration` is 2, then video segment will last 2 audio beats. Default is 2.

**delete_work_dir**: Delete working directory when finished. Default is true.

**offset**: Audio offset. Use it if audio appears to be out of sync with the video. Default is 0.

**force**: Force video dimensions. Sometimes the final mix can be glitchy if original videos have different sizes. Use this parameter to use fixed dimensions encoding. Must be include to numbers for width and height, e.g. `--force 1280 720` will result in a 1280x720 video. Default is no forcing.

**segment_duration**: Video duration for each chunk to use during video segmentation, in seconds. Default is 2.

**segment_start**: Number of seconds from the beginning of each video to segment from. Default is 0.

**segment_end**: Number of seconds before the ending of each video to segment to. Default is 0.

**force_segment**: Force segmentation even if segments already exist. Default is false.

3. Run `python main.py -s vidz` to create mix from videos in the `vidz` source (files in the `/home/user/raw/viz` folder). You can have multiple sources, e.g. `python main.py -s vidz highdef`.

4. Settings can be overridden with command-line parameters, e.g. `python main.py -s vidz --bpm 145`.

5. By default, the script tries to load config file in the same directory. A custom config can be passed using `--config` argument.

### As a package
You can also import `mvgen` as a package.
```python
from mvgen.mvgen import MVGen

g = MVGen(...)
g.load_audio(...)
g.generate(...)
g.make_join_file()
g.join(...)
g.finalize(...)
```
#### Example scenario

Suppose you have a collection of videos with a particular theme and you store them in `/home/user/raw/vidz`. You know bpm of your audio file, which is located at `/home/user/audio/song.mp3`. The audio doesn't need offsetting, because its beats start at zero and your videos come from the same source, with same codec and dimensions. You want a slower video with 4 beats per segment, and with bpm of 128 this means that segments will change every 1.875 seconds. This means that segments with 2 second duration will be more or less OK. In addition, your videos contains advertisements in the beginning and the end, so you decide to remove first and last 10 seconds of the footage.

And run the script with `python main.py -s vidz`. If later you want to run the same source with different file, you can just run `python main.py -s vidz --audio /home/user/audio/song2.mp3 --bpm 145`.

The generated mix will be in `/home/user/ready` with a unique name. In addition, you will find a text file with the same name that includes name of audio used and timestamps of the videos used (named using `{counter}_{original filename}_{segment_counter}` pattern).


