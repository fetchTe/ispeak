# STT (speech-to-text) Options/Config Reference

> For futher docs/details visit [`RealtimeSTT`](https://github.com/KoljaB/RealtimeSTT) and/or the speech-to-text engine itself [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper).

### ▎Notes

To save you time and effort, two features of RealtimeSTT have been intentionally omitted:

1. `wakeword*` is excluded in favor of a hotkey-driven workflow. While it's certainly possible to use a "wakeword" with a few minor tweaks, you'll regret it somewhere between the twentieth and umpteenth time you're forced to say it.
2. `realtime*` <del>is only practical for real-time applications</del> - I've had a lot of shower thoughts about what you could do with it, but realistically, I don't think it's worth the hassle.



### ▎All `stt` Options

```
- model (str, default="tiny"): Specifies the size of the transcription
    model to use or the path to a converted model directory.
    Valid options are 'tiny', 'tiny.en', 'base', 'base.en',
    'small', 'small.en', 'medium', 'medium.en', 'large-v1',
    'large-v2'.
    If a specific size is provided, the model is downloaded
    from the Hugging Face Hub.
- download_root (str, default=None): Specifies the root path
    were the Whisper models 
  are downloaded to. When empty, the default is used. 
- language (str, default=""): Language code for speech-to-text engine.
    If not specified, the model will attempt to detect the language
    automatically.
- compute_type (str, default="default"): Specifies the type of
    computation to be used for transcription.
    See https://opennmt.net/CTranslate2/quantization.html.
- input_device_index (int, default=0): The index of the audio input
    device to use.
- gpu_device_index (int, default=0): Device ID to use.
    The model can also be loaded on multiple GPUs by passing a list of
    IDs (e.g. [0, 1, 2, 3]). In that case, multiple transcriptions can
    run in parallel when transcribe() is called from multiple Python
    threads
- device (str, default="cuda"): Device for model to use. Can either be 
    "cuda" or "cpu".
- on_recording_start (callable, default=None): Callback function to be
    called when recording of audio to be transcripted starts.
- on_recording_stop (callable, default=None): Callback function to be
    called when recording of audio to be transcripted stops.
- on_transcription_start (callable, default=None): Callback function
    to be called when transcription of audio to text starts.
- ensure_sentence_starting_uppercase (bool, default=True): Ensures
    that every sentence detected by the algorithm starts with an
    uppercase letter.
- ensure_sentence_ends_with_period (bool, default=True): Ensures that
    every sentence that doesn't end with punctuation such as "?", "!"
    ends with a period
- use_microphone (bool, default=True): Specifies whether to use the
    microphone as the audio input source. If set to False, the
    audio input source will be the audio data sent through the
    feed_audio() method.
- spinner (bool, default=False): Show spinner animation with current
    state. NOTE: works with claude-speak-code, but not recommend.
- level (int, default=logging.WARNING): Logging level.
- batch_size (int, default=16): Batch size for the main transcription
- enable_realtime_transcription (bool, default=False): Enables or
    disables real-time transcription of audio. When set to True, the
    audio will be transcribed continuously as it is being recorded.
- use_main_model_for_realtime (str, default=False):
    If True, use the main transcription model for both regular and
    real-time transcription. If False, use a separate model specified
    by realtime_model_type for real-time transcription.
    Using a single model can save memory and potentially improve
    performance, but may not be optimized for real-time processing.
    Using separate models allows for a smaller, faster model for
    real-time transcription while keeping a more accurate model for
    final transcription.
- realtime_model_type (str, default="tiny"): Specifies the machine
    learning model to be used for real-time transcription. Valid
    options include 'tiny', 'tiny.en', 'base', 'base.en', 'small',
    'small.en', 'medium', 'medium.en', 'large-v1', 'large-v2'.
- realtime_processing_pause (float, default=0.1): Specifies the time
    interval in seconds after a chunk of audio gets transcribed. Lower
    values will result in more "real-time" (frequent) transcription
    updates but may increase computational load.
- init_realtime_after_seconds (float, default=0.2): Specifies the 
    initial waiting time after the recording was initiated before
    yielding the first realtime transcription
- on_realtime_transcription_update = A callback function that is
    triggered whenever there's an update in the real-time
    transcription. The function is called with the newly transcribed
    text as its argument.
- on_realtime_transcription_stabilized = A callback function that is
    triggered when the transcribed text stabilizes in quality. The
    stabilized text is generally more accurate but may arrive with a
    slight delay compared to the regular real-time updates.
- realtime_batch_size (int, default=16): Batch size for the real-time
    transcription model.
- silero_sensitivity (float, default=SILERO_SENSITIVITY): Sensitivity
    for the Silero Voice Activity Detection model ranging from 0
    (least sensitive) to 1 (most sensitive). Default is 0.5.
- silero_use_onnx (bool, default=False): Enables usage of the
    pre-trained model from Silero in the ONNX (Open Neural Network
    Exchange) format instead of the PyTorch format. This is
    recommended for faster performance.
- silero_deactivity_detection (bool, default=False): Enables the Silero
    model for end-of-speech detection. More robust against background
    noise. Utilizes additional GPU resources but improves accuracy in
    noisy environments. When False, uses the default WebRTC VAD,
    which is more sensitive but may continue recording longer due
    to background sounds.
- webrtc_sensitivity (int, default=WEBRTC_SENSITIVITY): Sensitivity
    for the WebRTC Voice Activity Detection engine ranging from 0
    (least aggressive / most sensitive) to 3 (most aggressive,
    least sensitive). Default is 3.
- post_speech_silence_duration (float, default=0.2): Duration in
    seconds of silence that must follow speech before the recording
    is considered to be completed. This ensures that any brief
    pauses during speech don't prematurely end the recording.
- min_gap_between_recordings (float, default=1.0): Specifies the
    minimum time interval in seconds that should exist between the
    end of one recording session and the beginning of another to
    prevent rapid consecutive recordings.
- min_length_of_recording (float, default=1.0): Specifies the minimum
    duration in seconds that a recording session should last to ensure
    meaningful audio capture, preventing excessively short or
    fragmented recordings.
- pre_recording_buffer_duration (float, default=0.2): Duration in
    seconds for the audio buffer to maintain pre-roll audio
    (compensates speech activity detection latency)
- on_vad_start (callable, default=None): Callback function to be called
    when the system detected the start of voice activity presence.
- on_vad_stop (callable, default=None): Callback function to be called
    when the system detected the stop (end) of voice activity presence.
- on_vad_detect_start (callable, default=None): Callback function to
    be called when the system listens for voice activity. This is not
    called when VAD actually happens (use on_vad_start for this), but
    when the system starts listening for it.
- on_vad_detect_stop (callable, default=None): Callback function to be
    called when the system stops listening for voice activity. This is
    not called when VAD actually stops (use on_vad_stop for this), but
    when the system stops listening for it.
- on_turn_detection_start (callable, default=None): Callback function
    to be called when the system starts to listen for a turn of speech.
- on_turn_detection_stop (callable, default=None): Callback function to
    be called when the system stops listening for a turn of speech.
- wakeword_backend (str, default=""): Specifies the backend library to
    use for wake word detection. Supported options include 'pvporcupine'
    for using the Porcupine wake word engine or 'oww' for using the
    OpenWakeWord engine.
- wakeword_backend (str, default="pvporcupine"): Specifies the backend
    library to use for wake word detection. Supported options include
    'pvporcupine' for using the Porcupine wake word engine or 'oww' for
    using the OpenWakeWord engine.
- openwakeword_model_paths (str, default=None): Comma-separated paths
    to model files for the openwakeword library. These paths point to
    custom models that can be used for wake word detection when the
    openwakeword library is selected as the wakeword_backend.
- openwakeword_inference_framework (str, default="onnx"): Specifies
    the inference framework to use with the openwakeword library.
    Can be either 'onnx' for Open Neural Network Exchange format 
    or 'tflite' for TensorFlow Lite.
- wake_words (str, default=""): Comma-separated string of wake words to
    initiate recording when using the 'pvporcupine' wakeword backend.
    Supported wake words include: 'alexa', 'americano', 'blueberry',
    'bumblebee', 'computer', 'grapefruits', 'grasshopper', 'hey google',
    'hey siri', 'jarvis', 'ok google', 'picovoice', 'porcupine',
    'terminator'. For the 'openwakeword' backend, wake words are
    automatically extracted from the provided model files, so specifying
    them here is not necessary.
- wake_words_sensitivity (float, default=0.5): Sensitivity for wake
    word detection, ranging from 0 (least sensitive) to 1 (most
    sensitive). Default is 0.5.
- wake_word_activation_delay (float, default=0): Duration in seconds
    after the start of monitoring before the system switches to wake
    word activation if no voice is initially detected. If set to
    zero, the system uses wake word activation immediately.
- wake_word_timeout (float, default=5): Duration in seconds after a
    wake word is recognized. If no subsequent voice activity is
    detected within this window, the system transitions back to an
    inactive state, awaiting the next wake word or voice activation.
- wake_word_buffer_duration (float, default=0.1): Duration in seconds
    to buffer audio data during wake word detection. This helps in
    cutting out the wake word from the recording buffer so it does not
    falsely get detected along with the following spoken text, ensuring
    cleaner and more accurate transcription start triggers.
    Increase this if parts of the wake word get detected as text.
- on_wakeword_detected (callable, default=None): Callback function to
    be called when a wake word is detected.
- on_wakeword_timeout (callable, default=None): Callback function to
    be called when the system goes back to an inactive state after when
    no speech was detected after wake word activation
- on_wakeword_detection_start (callable, default=None): Callback
     function to be called when the system starts to listen for wake
     words
- on_wakeword_detection_end (callable, default=None): Callback
    function to be called when the system stops to listen for
    wake words (e.g. because of timeout or wake word detected)
- on_recorded_chunk (callable, default=None): Callback function to be
    called when a chunk of audio is recorded. The function is called
    with the recorded audio chunk as its argument.
- debug_mode (bool, default=False): If set to True, the system will
    print additional debug information to the console.
- handle_buffer_overflow (bool, default=True): If set to True, the system
    will log a warning when an input overflow occurs during recording and
    remove the data from the buffer.
- beam_size (int, default=5): The beam size to use for beam search
    decoding.
- beam_size_realtime (int, default=3): The beam size to use for beam
    search decoding in the real-time transcription model.
- buffer_size (int, default=512): The buffer size to use for audio
    recording. Changing this may break functionality.
- sample_rate (int, default=16000): The sample rate to use for audio
    recording. Changing this will very probably functionality (as the
    WebRTC VAD model is very sensitive towards the sample rate).
- initial_prompt (str or iterable of int, default=None): Initial
    prompt to be fed to the main transcription model.
- initial_prompt_realtime (str or iterable of int, default=None):
    Initial prompt to be fed to the real-time transcription model.
- suppress_tokens (list of int, default=[-1]): Tokens to be suppressed
    from the transcription output.
- print_transcription_time (bool, default=False): Logs processing time
    of main model transcription 
- early_transcription_on_silence (int, default=0): If set, the
    system will transcribe audio faster when silence is detected.
    Transcription will start after the specified milliseconds, so 
    keep this value lower than post_speech_silence_duration. 
    Ideally around post_speech_silence_duration minus the estimated
    transcription time with the main model.
    If silence lasts longer than post_speech_silence_duration, the 
    recording is stopped, and the transcription is submitted. If 
    voice activity resumes within this period, the transcription 
    is discarded. Results in faster final transcriptions to the cost
    of additional GPU load due to some unnecessary final transcriptions.
- allowed_latency_limit (int, default=100): Maximal amount of chunks
    that can be unprocessed in queue before discarding chunks.
- no_log_file (bool, default=False): Skips writing of debug log file.
- use_extended_logging (bool, default=False): Writes extensive
    log messages for the recording worker, that processes the audio
    chunks.
- faster_whisper_vad_filter (bool, default=True): If set to True,
    the system will additionally use the VAD filter from the faster_whisper
    library for voice activity detection. This filter is more robust
    against background noise but requires additional GPU resources.
- normalize_audio (bool, default=False): If set to True, the system will
    normalize the audio to a specific range before processing. This can
    help improve the quality of the transcription.
- start_callback_in_new_thread (bool, default=False): If set to True,
    the callback functions will be executed in a
    new thread. This can help improve performance by allowing the
    callback to run concurrently with other operations.
```
