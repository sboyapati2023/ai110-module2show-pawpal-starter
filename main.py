"""Demo script: build an owner with two pets, show sorting/filtering, and print today's schedule."""

from pawpal_system import Owner, Pet, Scheduler, Task


def print_tasks(title: str, tasks: list[Task]) -> None:
    """Print a heading and one line per task."""
    print(f"\n{title}")
    print("-" * 60)
    if not tasks:
        print("  (none)")
    for task in tasks:
        status = "done" if task.completed else "todo"
        print(f"  {task.time or '--:--'}  {task.pet_name:<6} {task.description:<14} "
              f"({task.duration} min, {task.priority}, {status}, due {task.due_date:%b %d})")


def main() -> None:
    owner = Owner(name="Jordan", time_available_today=90, day_start="07:30")

    mochi = Pet(name="Mochi", species="dog", breed="Shiba Inu", age=3)
    luna = Pet(name="Luna", species="cat", breed="Tabby", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Added deliberately out of time order, including "8:00" without a leading zero
    mochi.add_task(Task("Brush coat", 20, "low", time="18:00", frequency="weekly", category="grooming"))
    luna.add_task(Task("Play session", 15, "medium", time="17:30", category="enrichment"))
    mochi.add_task(Task("Breakfast", 10, "high", time="08:15", frequency="daily", category="feeding"))
    luna.add_task(Task("Thyroid meds", 5, "high", time="09:00", frequency="daily", category="meds"))
    mochi.add_task(Task("Fetch in yard", 15, "medium", category="enrichment"))  # no preferred time
    mochi.add_task(Task("Morning walk", 30, "high", time="07:30", frequency="daily", category="walk"))
    luna.add_task(Task("Breakfast", 5, "high", time="8:00", frequency="daily", category="feeding"))
    # Deliberate clashes:
    #   08:15 - Luna's brush teeth at the same time as Mochi's breakfast (different pets)
    #   17:30 - Luna's ear cleaning at the same time as Luna's play session (same pet)
    #   07:45 - Mochi's nail trim starts inside Mochi's morning walk (overlap, same pet)
    luna.add_task(Task("Brush teeth", 5, "medium", time="08:15", category="grooming"))
    luna.add_task(Task("Ear cleaning", 10, "medium", time="17:30", category="grooming"))
    mochi.add_task(Task("Nail trim", 10, "low", time="07:45", category="grooming"))

    scheduler = Scheduler(owner)

    # Complete a daily task: the scheduler adds tomorrow's copy automatically
    meds = luna.tasks[1]  # Thyroid meds (daily)
    tomorrow_meds = scheduler.mark_task_complete(meds)
    print(f"Completed '{meds.description}' (due {meds.due_date}) -> "
          f"next occurrence due {tomorrow_meds.due_date}, completed={tomorrow_meds.completed}")

    all_tasks = owner.get_all_tasks()

    print_tasks("All tasks (in the order they were added)", all_tasks)
    print_tasks("Sorted by time (sort_by_time)", scheduler.sort_by_time(all_tasks))
    print_tasks("Sorted by priority (sort_tasks)", scheduler.sort_tasks(all_tasks))
    print_tasks("Only Luna's tasks (filter_tasks pet_name='Luna')", scheduler.filter_tasks(pet_name="Luna"))
    print_tasks("Completed tasks (filter_tasks completed=True)", scheduler.filter_tasks(completed=True))
    print_tasks(
        "Mochi's unfinished tasks, by time (filter + sort)",
        scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Mochi", completed=False)),
    )

    print("\nConflict check (detect_conflicts)")
    print("-" * 60)
    conflicts = scheduler.detect_conflicts()
    for warning in conflicts:
        print(f"  ! {warning}")
    expected = [
        ("Breakfast", "Brush teeth", "different pets"),
        ("Play session", "Ear cleaning", "same pet"),
        ("Morning walk", "Nail trim", "same pet"),
    ]
    for first, second, scope in expected:
        found = any(first in w and second in w and scope in w for w in conflicts)
        print(f"  [{'OK' if found else 'MISSING'}] {first} vs {second} ({scope})")

    plan = scheduler.generate_daily_plan()

    print(f"\n\nToday's Schedule for {owner.name}")
    print(f"Pets: {', '.join(p.name for p in owner.pets)} | Time available: {owner.time_available_today} min")
    print("=" * 60)
    for item in plan:
        task = item.task
        print(f"{item.start}-{item.end}  {task.pet_name:<6} {task.description:<14} "
              f"({task.duration} min, {task.priority})")

    if scheduler.conflicts:
        print("\nConflicts (if both are scheduled, the later one starts when the earlier one ends):")
        for warning in scheduler.conflicts:
            print(f"  ! {warning}")

    if scheduler.skipped:
        print("\nNot scheduled today:")
        for task in scheduler.skipped:
            print(f"  - {task.pet_name}: {task.description} ({task.duration} min, {task.priority})")

    print("\nWhy this plan:")
    for line in scheduler.get_reasoning().splitlines():
        print(f"  {line}")


if __name__ == "__main__":
    main()
