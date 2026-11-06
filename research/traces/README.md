# HD Rumble traces: Switch 2 games

Vibration values that Switch 2 games sent through HID command 214, recorded with `EDEN_HDRUMBLE_TRACE=1` (patch `0002`).

The values are **as the game sent them**. They are captured in `IHidServer::SendNx2VibrationValues`, before the emulator, the per-game intensity or RenHDrum touch them.

| File | Game | Recorded | Length |
|---|---|---|---|
| `ocarina-of-time_0400486024DEC000_session1.csv` | The Legend of Zelda: Ocarina of Time (Switch 2) | 2026-11-05, Lichii `frizti-v1` + this series | 108 s |
| `ocarina-of-time_0400486024DEC000_session2.csv` | The Legend of Zelda: Ocarina of Time (Switch 2) | 2026-11-06, K-code-AI/Lichii `build-4` + this series | 145 s |
| `donkey-kong-bananza_040074A01BF12000.csv` | Donkey Kong Bananza | 2026-11-06, K-code-AI/Lichii `build-4` + this series | 331 s |

All sessions ran on Windows x64 with one wired DualSense Edge as player 1, in normal play: walking, fighting, opening chests and falling in Ocarina of Time; punching and breaking terrain in Donkey Kong Bananza. For session 2 and the Donkey Kong Bananza session, the emulator log confirms the game it booted.

## Format

One row each time a controller side's vibration value changes:

| Column | Meaning |
|---|---|
| `ms` | Milliseconds since the first vibration of the session |
| `mode` | The 64-bit `Mode` argument of command 214. It was `2` in every row. |
| `npad_type`, `npad_id`, `device_index` | The `VibrationDeviceHandle`. Here always style 3 (full key), player 1; device 0 is left, 1 is right. |
| `low_amp`, `low_freq`, `high_amp`, `high_freq` | The 16-byte `VibrationValue`: the two bands' amplitude (0-1) and frequency (Hz) |

A value lasts until the next row for the same side, so statistics should weight each row by how long it held. [`analyze_trace.py`](analyze_trace.py) does that:

```bash
python analyze_trace.py "OoT 1=ocarina-of-time_0400486024DEC000_session1.csv" "DK=donkey-kong-bananza_040074A01BF12000.csv"
```

## Summary

Time-weighted, as printed by `analyze_trace.py`:

| | Ocarina of Time (session 1) | Ocarina of Time (session 2) | Donkey Kong Bananza |
|---|---|---|---|
| Length of play | 108 s | 145 s | 331 s |
| Rows (value changes) | 1,660 | 1,744 | 73,851 |
| Time vibrating (either band > 0) | 8 % | 6 % | 62 % |
| Median amplitude while vibrating | 0.001 | 0.006 | 0.014 |
| 90th percentile | 0.036 | 0.060 | 0.085 |
| 99th percentile | 0.096 | 0.111 | 0.234 |
| Peak | 0.096 | 0.178 | 0.401 |
| Vibrating time at 0.1 or more | 0.0 % | 1.5 % | 8.3 % |
| Vibrating time at 0.2 or more | 0.0 % | 0.0 % | 2.1 % |
| Median low-band frequency (amplitude-weighted) | 182 Hz | 160 Hz | 113 Hz |
| Median high-band frequency (amplitude-weighted) | 258 Hz | 263 Hz | 243 Hz |
| Low-band range | 42-241 Hz | 48-226 Hz | 30-399 Hz |
| High-band range | 182-327 Hz | 144-341 Hz | 40-504 Hz |

Ocarina of Time sends weaker amplitudes than Donkey Kong Bananza at every level: about half at the 99th percentile and the peak, and less at the median. Its frequencies stay in a narrow, ordinary band. Yet on a Switch 2 the game rumbles strongly, while played as sent on a DualSense it is barely felt. A 10x gain with a power curve (exponent 0.64 above a 0.02 knee) brought it close to the console by feel.

An earlier Donkey Kong Bananza session of 227 s, with a peak of 0.534, was summarized in the first version of this repository. Its file was overwritten and is not included here.
