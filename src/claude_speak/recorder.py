from typing import Protocol

from RealtimeSTT import AudioToTextRecorder

from .config import RealtimeSTTConfig


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


class RealtimeSTTRecorder:
    """RealtimeSTT-based audio recorder implementation"""

    def __init__(self, config: RealtimeSTTConfig) -> None:
        """Initialize recorder with configuration

        Args:
            config: RealtimeSTT configuration
        """
        self.config = config
        self._recorder: AudioToTextRecorder | None = None
        self._initialize_recorder()

    def _initialize_recorder(self) -> None:
        """Initialize the RealtimeSTT recorder with configuration"""
        try:
            config_dict = self.config.to_dict()
            self._recorder = AudioToTextRecorder(**config_dict)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize RealtimeSTT recorder: {e}") from e

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
        return self._recorder.text()

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
