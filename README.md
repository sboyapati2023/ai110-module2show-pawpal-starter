# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...

#Today's Schedule for Jordan
#Pets: Mochi, Luna | Time available: 90 min
#============================================================
#07:30-08:00  Mochi  Morning walk   (30 min, high)
#08:00-08:05  Luna   Breakfast      (5 min, high)
#08:15-08:25  Mochi  Breakfast      (10 min, high)
#09:00-09:05  Luna   Thyroid meds   (5 min, high)
#17:30-17:45  Luna   Play session   (15 min, medium)
#18:00-18:20  Mochi  Brush coat     (20 min, low)

#Why this plan:
#  Scheduled 'Breakfast' for Luna: high priority, 5 min fits (85 min left).
#  Scheduled 'Thyroid meds' for Luna: high priority, 5 min fits (80 min left).
#  Scheduled 'Breakfast' for Mochi: high priority, 10 min fits (70 min left).
#  Scheduled 'Morning walk' for Mochi: high priority, 30 min fits (40 min left).
#  Scheduled 'Play session' for Luna: medium priority, 15 min fits (25 min left).
#  Scheduled 'Brush coat' for Mochi: low priority, 20 min fits (5 min left).
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
python -m pytest

# Show each test by name:
python -m pytest -v

# Run with coverage (needs: pip install pytest-cov):
python -m pytest --cov
```

The tests cover the scheduler's core behaviors: sorting tasks into time order, creating the next occurrence when a daily or weekly task is completed, detecting overlapping or duplicate task times, filtering tasks, and basic task and pet operations. All tests live in `tests/test_pawpal.py` and test the classes in `pawpal_system.py` directly, without the Streamlit UI.

| Area | What the tests check |
|------|----------------------|
| Task basics | Marking a task complete changes its status; adding a task increases the pet's task count |
| Sorting | `sort_by_time()` returns tasks in time order, even when added out of order or entered as `"8:00"`; tasks with no time go last |
| Filtering | By pet name (case-insensitive), by completion status, both combined, no filters, and an unknown pet |
| Recurrence | Completing a daily task adds a copy due the next day; weekly adds one due a week later; one-off tasks add nothing; completing twice doesn't duplicate; tomorrow's copy stays out of today's plan |
| Conflict detection | The same time across different pets and for the same pet; partial overlaps; a long task overlapping several others; back-to-back tasks are not conflicts; completed and untimed tasks are ignored; `generate_daily_plan()` records conflicts |

Sample test output:

```
$ python -m pytest
============================= test session starts ==============================
collected 20 items

tests/test_pawpal.py ....................                                [100%]

============================== 20 passed in 0.02s ==============================
```

**Known gaps.** Extra edge-case testing found cases the scheduler doesn't handle yet:

- A low-priority task can push a high-priority one later.
- Tasks with no set time are placed at the end of the day.
- A plan can run past midnight.
- Two daily tasks with the same name don't both recur.

These aren't covered by the suite yet. See `reflection.md` for details.

**Confidence Level: ⭐⭐⭐☆☆ (3/5)**

All 20 tests pass, and the core behaviors are reliable for everyday use: sorting, the time budget, recurrence, conflict detection, and non-overlapping plans. I'm not giving it a higher rating because of the known gaps above, which can produce a plan with a high-priority task delayed or a recurring task missing. Fixing those and adding tests for them would raise it to 4–5 stars.

## 📐 Smarter Scheduling

All scheduling logic lives in `pawpal_system.py`. The `Scheduler` reads tasks for **every** pet through `Owner.get_all_tasks()`, so one plan covers all of an owner's pets.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.sort_tasks()` | By clock time, or by priority → duration → time |
| Filtering | `Scheduler.filter_tasks()` | By pet name, completion status, and/or due date |
| Time budget | `Scheduler.generate_daily_plan()` | Skips lower-priority tasks once the owner's minutes run out |
| Conflict handling | `Scheduler.detect_conflicts()` | Warns on overlapping time ranges, same pet or different pets |
| Recurring tasks | `Scheduler.mark_task_complete()`, `Task.next_occurrence()` | Daily → +1 day, weekly → +7 days |

### Sorting

- **`Scheduler.sort_by_time(tasks)`** orders tasks by preferred start time using a lambda key on the `"HH:MM"` string: `sorted(tasks, key=lambda t: t.time or "24:00")`. Times are zero-padded when a `Task` is created (`"8:30"` → `"08:30"`), so string order matches clock order. Tasks with no time sort last.
- **`Scheduler.sort_tasks(tasks)`** orders by priority (high → medium → low), then shorter duration first, then preferred time. This decides which tasks get into the plan first when time is limited.

### Filtering

- **`Scheduler.filter_tasks(pet_name=None, completed=None, due_by=None)`** starts from all of the owner's tasks and applies only the filters you pass:
  - `pet_name="Luna"`: one pet's tasks (case-insensitive)
  - `completed=False`: unfinished tasks; `completed=True`: finished ones
  - `due_by=date`: tasks due on or before that date
- Filters combine, e.g. `filter_tasks(pet_name="Mochi", completed=False)`.

### Building the daily plan

**`Scheduler.generate_daily_plan(day=None)`** runs four steps:

1. Collect pending tasks: not completed and due by `day` (default: today).
2. Check them for conflicts (see below).
3. **Select** tasks in `sort_tasks()` order while they fit `Owner.time_available_today`. A task that doesn't fit is skipped, but smaller tasks after it are still tried.
4. **Place** the selected tasks on the clock from `Owner.day_start`. A task with a preferred time starts then, or right after the previous task if that one runs late.

It returns a list of `ScheduledTask` objects (task, start, end). It also fills `scheduler.skipped`, `scheduler.conflicts`, and an explanation available from **`Scheduler.get_reasoning()`**.

### Conflict detection

- **`Scheduler.detect_conflicts(day=None)`** returns a warning string for each pair of pending, timed tasks whose time ranges overlap, not just identical start times. It labels each pair as **same pet** or **different pets**:
  ```
  Conflict (different pets): Mochi's 'Breakfast' (08:15-08:25) overlaps Luna's 'Brush teeth' (08:15-08:20).
  ```
- How it works: sort timed tasks by start, then compare each task with the ones after it. Because the list is sorted, the comparison stops at the first task that starts after the current one ends. One long task is still flagged against every task inside it.
- Back-to-back tasks (07:30–08:00 then 08:00) are **not** conflicts. Completed and untimed tasks are ignored.
- Conflicts produce warnings and never stop the plan from being built. When placing tasks, the one with the earlier preferred time keeps its slot and the other starts when it ends. Priority decides which tasks make the plan, not which one wins a clashing slot.

### Recurring tasks

- Each `Task` has a `frequency` (`"once"`, `"daily"`, `"weekly"`) and a `due_date` (default: today).
- **`Task.next_occurrence()`** returns a fresh, uncompleted copy due one day or one week later, or `None` for one-off tasks.
- **`Scheduler.mark_task_complete(task)`** marks the task done and adds its next occurrence to the same pet. Completing, undoing, and completing again doesn't create a duplicate.
- `generate_daily_plan()` only includes tasks due by the chosen day, so tomorrow's copy doesn't appear in today's schedule.
- Use `Scheduler.mark_task_complete()` rather than `Task.mark_complete()` when you want recurrence. A `Task` on its own can't add anything to its pet.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
