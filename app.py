import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

# Streamlit reruns this script on every click, so keep the Owner in session_state
# and only create it the first time.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", time_available_today=60)
owner = st.session_state.owner

st.subheader("Owner")
col1, col2, col3 = st.columns(3)
with col1:
    owner.name = st.text_input("Owner name", value=owner.name)
with col2:
    owner.time_available_today = int(
        st.number_input("Minutes available today", min_value=1, max_value=1440,
                        value=owner.time_available_today)
    )
with col3:
    owner.day_start = st.text_input("Day starts at (HH:MM)", value=owner.day_start)

st.subheader("Pets")
with st.form("add_pet", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
        breed = st.text_input("Breed (optional)")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
        age = st.number_input("Age (years)", min_value=0, max_value=40, value=1)
    if st.form_submit_button("Add pet"):
        if not pet_name.strip():
            st.error("Pet name is required.")
        elif owner.get_pet(pet_name.strip()):
            st.error(f"{owner.name} already has a pet named {pet_name.strip()}.")
        else:
            owner.add_pet(Pet(pet_name.strip(), species, breed=breed, age=int(age)))
            st.success(f"Added {pet_name.strip()}.")

if owner.pets:
    st.table([
        {"Name": p.name, "Species": p.species, "Breed": p.breed, "Age": p.age, "Tasks": len(p.tasks)}
        for p in owner.pets
    ])
else:
    st.info("No pets yet. Add one above.")

st.subheader("Tasks")
if not owner.pets:
    st.caption("Add a pet before adding tasks.")
else:
    with st.form("add_task", clear_on_submit=True):
        pet_choice = st.selectbox("For pet", [p.name for p in owner.pets])
        col1, col2, col3 = st.columns(3)
        with col1:
            description = st.text_input("Task", value="Morning walk")
            category = st.selectbox(
                "Category", ["walk", "feeding", "meds", "grooming", "enrichment", "general"]
            )
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        with col3:
            time = st.text_input("Preferred time (HH:MM, optional)")
            frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
        if st.form_submit_button("Add task"):
            try:
                task = Task(description.strip(), int(duration), priority,
                            time=time.strip() or None, frequency=frequency, category=category)
            except ValueError as e:
                st.error(f"Could not add task: {e}")
            else:
                owner.get_pet(pet_choice).add_task(task)
                st.success(f"Added '{task.description}' for {pet_choice}.")

    all_tasks = owner.get_all_tasks()
    if all_tasks:
        st.caption("Tick a task when it's done; daily and weekly tasks get their next occurrence "
                   "added automatically. Only tasks due today are scheduled.")
        scheduler = Scheduler(owner)
        for task in all_tasks:
            label = (f"{task.pet_name}: {task.description} "
                     f"({task.duration} min, {task.priority}, {task.time or 'any time'}, "
                     f"{task.frequency}, due {task.due_date:%b %d})")
            done = st.checkbox(label, value=task.completed, key=f"done_{id(task)}")
            if done and not task.completed:
                next_task = scheduler.mark_task_complete(task)
                if next_task:
                    st.rerun()  # redraw so the new occurrence shows in the list
            elif not done and task.completed:
                task.mark_incomplete()
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")

if st.button("Generate schedule"):
    try:
        scheduler = Scheduler(owner)
        plan = scheduler.generate_daily_plan()
    except ValueError as e:
        st.error(f"Could not build a schedule: {e}. Check that the day start time is HH:MM.")
    else:
        if plan:
            st.markdown(f"### Today's Schedule for {owner.name}")
            st.table([
                {"Start": item.start, "End": item.end, "Pet": item.task.pet_name,
                 "Task": item.task.description, "Minutes": item.task.duration,
                 "Priority": item.task.priority}
                for item in plan
            ])
        else:
            st.info("Nothing to schedule. Add some tasks that aren't completed yet.")

        for warning in scheduler.conflicts:
            st.warning(warning + " If both are scheduled, the later one starts when the earlier one ends.")

        if scheduler.skipped:
            st.warning("Not scheduled today (not enough time): " + ", ".join(
                f"{t.pet_name}: {t.description}" for t in scheduler.skipped))

        with st.expander("Why this plan?"):
            st.text(scheduler.get_reasoning())
