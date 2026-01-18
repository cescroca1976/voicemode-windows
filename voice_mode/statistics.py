"""
Conversation statistics and analytics for Voice Mode.

Tracks token usage, turnaround times, and success rates for voice
interactions. Supports exporting to JSON and displaying a terminal dashboard.
"""

import json
import logging
import os
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import Counter

from voice_mode.config import BASE_DIR, logger

class StatisticsManager:
    """Manages conversation statistics tracking and reporting."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(BASE_DIR) / "stats"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.current_stats_file = self.base_dir / f"stats_{date.today().isoformat()}.jsonl"

    def track_conversation(self, 
                          message: str, 
                          response: str, 
                          timing_str: Optional[str] = None,
                          transport: Optional[str] = None,
                          voice_provider: Optional[str] = None,
                          voice_name: Optional[str] = None,
                          model: Optional[str] = None,
                          success: bool = True,
                          error_message: Optional[str] = None):
        """Record a single voice interaction."""
        
        # Calculate turnaround time from timing string if present
        # Format usually: "Total: 1.2s (STT: 0.5s, TTS: 0.7s)"
        turnaround_ms = 0
        if timing_str and "Total:" in timing_str:
            try:
                # Extract the total seconds
                total_part = timing_str.split("s")[0].split("Total:")[1].strip()
                turnaround_ms = int(float(total_part) * 1000)
            except (ValueError, IndexError):
                pass

        entry = {
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "turnaround_ms": turnaround_ms,
            "timing_info": timing_str,
            "transport": transport,
            "provider": voice_provider,
            "voice": voice_name,
            "model": model,
            "input_len": len(message),
            "output_len": len(response),
            "error": error_message
        }
        
        # We use JSONL for efficient appending
        try:
            with open(self.current_stats_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to record statistics: {e}")

    def get_summary(self, days: int = 7) -> Dict[str, Any]:
        """Aggregate statistics for the last N days."""
        total_interactions = 0
        successful_interactions = 0
        total_turnaround = 0
        
        providers = Counter()
        voices = Counter()
        models = Counter()
        
        # Iterate through files for the last N days
        # (Simplified: just search all files in stats dir for now)
        for stats_file in self.base_dir.glob("stats_*.jsonl"):
            try:
                with open(stats_file, "r") as f:
                    for line in f:
                        if not line.strip(): continue
                        data = json.loads(line)
                        
                        total_interactions += 1
                        if data.get("success", True):
                            successful_interactions += 1
                            
                        total_turnaround += data.get("turnaround_ms", 0)
                        
                        if data.get("provider"):
                            providers[data["provider"]] += 1
                        if data.get("voice"):
                            voices[data["voice"]] += 1
                        if data.get("model"):
                            models[data["model"]] += 1
            except Exception:
                continue
                
        avg_turnaround = total_turnaround / total_interactions if total_interactions > 0 else 0
        success_rate = (successful_interactions / total_interactions * 100) if total_interactions > 0 else 0
        
        return {
            "total_interactions": total_interactions,
            "success_rate": round(success_rate, 1),
            "avg_turnaround_ms": int(avg_turnaround),
            "top_providers": dict(providers.most_common(3)),
            "top_voices": dict(voices.most_common(5)),
            "top_models": dict(models.most_common(5))
        }

    def display_dashboard(self):
        """Print a summary dashboard to the terminal."""
        summary = self.get_summary()
        
        print("\n" + "="*40)
        print(" VOICE MODE STATISTICS DASHBOARD ")
        print("="*40)
        print(f"Total Interactions:   {summary['total_interactions']}")
        print(f"Success Rate:         {summary['success_rate']}%")
        print(f"Avg Turnaround:       {summary['avg_turnaround_ms']}ms")
        
        if summary['top_providers']:
            print("\nTop Providers:")
            for p, count in summary['top_providers'].items():
                print(f"  - {p:12} {count}")
                
        if summary['top_voices']:
            print("\nTop Voices:")
            for v, count in summary['top_voices'].items():
                print(f"  - {v:12} {count}")
        
        print("="*40 + "\n")


# Global tracking function used by tools
_manager = None

def track_conversation(*args, **kwargs):
    """Global helper to track a conversation interaction."""
    global _manager
    if _manager is None:
        _manager = StatisticsManager()
    _manager.track_conversation(*args, **kwargs)


def get_stats_manager() -> StatisticsManager:
    """Get the global StatisticsManager instance."""
    global _manager
    if _manager is None:
        _manager = StatisticsManager()
    return _manager


if __name__ == "__main__":
    # Test stub
    mgr = StatisticsManager()
    mgr.track_conversation("hello", "hi there", "Total: 1.1s", "mcp", "openai", "nova", "tts-1")
    mgr.display_dashboard()
