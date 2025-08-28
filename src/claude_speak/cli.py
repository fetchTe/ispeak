#!/usr/bin/env python3

import argparse
import subprocess
import sys
import json
from pathlib import Path
from typing import Optional

import pynput.keyboard
import pyautogui
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.panel import Panel

from .config import ConfigManager, AppConfig
from .core import VoiceInput, key_to_str


def configure_voice() -> None:
    """Interactive configuration for voice settings."""
    console = Console()
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    console.print(Panel.fit(
        "[bold]Claude Speak Configuration[/bold]",
        title="🎙️ Setup"
    ))
    
    # Configure push-to-talk key
    console.print(f"\nCurrent PTT (push-to-talk) key: [yellow]{config.claude_speak.push_to_talk_key}[/yellow]")
    console.print("Press your desired PTT key (or Enter to keep current)...")
    
    captured_key = None
    
    def on_key_press(key):
        nonlocal captured_key
        captured_key = key_to_str(key)
        console.print(f"Captured: [green]{captured_key}[/green]")
        return False  # Stop listener
    
    listener = pynput.keyboard.Listener(on_press=on_key_press)
    listener.start()
    listener.join()  # Wait for key press
    
    if captured_key:
        config.claude_speak.push_to_talk_key = captured_key
    
    # Configure recording indicator
    console.print(f"\nRecording indicator character: [yellow]{config.claude_speak.recording_indicator}[/yellow]")
    new_indicator = Prompt.ask(
        "Enter new indicator (or press Enter to keep current)",
        default=config.claude_speak.recording_indicator
    )
    config.claude_speak.recording_indicator = new_indicator
    
    # Configure language
    console.print(f"\nLanguage (current: [yellow]{config.realtime_stt.language}[/yellow]):")
    console.print("Common options: en, es, fr, de, it, pt, ru, ja, ko, zh, auto")
    language = Prompt.ask(
        "Language code",
        default=config.realtime_stt.language
    )
    config.realtime_stt.language = language
    
    # Configure model size
    console.print(f"\nModel size (current: [yellow]{config.realtime_stt.model}[/yellow]):")
    console.print("- tiny: Fastest, lowest accuracy")
    console.print("- base: Good balance (recommended)")
    console.print("- small: Better accuracy, slower")
    console.print("- large: Best accuracy, slowest")
    console.print("- Or path to custom model")
    
    model = Prompt.ask(
        "Model",
        default=config.realtime_stt.model,
        choices=['tiny', 'base', 'small', 'medium', 'large-v1', 'large-v2']
    )
    config.realtime_stt.model = model
    
    # Configure text processing
    console.print(f"\nText Processing Options:")
    config.claude_speak.normalize_output = Confirm.ask(
        "Normalize output (lowercase, trim whitespace)?",
        default=config.claude_speak.normalize_output
    )
    
    config.claude_speak.remove_trailing_period = Confirm.ask(
        "Remove trailing periods?",
        default=config.claude_speak.remove_trailing_period
    )
    
    # Save configuration
    try:
        config_manager.save_config(config)
        console.print(f"\n[green]✓ Configuration saved to {config_manager.config_path}[/green]")
        
        # Show configuration summary
        console.print(Panel.fit(
            f"PTT Key: [yellow]{config.claude_speak.push_to_talk_key}[/yellow]\n"
            f"Indicator: [yellow]{config.claude_speak.recording_indicator}[/yellow]\n"
            f"Language: [yellow]{config.realtime_stt.language}[/yellow]\n"
            f"Model: [yellow]{config.realtime_stt.model}[/yellow]",
            title="📋 Configuration Summary"
        ))
        
    except Exception as e:
        console.print(f"[red]Failed to save configuration: {e}[/red]")
        sys.exit(1)


