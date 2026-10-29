"""PawPal+ core classes: Owner, Pet, Task, and Scheduler.

These are stubs that mirror diagrams/uml.mmd. Logic is filled in later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Task:
    """A single pet care activity (walk, feeding, meds, grooming, ...)."""

    title: str
    category: str  # e.g. "walk", "feeding", "meds", "grooming"
    duration: int  # minutes, required
    priority: str  # "high", "medium", or "low", required
    preferred_time: Optional[str] = None  # e.g. "08:00" or "morning"
    is_recurring: bool = False

    def priority_rank(self) -> int:
        """Return a sortable number for this task's priority (lower = more important)."""
        pass


@dataclass
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str
    breed: str = ""
    age: int = 0
    # Excluded from repr/eq to avoid infinite recursion via Owner.pets
    owner: Optional[Owner] = field(default=None, repr=False, compare=False)
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
        pass

    def remove_task(self, title: str) -> None:
        """Remove a task by title."""
        pass


@dataclass
class Owner:
    """The person caring for one or more pets."""

    name: str
    time_available_today: int  # total minutes available for pet care
    preferences: dict = field(default_factory=dict)  # e.g. {"walk_window": "morning"}
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner and link the pet back to the owner."""
        pass


class Scheduler:
    """Builds a daily care plan for a pet within the owner's time budget."""

    def __init__(self) -> None:
        self.scheduled: list[Task] = []
        self.skipped: list[Task] = []
        self.reasons: list[str] = []

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by priority rules (high first, then shorter duration)."""
        pass

    def generate_daily_plan(self, pet: Pet, owner: Owner) -> list[Task]:
        """Fit the pet's tasks into the owner's available time.

        Sorts tasks, adds them while time remains, and records lower
        priority tasks that were skipped because time ran out.
        """
        pass

    def get_reasoning(self) -> str:
        """Explain why each task was scheduled or skipped."""
        pass
