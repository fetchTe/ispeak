<h1>
ispeak
<img align="right" src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white" />
<a href="https://mibecode.com">
  <img align="right" title="≥95% Human Code" alt="≥95% Human Code" src="https://mibecode.com/badge.svg">
</a>
</h1>



An inline speech-to-text tool that works wherever you can type; [`vim`](https://www.vim.org/), [`emacs`](https://www.gnu.org/software/emacs/), [`firefox`](https://www.firefox.com), and CLI/AI tools like [`aider`](https://github.com/paul-gauthier/aider), [`codex`](https://github.com/openai/codex), [`claude`](https://claude.ai/code), or whatever you fancy

<img align="right"  width="188" height="204" alt="ispeak logo" src="https://raw.githubusercontent.com/fetchTe/ispeak/master/docs/ispeak-logo.png" />

+ **Multilingual, Local, Fast** - Powered via [faster-whisper](https://github.com/SYSTRAN/faster-whisper) 
+ **Transcribed Speech** - As keyboard (type) or clipboard (copy) events
+ **Inline UX** - Recording indicator displayed in the active buffer & self-deletes
+ **Hotkey-Driven & Configurable** - Tune the operation/model to your liking
+ **Post-Transcribe Plugin Pipeline** - [Replace](#-replace), [text2num](#-text2num), and [num2text](#-num2text)
+ **Cross-Platform** - Works on [Linux](#linux)/[macOS](#macos)/[Windows](#windows) with GPU or CPU

<br />

<img align="center" alt="ispeak-demo-short" src="https://raw.githubusercontent.com/fetchTe/ispeak/master/docs/ispeak-demo-short.gif">


## Quick Start


1. **Run**: `ispeak` (add `-b <program>` to target a specific executable)
2. **Activate**: Press the hotkey (default `shift_l`) - the 'recording indicator' is text-based (default `;`)
3. **Record**: Speak freely; no automatic timeout or voice activity cutoff
4. **Complete**: Press the hotkey again to delete the indicator and transcribe your speech (abort via `escape`)
5. **Output**: Your words appear as typed text at your cursor's location


> **IMPORTANT**: The output goes to the application that currently has keyboard focus, which allows you to use the same `ispeak` instance between applications. This may be a feature or a bug.


### ▎Install

```sh
#> copy'n'paste system/global install
pip install ispeak
uv tool install ispeak
# cpu-only + plugins; it's better to simply clone & run: uv tool install ".[cpu,plugin]"
uv pip install --system "ispeak[plugin]" --torch-backend=cpu
```
> [`uv`](https://docs.astral.sh/uv/) is a python package installer


```sh
#> clone'n'install
git clone https://github.com/fetchTe/ispeak && cd ispeak

# global install (extra: cpu, cu118, cu128, plugin)
uv tool install ".[plugin]"      # CUDA + plugins
uv tool install ".[cpu,plugin]"  # CPU-only (no CUDA) + plugins

# local install (extra: cpu, cu118, cu128, plugin)
uv sync --group dev                # CUDA (default) + dev (ruff, pyright, pytest)
uv sync --extra cpu --extra plugin # CPU-only (no CUDA) + plugins

# pip install + plugins
pip install RealtimeSTT pynput pyperclip num2words text2num
```


### ▎Usage

```crystal
# USAGE
  ispeak [options...]

# OPTIONS
  -b, --binary      Executable to launch with voice input (default: none)
  -c, --config      Path to configuration file
  -l, --log-file    Path to voice transcription append log file
  -n, --no-output   Disables all output/actions - typing, copying, and record indicator
  -p, --copy        Use the 'clipboard' to copy instead of the 'keyboard' to type the output
  -s, --setup       Configure voice settings
  -t, --test        Test voice input functionality
  --config-show     Show current configuration

# EXAMPLES
ispeak --setup         # Interactive configuration wizard
ispeak --copy          # Start with the output mode set as 'clipboard'
ispeak -l words.log    # Log transcriptions to file

# DEV/LOCAL USAGE
uv run ispeak --setup  # via uv
```
<br/>



## Configuration
Can be defined via [JSON](https://en.wikipedia.org/wiki/JSON) or [TOML](https://en.wikipedia.org/wiki/TOML), and the lookup is performed in the following order:

1. **Environment Variable**: `ISPEAK_CONFIG` environment variable is set to the path of the config file
2. **Platform-Specific Config**
   - **macOS**: `~/Library/Preferences/ispeak/ispeak.{json,toml}`
   - **Windows**: `%APPDATA%\ispeak\ispeak.{json,toml}` (or `~/AppData/Roaming/ispeak/ispeak.{json,toml}`)
   - **Linux**: `$XDG_CONFIG_HOME/ispeak/ispeak.{json,toml}` (or `~/.config/ispeak/ispeak.{json,toml}`)
3. **Local**: `./ispeak.{json,toml}` in the current working directory
4. **Default**: fallback

```json
{
  "ispeak": {
    "binary": null,
    "delete_key": null,
    "delete_keyword": ["delete", "undo"],
    "escape_key": "esc",
    "keyboard_interval": 0,
    "log_file": null,
    "output": "keyboard",
    "push_to_talk_key": "shift_l",
    "push_to_talk_key_delay": 0.3,
    "recording_indicator": ";",
    "strip_whitespace": true
  },
  "stt": {
    "model": "tiny",
    "language": "auto",
    "beam_size": 5,
    "compute_type": "auto",
    "download_root": null,
    "enable_realtime_transcription": false,
    "ensure_sentence_ends_with_period": true,
    "ensure_sentence_starting_uppercase": true,
    "initial_prompt": null,
    "no_log_file": true,
    "normalize_audio": true,
    "spinner": false
  },
  "plugin": {}
}
```
> **NOTE**: Highly recommend using `ispeak --setup` for initial setup


<br/>


### ▎ `ispeak`

- `binary` (str/null): Default executable to launch with voice input
- `delete_key` (str/null): Key to trigger deletion of previous input via backspace
- `delete_keyword` (list/bool): Words that trigger deletion of previous input via backspace (must be exact)
- `escape_key` (str/null): Key to cancel current recording without transcription
- `keyboard_interval` (float/null): delay applied after each 'keyboard' character
- `log_file` (str/null): Path to file for logging voice transcriptions
- `output` (str/false): Mode of output; 'keyboard' (type), 'clipboard' (copy), or false for none
  - For all languages aside from English, using 'clipboard' is recommended
- `push_to_talk_key_delay` (float): Brief delay after hotkey press to prevent input conflicts
- `push_to_talk_key` (str/null): Hotkey to start/stop recording sessions
- `recording_indicator` (str/null): Visual indicator typed when recording starts **must be a typeable**
- `strip_whitespace` (bool): Remove extra whitespace from transcribed text

> Hotkeys work via [pynput](https://github.com/moses-palmer/pynput) and support: <br/>
> ╸ Simple characters: `a`, `b`, `c`, `1`, etc. <br/>
> ╸ Special keys: `end`, `alt_l`, `ctrl_l` - (see [pynput Key class](https://github.com/moses-palmer/pynput/blob/74c5220a61fecf9eec0734abdbca23389001ea6b/lib/pynput/keyboard/_base.py#L162)) <br/>
> ╸ Key combinations: `<ctrl>+<alt>+h`, `<shift>+<f1>`<br/>
<br/>


### ▎`stt`
> A full config reference can be found in [`./docs/stt-options.md`](https://github.com/fetchTe/ispeak/blob/master/docs/stt-options.md) <br/>
> ╸ [`RealtimeSTT`](https://github.com/KoljaB/RealtimeSTT) handles the input/mic setup and processing <br/>
> ╸ [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper) is the actual speech-to-text engine implementation

- `model` (str): Model size or path to local CTranslate2 model (for English variants append `.en`)
    - `tiny`: Ultra fast, workable accuracy (~39MB, CPU/GPU)
    - `base`: Respectable accuracy/speed (~74MB, CPU/GPU ~1GB/VRAM)
    - `small`: Decent accuracy (~244MB,  CPU+/GPU ~2GB/VRAM)
    - `medium`: Good accuracy (~769MB, GPU ~3GB/VRAM)
    - `large-v1`/`large-v2`: Superb accuracy (~1550MB, GPU ~4GB/VRAM) 
- `language` (str): Language code (`en`, `es`, `fr`, `de`, etc) or `"auto"` for automatic detection
- `beam_size` (int): Size to use for beam search decoding (worth bumping up)
- `download_root` (str/null): Root path were the models are downloaded/loaded from
- `enable_realtime_transcription` (bool): Enable continuous transcription (2x computation)
- `ensure_sentence_ends_with_period` (bool): Add periods to sentences without punctuation
- `ensure_sentence_starting_uppercase` (bool): Ensure sentences start with uppercase letters
- `initial_prompt` (null/str): Initial prompt to be fed to the main transcription model
- `no_log_file` (bool): Skip debug log file creation
- `normalize_audio` (bool): Normalize audio range before processing for better transcription quality
- `spinner` (bool): Show spinner animation (set to `false` to avoid terminal conflicts)


> Apart from using [faster-distil-whisper-large-v3](https://huggingface.co/Systran/faster-distil-whisper-large-v3), I've had good results with the following

```json
{
  "model": "Systran/faster-distil-whisper-medium.en",
  "initial_prompt": "In this session, we'll discuss concise expression.",
  "beam_size": 8,
  "post_speech_silence_duration": 0.4,
}
```
> **NOTE**: `initial_prompt` defines style and/or spelling, not instructions [cookbook](https://cookbook.openai.com/examples/whisper_prompting_guide#comparison-with-gpt-prompting)/[ref](https://platform.openai.com/docs/guides/speech-to-text/improving-reliability)


<br/>



## Plugin

The plugin system processes transcribed text through a configurable pipeline of text transformation plugins. Plugins are loaded and executed in order based on their configuration, and each can be configured with the following fields:

- `use` (bool): Enable/disable the plugin (default: `true`)
- `order` (int): Execution order - plugins run in ascending order (default: `999`)
- `settings` (dict): Plugin-specific configuration options


### ▎ `replace`
Regex-based text replacement, mainly for simple string replacements, but also capable of handling Regex patterns with capture groups and flags.

```json5
{
  "plugin": {
    "replace": {
      "use": true,
      "order": 1,
      "settings": {
        // simple string replacements
        "iSpeak": "ispeak",
        " one ": " 1 ",
        "read me": "README",

        // regex with capture groups
        "(\\s+)(semi)(\\s+)": ";\\g<3>",
        "(\\s+)(comma)(\\s+)": ",\\g<3>",

        // common voice transcription cleanup
        "\\s+question\\s*mark\\.?": "?",
        "\\s+exclamation\\s*mark\\.?": "!",
        
        // code-specific replacements
        "\\s+open\\s*paren\\s*": "(",
        "\\s+close\\s*paren\\s*": ")",
        "\\s+open\\s*brace\\s*": "{",
        "\\s+close\\s*brace\\s*": "}",

        // regex patterns with flags (/pattern/flags format)
        "/hello/i": "HI",           // case insensitive
        "/^start/m": "BEGIN",       // multiline
        "/comma/gmi": ","           // global, multiline, case insensitive
      }
    }
  }
}
```
> **Flags**: Use `/pattern/flags` format (supports `i`, `m`, `s`, `x` flags) <br/>
> **Substitution**: Use `\1`, `\2` or `\g<1>`, `\g<2>` syntax <br/>
> **Tests**: [`./tests/test_plugin_replace.py`](https://github.com/fetchTe/ispeak/blob/master/tests/test_plugin_replace.py) <br/>

<br/>


### ▎ `num2text` 
Convert digits to text numbers, like "42" into "forty-two" via [`num2words`](https://github.com/savoirfairelinux/num2words)

```json5
{
  "plugin": {
    "num2text": {
      "use": true,
      "order": 3,
      "settings": {
        "lang": "en",         // language code
        "to": "cardinal",     // cardinal, ordinal, ordinal_num, currency, year
        "min": null,          // minimum value to convert
        "max": null,          // maximum value to convert
        "currency": "USD",    // currency code for currency conversion
        "cents": true,        // include cents in currency
        "percent": "percent"  // suffix for percentage conversion
      }
    }
  }
}
```
> **Tests**: [`./tests/test_plugin_num2text.py`](https://github.com/fetchTe/ispeak/blob/master/tests/test_plugin_num2text.py)  <br/>
> **Dependency**: [`num2words`](https://github.com/savoirfairelinux/num2words) -> `uv pip install num2words` <br/>

<br/>


### ▎ `text2num`
Convert text numbers to digits, like "forty-two" into "42" via [`text_to_num`](https://github.com/allo-media/text2num)


```json
{
  "plugin": {
    "text2num": {
      "use": true,
      "order": 2,
      "settings": {
        "lang": "en",
        "threshold": 0
      }
    }
  }
}
```
> **Tests**: [`./tests/test_plugin_text2num.py`](https://github.com/fetchTe/ispeak/blob/master/tests/test_plugin_text2num.py)  <br/>
> **Dependency**: [`text_to_num`](https://github.com/allo-media/text2num) -> `uv pip install text_to_num` <br/>
> **IMPORTANT**: the `threshold` may, or, may not work if cardinal; check out the `TestWishyWashyThreshold` test for more dets<br/>

<br/>



## Troubleshooting

+ **Hotkey Issues**: Check/grant permissions see [linux](#linux), [macOS](#macos), [windows](#windows)
+ **Recording Indicator Misfire(s)**: Increase `push_to_talk_key_delay` (try 0.2-1.0)
+ **Typing/Character Issues**: Try using `"output": "clipboard"`
  + If missing/skipping ASCII characters try using `"keyboard_interval": 0.1`
+ **Transcription Issues**: Try the CPU-only and/or the following minimal test code to isolate the problem:

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
- You must run your script as root, so that it has the required permissions for *uinput*

The latter requirement for *X* means that running *pynput* over *SSH* generally will not work. To work around that, make sure to set `$DISPLAY`:

``` sh
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

```
# USAGE (ispeak)
   make [flags...] <target>

# TARGET
  -------------------
   run                   execute entry-point -> uv run main.py
   build                 build wheel/source distributions -> hatch build
   clean                 delete build artifacts, cache files, and temporary files
  -------------------
   publish               publish to pypi.org -> twine upload
   publish_test          publish to test.pypi.org -> twine upload --repository testpypi
   publish_check         check distributions -> twine check
   release               clean, format, lint, test, build, check, and optionally publish
  -------------------
   install               install dependencies -> uv sync
   install_cpu           install dependencies -> uv sync --extra cpu
   install_dev           install dev dependencies -> uv sync --group dev --extra plugin
   install_plugin        install plugin dependencies -> uv sync --extra plugin
   update                update dependencies -> uv lock --upgrade && uv sync
   update_dry            show outdated dependencies  -> uv tree --outdated
   venv                  setup virtual environment if needed -> uv venv -p 3.11
  -------------------
   check                 run all checks: lint, type, and format
   format                format check -> ruff format --check
   lint                  lint check -> ruff check
   type                  type check -> pyright
   format_fix            auto-fix format -> ruff format
   lint_fix              auto-fix lint -> ruff check --fix
  -------------------
   test                  test -> pytest
   test_fast             test & fail-fast -> pytest -x -q
  -------------------
   help                  displays (this) help screen

# FLAGS
  -------------------
   UV                    [? ] uv build flag(s) (e.g: make UV="--no-build-isolation")
  -------------------
   BAIL                  [?1] fail fast (bail) on the first test or lint error
   PUBLISH               [?0] publishes to PyPI after build (requires twine config)
  -------------------
   DEBUG                 [?0] enables verbose logging for tools (uv, pytest, ruff)
   QUIET                 [?0] disables pretty-printed/log target (INIT/DONE) info
   NO_COLOR              [?0] disables color logging/ANSI codes
```


<br/>



## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Install development dependencies: `uv sync --group dev`
4. Make your changes following the existing code style
5. Run quality checks & test:
   ```sh
   make format_fix  # auto-fix format -> ruff format
   make check       # run all checks: lint, type, and format
   make test        # run all tests
   ```
6. Commit your changes: `git commit -m 'feat: add amazing feature'`
7. Push to your branch: `git push origin feature/amazing-feature`
8. Open a Pull Request with a clear description of your changes

<br/>



## Respects

- **[`RealtimeSTT`](https://github.com/KoljaB/RealtimeSTT)** - A swell wrapper around [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper) that powers the speech-to-text engine
- **[`pynput`](https://github.com/moses-palmer/pynput)** - Cross-platform controller and monitorer for the keyboard
- **[`pyperclip`](https://github.com/asweigart/pyperclip)** - Cross-platform clipboard
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
