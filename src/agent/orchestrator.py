"""
Agent Orchestrator.
Coordinates the full pipeline from audio to SQL results.
"""

import sys
import os
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import config
from src.audio.capture import record_with_vad, record_audio
from src.audio.transcribe import transcribe_audio, transcribe_file
from src.sql.generator import generate_sql
from src.sql.executor import execute_query, format_results_table, format_results_natural


class QueryMode(Enum):
    """How to get the query."""
    TEXT = "text"           # Direct text input
    AUDIO_FILE = "file"     # From audio file
    MICROPHONE = "mic"      # Live microphone


@dataclass
class PipelineResult:
    """Result of running the full pipeline."""
    success: bool
    
    # Input
    mode: QueryMode
    audio_path: Optional[str] = None
    
    # Transcription
    transcription: Optional[str] = None
    transcription_error: Optional[str] = None
    
    # SQL Generation
    generated_sql: Optional[str] = None
    sql_generation_error: Optional[str] = None
    
    # Execution
    query_result: Optional[dict] = None
    execution_error: Optional[str] = None
    
    # Formatted output
    formatted_output: Optional[str] = None
    
    def __str__(self):
        lines = []
        
        if self.transcription:
            lines.append(f"📝 You said: \"{self.transcription}\"")
            lines.append("")
        
        if self.generated_sql:
            lines.append(f"🔍 Generated SQL:")
            lines.append(f"   {self.generated_sql}")
            lines.append("")
        
        if self.formatted_output:
            lines.append(f"📊 Results:")
            lines.append(self.formatted_output)
        
        if not self.success:
            if self.transcription_error:
                lines.append(f"❌ Transcription error: {self.transcription_error}")
            if self.sql_generation_error:
                lines.append(f"❌ SQL generation error: {self.sql_generation_error}")
            if self.execution_error:
                lines.append(f"❌ Execution error: {self.execution_error}")
        
        return "\n".join(lines)


class VoiceToSQLAgent:
    """
    Main agent class that orchestrates the voice-to-SQL pipeline.
    """
    
    def __init__(
        self,
        on_status: Optional[Callable[[str], None]] = None,
        verbose: bool = True
    ):
        """
        Initialize the agent.
        
        Args:
            on_status: Optional callback for status updates
            verbose: Whether to print status messages
        """
        self.on_status = on_status
        self.verbose = verbose
    
    def _status(self, message: str):
        """Emit a status message."""
        if self.verbose:
            print(message)
        if self.on_status:
            self.on_status(message)
    
    def process_text(self, text: str) -> PipelineResult:
        """
        Process a text query directly (skip audio/transcription).
        
        Args:
            text: Natural language query
            
        Returns:
            PipelineResult with SQL and results
        """
        result = PipelineResult(
            success=False,
            mode=QueryMode.TEXT,
            transcription=text
        )
        
        # Generate SQL
        self._status("Generating SQL...")
        sql_result = generate_sql(text)
        
        if not sql_result['success']:
            result.sql_generation_error = sql_result['error']
            return result
        
        result.generated_sql = sql_result['sql']
        
        # Execute query
        self._status("Executing query...")
        query_result = execute_query(sql_result['sql'])
        result.query_result = query_result.to_dict()
        
        if not query_result.success:
            result.execution_error = query_result.error
            return result
        
        # Format results
        result.formatted_output = format_results_natural(query_result)
        result.success = True
        
        return result
    
    def process_audio_file(self, audio_path: str) -> PipelineResult:
        """
        Process an audio file.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            PipelineResult
        """
        result = PipelineResult(
            success=False,
            mode=QueryMode.AUDIO_FILE,
            audio_path=audio_path
        )
        
        # Transcribe
        self._status(f"Transcribing {audio_path}...")
        trans_result = transcribe_file(audio_path)
        
        if not trans_result['success']:
            result.transcription_error = trans_result['error']
            return result
        
        result.transcription = trans_result['text']
        self._status(f"Transcription: \"{result.transcription}\"")
        
        # Continue with text processing
        text_result = self.process_text(result.transcription)
        
        # Merge results
        result.generated_sql = text_result.generated_sql
        result.sql_generation_error = text_result.sql_generation_error
        result.query_result = text_result.query_result
        result.execution_error = text_result.execution_error
        result.formatted_output = text_result.formatted_output
        result.success = text_result.success
        
        return result
    
    def process_microphone(
        self,
        energy_threshold: float = 0.02,
        silence_duration: float = 1.5,
        max_duration: float = 30.0
    ) -> PipelineResult:
        """
        Record from microphone and process.
        
        Args:
            energy_threshold: Voice activity detection threshold
            silence_duration: Seconds of silence to stop recording
            max_duration: Maximum recording duration
            
        Returns:
            PipelineResult
        """
        result = PipelineResult(
            success=False,
            mode=QueryMode.MICROPHONE
        )
        
        # Record audio
        self._status("🎤 Listening... (speak your query, then pause)")
        audio_result = record_with_vad(
            energy_threshold=energy_threshold,
            silence_duration=silence_duration,
            max_duration=max_duration
        )
        
        if not audio_result['success']:
            result.transcription_error = audio_result['error']
            return result
        
        # Transcribe
        self._status("Transcribing...")
        trans_result = transcribe_audio(
            audio_result['audio_data'],
            audio_result['sample_rate']
        )
        
        if not trans_result['success']:
            result.transcription_error = trans_result['error']
            return result
        
        result.transcription = trans_result['text']
        self._status(f"You said: \"{result.transcription}\"")
        
        # Continue with text processing
        text_result = self.process_text(result.transcription)
        
        # Merge results
        result.generated_sql = text_result.generated_sql
        result.sql_generation_error = text_result.sql_generation_error
        result.query_result = text_result.query_result
        result.execution_error = text_result.execution_error
        result.formatted_output = text_result.formatted_output
        result.success = text_result.success
        
        return result


def run_interactive_session():
    """Run an interactive voice-to-SQL session."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    
    console = Console()
    agent = VoiceToSQLAgent(verbose=False)
    
    console.print(Panel.fit(
        "[bold blue]Voice-to-SQL Agent[/bold blue]\n"
        "Speak your database questions naturally!\n\n"
        "Commands:\n"
        "  [green]q[/green] or [green]quit[/green] - Exit\n"
        "  [green]t:[query][/green] - Text mode (skip audio)\n"
        "  [green]Press Enter[/green] - Voice input"
    ))
    
    while True:
        try:
            user_input = console.input("\n[bold]Press Enter to speak (or type command):[/bold] ").strip()
            
            if user_input.lower() in ('q', 'quit', 'exit'):
                console.print("[yellow]Goodbye![/yellow]")
                break
            
            if user_input.startswith('t:'):
                # Text mode
                query = user_input[2:].strip()
                console.print(f"[dim]Processing text query: {query}[/dim]")
                result = agent.process_text(query)
            else:
                # Voice mode
                result = agent.process_microphone()
            
            # Display result
            console.print()
            if result.success:
                if result.transcription:
                    console.print(f"[green]📝 You said:[/green] \"{result.transcription}\"")
                console.print(f"[blue]🔍 SQL:[/blue] {result.generated_sql}")
                console.print(f"[cyan]📊 Results:[/cyan]")
                console.print(result.formatted_output)
            else:
                console.print(f"[red]Error:[/red] {result}")
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Goodbye![/yellow]")
            break


if __name__ == "__main__":
    run_interactive_session()
