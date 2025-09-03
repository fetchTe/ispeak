# ispeak

A keyboard-centric CLI speech-to-text tool that works wherever you can type, be it [`vim`](https://www.vim.org/), [`emacs`](https://www.gnu.org/software/emacs/), [`firefox`](https://www.firefox.com), or AI tools like [`aider`](https://github.com/paul-gauthier/aider), [`codex`](https://github.com/openai/codex), and [`claude`](https://claude.ai/code)

<!-- 
<img align="right" width="200" height="217" alt="ispeak logo" src="#" />
 -->

+ **Keyboard Output** - Transcribed speech as keyboard (press/release) events
+ **Inline UX** - Recording indicator is displayed in the active buffer & self-deletes
+ **Hotkey-Driven & Configurable** - Models, delete, and replace commands
+ **Local & Fast** - Powered via [faster-whisper](https://github.com/SYSTRAN/faster-whisper) with help from [RealtimeSTT](https://github.com/KoljaB/RealtimeSTT)
+ **Cross-Platform** - Works on Linux/macOS/Windows with GPU or CPU



## Quick Start

1. **Run**: `ispeak` (add `-b <program>` to target a specific executable)
2. **Activate**: Press the hotkey (default `end`) - the 'recording indicator' is text-based (default `;`)
3. **Record**: Speak freely; no automatic timeout or voice activity cutoff
4. **Complete**: Press the hotkey again to delete the indicator and transcribe your speech (abort via `escape`)
5. **Output**: Your words appear as typed text at your cursor's location


> **IMPORTANT**: The output goes to the application that currently has keyboard focus, which allows you to use the same `ispeak` instance between applications. This may be a feature or a bug.


### ▎Install

```bash
#> copy'n'paste
uv tool install ispeak
pip install ispeak      # python’s default package installer
```
> [`uv`](https://docs.astral.sh/uv/) is a python package installer

```bash
#> clone'n'install
git clone https://github.com/fetchTe/ispeak
cd ispeak

# global install
uv tool install .          # with CUDA (default)
uv tool install ".[cpu]"   # CPU-only (no CUDA)
uv tool install ".[cu118]" # CUDA v11.8
uv tool install ".[cu128]" # CUDA v12.8

# local/dev install
uv sync                    # with CUDA (default)
uv sync --extra cpu        # CPU-only (no CUDA)
uv sync --extra cu118      # CUDA v11.8
uv sync --extra cu128      # CUDA v12.8

# pip/dev install (with CUDA)
pip install RealtimeSTT pynput rich

# pip/dev install (CPU-only)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install RealtimeSTT pynput rich
```


### ▎Usage

```bash
# USAGE (v0.1.0)
  ispeak [options...]

# OPTIONS
  -b, --binary      Executable to launch with voice input
  -c, --config      Path to configuration file
  -l, --log-file    Path to voice transcription append log file
  -n, --no-output   Disable typing output and record indicator
  -s, --setup       Configure voice settings
  -t, --test        Test voice input functionality
  --config-show     Show current configuration

# EXAMPLES
ispeak --setup         # Interactive configuration wizard
ispeak -b vim          # Start with vim
ispeak -l words.log    # Log transcriptions to file

# DEV/LOCAL USAGE
uv run ispeak --setup  # via uv
```
<br/>



## Configuration
> **Recommend** using `ispeak --setup` for initial setup

```json
{
  "ispeak": {
    "binary": null,
    "push_to_talk_key": "end",
    "push_to_talk_key_delay": 0.2,
    "escape_key": "esc",
    "log_file": null,
    "no_output": false,
    "recording_indicator": ";",
    "delete_keywords": ["delete", "undo"],
    "strip_whitespace": true
  },
  "realtime_stt": {
    "model": "tiny",
    "compute_type": "auto",
    "enable_realtime_transcription": false,
    "ensure_sentence_ends_with_period": true,
    "ensure_sentence_starting_uppercase": true,
    "language": "auto",
    "no_log_file": true,
    "normalize_audio": true,
    "post_speech_silence_duration": 1.0,
    "spinner": false
  },
  "replace": null
}
```

1. **Environment Variable**: Set `ISPEAK_CONFIG` environment variable to specify a custom config file path
2. **Platform-Specific Default**: `<config_dir>/ispeak/ispeak.json`
   - **macOS**: `~/Library/Preferences/ispeak/ispeak.json`
   - **Windows**: `%APPDATA%\ispeak\ispeak.json` (or `~/AppData/Roaming/ispeak/ispeak.json`)
   - **Linux**: `$XDG_CONFIG_HOME/ispeak/ispeak.json` (or `~/.config/ispeak/ispeak.json`)
3. **Local Fallback**: `./ispeak.json` in the current working directory
<br/>

### ▎ `ispeak`

- `binary` (str/null): Default executable to launch with voice input
- `delete_keywords` (list/bool): Words that trigger deletion of previous input via backspace (must be exact)
- `escape_key` (str/null): Key to cancel current recording without transcription
- `log_file` (str/null): Path to file for logging voice transcriptions
- `no_output` (bool): Disable typing any output or recording indicator (still logs)
- `push_to_talk_key_delay` (float): Brief delay after hotkey press to prevent input conflicts
- `push_to_talk_key` (str/null): Hotkey to start/stop recording sessions
- `strip_whitespace` (bool): Remove extra whitespace from transcribed text
- `recording_indicator` (str/null): Visual indicator typed when recording starts **must be a typeable character**

> Hotkeys work via [pynput](https://github.com/moses-palmer/pynput) and support: <br/>
> ╸ Simple characters: `a`, `b`, `c`, `1`, etc. <br/>
> ╸ Special keys: `end`, `alt_l`, `ctrl_l` - (see [pynput Key class](https://github.com/moses-palmer/pynput/blob/master/lib/pynput/keyboard/_base.py#L162)) <br/>
> ╸ Key combinations: `<ctrl>+<alt>+h`, `<shift>+<space>`<br/>
<br/>

### ▎`realtime_stt`
Full documentation available in [./RealtimeSTT.md](RealtimeSTT.md) or the [RealtimeSTT](https://github.com/KoljaB/RealtimeSTT) repository.

- `model` (str): Model size or path to local CTranslate2 model (for English variants append `.en`)
    - `tiny`: Ultra fast, decent accuracy (~39MB, CPU/GPU)
    - `base`: Balance of speed/accuracy (~74MB, CPU/GPU ~1GB/VRAM)
    - `small`: Better accuracy (~244MB, GPU ~2GB/VRAM)
    - `medium`: Better accuracy (~769MB, GPU ~3GB/VRAM)
    - `large-v1`/`large-v2`: Best accuracy (~1550MB, GPU ~4GB/VRAM)
- `compute_type` (str): Computation type for transcription (`"auto"` for automatic selection)
- `enable_realtime_transcription` (bool): Enable continuous transcription (2x computation)
- `ensure_sentence_ends_with_period` (bool): Add periods to sentences without punctuation
- `ensure_sentence_starting_uppercase` (bool): Ensure sentences start with uppercase letters
- `language` (str): Language code (`en`, `es`, `fr`, `de`, etc) or `"auto"` for automatic detection
- `no_log_file` (bool): Skip debug log file creation
- `normalize_audio` (bool): Normalize audio range before processing for better transcription quality
- `post_speech_silence_duration` (float): How long to wait after you stop talking (default: 1.0)
- `spinner` (bool): Show spinner animation (set to `false` to avoid terminal conflicts)
<br/>

### ▎ `replace`

Regex replacement rules - either a dict of pattern/replacement pairs or a list of JSON file paths that contain a dict of pattern/replacement pairs. Rules are applied to the transcribed text; best suited for simple operations. 

```json
{
  "replace": {
    " one ": "1",
    "read me": "README",

    "(\\s+)(semi)(\\s+)": ";\\g<3>",
    "(\\s+)(comma)(\\s+)": ",\\g<3>",

    "\\s*question\\s*mark\\s*": "?",
    "\\s*exclamation\\s*mark\\s*": "!",

    "\\s*open\\s*paren\\s*": "(",
    "\\s*close\\s*paren\\s*": ")",

    "/^start/m": "BEGIN",
    "/finish$/m": "END"
  }
}
```
> tests: `./tests/test_replace.py`



<br/>



## Troubleshooting

+ **Hotkey/Keyboard Issues**: Check/grant permissions see [linux](#linux), [macOS](#linux), [windows](#windows)
+ **Recording Indicator Misfire(s)**: Increase `push_to_talk_key_delay` (try 0.2-1.0)
+ **Transcription Issues**: Try the CPU-only installation and/or the following minimal test code to isolate the problem:

```python
# test_audio.py -> uv run ./test_audio.py
from RealtimeSTT import AudioToTextRecorder

def process_text(text):
    print(f"Transcribed: {text}")

if __name__ == '__main__':
    print("Testing RealtimeSTT - speak after you see 'Listening...'")
    try:
        recorder = AudioToTextRecorder()
        while True:
            recorder.text(process_text)
    except KeyboardInterrupt:
        print("\nTest completed.")
    except Exception as e:
        print(f"Error: {e}")
```

<br/>



## Platform Limitations
> These limitations/quirks come from the `pynput` [docs](https://pynput.readthedocs.io/en/latest/limitations.html)


### ▎Linux
When running under *X*, the following must be true:
- An *X server* must be running
- The environment variable `$DISPLAY` must be set

When running under *uinput*, the following must be true:
- You must run your script as root, to that is has the required permissions for *uinput*

The latter requirement for *X* means that running *pynput* over *SSH* generally will not work. To work around that, make sure to set `$DISPLAY`:

``` bash
$ DISPLAY=:0 python -c 'import pynput'
```

Please note that the value `DISPLAY=:0` is just an example. To find the
actual value, please launch a terminal application from your desktop
environment and issue the command `echo $DISPLAY`.

When running under *Wayland*, the *X server* emulator `Xwayland` will usually run, providing limited functionality. Notably, you will only receive input events from applications running under this emulator.


### ▎macOS
Recent versions of *macOS* restrict monitoring of the keyboard for security reasons. For that reason, one of the following must be true:

- The process must run as root.
- Your application must be white listed under *Enable access for assistive devices*. Note that this might require that you package your application, since otherwise the entire *Python* installation must be white listed.
- On versions after *Mojave*, you may also need to whitelist your terminal application if running your script from a terminal.

All listener classes have the additional attribute `IS_TRUSTED`, which is `True` if no permissions are lacking.


### ▎Windows
Virtual events sent by *other* processes may not be received. This library takes precautions, however, to dispatch any virtual events generated to all currently running listeners of the current process.

<br/>



## Development

### ▎Structure

```
ispeak/
├── src/ispeak/            # Main package source
│   ├── __init__.py            # Package initialization and exports
│   ├── cli.py                 # Command-line interface and interactive setup
│   ├── config.py              # Configuration management and validation
│   ├── core.py                # Core voice input and text processing logic
│   └── recorder.py            # Audio recording abstraction layer
├── main.py                    # Development entry point
├── ispeak                 # Shell helper script
├── ispeak.json            # Local fallback configuration
├── pyproject.toml             # Project metadata and dependencies
└── README.md                  # Documentation
```


### ▎Development Commands

```bash
# Type checking
uv run pyright                 # Type check all source files

# Code linting and formatting
uv run ruff check .            # Lint code
uv run ruff check . --fix      # Auto-fix linting issues
uv run ruff format .           # Format code

# Run in development mode
uv run ispeak --setup      # Test setup wizard
uv run ispeak --test       # Test voice input
```

<br/>



## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Install development dependencies: `uv sync --group dev`
4. Make your changes following the existing code style
5. Run quality checks & test:

   ```bash
   uv run ruff check . --fix    # Fix linting issues
   uv run ruff format .         # Format code
   uv run pyright               # Type checking
   uv run pytest                # Run Test
   ```

6. Commit your changes: `git commit -m 'feat: add amazing feature'`
7. Push to your branch: `git push origin feature/amazing-feature`
8. Open a Pull Request with a clear description of your changes

<br/>



## Acknowledgments

- **[`RealtimeSTT`](https://github.com/KoljaB/RealtimeSTT)** - A swell wrapper around [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper) that powers the speech-to-text engine
- **[`pynput`](https://github.com/moses-palmer/pynput)** - Cross-platform controller and monitorer for the keyboard
- **[`whisper`](https://github.com/openai/whisper)** - The foundational speech-to-text recognition model


<br/>



## License

```
MIT License

Copyright (c) 2025 te <legal@fetchTe.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
