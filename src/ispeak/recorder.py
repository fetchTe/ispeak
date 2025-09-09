from typing import Protocol

from RealtimeSTT import AudioToTextRecorder

from .config import ModelSTTConfig


class AudioRecorder(Protocol):
    """Protocol for audio recorder implementations"""

    def start(self) -> None:
        """Start recording audio"""
        ...

    def stop(self) -> None:
        """Stop recording audio"""
        ...

    def text(self) -> str:
        """Get transcribed text from recording"""
        ...

    def shutdown(self) -> None:
        """Shutdown recorder and cleanup resources"""
        ...


class ModelSTTRecorder:
    """ModelSTT-based audio recorder implementation"""

    def __init__(self, config: ModelSTTConfig) -> None:
        """Initialize recorder with configuration

        Args:
            config: ModelSTT configuration
        """
        self.config = config
        self._recorder: AudioToTextRecorder | None = None
        self._initialize_recorder()

    def _initialize_recorder(self) -> None:
        """Initialize the ModelSTT recorder with configuration"""
        try:
            config_dict = self.config.to_dict()
            # @TODO -> meh, wake_words are really not worth the hassle
            # if 'wake_words' in config_dict:
            #     config_dict['on_wakeword_detection_start'] = self.on_key
            #     config_dict['on_wakeword_detection_end'] = self.on_key
            self._recorder = AudioToTextRecorder(**config_dict)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize ModelSTT recorder: {e}") from e

    def start(self) -> None:
        """Start recording audio"""
        if self._recorder is None:
            raise RuntimeError("Recorder not initialized")
        self._recorder.start()

    def stop(self) -> None:
        """Stop recording audio"""
        if self._recorder is None:
            raise RuntimeError("Recorder not initialized")
        self._recorder.stop()

    def text(self) -> str:
        """
        Get transcribed text from recording

        Returns:
            Transcribed text from the last recording session
        """
        if self._recorder is None:
            raise RuntimeError("Recorder not initialized")
        res = self._recorder.text()
        if not res:
            return ""
        return res

    def shutdown(self) -> None:
        """Shutdown recorder and cleanup resources"""
        if self._recorder is not None:
            try:
                self._recorder.shutdown()
            except Exception:
                # ignore shutdown errors as they're often harmless
                pass
            finally:
                self._recorder = None

    def __del__(self) -> None:
        # ensure cleanup on deletion
        self.shutdown()
