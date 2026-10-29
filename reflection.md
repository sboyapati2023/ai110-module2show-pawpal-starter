# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

- Add pet class. Attributes: name, breed/species, age, owner (reference or string).
- Add owner class. Attributes: title, category (e.g., walk, feeding, meds, grooming), duration (in minutes, required), priority (e.g., High, Medium, Low, required), preferred_time (optional), is_recurring (optional).
- Add task class. Attributes: name, time_available_today (total minutes they can spend on pet care), preferences (e.g., preferred walk windows).
- Add scheduler class creates schedules using pet, owner and tasks. Required actions/methods for scheduler: 
  Scheduler Methods:
    - sort_tasks(): Sorts the pet's task queue based on priority rules.
	- generate_daily_plan(pet, owner): Evaluates constraints, fits tasks into the available time budget, drops or flags lower priority items if time runs out, and builds the finalized schedule.
	- get_reasoning(): Returns a string explaining why items were selected or omitted.


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?


    The scheduler should primarily evaluate three core constraints:
    • Time Availability (Hard Constraint): The total minutes required by scheduled tasks cannot exceed the owner's time_available_today.
    • Task Priority (Sorting Constraint): Tasks are categorized into tiers (e.g., High for medications/feeding, Medium for walks, Low for grooming). High-priority items are always evaluated and slotted first.
    • Owner Preferences (Soft Constraint): Optional parameters such as preferred time-of-day windows (e.g., Morning vs. Evening) or task cap limits (e.g., no more than 2 high-energy tasks per day).

    How did you decide which constraints mattered most?

    The hierarchy is determined by pet safety and user feasibility:
    1. Time availability is the absolute bottleneck. A busy owner physically cannot execute 4 hours of tasks if they only have 2 hours available.
    2. Priority ranks second because vital medical and nutritional needs (meds, feeding) must take precedence over flexible enrichment (grooming, teaching new tricks) when time is scarce.

- How did you decide which constraints mattered most?

    1. Time availability is the absolute bottleneck. A busy owner physically cannot execute 4 hours of tasks if they only have 2 hours available.
    2. Priority ranks second because vital medical and nutritional needs (meds, feeding) must take precedence over flexible enrichment (grooming, teaching new tricks) when time is scarce.
    3. Preferences rank last as soft constraints; it is better to walk a dog at a non-ideal time than to skip the walk entirely.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
    The scheduler utilizes a Greedy Algorithm approach based on priority-first sorting, rather than a complex optimization algorithm (like Knapsack optimization).
    • The Tradeoff: If a high-priority task takes up a massive block of time (e.g., a 60-minute vet run), the scheduler will select it and run out of time, leaving several medium-priority, short tasks unscheduled (e.g., a 15-minute fetch session and a 10-minute brush). It prioritizes importance over maximizing the total number of tasks completed.

- Why is that tradeoff reasonable for this scenario?
    This is highly reasonable for pet care because skipping a critical task can have severe health consequences.
    • Missing a high-priority medication window or feeding time because the algorithm wanted to pack three low-priority items into the schedule would be a failure of care.
    • Real-world pet ownership naturally operates on a "must-do first" basis, making a greedy, priority-first approach intuitive and safe for the user.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?

AI was used as an architectural sounding board to map out the system requirements into logical, cleanly decoupled software layers.
• How it was used: It helped structure the core relationship between the Pet, Task, and Scheduler entities, ensuring that the scheduling engine was treated as a separate business-logic object rather than cramming algorithm complexity inside the data models.
• Most helpful prompt styles: Highly specific role-playing prompts. For example:"Act as a software architect. I am building a pet-care scheduling app with hard time limits and multi-tier priorities. Suggest a clean Python class layout that separates data from the scheduling engine, and identify two potential edge cases in this setup."
- What kinds of prompts or questions were most helpful?

The initial implementation of the scheduler ran into a classic problem: it only optimized for priority, occasionally starving the user of smaller, high-yield tasks when a single high-priority task took up the entire day's time budget.
• How it was used: AI was used to analyze the greedy choice property of the algorithm and suggest refactoring methods to safely track remaining time while generating descriptive "reasoning strings" explaining why a task was skipped.
• Most helpful prompt styles: Comparative optimization questions. For example:"Here is my Python function that loops through a sorted list of tasks. How can I refactor this loop so that it logs explicit reasons (e.g., 'Skipped: exceeds remaining time budget of 15 mins') into a dictionary while it executes?"

Tradeoff: When two tasks overlap, the scheduler flags the conflict with a warning but resolves it by clock order, not priority: the task with the earlier preferred time keeps its slot and the other is pushed back to start when the first ends. This means a low-priority task (e.g., a 07:45 nail trim) can delay a high-priority one (an 08:00 feeding) by a few minutes.

