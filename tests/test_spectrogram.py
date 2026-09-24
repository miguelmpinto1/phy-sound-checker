# SPDX-License-Identifier: MIT
import numpy as np

import spectrogram
from spectrogram import LiveSpectrogram, RAMP, SAMPLE_RATE


def _tone(freq, n=SAMPLE_RATE // 10, amp=0.5):
    return amp * np.sin(2 * np.pi * freq * np.arange(n) / SAMPLE_RATE)


def test_silence_is_blank():
    line = LiveSpectrogram(cols=60).render(np.zeros(4410))
    assert line == " " * 60


def test_line_width_matches_cols():
    assert len(LiveSpectrogram(cols=50).render(_tone(1000))) == 50


def test_tone_lights_up_the_right_column():
    view = LiveSpectrogram(cols=60)
    line = view.render(_tone(2000))
    darkest = max(range(60), key=lambda i: RAMP.index(line[i]))
    expected = round(2000 / spectrogram.FREQ_MAX * 60)
    assert abs(darkest - expected) <= 1
    assert line[darkest] == RAMP[-1]


def test_short_block_is_accepted():
    assert len(LiveSpectrogram(cols=40).render(_tone(1500, n=100))) == 40
