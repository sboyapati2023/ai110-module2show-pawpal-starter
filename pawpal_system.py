"""PawPal+ core classes: Owner, Pet, Task, and Scheduler."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from typing import Optional

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
FREQUENCIES = {"once", "daily", "weekly"}
RECURRENCE_GAP = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}


def _to_minutes(hhmm: str) -> int:
    """Convert "HH:MM" to minutes after midnight."""
    try:
        hours, minutes = (int(part) for part in hhmm.split(":"))
    except ValueError:
        raise ValueError(f"time '{hhmm}' must be in HH:MM format, e.g. 08:30") from None
    if not (0 <= hours < 24 and 0 <= minutes < 60):
        raise ValueError(f"time '{hhmm}' is not a valid clock time")
    return hours * 60 + minutes


def _to_hhmm(total: int) -> str:
    """Convert minutes after midnight to "HH:MM"."""
    return f"{total // 60:02d}:{total % 60:02d}"


@dataclass
class Task:
    """A single pet care activity (walk, feeding, meds, grooming, ...)."""

    description: str
    duration: int  # minutes, required
    priority: str = "medium"  # "high", "medium", or "low"
    time: Optional[str] = None  # preferred start time, "HH:MM"
    frequency: str = "once"  # "once", "daily", or "weekly"
    completed: bool = False
    category: str = "general"  # e.g. "walk", "feeding", "meds", "grooming"
    pet_name: str = ""  # set by Pet.add_task
    due_date: date = field(default_factory=date.today)

    def __post_init__(self) -> None:
        """Normalize case and reject invalid duration, priority, frequency, or time."""
        self.priority = self.priority.lower()
        self.frequency = self.frequency.lower()
        if self.duration <= 0:
            raise ValueError("duration must be a positive number of minutes")
        if self.priority not in PRIORITY_ORDER:
            raise ValueError(f"priority must be one of {list(PRIORITY_ORDER)}")
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {sorted(FREQUENCIES)}")
        if self.time is not None:
            # Zero-pad ("8:30" -> "08:30") so times sort correctly as strings
            self.time = _to_hhmm(_to_minutes(self.time))

    @property
    def start_minutes(self) -> Optional[int]:
        """Preferred start as minutes after midnight, or None if the task has no time."""
        return _to_minutes(self.time) if self.time else None

    @property
    def end_time(self) -> Optional[str]:
        """Preferred end as "HH:MM", or None if the task has no time."""
        return _to_hhmm(self.start_minutes + self.duration) if self.time else None

    def priority_rank(self) -> int:
        """Return a sortable number for this task's priority (lower = more important)."""
        return PRIORITY_ORDER[self.priority]

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Reset this task to not done."""
        self.completed = False

    def next_occurrence(self) -> Optional[Task]:
        """Return a fresh copy due one day/week later, or None for one-off tasks."""
        gap = RECURRENCE_GAP.get(self.frequency)
        if gap is None:
            return None
        return replace(self, completed=False, due_date=self.due_date + gap)


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
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, description: str) -> bool:
        """Remove the first task with this description. Returns True if one was removed."""
        for i, task in enumerate(self.tasks):
            if task.description == description:
                del self.tasks[i]
                return True
        return False

    def pending_tasks(self) -> list[Task]:
        """Return tasks that are not completed yet."""
        return [t for t in self.tasks if not t.completed]


@dataclass
class Owner:
    """The person caring for one or more pets."""

    name: str
    time_available_today: int  # total minutes available for pet care
    day_start: str = "08:00"  # when pet care can begin, "HH:MM"
    preferences: dict = field(default_factory=dict)  # e.g. {"walk_window": "morning"}
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner and link the pet back to the owner."""
        pet.owner = self
        self.pets.append(pet)

    def get_pet(self, name: str) -> Optional[Pet]:
        """Return the pet with this name, or None."""
        return next((p for p in self.pets if p.name == name), None)

    def get_all_tasks(self) -> list[Task]:
        """Return every pet's tasks together in one list."""
        return [task for pet in self.pets for task in pet.tasks]


@dataclass
class ScheduledTask:
    """A task placed at a specific time in the daily plan."""

    task: Task
    start: str  # "HH:MM"
    end: str  # "HH:MM"


