# mvgen - Automated video generation

## Description
`mvgen` generates video mixes for you in an automated fashion. Given a set of video sources
and one audio file, it will randomly select clips from those videos, stich them together and overlay the audio file.

## Prerequisites
[Python 3.6.7](https://www.python.org/downloads/)
[ffmpeg](https://www.ffmpeg.org/)

When installing FFmpeg on Windows you'll need to make sure you set your environmental variables to the `bin` directory contained within the FFmpeg download. Example tutorial [here](https://www.wikihow.com/Install-FFmpeg-on-Windows).

## Visuall C++ Requirements
#### Required for compiling numpy, scipy, pandas, and PyWavelet on Windows
[Visual C++ Build Tools](https://visualstudio.microsoft.com/downloads/?q=build+tools)

Download the Visual Studio Installer, go through a custom installation and install the below tools.

* Windows Universal C Runtime
* C++ Build Tools core features
* MSVC v143 - VS 2022 C++ x64/x86 build tools
* C++ CMake tools for Windows
* C++ AddressSanitizer
* C++ core features
* Windows 10 SDK

## Installation
`pip install -r requirements.txt` 

## Usage
### As a script
1. Place your source video files within a sub directory of `src_directory`. For example `vidz`.

2. Update `config.yaml` file with your settings. As a bare minimum you will need to change paths to to "src_directory", "segments_directory", "work_direcotry", "ready_directory", and "audio". 
    
3. Run `python main.py -s vidz` to create mix from videos in the `vidz` source (files in the `/home/user/raw/viz` folder). You can have multiple sources, e.g. `python main.py -s vidz highdef`.

4. Settings can be overridden with command-line parameters, e.g. `python main.py -s vidz --bpm 145`.

5. By default, the script tries to load config file in the same directory. A custom config file can be passed using `--config` argument.

## Config
The config file is expected in the same directory as program execution. 

```yaml
src_directory: /path/to/directory # Directory containing video source files
segments_directory: /path/to/directory # Directory where temporary video segments are stored
work_directory: /path/to/directory # Directory where temporary work files are stored
ready_directory: /path/to/directory # Directory where the final video will be stored
audio: /path/to/file # Directory containing your source audio file
delete_work_dir: true # To delete or not delete the working directory when finished. Default is true
duration: 2 # Number of beats per video segment
bpm: null # Value for audio beats per minute(bpm). Options: `null`, `integer` The BPM to use, `auto` Detects BPM to use. Great for non constant BPM like audio mixes, and `/path/to/file` for a file containing peak locations in seconds, separated by commas. Default is `null`
keep_work_dir: false # Default false. To delete or not delete the work directory.
offset: 0 # Audio offset. Used for syncing audio with the beat.
force: false # Force video dimensions. Use this to set the output resolution. Ex. 1280 720
segment_duration: 2 # Duration of each video segment in seconds. Default is 2.
segment_start: 0 # Number of seconds into your video clips to start pulling segments from.
segment_end: 0 # Number of seconds before the end of the video to stop pulling segments from.
force_segment: false # Force segmentation even if segments already exist. Default is false
audio_mode: "audio" # 'audio', 'original', 'mix'. audio uses the audio from the audio directory. original uses the original audio from the video clips. mix uses the audio from the audio file and the video clips and mixes them. 
```
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