def test_voice() -> None:
    """Test voice input functionality."""
    console = Console()
    
    console.print(Panel.fit(
        "[bold]Voice Input Test[/bold]\n"
        "This will test your microphone and transcription.\n"
        "Press Escape to stop testing.",
        title="🧪 Test Mode"
    ))
    
    def handle_test_text(text: str) -> None:
        console.print(f"[green]Transcribed:[/green] {text}")
    
    try:
        voice_input = VoiceInput()
        voice_input.start(handle_test_text)
        
        console.print("\n[yellow]Voice input active. Press your PTT key to test.[/yellow]")
        console.print("[dim]Press Ctrl+C to stop testing.[/dim]")
        
        # Keep running until interrupted
        try:
            while True:
                input()  # Wait for Enter or Ctrl+C
        except KeyboardInterrupt:
            pass
        
    except Exception as e:
        console.print(f"[red]Error starting voice input: {e}[/red]")
        sys.exit(1)
    finally:
        if 'voice_input' in locals():
            voice_input.stop()
        console.print("\n[yellow]Test completed.[/yellow]")


def show_config() -> None:
    """Display current configuration."""
    console = Console()
    config_manager = ConfigManager()
    
    try:
        config = config_manager.load_config()
        
        # Convert to JSON for display
        config_dict = {
            "realtime_stt": config.realtime_stt.__dict__,
            "claude_speak": config.claude_speak.__dict__
        }
        
        console.print(Panel.fit(
            f"[bold]Configuration File:[/bold] {config_manager.config_path}\n\n"
            f"```json\n{json.dumps(config_dict, indent=2)}\n```",
            title="📋 Current Configuration"
        ))
        
    except Exception as e:
        console.print(f"[red]Error loading configuration: {e}[/red]")
        sys.exit(1)


def run_with_claude(claude_args: list) -> int:
    """Run claude with voice integration.
    
    Args:
        claude_args: Arguments to pass to claude command.
        
    Returns:
        Exit code from claude execution.
    """
    console = Console()
    
    console.print(Panel.fit(
        "[bold]Claude Code with Voice Support[/bold]\n"
        "Voice integration will start automatically.",
        title="🎙️ Claude Speak"
    ))
    
    voice_enabled = False
    voice_input = None
    
    def handle_voice_text(text: str) -> None:
        """Handle transcribed text by typing it."""
        try:
            pyautogui.typewrite(text + " ")
        except Exception as e:
            console.print(f"[red]Error typing text: {e}[/red]")
    
    # Try to start voice input
    try:
        voice_input = VoiceInput()
        voice_input.start(handle_voice_text)
        voice_enabled = True
        
    except Exception as e:
        console.print(f"[yellow]Could not start voice input: {e}[/yellow]")
        console.print("[yellow]Continuing without voice support...[/yellow]")
    
    console.print("\n[green]Starting Claude Code...[/green]")
    
    try:
        # Build command and run claude
        cmd = ['claude'] + claude_args
        result = subprocess.run(cmd)
        return_code = result.returncode
        
    except KeyboardInterrupt:
        return_code = 0
    except FileNotFoundError:
        console.print("[red]Error: 'claude' command not found. Make sure Claude Code is installed.[/red]")
        return_code = 1
    except Exception as e:
        console.print(f"[red]Error running Claude: {e}[/red]")
        return_code = 1
    finally:
        # Clean up voice input
        if voice_enabled and voice_input:
            try:
                voice_input.stop()
            except Exception:
                pass  # Ignore cleanup errors
    
    return return_code


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Claude Code with Voice Input",
        add_help=False  # We'll handle help ourselves to pass it to claude
    )
    
    # Our specific arguments
    parser.add_argument("--configure-voice", action="store_true",
                       help="Configure voice settings")
    parser.add_argument("--test-voice", action="store_true",
                       help="Test voice input functionality")
    parser.add_argument("--show-config", action="store_true",
                       help="Show current configuration")
    
    # Parse known args to separate ours from claude's
    our_args, claude_args = parser.parse_known_args()
    
    # Handle our specific commands
    if our_args.configure_voice:
        configure_voice()
        return 0
    
    if our_args.test_voice:
        test_voice()
        return 0
    
    if our_args.show_config:
        show_config()
        return 0
    
    # If no specific command, run with claude integration
    return run_with_claude(claude_args)


if __name__ == "__main__":
    sys.exit(main())