class Scheduler:
    """Retrieves, organizes, and plans tasks across all of an owner's pets."""

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler for this owner with an empty plan."""
        self.owner = owner
        self.plan: list[ScheduledTask] = []
        self.skipped: list[Task] = []
        self.reasons: list[str] = []
        self.conflicts: list[str] = []

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
        due_by: Optional[date] = None,
    ) -> list[Task]:
        """Return the owner's tasks, optionally filtered by pet name, completion status, and due date."""
        tasks = self.owner.get_all_tasks()
        if pet_name is not None:
            tasks = [t for t in tasks if t.pet_name.lower() == pet_name.strip().lower()]
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        if due_by is not None:
            tasks = [t for t in tasks if t.due_date <= due_by]
        return tasks

    def mark_task_complete(self, task: Task) -> Optional[Task]:
        """Complete a task and, if it recurs, add its next occurrence to the same pet."""
        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task is None:
            return None
        pet = self.owner.get_pet(task.pet_name)
        if pet is None:
            raise ValueError(f"no pet named '{task.pet_name}' for task '{task.description}'")
        # Don't create a duplicate if this task was completed, undone, and completed again
        for existing in pet.tasks:
            if existing.description == next_task.description and existing.due_date == next_task.due_date:
                return existing
        pet.add_task(next_task)
        return next_task

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order tasks by priority (high first), then shorter duration, then preferred time."""
        # "HH:MM" strings sort chronologically; "24:00" is later than any real time
        return sorted(tasks, key=lambda t: (t.priority_rank(), t.duration, t.time or "24:00"))

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Order tasks by preferred time; tasks with no time go last."""
        return sorted(tasks, key=lambda t: t.time or "24:00")

    def detect_conflicts(self, day: Optional[date] = None) -> list[str]:
        """Return a warning for each pair of pending timed tasks due by `day` whose times overlap."""
        return self._find_conflicts(self._pending_tasks(day or date.today()))

    def generate_daily_plan(self, day: Optional[date] = None) -> list[ScheduledTask]:
        """Pick pending tasks due by `day` (default today) by priority, then place them on the clock."""
        pending = self._pending_tasks(day or date.today())
        self.conflicts = self._find_conflicts(pending)
        chosen = self._select_within_budget(pending)
        self.plan = self._place_on_clock(chosen)
        return self.plan

    def _pending_tasks(self, day: date) -> list[Task]:
        """Return tasks that are not completed and are due on or before `day`."""
        return self.filter_tasks(completed=False, due_by=day)

    def _find_conflicts(self, tasks: list[Task]) -> list[str]:
        """Return a warning for each pair of timed tasks whose time ranges overlap."""
        timed = self.sort_by_time([t for t in tasks if t.time])
        warnings = []
        for i, first in enumerate(timed):
            first_end = first.start_minutes + first.duration
            # Sorted by start, so stop once a later task starts after `first` ends
            for second in timed[i + 1:]:
                if second.start_minutes >= first_end:
                    break
                scope = "same pet" if first.pet_name == second.pet_name else "different pets"
                warnings.append(
                    f"Conflict ({scope}): {first.pet_name}'s '{first.description}' "
                    f"({first.time}-{first.end_time}) overlaps {second.pet_name}'s "
                    f"'{second.description}' ({second.time}-{second.end_time})."
                )
        return warnings

    def _select_within_budget(self, tasks: list[Task]) -> list[Task]:
        """Greedily choose tasks in priority order while they fit the owner's time budget."""
        self.skipped, self.reasons = [], []
        budget = self.owner.time_available_today
        chosen, used = [], 0
        for task in self.sort_tasks(tasks):
            if used + task.duration <= budget:
                chosen.append(task)
                used += task.duration
                self.reasons.append(
                    f"Scheduled '{task.description}' for {task.pet_name}: "
                    f"{task.priority} priority, {task.duration} min fits "
                    f"({budget - used} min left)."
                )
            else:
                self.skipped.append(task)
                self.reasons.append(
                    f"Skipped '{task.description}' for {task.pet_name}: "
                    f"needs {task.duration} min but only {budget - used} min left."
                )
        return chosen

    def _place_on_clock(self, tasks: list[Task]) -> list[ScheduledTask]:
        """Lay tasks out from the owner's day start, honoring preferred times without overlap."""
        plan = []
        cursor = _to_minutes(self.owner.day_start)
        for task in self.sort_by_time(tasks):
            if task.time:
                cursor = max(cursor, task.start_minutes)
            end = cursor + task.duration
            plan.append(ScheduledTask(task, _to_hhmm(cursor), _to_hhmm(end)))
            cursor = end
        return plan

    def get_reasoning(self) -> str:
        """Explain why each task was scheduled or skipped."""
        if not self.reasons:
            return "No plan generated yet."
        return "\n".join(self.reasons)
