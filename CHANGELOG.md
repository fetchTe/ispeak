## [`v0.4.4`](https://github.com/fetchTe/ispeak/releases/tag/v0.4.4) - `2025-09-25`

### ▎Added
- `--version` flag
- README demo gif


### ▎Changed
- Order initial startup meta alphabetical and display version


### ▎Fixed
- `log_file` check/create directory and `expanduser`
- Post-shutown text generation on Ctrl+C


## [`v0.4.2`](https://github.com/fetchTe/ispeak/releases/tag/v0.4.2) - `2025-09-18`

### ▎Fixed
- Plugin output



## [`v0.4.0`](https://github.com/fetchTe/ispeak/releases/tag/v0.4.0) - `2025-09-11`

### ▎Added
- Configurable keyboard interval delay with `keyboard_interval` setting


### ▎Changed
- 30x faster CLI `--help` performance
- README initial prompt recommendation



## [`v0.2.5`](https://github.com/fetchTe/ispeak/releases/tag/v0.2.5) - `2025-09-10`

### ▎Added
- README ispeak logo and minimum python version tag


### ▎Changed
- Replace README relative links with absolute URLs in
- Remove README install/provides-extra examples



## [`v0.2.4`](https://github.com/fetchTe/ispeak/releases/tag/v0.2.4) - `2025-09-10`

### ▎BREAKING
- Rename `realtime_stt` configuration key to `stt` for clearer naming
- Replace `no_output` boolean with `output` setting (`keyboard`, `clipboard`, or `false`) 
- Move text replacement rules from root config to `plugin.replace` section


### ▎Added
- Plugin system with built-in plugins for text transformations (num2text, text2num, replace)
- Clipboard output support via new `output` configuration option and `--copy` CLI flag
- Delete key functionality for triggering voice-based delete commands
- TOML configuration file support alongside existing JSON format
- Build targets for plugin dependency installation and virtual environment setup
- Full test and lint `on-release.yml` action


### ▎Changed
- Default push-to-talk key changed from 'end' to 'shift_l' for better accessibility
- Configuration structure: `realtime_stt` renamed to `stt`
- Delete keywords configuration simplified to `delete_keyword` for clarity
- Core text processing now uses plugin registry instead of direct TextReplacer class
- Documentation improvements for STT options with notes on intentionally omitted features



## [`v0.1.1`](https://github.com/fetchTe/ispeak/releases/tag/v0.1.1) - `2025-09-03`

### ▎BREAKING
- Rename project from `code_speak` to `ispeak` for broader AI tool support
- Remove `pyautogui` dependency in favor of `pynput` keyboard for better reliability
- Remove `fast_delete` and `pyautogui_interval` configuration options
- Rename CLI option `--config` to `--config-show` to avoid conflicts
- Rename `--log` to `--log-file` for clarity
- Rename configuration option `no_typing` to `no_output`


### ▎Added
- Standalone voice input operation mode (binary-less default)
- Text replacement with regex-based rules via `replace` config option
- Custom configuration file path support via `-c, --config` CLI option
- Transcript logging to file via `-l/--log-file` CLI option
- `--no-typing` CLI flag to prevent automated text output
- Global hotkeys for escape and push-to-talk functionality
- Configurable escape key and push-to-talk key delay settings
- Cross-platform configuration path resolution (XDG spec compliant)
- GitHub Actions CI pipeline with automated testing and linting
- Test suite with proper pytest configuration


### ▎Changed
- Python version requirement lowered to 3.10 for broader compatibility
- Configuration handling centralized with better validation
- Voice input test instructions and stopping mechanism
- Text processing streamlined with single `strip` option
- LICENSE file renamed from LICENSE.txt to LICENSE
- Use `importlib.metadata` for package version retrieval
- Remove Rich library dependency for logging and interactive prompts
- Shell script removal - use `uv` directly for execution


### ▎Fixed
- Graceful handling of recorder start failures
- Empty text result handling in recorder
- Key capture now correctly stops listening after key press
- Voice input properly stopped in test function on failure
- GitHub Actions CI issues with DISPLAY environment and dependencies