Why it's reasonable: Pet care times are usually flexible by a few minutes, so a warning that lets the owner decide is more useful than silently reshuffling the day. "Earlier time goes first" is simple and predictable, and priority still controls the decision that matters most: which tasks make it into the plan when time is limited. If a task had to happen at an exact time (like medication), I would add a "fixed time" option so it keeps its slot and other tasks move around it.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?


8:33 PM
I tested 61 behaviors: 43 pass and 17 fail, and the main.py demo run works. Each failure points to a bug.

Your suite (17/17 pass): marking tasks complete, adding tasks, filtering by pet and status, daily/weekly/one-time repeats, and conflict detection (same pet, different pets, back-to-back, long overlaps).

Demo (main.py): sorting, filtering, repeating tasks, and all 3 deliberate conflicts work.

My logic tests (17 pass, 15 fail)

✅ Invalid times and durations are rejected, and times like 8:05 are formatted as 08:05.
✅ The time budget works: a task that uses it up exactly fits, and the plan skips a task that's too big but fits smaller ones after it.
✅ Overdue tasks are included, future tasks are left out, and scheduled tasks never overlap.
❌ Validation gaps: blank task names, bad Owner start times and budgets, and confusing errors for None or text values.
❌ Scheduling bugs:
Low-priority tasks can push high-priority ones later.
Tasks with no set time go at the end of the day.
The schedule can run past midnight.
"Why this plan?" never says when a task was moved.
❌ Repeating-task bugs:
Two daily tasks with the same name: only one comes back tomorrow.
Completing an overdue task creates a copy that is still overdue.
Un-ticking a task leaves tomorrow's copy behind.
❌ Pets named "Max" and "max" get their tasks mixed together.
My UI tests (9 pass, 2 fail)

✅ The app loads, pets and tasks can be added, and bad inputs show errors instead of crashing.
✅ Tasks over the time budget are listed as skipped, and ticking a daily task adds its next copy.
❌ A blank task name is accepted.
❌ Ticking any checkbox makes the schedule disappear.
Not tested yet: performance, the preferences field, and how the layout looks in a real browser.

- Why were these tests important?

These tests mattered because they check whether the app does its main job, building a schedule a pet owner can trust, and not just whether the code runs:

Scheduling tests check that the core promise holds: the most important care happens on time and within the owner's available time. A wrong plan could mean a late insulin dose or a missed walk.
Repeating-task tests matter because daily meds and feedings are the tasks most likely to repeat. If one quietly stops coming back or gets mixed up with another, the owner might never notice.
Conflict tests make sure the app warns the owner when two tasks clash, instead of quietly moving one of them.
Validation tests make sure bad input (blank names, bad times, wrong types) shows a clear error, not a crash or a confusing schedule.
UI tests confirm the screens work as a user would actually use them, since correct logic is useless if the schedule disappears on a click.
Edge cases (exact time budget, midnight, overdue tasks, duplicate names) are where bugs usually hide; the normal "happy path" already worked.
Together they showed the basics are solid and pinpointed 12 specific bugs to fix.

Requirement	Test(s) in tests/test_pawpal.py	Status
Sorting (tasks come back in time order)	test_sort_by_time_returns_chronological_order checks that tasks added out of order come back as 07:30, 08:00, 12:15, 18:00, including one entered as 8:00<br>test_sort_by_time_puts_untimed_tasks_last checks that tasks with no set time go last	New
Recurrence (a completed daily task comes back the next day)	test_completing_daily_task_creates_next_day_copy checks that the new copy is due the next day, isn't completed, and keeps the same name, time and pet	Already there
Conflict detection (tasks at the same time get flagged)	test_detects_same_time_conflict_across_different_pets checks two pets at 08:00<br>test_detects_duplicate_time_for_same_pet checks one pet with two tasks at 17:30	First already there; second is new
There was no sorting test before, so I added two. I also added the same-pet duplicate-time test so conflicts are checked for one pet as well as across pets. I only changed the test file; the app code is unchanged.




**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I'm most satisfied with the conflict detection and the "Why this plan?" explanations. The scheduler doesn't just build a plan; it warns when tasks overlap (for the same pet or across pets) and explains why each task was scheduled or skipped. That makes the app feel trustworthy, because the owner can see the reasoning instead of just getting a list.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
I would redesign the clock placement so it considers priority, not just time order. Right now a low-priority task can push a high-priority one (like meds) later, and tasks with no set time get placed at the end of the day instead of filling earlier gaps. I'd also fix recurring tasks with the same name so both repeat, stop schedules from running past midnight, and use the owner's preferences field, which currently isn't used. Finally, I'd keep the generated schedule visible in the app after ticking a task.
**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

I learned that passing tests don't prove the system is correct. All my original tests passed, but edge-case testing with AI found 12 bugs, like low-priority tasks delaying high-priority ones and recurring tasks disappearing. My first tests mostly checked the cases I already expected to work. Working with AI was most useful when I asked it to try to break the system, not just confirm it worked. I still had to judge which failures were real bugs and which were design choices.

I rated the scheduler's reliability ⭐⭐⭐☆☆ (3/5) and added that rating