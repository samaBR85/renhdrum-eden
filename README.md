# renhdrum-eden

HD Rumble and DualSense haptics for **Eden-based Switch emulators** (Eden, Eglantine, Lichii and their forks), powered by [RenHDrum](https://github.com/trzz1214/RenHDrum).

This repository is a **patch series**. You apply it to an emulator's source tree and build the emulator yourself. It contains no emulator binaries, no keys, no firmware and no game data.

| Patch | What it adds |
|---|---|
| `0001` | Vibration routed through RenHDrum: HD Rumble packets for Switch controllers, 48 kHz audio haptics for a wired DualSense. SDL3 built from source with RenHDrum's HD Rumble transport patches. |
| `0002` | An **HD Rumble** settings dialog (Controls > Vibration > Configure > HD Rumble...). |
| `0003` | Per-game **Intensity** and **Weak rumble boost**, for games that send very weak vibration (see [Findings](#findings-ocarina-of-time)). |
| `0004` | `EDEN_HDRUMBLE_TRACE=1`: writes every vibration value a game sends to a CSV, for studying a game's HD Rumble. Optional. |

Patches `0002`-`0004` depend on `0001`. `0004` is a diagnostic tool and can be left out.

---

## What it does

Switch and Switch 2 games describe vibration as two bands (low and high), each with an amplitude and a frequency, sent every few milliseconds. Most emulators collapse that into a plain "motor strength" rumble. With these patches, the emulator hands the full signal to RenHDrum, which plays it on the controller:

| Controller | Connection | What you get |
|---|---|---|
| Nintendo Switch Pro Controller, Joy-Con | USB or Bluetooth | Real HD Rumble packets: 5 ms AM/FM envelope, frequency changes inside a packet, "crisp notes" (stronger attack, softer sustain), Bluetooth pacing that keeps input lag down |
| Sony DualSense / DualSense Edge | **USB** | The vibration played as 4-channel 48 kHz audio on the controller's haptic voice coils, the most detailed rumble available on PC |
| Sony DualSense / DualSense Edge | Bluetooth | Standard rumble (unchanged) |
| Other controllers | any | Standard rumble (unchanged) |

Switch 2 games send their vibration through HID command 214 (`SendNx2VibrationValues`), which Eglantine and Lichii already implement, so their HD Rumble reaches RenHDrum too.

For how HD Rumble works and how RenHDrum reproduces it, read the RenHDrum author's [research notebook](https://ryuhdr.threedola.workers.dev) and the [research notes in the RenHDrum repository](https://github.com/trzz1214/RenHDrum/tree/main/docs/research).

---

## Compatibility

The series was written against **Lichii `frizti-v1`** ([Frizti/Lichii](https://github.com/Frizti/Lichii)), which is where it was built and played, and carried unchanged to `frizti-v2`. Weekly CI checks that it still applies to these trees:

| Tree | Branch | Applies | Built and played |
|---|---|---|---|
| [Frizti/Lichii](https://github.com/Frizti/Lichii) | `frizti-v1` tag | ✅ | ✅ Windows x64, MSVC |
| [Frizti/Lichii](https://github.com/Frizti/Lichii) | `frizti-v2` tag | ✅ | ✅ built (Windows x64, MSVC) |
| [Frizti/Lichii](https://github.com/Frizti/Lichii) | `nx2` | ✅ | not yet |
| [zortos293/Lichii](https://github.com/zortos293/Lichii) | `nx2` | ✅ | not yet |
| [Djihads80/Eglantine](https://github.com/Djihads80/Eglantine) | `nx2` | ✅ | not yet |

[![Check patches](https://github.com/samaBR85/renhdrum-eden/actions/workflows/check-patches.yml/badge.svg)](https://github.com/samaBR85/renhdrum-eden/actions/workflows/check-patches.yml)

Upstream [Eden](https://git.eden-emu.dev/eden-emu/eden) and other forks share the same input code and should take the series with little or no change, but have not been tried. If you port it to another fork, a pull request adding it to this table is welcome.

Only Windows x64 (MSVC) has been built so far. The code itself is not Windows-specific (RenHDrum builds a `.so` and a `.dylib` too), but the CMake part links `renhdrum.dll.lib` and needs a small change for other platforms.

---

## Applying the patches

```bash
# in your emulator checkout
git am --3way /path/to/renhdrum-eden/patches/*.patch
```

To take only some of them, pass the files you want, in order (`0001` is always needed). If a patch does not apply, `git am --3way` leaves conflict markers. Fix them, then `git add` the files and run `git am --continue`.

---

## Building

### 1. Build RenHDrum

You need [Rust](https://rustup.rs/).

```bash
git clone https://github.com/trzz1214/RenHDrum.git
cd RenHDrum
cargo build --release
```

This produces `target/release/renhdrum.dll` and `target/release/renhdrum.dll.lib`. CMake looks for the RenHDrum checkout next to the emulator source (`../RenHDrum`); point it elsewhere with `-DRENHDRUM_DIR=...`. The configure step stops with a clear message if RenHDrum is not built.

### 2. Configure the emulator

Use the emulator's normal build (its `docs/Build.md`), with **two extra rules**:

- **SDL3 must be built from source**, so the RenHDrum SDL patches get applied. Windows builds download a prebuilt SDL3 by default, which does not have them. Add:
  `-DYUZU_USE_BUNDLED_SDL3=OFF -DSDL3_FORCE_BUNDLED=ON`
  The configure log then shows `patching file src/joystick/hidapi/SDL_hidapi_switch.c` and friends.
- **Point CMake at RenHDrum** if it is not in `../RenHDrum`: `-DRENHDRUM_DIR=D:/path/to/RenHDrum`

The Windows configure line used for the tested build (Qt 6.8.3 `msvc2022_64`, Ninja, Visual Studio 2022 Build Tools environment loaded):

```bat
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release ^
  -DYUZU_TESTS=OFF -DYUZU_CMD=ON -DYUZU_ROOM=OFF -DYUZU_USE_BUNDLED_QT=OFF ^
  -DYUZU_USE_BUNDLED_SDL3=OFF -DSDL3_FORCE_BUNDLED=ON ^
  -DVulkanHeaders_FORCE_BUNDLED=ON -DVulkanUtilityLibraries_FORCE_BUNDLED=ON ^
  -DCMAKE_PREFIX_PATH=C:/Qt/6.8.3/msvc2022_64 ^
  -DRENHDRUM_DIR=C:/src/RenHDrum
cmake --build build
```

Build tips:

- **CMake from Visual Studio.** If another CMake comes first on your `PATH` (MSYS2 or devkitPro, for example), call Visual Studio's own `cmake.exe` instead. A foreign CMake fails at "Detecting C compiler ABI info".
- **Shader compiler.** `glslangValidator` must be on `PATH`. The [glslang releases](https://github.com/KhronosGroup/glslang/releases) ship it as `glslang.exe`; copy it to `glslangValidator.exe`.
- **`renhdrum.dll`.** The build copies it next to the emulator executable. When you package the emulator, ship it alongside.

---

## Using it

Nothing to switch on: a supported controller uses RenHDrum as soon as it connects. The emulator log confirms it:

```
Initialized RenHDrum DualSense DSP for controller 054C:0DF2
DualSense haptics audio opened on "Speakers (DualSense Edge Wireless Controller)" (... 4 ch 48000 Hz ...)
```

or, for a Switch controller:

```
Initialized RenHDrum engine for Switch controller 057E:2009 (BT: false)
RenHDrum HD Rumble wired: 15 ms, no-queue (written while SDL is idle), card 3 5 ms envelope, cards 5 + 7, card 8 crisp notes
```

### The HD Rumble dialog (patch 0002)

Open it from **Emulation > Configure > Controls > Vibration: Configure > HD Rumble...**

- **Enabled** turns RenHDrum on or off for every controller. Off means the emulator's standard rumble.
- **Intensity** and **Weak rumble boost** (patch 0003) apply to all controllers. See below.
- **Switch Controller**
  - **Wired:** packet interval (15 ms is the console's rate), 5 ms envelope, frequency changes inside a packet, crisp notes.
  - **Bluetooth:** level 1 Stable / 2 Balanced / 3 Quality (60 / 45 / 35 ms), send right after an input report, 5 ms envelope while the link is idle, crisp notes.
- **DualSense:** use the voice coils, volume, crisp notes.
- **Restore Defaults** goes back to RenHDrum's recommended mode.

Changes reach connected controllers on their next vibration, without restarting the game. To feel them right away, hold a controller button in the Vibration dialog.

The per-player vibration strength in the Vibration dialog still applies on top. Keep it at 100 %. **Enable Accurate Vibration** makes no difference with these patches: patch 0001 removes the 15 ms filter it used to bypass, because RenHDrum paces the packets itself.

### Per-game intensity and weak rumble boost (patch 0003)

| Setting | Range | What it does |
|---|---|---|
| `hd_rumble_gain` | 25-1000 % | Multiplies the amplitudes the game sends. |
| `hd_rumble_low_boost` | 0-100 % | A power curve after the gain: lifts weak vibrations more than strong ones. Exponent 1.0 at 0 %, 0.4 at 100 %. Below 0.02 the curve turns quadratic, so the near-silent values a game sends between hits do not become a constant buzz. |

Both are per-game settings. The global value stays at 100 % / 0 %, and a game gets its own values in its custom config. On Windows that file is `%APPDATA%\eden\config\custom\<title id>.ini`, under `[Controls]`:

```ini
[Controls]
hd_rumble_gain\use_global=false
hd_rumble_gain\default=false
hd_rumble_gain=1000
hd_rumble_low_boost\use_global=false
hd_rumble_low_boost\default=false
hd_rumble_low_boost=60
```

With the game running, the HD Rumble dialog shows that game's values. Changes there apply right away, but write the final values into the file above to keep them.

### Vibration trace (patch 0004)

Set `EDEN_HDRUMBLE_TRACE=1`, either in the environment or in `nx2_switches.txt` next to the emulator. Every change of a vibration value sent through command 214 is then written to `<log dir>/hdrumble_trace.csv`: time, mode, controller, low/high amplitude, low/high frequency. The file is created on the first vibration and replaced each session. It stops after 3 million lines.

---

## Findings: Ocarina of Time

The trace was recorded on Lichii with a wired DualSense Edge, about two minutes of play per game:

| | The Legend of Zelda: Ocarina of Time (Switch 2, `0400486024DEC000`) | Donkey Kong Bananza |
|---|---|---|
| Command / mode | 214, Mode 2 | 214, Mode 2 |
| Peak amplitude | **0.096** | 0.534 |
| Median amplitude (when vibrating) | 0.003 | 0.009 |
| Samples above 0.1 | **none** | ~1,500 |
| Frequency range | 40-330 Hz | 40-510 Hz |

Ocarina of Time never sends an amplitude above 0.1, yet it rumbles strongly on a Switch 2. Played as sent, it feels as weak as an emulator's default rumble. **Intensity 1000 % with weak rumble boost 60 %** came close to the console.

This fits the "equalization between hardware generations" that the RenHDrum author found in Nintendo patent filings (see [research/11](https://github.com/trzz1214/RenHDrum/blob/main/docs/research/11-switch2-hd-rumble.md)): the console seems to scale Mode 2 amplitudes for its own actuators. With traces from more games, it might become a curve applied automatically rather than per game.

---

## Known limitations

- **Command 213 is a stub** in Eglantine and Lichii. A game that vibrates only through it stays silent; this series does not change that.
- **Xbox One controllers:** the four-motor translation RenHDrum supports is not in this series yet. They use standard rumble.
- **Switch 2 Pro Controller and Joy-Con 2:** not supported by RenHDrum yet.
- **DualSense over Bluetooth** uses standard rumble. RenHDrum has Bluetooth haptics (report `0x32`), but this series does not wire it up yet.
- **Reorganizing the code.** Most of patch `0001` lives inside `sdl_driver.cpp`. Moving it to its own file, with a CMake option and a downloaded prebuilt `renhdrum.dll`, would make it easier to carry in other forks. That is planned.

---

## Credits

This series is a port and extension of other people's work:

- **[RenHDrum](https://github.com/trzz1214/RenHDrum)** by **Three-Dola** ([trzz1214](https://github.com/trzz1214)): the HD Rumble and DualSense haptics engine, the [SDL3 HD Rumble patches](https://github.com/trzz1214/RenHDrum/tree/main/integrations/sdl3/sdl3-patches), and the [Brontide reference patches](https://github.com/trzz1214/RenHDrum/tree/main/integrations/brontide) that patch `0001` is ported from. Their [research notebook](https://ryuhdr.threedola.workers.dev) explains the whole subject. RenHDrum in turn credits dekuNukem, the Switchbrew wiki contributors, felipearmat, rei-github, ClearlyClaire, CTCaer, Nielk1, egormanga, the SDL team and others: see [its credits](https://github.com/trzz1214/RenHDrum#research-credits--acknowledgments) and [NOTICE](https://github.com/trzz1214/RenHDrum/blob/main/NOTICE).
- **neo Luigi**, for HID command 214 (`SendVibrationValuesInMode`) dispatching in [Eglantine PR #155](https://github.com/eglantine-emu/eglantine/pull/155). That is what carries Switch 2 vibration to the input layer.
- **[Eden](https://git.eden-emu.dev/eden-emu/eden)** and the yuzu project, the emulator these trees come from.
- **[Eglantine](https://github.com/Djihads80/Eglantine)** (Djihads80), the Switch 2 Eden fork; **[Lichii](https://github.com/zortos293/Lichii)** (zortos293); and **[Frizti/Lichii](https://github.com/Frizti/Lichii)** (Frizti), the tree this series was built and tested on.
- **[PokeDinner](https://github.com/Franseven/PokeDinner)** by Franseven, the base of Brontide-NS2, RenHDrum's own Switch 2 testbed.
- **[SDL](https://github.com/libsdl-org/SDL)** (Sam Lantinga, Valve and contributors).

The port to Lichii, the HD Rumble dialog, the per-game intensity and boost, the trace and the Ocarina of Time findings are by **[samaBR85](https://github.com/samaBR85)**, written with [Claude Code](https://claude.com/claude-code).

---

## License

- **The patches** modify GPL-licensed emulator code and include code ported from RenHDrum's Brontide patches (GPL-3.0-or-later). They are licensed under the **GNU General Public License v3.0 or later**; see [LICENSE](LICENSE).
- **RenHDrum** itself is MIT OR Apache-2.0. Its **SDL3 patches**, which patch `0001` adds under `.patch/sdl3/`, are under the zlib license. Both keep their own licenses: see the [RenHDrum repository](https://github.com/trzz1214/RenHDrum).

Nintendo Switch, Joy-Con and Pro Controller are trademarks of Nintendo. PlayStation and DualSense are trademarks of Sony Interactive Entertainment. This project is not affiliated with Nintendo, Sony or the RenHDrum author. Bring your own legally dumped games and keys.
