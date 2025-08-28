#!/usr/bin/env python3

from abc import ABC, abstractmethod
from typing import Optional, Protocol

from RealtimeSTT import AudioToTextRecorder

from .config import RealtimeSTTConfig


class AudioRecorder(Protocol):
    """Protocol for audio recorder implementations."""
    
    def start(self) -> None:
        """Start recording audio."""
        ...
    
    def stop(self) -> None:
        """Stop recording audio."""
        ...
    
    def text(self) -> str:
        """Get transcribed text from recording."""
        ...
    
    def shutdown(self) -> None:
        """Shutdown recorder and cleanup resources."""
        ...


class RealtimeSTTRecorder:
    """RealtimeSTT-based audio recorder implementation."""
    
    def __init__(self, config: RealtimeSTTConfig) -> None:
        """Initialize recorder with configuration.
        
        Args:
            config: RealtimeSTT configuration.
        """
        self.config = config
        self._recorder: Optional[AudioToTextRecorder] = None
        self._initialize_recorder()
    
    def _initialize_recorder(self) -> None:
        """Initialize the RealtimeSTT recorder with configuration."""
        try:
            config_dict = self.config.to_dict()
            self._recorder = AudioToTextRecorder(**config_dict)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize RealtimeSTT recorder: {e}") from e
    
    def start(self) -> None:
        """Start recording audio."""
        if self._recorder is None:
            raise RuntimeError("Recorder not initialized")
        self._recorder.start()
    
    def stop(self) -> None:
        """Stop recording audio."""
        if self._recorder is None:
            raise RuntimeError("Recorder not initialized")
        self._recorder.stop()
    
    def text(self) -> str:
        """Get transcribed text from recording.
        
        Returns:
            Transcribed text from the last recording session.
        """
        if self._recorder is None:
            raise RuntimeError("Recorder not initialized")
        return self._recorder.text()
    
    def shutdown(self) -> None:
        """Shutdown recorder and cleanup resources."""
        if self._recorder is not None:
            try:
                self._recorder.shutdown()
            except Exception:
                # Ignore shutdown errors as they're often harmless
                pass
            finally:
                self._recorder = None
    
    def __del__(self) -> None:
        """Ensure cleanup on deletion."""
        self.shutdown()


class MockRecorder:
    """Mock recorder for testing purposes."""
    
    def __init__(self, test_text: str = "test transcription") -> None:
        """Initialize mock recorder.
        
        Args:
            test_text: Text to return from text() method.
        """
        self.test_text = test_text
        self.is_recording = False
    
    def start(self) -> None:
        """Start mock recording."""
        self.is_recording = True
    
    def stop(self) -> None:
        """Stop mock recording."""
        self.is_recording = False
    
    def text(self) -> str:
        """Get mock transcribed text."""
        return self.test_text
    
    def shutdown(self) -> None:
        """Mock shutdown."""
        self.is_recording = False