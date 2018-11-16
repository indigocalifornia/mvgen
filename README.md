# pmvc

## Description
pmvc (PMV Creator) generates PMVs for you in an automated fashion. Given some video sources
and an audio file, it will randomly select parts of those videos and collect them together
in a single music video.

## Prerequisites
[Python 3.7](https://www.python.org/downloads/)

[ffmpeg](https://www.ffmpeg.org/)

## Installation
Installation requirements are outlined in `setup.py`. Navigate to the repository folder
and run `python setup.py install`:

```
git clone https://github.com/indigocalifornia/pmvc.git
cd pmvc
python setup.py install
```

## Usage
### Script
Easiest way to use it is to run as a standalone Python script.

1. Order your video sources by folder. E.g. if you have a collection of videos you want to use
in a single PMV, put in a location with structure `raw_directory/vidz/`, where `vidz` will be name of your
PMV *source*, e.g. `/home/user/raw/vidz`.

2. Modify `config.yaml` with your settings. As a bare minimum you will need to change paths to
to "raw", "segments", "work" and "ready" directories, and path to audio file.

**raw_directory**: Absolute path to video sources. In the example above it would be `/home/user/raw`

**segments_directory**: Absolute path to where video segments will be kept. To speed up the process, each original video
will be pre-segmented into small chunks. This is supposed to be a one-time process, so that when you use the same
sources later on, the segments can be re-used. Sometimes however, segmentation will need to be re-run, e.g.
if your segments turn out to be too short.

**work_directory**: Absolute path to directory where temporary work files will be stored.

**ready_directory**: Absolute path to directory where complete files will be copied to.

**audio**: Path to audio file to use.

**bpm**: Value for audio bpm. Can be either
    - a number: value of bpm to use,
    - "auto": use peak detection (useful when bpm is not constant, e.g. audio mixes),
    - path to file: text file with peak locations in seconds, separated by commas,
    - not used (null): attempt to detect constant bpm automatically.
Defaault is null.

**duration**: This is a modifier for number of beats per video segment. For example, if `duration` is 2, then
video segment will last 2 audio beats. Default is 2.

**delete_work_dir**: Delete working directory when finished. Default is true.

**offset**: Audio offset. Use it if audio appears to be out of sync with the video. Default is 0.

**force**: Force video dimensions. Sometimes the final PMV can be glitchy if original videos have different sizes. Use this
parameter to use fixed dimensions encoding. Must be include to numbers for width and height, e.g. `--force 1280 720` will
result in a 1280x720 video. Default is no forcing.

**segment_duration**: Video duration for each chunk to use during video segmentation, in seconds. Default is 2.

**segment_start**: Number of seconds from the beginning of each video to segment from. Default is 0.

**segment_end**: Number of seconds before the ending of each video to segment to. Default is 0.

**force_segment**: Force segmentation even if segments already exist. Default is false.

3. Run `python pmvc.py -s vidz` to create PMV from videos in the `vidz` source (files in the
`/home/user/raw/viz` folder). You can have multiple sources, e.g. `python pmvc.py -s vidz highdef`.

4. Settings can be overridden with command-line parameters, e.g. `python pmvc.py -s vidz --bpm 145`.

5. By default, the script tries to load config file in the same directory. A custom config can be passed using `--config`
argument.

### Package
You can also import `pmvc` as a package.
```
from pmvc.pmvc import PMVC
p = PMVC(...)
p.load_audio(...)
p.generate(...)
p.make_join_file()
p.join(...)
p.finalize(...)
```

# Support
Feel free to contribute by making pull requests.

Ask questions on Reddit: [https://www.reddit.com/r/PMVGeneration](https://www.reddit.com/r/PMVGeneration)

Support me on Patreon: [https://www.patreon.com/indigocalifornia](https://www.patreon.com/indigocalifornia)
