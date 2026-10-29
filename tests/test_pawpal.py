"""Tests for PawPal+ core classes."""

from datetime import date, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


def make_scheduler():
    """Owner with two pets; Luna's breakfast is already done."""
    owner = Owner("Jordan", 60)
    mochi, luna = Pet("Mochi", "dog"), Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    mochi.add_task(Task("Walk", 30, "high"))
    luna.add_task(Task("Meds", 5, "high"))
    breakfast = Task("Breakfast", 10, "high")
    luna.add_task(breakfast)
    breakfast.mark_complete()
    return Scheduler(owner)


def test_mark_complete_changes_status():
    task = Task("Morning walk", 30, "high")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet("Mochi", "dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Breakfast", 10, "high"))

    assert len(pet.tasks) == 1


def test_filter_tasks_by_pet_name():
    scheduler = make_scheduler()

    names = [t.description for t in scheduler.filter_tasks(pet_name="Luna")]

    assert names == ["Meds", "Breakfast"]


def test_filter_tasks_by_completion_status():
    scheduler = make_scheduler()

    assert [t.description for t in scheduler.filter_tasks(completed=True)] == ["Breakfast"]
    assert [t.description for t in scheduler.filter_tasks(completed=False)] == ["Walk", "Meds"]


def test_filter_tasks_by_pet_and_status_combined():
    scheduler = make_scheduler()

    names = [t.description for t in scheduler.filter_tasks(pet_name="luna", completed=False)]

    assert names == ["Meds"]


def test_filter_tasks_with_no_filters_or_unknown_pet():
    scheduler = make_scheduler()

    assert len(scheduler.filter_tasks()) == 3
    assert scheduler.filter_tasks(pet_name="Rex") == []


def make_owner_with(task):
    """Owner with one pet that has the given task."""
    owner = Owner("Jordan", 60)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    pet.add_task(task)
    return owner, pet


def test_completing_daily_task_creates_next_day_copy():
    today = date(2026, 10, 28)
    walk = Task("Walk", 30, "high", time="07:30", frequency="daily", due_date=today)
    owner, pet = make_owner_with(walk)

    next_walk = Scheduler(owner).mark_task_complete(walk)

    assert walk.completed is True
    assert next_walk in pet.tasks
    assert next_walk.due_date == today + timedelta(days=1)
    assert next_walk.completed is False
    assert (next_walk.description, next_walk.time, next_walk.pet_name) == ("Walk", "07:30", "Mochi")


def test_completing_weekly_task_creates_copy_one_week_later():
    today = date(2026, 10, 28)
    bath = Task("Bath", 20, "low", frequency="weekly", due_date=today)
    owner, pet = make_owner_with(bath)

    next_bath = Scheduler(owner).mark_task_complete(bath)

    assert next_bath.due_date == today + timedelta(weeks=1)
    assert len(pet.tasks) == 2


def test_completing_one_off_task_creates_nothing():
    vet = Task("Vet visit", 60, "high")  # frequency defaults to "once"
    owner, pet = make_owner_with(vet)

    assert Scheduler(owner).mark_task_complete(vet) is None
    assert len(pet.tasks) == 1


def test_recompleting_task_does_not_duplicate_next_occurrence():
    walk = Task("Walk", 30, "high", frequency="daily")
    owner, pet = make_owner_with(walk)
    scheduler = Scheduler(owner)

    scheduler.mark_task_complete(walk)
    walk.mark_incomplete()
    scheduler.mark_task_complete(walk)

    assert len(pet.tasks) == 2


def test_next_occurrence_is_not_in_todays_plan():
    today = date(2026, 10, 28)
    walk = Task("Walk", 30, "high", frequency="daily", due_date=today)
    owner, _ = make_owner_with(walk)
    scheduler = Scheduler(owner)
    scheduler.mark_task_complete(walk)

    assert scheduler.generate_daily_plan(day=today) == []
    tomorrow_plan = scheduler.generate_daily_plan(day=today + timedelta(days=1))
    assert [item.task.description for item in tomorrow_plan] == ["Walk"]


def make_conflict_scheduler(*pet_tasks):
    """Scheduler for an owner with Mochi and Luna; pet_tasks are (pet_name, Task) pairs."""
    owner = Owner("Jordan", 120)
    owner.add_pet(Pet("Mochi", "dog"))
    owner.add_pet(Pet("Luna", "cat"))
    for pet_name, task in pet_tasks:
        owner.get_pet(pet_name).add_task(task)
    return Scheduler(owner)


def test_detects_same_time_conflict_across_different_pets():
    scheduler = make_conflict_scheduler(
        ("Mochi", Task("Breakfast", 10, "high", time="08:00")),
        ("Luna", Task("Breakfast", 5, "high", time="08:00")),
    )

    conflicts = scheduler.detect_conflicts()

    assert len(conflicts) == 1
    assert "different pets" in conflicts[0]


def test_detects_overlap_for_same_pet():
    scheduler = make_conflict_scheduler(
        ("Mochi", Task("Walk", 30, "high", time="07:30")),
        ("Mochi", Task("Nail trim", 10, "low", time="07:45")),
    )

    conflicts = scheduler.detect_conflicts()

    assert len(conflicts) == 1
    assert "same pet" in conflicts[0]
    assert "Walk" in conflicts[0] and "Nail trim" in conflicts[0]


def test_back_to_back_tasks_are_not_a_conflict():
    scheduler = make_conflict_scheduler(
        ("Mochi", Task("Walk", 30, "high", time="07:30")),
        ("Luna", Task("Breakfast", 5, "high", time="08:00")),
    )

    assert scheduler.detect_conflicts() == []


def test_completed_and_untimed_tasks_are_ignored():
    done = Task("Meds", 5, "high", time="08:00")
    done.mark_complete()
    scheduler = make_conflict_scheduler(
        ("Mochi", Task("Breakfast", 10, "high", time="08:00")),
        ("Luna", done),
        ("Luna", Task("Play", 15, "medium")),
    )

    assert scheduler.detect_conflicts() == []


def test_long_task_conflicts_with_every_task_inside_it():
    scheduler = make_conflict_scheduler(
        ("Mochi", Task("Hike", 120, "high", time="09:00")),
        ("Luna", Task("Meds", 5, "high", time="09:30")),
        ("Luna", Task("Lunch", 10, "high", time="10:30")),
    )

    assert len(scheduler.detect_conflicts()) == 2


def test_generate_daily_plan_records_conflicts():
    scheduler = make_conflict_scheduler(
        ("Mochi", Task("Breakfast", 10, "high", time="08:00")),
        ("Luna", Task("Breakfast", 5, "high", time="08:00")),
    )

    plan = scheduler.generate_daily_plan()

    assert len(scheduler.conflicts) == 1
    assert [(item.start, item.end) for item in plan] == [("08:00", "08:05"), ("08:05", "08:15")]
