"""
Progress Tracker

Provides visual progress feedback during long-running simulations.
Shows progress bars and estimated time remaining.
"""

from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime
import time


@dataclass
class ProgressStage:
    """Represents a stage in the simulation process."""
    name: str
    percentage: float  # 0-100
    completed: bool = False
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class ProgressTracker:
    """
    Tracks and reports simulation progress with visual feedback.
    
    Provides progress bars and time estimates for long-running simulations.
    
    Example:
        >>> tracker = ProgressTracker()
        >>> tracker.start("Parkstraße DH", "DH")
        >>> tracker.update("Creating network topology")
        >>> tracker.update("Running hydraulic simulation")
        >>> tracker.complete()
    """
    
    # Define progress stages for each simulation type
    DH_STAGES = [
        ProgressStage("Loading building data", 5),
        ProgressStage("Validating inputs", 10),
        ProgressStage("Creating network topology", 25),
        ProgressStage("Adding heat exchangers", 35),
        ProgressStage("Running hydraulic simulation", 60),
        ProgressStage("Running thermal simulation", 80),
        ProgressStage("Extracting results", 95),
        ProgressStage("Exporting GeoJSON", 100),
    ]
    
    HP_STAGES = [
        ProgressStage("Loading building data", 5),
        ProgressStage("Validating inputs", 10),
        ProgressStage("Creating LV network", 25),
        ProgressStage("Adding transformer", 35),
        ProgressStage("Adding loads", 50),
        ProgressStage("Running power flow", 80),
        ProgressStage("Checking constraints", 90),
        ProgressStage("Extracting results", 100),
    ]
    
    def __init__(self, enable_progress_bar: bool = False):
        """
        Initialize progress tracker.
        
        Args:
            enable_progress_bar: If True, use tqdm progress bars
        """
        self.current_scenario = None
        self.stages: List[ProgressStage] = []
        self.current_stage_idx = 0
        self.start_time = None
        self.enable_progress_bar = enable_progress_bar
        
        # Try to import tqdm for progress bars
        if enable_progress_bar:
            try:
                from tqdm import tqdm
                self.tqdm = tqdm
            except ImportError:
                self.tqdm = None
                self.enable_progress_bar = False
    
    def start(self, scenario_name: str, simulation_type: str = "DH"):
        """
        Initialize progress tracking for a new simulation.
        
        Args:
            scenario_name: Name of scenario being simulated
            simulation_type: "DH" or "HP"
        """
        self.current_scenario = scenario_name
        self.stages = (self.DH_STAGES.copy() if simulation_type == "DH" 
                      else self.HP_STAGES.copy())
        self.current_stage_idx = 0
        self.start_time = time.time()
        
        print(f"\n  🚀 Starting: {scenario_name}")
        print(f"  Progress: [{'░' * 20}] 0%")
    
    def update(self, stage_name: str):
        """
        Update progress to a specific stage.
        
        Args:
            stage_name: Name of the stage being entered
        """
        for idx, stage in enumerate(self.stages):
            if stage.name == stage_name:
                self.current_stage_idx = idx
                stage.completed = True
                stage.end_time = datetime.now()
                
                progress_pct = stage.percentage
                filled = int(progress_pct / 5)  # 20 chars total
                bar = "█" * filled + "░" * (20 - filled)
                
                # Estimate remaining time
                remaining = self._estimate_remaining()
                remaining_str = f" (~{remaining:.0f}s remaining)" if remaining else ""
                
                print(f"\r  Progress: [{bar}] {progress_pct:.0f}% - {stage_name}{remaining_str}", end="")
                
                if progress_pct >= 100:
                    print()  # New line at completion
                
                return
    
    def complete(self):
        """Mark simulation as complete."""
        if self.start_time:
            elapsed = time.time() - self.start_time
            print(f"\n  ✅ Complete: {self.current_scenario} ({elapsed:.1f}s)")
        
        self.current_scenario = None
    
    def _estimate_remaining(self) -> Optional[float]:
        """
        Estimate remaining time in seconds.
        
        Returns:
            Estimated seconds remaining, or None if cannot estimate
        """
        if self.current_stage_idx == 0 or not self.start_time:
            return None
        
        elapsed = time.time() - self.start_time
        current_progress = self.stages[self.current_stage_idx].percentage
        
        if current_progress == 0:
            return None
        
        total_estimated = (elapsed / current_progress) * 100
        remaining = total_estimated - elapsed
        
        return max(0, remaining)
    
    def with_progress_bar(self, iterable, desc: str = "Processing"):
        """
        Wrap an iterable with a progress bar (if tqdm available).
        
        Args:
            iterable: Iterable to wrap
            desc: Description for progress bar
        
        Returns:
            tqdm-wrapped iterable or original iterable
        """
        if self.enable_progress_bar and self.tqdm:
            return self.tqdm(iterable, desc=desc)
        else:
            return iterable

