"""Audio utilities."""

import wave
import pywt
import logging
import numpy as np

from scipy import signal

LOG = logging.getLogger(__name__)


def read_wav(filename):
    with wave.open(filename, 'rb') as wf:
        nsamps = wf.getnframes()
        fs = wf.getframerate()
        samps = np.frombuffer(wf.readframes(nsamps), dtype=np.int32)
    return samps, fs


def peak_detect(data):
    # Simple peak detection
    max_val = np.amax(abs(data))
    peak_ndx = np.where(data == max_val)

    # If nothing found then the max must be negative
    if len(peak_ndx[0]) == 0:
        peak_ndx = np.where(data == -max_val)

    return peak_ndx


def bpm_detector(data, fs):
    cA = []
    cD = []
    correl = []
    cD_sum = []
    levels = 4
    max_decimation = 2 ** (levels - 1)
    min_ndx = 60. / 220 * (fs / max_decimation)
    max_ndx = 60. / 40 * (fs / max_decimation)

    min_ndx, max_ndx = int(np.round(min_ndx)), int(np.round(max_ndx))

    for loop in range(0, levels):
        cD = []

        # 1) DWT
        if loop == 0:
            [cA, cD] = pywt.dwt(data, 'db4')
            cD_minlen = int(len(cD) / max_decimation + 1)
            cD_sum = np.zeros(cD_minlen)
        else:
            [cA, cD] = pywt.dwt(cA, 'db4')

        # 2) Filter
        cD = signal.lfilter([0.01], [1 - 0.99], cD)

        # 4) Subtractargs.filename out the mean.

        # 5) Decimate for reconstruction later.
        cD = abs(cD[::(2 ** (levels - loop - 1))])
        cD = cD - np.mean(cD)

        # 6) Recombine the signal before ACF
        #    essentially, each level I concatenate
        #    the detail coefs (i.e. the HPF values)
        #    to the beginning of the array
        cD_sum = cD[0:cD_minlen] + cD_sum

    if [b for b in cA if b != 0.0] == []:
        LOG.info('No audio data for sample, skipping...')
        return

    # Adding in the approximate data as well...
    cA = signal.lfilter([0.01], [1 - 0.99], cA)
    cA = abs(cA)
    cA = cA - np.mean(cA)
    cD_sum = cA[0:cD_minlen] + cD_sum

    # ACF
    correl = np.correlate(cD_sum, cD_sum, 'full')

    midpoint = int(len(correl) / 2)
    correl_midpoint_tmp = correl[midpoint:]

    peak_ndx = peak_detect(correl_midpoint_tmp[min_ndx:max_ndx])
    if len(peak_ndx) > 1:
        LOG.info('No audio data for sample, skipping...')
        return

    peak_ndx_adjusted = peak_ndx[0] + min_ndx

    bpm = 60. / peak_ndx_adjusted * (fs / max_decimation)

    return bpm


def get_bpm(filename, window=3):
    samps, fs = read_wav(filename)

    data = []
    bpm = 0
    nsamps = len(samps)
    window_samps = int(window * fs)
    samps_ndx = 0  # First sample in window_ndx
    max_window_ndx = int(nsamps / window_samps)
    bpms = np.zeros(max_window_ndx)

    # Iterate through all windows
    for window_ndx in range(0, max_window_ndx):
        data = samps[samps_ndx:samps_ndx + window_samps]
        if not ((len(data) % window_samps) == 0):
            raise AssertionError(str(len(data)))

        bpm = bpm_detector(data, fs)

        if bpm is None:
            continue

        bpms[window_ndx] = bpm

        # Iterate at the end of the loop
        samps_ndx = samps_ndx + window_samps

    bpm = np.median(bpms)

    return bpm


def get_beats(path):
    from aubio import source, tempo

    s = source(path)
    o = tempo("specdiff")
    # List of beats, in samples
    beats = []
    # Total number of frames read
    total_frames = 0

    while True:
        samples, read = s()
        is_beat = o(samples)
        # v = max(samples)
        if is_beat:
            this_beat = o.get_last_s()
            beats.append(this_beat)

        total_frames += read
        if read < s.hop_size:
            break

    return beats
