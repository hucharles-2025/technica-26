"""
Chronic-migraine / mobility-impairment student day  --  handle_minute() rule set
================================================================================

Compiled from the player's specification. Exposes (global namespace):

    GAME_STATE_START   initial GAME_STATE dict (07:00, in the dorm)
    handle_minute(s)   per-tick rule handler (returns a GAME_STATE dict)
    SAY(), ASK()       shims for standalone testing; the engine overrides them
                       (ASK is used to choose a travel destination)

Game constructs used (see comments throughout):
    task                 -> a dict in state["tasks"]; the player activates it
    mutex_groups         -> "BODY" = occupies your body/attention (class, lab, travel,
                            sleep, eating, errands, studying, rehearsing)
                            "SLEEP" = cannot be done asleep (drinking, taking meds)
    timeblockstart/end   -> engine enforces (class meetings, lab sessions)
    deadline             -> handle_minute() compares against it to resolve outcomes
    location             -> engine enforces; handle_minute() moves state["location"]
                            when a travel task completes
    burn rates           -> handle_minute() rewrites them every tick (headaches, hunger,
                            thirst, walking); the engine is assumed to apply them
    hidden task          -> TAKE_MEDS (visibility False until overdue or a headache)
    highlight            -> reminders and warnings (red/blinking)

ASSUMPTIONS ABOUT THE ENGINE
    * The engine subtracts the *_burn_rate values from energy/water/food each tick.
    * The engine ends the game when energy <= 0 or GPA < 2.5. This file only warns.
    * The engine increments time_spent for every task in active_task_set each tick.
    * The engine moves queued tasks into active_task_set when their time/location fit.

Run `python migraine_student_game.py` for a randomized smoke test with a mock engine.
"""

import copy
import random

# =============================================================================
# SECTION 0: engine shims (the engine replaces these with real versions)
# =============================================================================
try:
    SAY
except NameError:
    def SAY(message):
        print("[SAY] " + str(message))

try:
    ASK
except NameError:
    def ASK(question, choices):
        # Used to pick a travel destination. The engine supplies the real version;
        # this stand-in just picks the first choice.
        print("[ASK] %s %s" % (question, choices))
        return choices[0] if choices else None

try:
    get_minutes
except NameError:
    def get_minutes(hours, minutes=0):
        return hours * 60 + minutes


# =============================================================================
# SECTION 1: TUNING CONSTANTS  (adjust severity here, not in the logic)
# =============================================================================

# ---- GPA effects (all values are positive magnitudes) ------------------------
GPA_EE244_QUIZ_BONUS = 0.10
GPA_EE244_QUIZ_MISS_PENALTY = 0.15
GPA_PH161_QUIZ_BONUS = 0.08
GPA_PH161_QUIZ_ZERO_PENALTY = 0.15
GPA_OC225A_FULL_ATTENDANCE_BONUS = 0.05
GPA_OC225A_SKIP_PENALTY = 0.20            # scaled by fraction of period missed
GPA_OC225B_FULL_ATTENDANCE_BONUS = 0.05
GPA_OC225B_SKIP_PENALTY = 0.20            # scaled by fraction of period missed
GPA_PRESENTATION_MAX_BONUS = 0.15         # fully rehearsed + full feedback
GPA_PRESENTATION_MAX_PENALTY = 0.30       # went in blind ("substantial")
GPA_LAB_COMPLETE_BONUS = 0.10
GPA_LAB_INCOMPLETE_PENALTY = 0.25         # scaled by fraction of assignment left
GPA_STUDY_DONE_BONUS = 0.03
GPA_STUDY_MISSED_PENALTY = 0.10
GPA_SCHOLARSHIP_WARNING = 2.75            # SAY() a warning below this

# ---- Class attendance rules --------------------------------------------------
ATTENDANCE_GRACE_MIN = 2                  # tick-alignment slack on "entire period"
PRESENTATION_PRACTICE_WEIGHT = 0.65       # presentation quality = practice ...
PRESENTATION_FEEDBACK_WEIGHT = 0.35       # ... + OC225A feedback attendance
PRESENTATION_NO_SHOW_FRACTION = 0.5       # below this OC225B attendance = no-show
EXCUSED_ABSENCE_COUNTS_AS_FEEDBACK = False  # a note waives GPA hit, not missed feedback
PH161_QUIZ_PROB = 0.5                     # chance today has a pop quiz
HIGHLIGHT_LEAD_MIN = 10                   # highlight scheduled tasks this early

# ---- Energy / water / food ---------------------------------------------------
BASE_ENERGY_BURN = 0.08                   # energy points per minute
BASE_WATER_BURN = 0.50
BASE_FOOD_BURN = 0.05
SLEEP_BURN_MULT = 0.5                     # water/food burn multiplier while asleep
WATER_PER_DRINK_MIN = 10.0                # water restored per minute of drinking
FOOD_PER_EAT_MIN = 2.0                    # food restored per minute of eating
ENERGY_PER_EAT_MIN = 0.25                 # energy restored per minute of eating
SLEEP_ENERGY_GAIN_PER_MIN = 0.6           # energy restored per minute of sleep
FOOD_LOW_THRESHOLD = 15.0
HUNGER_LOW_ENERGY_MULT = 1.5              # energy burn multiplier when food is low
HUNGER_EMPTY_ENERGY_MULT = 2.0            # ... when food is zero
DEHYDRATION_ENERGY_MULT = 2.0             # energy burn multiplier when water is zero
ENERGY_WARN_LEVELS = (25.0, 10.0)

# ---- Hydration rule ----------------------------------------------------------
WATER_WARN_MIN = 20                       # warned 20-25 min after last drink
WATER_WARN_MAX = 25
WATER_DEADLINE = 30                       # headache guaranteed at this gap
DRINK_MINUTES = 2

# ---- Headaches ---------------------------------------------------------------
BASE_HEADACHE_PROB_PER_MIN = 0.003        # 0.3% per minute
WALK_HEADACHE_MULT = 2.0                  # walking doubles the chance
MED_MISSED_HEADACHE_MULT = 4.0            # overdue medication raises the chance
HEADACHE_ESCALATION_PER_MIN = 0.05        # energy burn x (1 + 0.05 * minutes)
HEADACHE_MAX_MULT = 8.0                   # cap on the escalation multiplier
HEADACHE_REMINDER_EVERY = 20              # minutes between "still hurting" messages

# ---- Sleep -------------------------------------------------------------------
SLEEP_MIN_TO_CLEAR_HEADACHE = 60          # one unbroken stretch, in minutes
SLEEP_CAP_MINUTES = 480                   # total sleep available today

# ---- Medication --------------------------------------------------------------
MED_INTERVAL = 360                        # a dose every 6 hours
MED_LAST_DOSE_BEFORE_START = get_minutes(6, 0)   # last dose taken at 06:00
MED_GRACE_MIN = 30                        # hidden until this long overdue
MED_MIN_INTERVAL = 180                    # earliest a rescue dose is allowed
MED_INITIAL_SUPPLY = 0
MED_DOSES_PER_PICKUP = 4
MED_PICKUP_MINUTES = 20
EXCUSE_NOTE_MINUTES = 30

# ---- Travel ------------------------------------------------------------------
WALK_MIN, WALK_MAX = 9, 12
WALK_OBSTRUCTION_PROB = 0.20              # elevator out / ramp blocked
WALK_OBSTRUCTED_MINUTES = 16
WALK_EXTRA_ENERGY_BURN = 0.15             # extra energy per minute while walking
PARA_ON_TIME_PROB = 0.60                  # overall on-time rate
PARA_CANCEL_PROB = 0.10                   # driver cancels, player must walk
PARA_LATE_PROB = 1.0 - PARA_ON_TIME_PROB - PARA_CANCEL_PROB
PARA_ON_TIME_MIN, PARA_ON_TIME_MAX = 6, 8
PARA_LATE_MIN, PARA_LATE_MAX = 18, 21

# ---- Lab ---------------------------------------------------------------------
LAB_ASSIGNMENT_MIN = 90                   # assignment takes 1.5 - 2.5 hours
LAB_ASSIGNMENT_MAX = 150
LAB_BREAK_MIN, LAB_BREAK_MAX = 3, 5       # TA sign-out / storage-room round trip

# ---- Study -------------------------------------------------------------------
STUDY_MINUTES = 60                        # CS216 make-up study
STUDY_HIGHLIGHT_LEAD = 120

# ---- Clock -------------------------------------------------------------------
START_MINUTE = get_minutes(7, 0)
END_OF_DAY = 1439


# =============================================================================
# SECTION 2: SCHEDULE AND LOCATIONS
# =============================================================================
LOC_DORM = "Dorm"
LOC_EE = "Electrical Engineering Building"
LOC_CS = "Computer Science Building"
LOC_ARTS = "Arts Building"
LOC_PHYS = "Physics Building"
LOC_HEALTH = "Health & Biological Sciences Complex"
LOC_DINING = "North Dining Hall"
LOC_TRANSIT = "In Transit"                # set while a travel task is running

LOCATION_NAMES = {
    "DORM": LOC_DORM, "EE": LOC_EE, "CS": LOC_CS, "ARTS": LOC_ARTS,
    "PHYSICS": LOC_PHYS, "HEALTH": LOC_HEALTH, "DINING": LOC_DINING,
}

# Class meeting times (minutes since 00:00)
EE244_START, EE244_END = get_minutes(9, 0), get_minutes(9, 50)
EE244_QUIZ_MIN = get_minutes(9, 5)
CS216_START, CS216_END = get_minutes(10, 0), get_minutes(10, 50)
CS216_CONTEXT_START, CS216_CONTEXT_END = get_minutes(10, 3), get_minutes(10, 13)
OC225A_START, OC225A_END = get_minutes(11, 0), get_minutes(12, 15)
PH161_START, PH161_END = get_minutes(14, 0), get_minutes(14, 50)
PH161_QUIZ_START, PH161_QUIZ_END = PH161_END - 10, PH161_END   # last 10 minutes
OC225B_START, OC225B_END = get_minutes(17, 0), get_minutes(18, 50)
REHEARSAL_MINUTES = 50

# Lab sessions (3 separate tasks because a task has a single time block)
LAB_SESSIONS = {
    "EE222_A": (get_minutes(12, 30), get_minutes(13, 45)),
    "EE222_B": (get_minutes(15, 0), get_minutes(16, 45)),
    "EE222_C": (get_minutes(21, 0), get_minutes(22, 15)),
}
LAB_IDS = list(LAB_SESSIONS.keys())
CLASS_IDS = ["EE244", "CS216", "OC225A", "PH161", "OC225B"]
SCHEDULED_IDS = CLASS_IDS + LAB_IDS

# Travel task ids -> mode. Only two travel tasks exist; the destination is chosen
# with ASK() at the moment the player activates one of them.
TRAVEL_TASKS = {"WALK": "walk", "PARATRANSIT": "para"}
TRAVEL_CANCEL_CHOICE = "Never mind"


# =============================================================================
# SECTION 3: TASK FACTORY AND INITIAL STATE
# =============================================================================
def _task(shortdesc, longdesc, visible=True, start=None, end=None, deadline=None,
          required=1, can_cancel=True, mutex=None, location=None):
    """Build a task dict that complies with the engine's task schema."""
    return {
        "shortdesc": shortdesc,
        "longdesc": longdesc,
        "visibility": visible,
        "timeblockstart": start,
        "timeblockend": end,
        "deadline": deadline,
        "time_spent": 0,
        "requiredmins": required,
        "can_cancel": can_cancel,
        "mutex_groups": list(mutex or []),
        "highlight": False,
        "location": location,
    }


def _build_initial_tasks():
    t = {}

    # ---- Academic commitments (mutex "BODY": you can only be in one place) ----
    t["EE244"] = _task(
        "EE244 Digital Logic Recitation",
        "9:00-9:50 AM, Electrical Engineering Building. A quiz starts at 9:05 AM: "
        "be here or your GPA drops. The rest of the class is mostly skippable.",
        start=EE244_START, end=EE244_END, deadline=EE244_END,
        required=EE244_END - EE244_START, mutex=["BODY"], location=LOC_EE)
    t["CS216"] = _task(
        "CS216 Operating Systems Lecture",
        "10:00-10:50 AM, Computer Science Building. No penalty for missing it, but "
        "missing any of 10:03-10:13 means you will need an hour of study later.",
        start=CS216_START, end=CS216_END, deadline=CS216_END,
        required=CS216_END - CS216_START, mutex=["BODY"], location=LOC_CS)
    t["OC225A"] = _task(
        "OC225A Oral Communications Lecture",
        "11:00 AM-12:15 PM, Arts Building. Full attendance is mandatory unless you "
        "have a health-center excuse note. Today is feedback day for your "
        "OC225B presentation: the more you skip, the worse it goes.",
        start=OC225A_START, end=OC225A_END, deadline=OC225A_END,
        required=OC225A_END - OC225A_START, mutex=["BODY"], location=LOC_ARTS)
    t["PH161"] = _task(
        "PH161 Physics I Lecture",
        "2:00-2:50 PM, Physics Building. Attendance isn't recorded, but pop quizzes "
        "can happen in the last 10 minutes. Being out for any reason without an "
        "excuse note means a zero.",
        start=PH161_START, end=PH161_END, deadline=PH161_END,
        required=PH161_END - PH161_START, mutex=["BODY"], location=LOC_PHYS)
    t["OC225B"] = _task(
        "OC225B Oral Communications Recitation",
        "5:00-6:50 PM, Arts Building. Full attendance mandatory unless excused. "
        "You give your presentation; the score depends on rehearsal and on how "
        "much feedback you got in OC225A.",
        start=OC225B_START, end=OC225B_END, deadline=OC225B_END,
        required=OC225B_END - OC225B_START, mutex=["BODY"], location=LOC_ARTS)
    t["REHEARSE_OC225B"] = _task(
        "Rehearse OC225B presentation",
        "About 50 minutes of practice. Only effective in the OC225A classroom "
        "(Arts Building). Must be done before OC225B starts at 5:00 PM.",
        end=OC225B_START, deadline=OC225B_START, required=REHEARSAL_MINUTES,
        mutex=["BODY"], location=LOC_ARTS)

    # ---- EE222 open lab: three sessions, one shared assignment ----
    for tid, (s, e) in LAB_SESSIONS.items():
        t[tid] = _task(
            "EE222 Signal Processing Open Lab (%s)" % _fmt(s),
            "Open lab with a TA present. No attendance, but your major lab "
            "assignment (1.5-2.5 h of bench time) needs the special equipment. No food "
            "or drink in the lab; to drink, leave the lab and take a 'Lab break'.",
            start=s, end=e, deadline=e, required=e - s,
            mutex=["BODY", "LAB"], location=LOC_EE)
    t["LAB_BREAK"] = _task(
        "Lab break (sign out, storage room, sign back in)",
        "Needed before you can drink in the lab. Takes 3-5 minutes. Drink water "
        "while you do this.",
        required=random.randint(LAB_BREAK_MIN, LAB_BREAK_MAX),
        mutex=["BODY"], location=LOC_EE)

    # ---- Body needs ----
    t["SLEEP"] = _task(
        "Sleep / nap",
        "Restores energy. Needs 60+ unbroken minutes to clear a migraine. "
        "Dorm only. Up to 8 hours total today.",
        required=SLEEP_CAP_MINUTES, mutex=["BODY", "SLEEP"], location=LOC_DORM)
    t["EAT"] = _task(
        "Eat a meal",
        "20 minutes at North Dining Hall.",
        required=20, mutex=["BODY"], location=LOC_DINING)
    t["DRINK_WATER"] = _task(
        "Drink water",
        "Drink every 30 minutes or a migraine is guaranteed. "
        "Not allowed in the lab without a lab break.",
        required=DRINK_MINUTES, mutex=["SLEEP"])

    # ---- Medical (health complex) ----
    t["MED_PICKUP"] = _task(
        "Pick up migraine medication",
        "About 20 minutes at the Health & Biological Sciences Complex. "
        "Gives you several doses.",
        required=MED_PICKUP_MINUTES, mutex=["BODY"], location=LOC_HEALTH)
    t["EXCUSE_NOTE"] = _task(
        "Get an excuse note",
        "30 minutes at the Health & Biological Sciences Complex. Excuses "
        "OC225A, OC225B and the PH161 quiz, but only for classes that "
        "haven't ended yet. It is not retroactive.",
        required=EXCUSE_NOTE_MINUTES, mutex=["BODY"], location=LOC_HEALTH)
    # HIDDEN task: the player may forget it until the symptoms make it reappear.
    t["TAKE_MEDS"] = _task(
        "Take migraine medication",
        "Take a dose. Clears a migraine. Doses are due every 6 hours.",
        visible=False, required=1, mutex=["SLEEP"])

    # ---- Travel: two tasks; destination is picked via ASK() when activated ----
    # BODY mutex so you can't travel mid-class; can_cancel False so a trip can't be
    # abandoned halfway (handle_minute still guards against it).
    t["WALK"] = _task(
        "Walk somewhere",
        "Choose a destination when you start. 9-12 minutes, but ~20% of the time an "
        "elevator is out or a ramp is blocked and it takes 16. Raises migraine risk "
        "and costs extra energy.",
        required=10, can_cancel=False, mutex=["BODY", "TRAVEL"])
    t["PARATRANSIT"] = _task(
        "Take paratransit somewhere",
        "Choose a destination when you start. 6-8 minutes if on time (about 60% of "
        "the time), 18-21 if late. Occasionally the ride is cancelled and you have "
        "to walk. No extra migraine risk.",
        required=7, can_cancel=False, mutex=["BODY", "TRAVEL"])
    return t


def make_game_state_start():
    """Fresh GAME_STATE for a new game."""
    return {
        "current_minute": START_MINUTE,
        "minutes_slept_last_night": 540,
        "energy": 100,
        "energy_burn_rate": BASE_ENERGY_BURN,
        "water": 60,
        "water_burn_rate": BASE_WATER_BURN,
        "food": 40,
        "food_burn_rate": BASE_FOOD_BURN,
        "gpa": 3.2,
        "active_task_set": [],
        "awaiting_task_set": [],
        "location": LOC_DORM,
        "tasks": _build_initial_tasks(),
    }


def _fmt(minute):
    """Minutes-since-midnight -> '9:05 AM'."""
    h, m = divmod(int(minute), 60)
    suffix = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return "%d:%02d %s" % (h12, m, suffix)


GAME_STATE_START = make_game_state_start()


# =============================================================================
# SECTION 4: RUNTIME (per-game bookkeeping that doesn't fit in GAME_STATE)
# =============================================================================
_RT = None   # created on the first tick of every new game


def _new_runtime(now):
    return {
        "last_minute": None,
        "intro_done": False,
        "evaluated": set(),            # scheduled tasks already resolved
        # --- quizzes and attendance ---
        "ee244_quiz_done": False,
        "ph161_quiz_today": random.random() < PH161_QUIZ_PROB,
        "ph161_absent": False,
        "cs216_missed_context": False,
        "study_created": False,
        "study_resolved": False,
        "oc225a_attended_frac": 0.0,
        "oc225a_excused": False,
        "rehearsal_done": False,
        "note_minute": None,
        # --- lab ---
        "lab_required": random.randint(LAB_ASSIGNMENT_MIN, LAB_ASSIGNMENT_MAX),
        "lab_done": False,
        # --- water ---
        "water_last": now,
        "water_threshold": random.randint(WATER_WARN_MIN, WATER_WARN_MAX),
        "water_warned": False,
        # --- migraine ---
        "headache": False,
        "headache_minutes": 0,
        "headache_cause": None,
        # --- meds ---
        "meds_supply": MED_INITIAL_SUPPLY,
        "last_dose": MED_LAST_DOSE_BEFORE_START,
        "med_overdue": False,
        "med_overdue_announced": False,
        # --- misc ---
        "sleep_run": 0,                # consecutive minutes asleep
        "travel": None,                # dict while a trip is in progress
        "energy_warned": set(),
        "gpa_warned": False,
    }


# =============================================================================
# SECTION 5: SMALL HELPERS
# =============================================================================
def _gpa(state, delta, reason):
    """Change GPA by delta (+/-), clamp to [0, 4], and tell the player why."""
    state["gpa"] = round(max(0.0, min(4.0, state["gpa"] + delta)), 3)
    SAY("GPA %s%.2f (%s). GPA is now %.2f." %
        ("+" if delta >= 0 else "-", abs(delta), reason, state["gpa"]))


def _finish(state, tid, hide=False, reset=True):
    """Mark a task complete: removing from the active set is allowed for handle_minute()."""
    if tid in state["active_task_set"]:
        state["active_task_set"].remove(tid)
    t = state["tasks"][tid]
    t["highlight"] = False
    if reset:
        t["time_spent"] = 0
    if hide:
        t["visibility"] = False


def _lab_progress(state):
    return sum(state["tasks"][i]["time_spent"] for i in LAB_IDS)


def _has_note():
    return _RT["note_minute"] is not None


def _is_walking():
    tr = _RT["travel"]
    return tr is not None and tr["mode"] == "walk"


# =============================================================================
# SECTION 6: TRAVEL  (Part II: how the player changes location)
# =============================================================================
def _roll_walk():
    if random.random() < WALK_OBSTRUCTION_PROB:
        return WALK_OBSTRUCTED_MINUTES, True
    return random.randint(WALK_MIN, WALK_MAX), False


def _start_trip(state, tid, mode):
    """Ask where to, then roll the trip's duration (this is when the dice are cast)."""
    rt = _RT
    task = state["tasks"][tid]
    origin = state["location"]

    # ASK() blocks until the player answers. Offer every place except the current one.
    options = [name for name in LOCATION_NAMES.values() if name != origin]
    choice = ASK("Where do you want to go?", options + [TRAVEL_CANCEL_CHOICE])
    if choice not in options:                    # "Never mind" or an unexpected answer
        _finish(state, tid)
        return
    dest = choice

    effective_mode = mode
    if mode == "walk":
        total, blocked = _roll_walk()
        if blocked:
            SAY("An elevator is out / a ramp is blocked. The walk to %s will take %d minutes."
                % (dest, total))
        else:
            SAY("You set off on foot for %s. About %d minutes." % (dest, total))
    else:
        r = random.random()
        if r < PARA_CANCEL_PROB:
            effective_mode = "walk"       # ride cancelled -> walk, with walking costs
            total, blocked = _roll_walk()
            SAY("Paratransit cancelled your ride. You have to walk to %s: about %d minutes%s." %
                (dest, total, " (route blocked)" if blocked else ""))
        elif r < PARA_CANCEL_PROB + PARA_LATE_PROB:
            total = random.randint(PARA_LATE_MIN, PARA_LATE_MAX)
            SAY("Your paratransit van to %s is running late. Expect about %d minutes."
                % (dest, total))
        else:
            total = random.randint(PARA_ON_TIME_MIN, PARA_ON_TIME_MAX)
            SAY("Your paratransit van to %s arrived on time. About %d minutes." % (dest, total))

    task["requiredmins"] = total
    task["time_spent"] = 0
    rt["travel"] = {"tid": tid, "mode": effective_mode, "origin": origin,
                    "dest": dest, "total": total}
    state["location"] = LOC_TRANSIT


def _handle_travel(state, now):
    rt = _RT
    active = state["active_task_set"]
    tr = rt["travel"]

    if tr is None:
        for tid, mode in TRAVEL_TASKS.items():
            if tid in active:
                _start_trip(state, tid, mode)
                break
        return

    tid = tr["tid"]
    task = state["tasks"][tid]
    if tid not in active:
        # Trip abandoned (should be blocked by can_cancel=False, but be safe).
        state["location"] = tr["origin"]
        task["time_spent"] = 0
        rt["travel"] = None
        SAY("You turned back and are at %s again." % tr["origin"])
        return

    if task["time_spent"] >= tr["total"]:
        state["location"] = tr["dest"]
        _finish(state, tid)
        rt["travel"] = None
        SAY("You arrived at %s (%s)." % (tr["dest"], _fmt(now)))


# =============================================================================
# SECTION 7: LAB, QUIZ AND PRESENCE TRACKING
# =============================================================================
def _track_presence_and_quizzes(state, now):
    rt = _RT
    active = state["active_task_set"]

    # CS216: any minute missed in 10:03-10:13 means a make-up study hour later.
    if CS216_CONTEXT_START <= now <= CS216_CONTEXT_END and "CS216" not in active:
        rt["cs216_missed_context"] = True

    # PH161: pop quiz window = last 10 minutes; any absence is an absence.
    if PH161_QUIZ_START <= now < PH161_QUIZ_END and "PH161" not in active:
        rt["ph161_absent"] = True

    # EE244: the quiz happens at 9:05; you must be in class at that moment.
    if not rt["ee244_quiz_done"] and now >= EE244_QUIZ_MIN:
        rt["ee244_quiz_done"] = True
        if "EE244" in active:
            _gpa(state, GPA_EE244_QUIZ_BONUS, "you were there for the EE244 quiz")
        else:
            _gpa(state, -GPA_EE244_QUIZ_MISS_PENALTY, "you missed the EE244 quiz")

    # CS216 make-up study task appears once the context window has passed.
    if (rt["cs216_missed_context"] and not rt["study_created"]
            and now > CS216_CONTEXT_END):
        rt["study_created"] = True
        state["tasks"]["STUDY_CS216"] = _task(
            "Study CS216 (make-up hour)",
            "You missed the start of the lecture and can't follow it. Put in an "
            "hour of study (any place, any time) before the day ends.",
            start=CS216_END, deadline=END_OF_DAY, required=STUDY_MINUTES,
            mutex=["BODY"])
        SAY("You missed the start of CS216 and the rest made no sense. "
            "You will need to study for an hour later today.")


def _handle_lab(state, now):
    """Lab rules: no eating/drinking without a lab break; track assignment progress."""
    rt = _RT
    active = state["active_task_set"]
    tasks = state["tasks"]

    # Drink/eat is blocked while in a lab session (stepping out requires LAB_BREAK).
    in_lab = any(i in active for i in LAB_IDS)
    if in_lab:
        for tid in ("DRINK_WATER", "EAT"):
            if tid in active:
                active.remove(tid)
                tasks[tid]["time_spent"] = 0
                tasks["LAB_BREAK"]["highlight"] = True
                SAY("No food or drink in the lab. Leave the lab, take a 'Lab break' "
                    "(3-5 min to sign out and use the storage room), then drink.")

    # Assignment completes once enough bench time has been logged.
    if not rt["lab_done"] and _lab_progress(state) >= rt["lab_required"]:
        rt["lab_done"] = True
        for tid in LAB_IDS:
            rt["evaluated"].add(tid)
            _finish(state, tid, hide=True, reset=False)
        _gpa(state, GPA_LAB_COMPLETE_BONUS, "you finished the EE222 lab assignment")


# =============================================================================
# SECTION 8: ORDINARY TASKS (drink, eat, sleep, meds, errands, rehearsal)
# =============================================================================
def _handle_simple_tasks(state, now):
    rt = _RT
    tasks = state["tasks"]
    active = state["active_task_set"]

    # ---- DRINK_WATER: restores water and resets the 30-minute clock ----
    if "DRINK_WATER" in active:
        state["water"] += WATER_PER_DRINK_MIN
        rt["water_last"] = now
        rt["water_warned"] = False
        rt["water_threshold"] = random.randint(WATER_WARN_MIN, WATER_WARN_MAX)
        d = tasks["DRINK_WATER"]
        d["highlight"] = False
        if d["time_spent"] >= d["requiredmins"]:
            _finish(state, "DRINK_WATER")

    # ---- EAT: restores food (and a little energy) per minute ----
    if "EAT" in active:
        state["food"] += FOOD_PER_EAT_MIN
        state["energy"] += ENERGY_PER_EAT_MIN
        e = tasks["EAT"]
        if e["time_spent"] >= e["requiredmins"]:
            _finish(state, "EAT")
            SAY("You finished your meal.")

    # ---- SLEEP: energy back, migraine cleared after a long enough stretch ----
    if "SLEEP" in active:
        rt["sleep_run"] += 1
        state["energy"] += SLEEP_ENERGY_GAIN_PER_MIN
        rt["water_last"] += 1                      # water clock pauses while asleep
        if rt["headache"] and rt["sleep_run"] >= SLEEP_MIN_TO_CLEAR_HEADACHE:
            _clear_headache(state, "sleeping it off")
        if tasks["SLEEP"]["time_spent"] >= tasks["SLEEP"]["requiredmins"]:
            _finish(state, "SLEEP", hide=True, reset=False)
            SAY("You've had all the sleep you can fit in today.")
    else:
        rt["sleep_run"] = 0

    # ---- TAKE_MEDS (hidden task) ----
    if "TAKE_MEDS" in active:
        if rt["meds_supply"] <= 0:
            active.remove("TAKE_MEDS")
            tasks["TAKE_MEDS"]["time_spent"] = 0
            SAY("You're out of medication. Pick more up at the Health & Biological "
                "Sciences Complex.")
        elif tasks["TAKE_MEDS"]["time_spent"] >= tasks["TAKE_MEDS"]["requiredmins"]:
            rt["meds_supply"] -= 1
            rt["last_dose"] = now
            rt["med_overdue"] = False
            rt["med_overdue_announced"] = False
            _finish(state, "TAKE_MEDS", hide=True)
            SAY("You took your medication (%d doses left)." % rt["meds_supply"])
            if rt["headache"]:
                _clear_headache(state, "medication")

    # ---- MED_PICKUP ----
    if "MED_PICKUP" in active and tasks["MED_PICKUP"]["time_spent"] >= MED_PICKUP_MINUTES:
        rt["meds_supply"] += MED_DOSES_PER_PICKUP
        _finish(state, "MED_PICKUP")
        SAY("You picked up your medication (%d doses on hand)." % rt["meds_supply"])

    # ---- EXCUSE_NOTE: covers classes that haven't ended yet ----
    if "EXCUSE_NOTE" in active and tasks["EXCUSE_NOTE"]["time_spent"] >= EXCUSE_NOTE_MINUTES:
        rt["note_minute"] = now
        _finish(state, "EXCUSE_NOTE", hide=True)
        SAY("You have an excuse note (%s). It covers OC225A, OC225B and the PH161 "
            "quiz if they haven't finished yet." % _fmt(now))

    # ---- REHEARSE_OC225B: progress accumulates across sessions ----
    if ("REHEARSE_OC225B" in active and not rt["rehearsal_done"]
            and tasks["REHEARSE_OC225B"]["time_spent"] >= REHEARSAL_MINUTES):
        rt["rehearsal_done"] = True
        _finish(state, "REHEARSE_OC225B", hide=True, reset=False)
        SAY("Rehearsal done. You feel ready for the presentation.")

    # ---- LAB_BREAK: finishing it re-rolls the next break's length ----
    if "LAB_BREAK" in active:
        tasks["LAB_BREAK"]["highlight"] = False
        if tasks["LAB_BREAK"]["time_spent"] >= tasks["LAB_BREAK"]["requiredmins"]:
            _finish(state, "LAB_BREAK")
            tasks["LAB_BREAK"]["requiredmins"] = random.randint(LAB_BREAK_MIN, LAB_BREAK_MAX)
            SAY("Lab break done. You can go back into the lab.")

    # ---- STUDY_CS216 (created dynamically) ----
    if "STUDY_CS216" in tasks and not rt["study_resolved"]:
        s = tasks["STUDY_CS216"]
        if s["time_spent"] >= STUDY_MINUTES:
            rt["study_resolved"] = True
            _finish(state, "STUDY_CS216", hide=True, reset=False)
            _gpa(state, GPA_STUDY_DONE_BONUS, "you caught up on CS216")


# =============================================================================
# SECTION 9: DEADLINE RESOLUTION (classes, lab, study)
# =============================================================================
def _attended_fraction(task):
    """Fraction of a class period attended, forgiving ATTENDANCE_GRACE_MIN."""
    req = task["requiredmins"]
    missed = max(0, req - task["time_spent"] - ATTENDANCE_GRACE_MIN)
    return 1.0 - missed / float(req)


def _resolve_oc225a(state):
    rt = _RT
    frac = _attended_fraction(state["tasks"]["OC225A"])
    excused = _has_note()
    rt["oc225a_excused"] = excused
    rt["oc225a_attended_frac"] = frac
    if frac >= 1.0:
        _gpa(state, GPA_OC225A_FULL_ATTENDANCE_BONUS, "you stayed for all of OC225A")
    elif excused:
        SAY("You missed part of OC225A, but your excuse note covers the attendance penalty.")
    else:
        _gpa(state, -GPA_OC225A_SKIP_PENALTY * (1.0 - frac),
             "you skipped %d%% of OC225A" % round((1.0 - frac) * 100))
    if frac < 1.0:
        SAY("Because you missed part of the feedback session, your presentation will suffer.")


def _resolve_oc225b(state):
    rt = _RT
    task = state["tasks"]["OC225B"]
    frac = _attended_fraction(task)
    excused = _has_note()

    # Attendance
    if frac >= 1.0:
        _gpa(state, GPA_OC225B_FULL_ATTENDANCE_BONUS, "you stayed for all of OC225B")
    elif excused:
        SAY("You missed part of OC225B, but your excuse note covers it.")
    else:
        _gpa(state, -GPA_OC225B_SKIP_PENALTY * (1.0 - frac),
             "you skipped %d%% of OC225B" % round((1.0 - frac) * 100))

    # Presentation
    if frac < PRESENTATION_NO_SHOW_FRACTION:
        if excused:
            SAY("Your presentation is rescheduled thanks to your excuse note.")
        else:
            _gpa(state, -GPA_PRESENTATION_MAX_PENALTY,
                 "you missed your presentation")
        return
    practice = min(1.0, state["tasks"]["REHEARSE_OC225B"]["time_spent"] / float(REHEARSAL_MINUTES))
    feedback = rt["oc225a_attended_frac"]
    if rt["oc225a_excused"] and EXCUSED_ABSENCE_COUNTS_AS_FEEDBACK:
        feedback = 1.0
    quality = (PRESENTATION_PRACTICE_WEIGHT * practice
               + PRESENTATION_FEEDBACK_WEIGHT * feedback)
    delta = -GPA_PRESENTATION_MAX_PENALTY + quality * (
        GPA_PRESENTATION_MAX_PENALTY + GPA_PRESENTATION_MAX_BONUS)
    _gpa(state, delta, "presentation: %d%% rehearsed, %d%% of feedback session" %
         (round(practice * 100), round(feedback * 100)))


def _resolve_ph161(state):
    rt = _RT
    if not rt["ph161_quiz_today"]:
        return
    SAY("Your professor ran a pop quiz in the last 10 minutes of PH161.")
    if not rt["ph161_absent"]:
        _gpa(state, GPA_PH161_QUIZ_BONUS, "you aced the PH161 pop quiz")
    elif _has_note():
        SAY("You were out during the quiz, but your excuse note exempts you.")
    else:
        _gpa(state, -GPA_PH161_QUIZ_ZERO_PENALTY,
             "you were out during the PH161 pop quiz and got a zero")


def _resolve_lab_final(state):
    rt = _RT
    if rt["lab_done"]:
        return
    progress = _lab_progress(state)
    remaining = max(0.0, 1.0 - progress / float(rt["lab_required"]))
    SAY("The last lab session has ended. You logged %d minutes at the bench in total." % progress)
    _gpa(state, -GPA_LAB_INCOMPLETE_PENALTY * remaining,
         "the EE222 lab assignment isn't finished")


def _evaluate_deadlines(state, now):
    rt = _RT
    tasks = state["tasks"]

    resolvers = {"OC225A": _resolve_oc225a, "OC225B": _resolve_oc225b,
                 "PH161": _resolve_ph161}
    for tid in CLASS_IDS:
        if tid in rt["evaluated"] or now < tasks[tid]["deadline"]:
            continue
        rt["evaluated"].add(tid)
        if tid in resolvers:
            resolvers[tid](state)
        _finish(state, tid, hide=True, reset=False)

    last_lab = LAB_IDS[-1]
    for tid in LAB_IDS:
        if tid in rt["evaluated"] or now < tasks[tid]["deadline"]:
            continue
        rt["evaluated"].add(tid)
        _finish(state, tid, hide=True, reset=False)
        if tid == last_lab:
            _resolve_lab_final(state)
        elif not rt["lab_done"]:
            SAY("Lab session over. %d minutes logged so far." % _lab_progress(state))

    # Study deadline: end of day
    if ("STUDY_CS216" in tasks and not rt["study_resolved"]
            and now >= tasks["STUDY_CS216"]["deadline"]):
        rt["study_resolved"] = True
        _finish(state, "STUDY_CS216", hide=True, reset=False)
        _gpa(state, -GPA_STUDY_MISSED_PENALTY, "you never made up the CS216 study hour")


# =============================================================================
# SECTION 10: WATER CLOCK, MEDICATION SCHEDULE, MIGRAINES
# =============================================================================
def _update_water_clock(state, now):
    rt = _RT
    if "SLEEP" in state["active_task_set"]:
        return
    gap = now - rt["water_last"]
    if gap >= rt["water_threshold"]:
        d = state["tasks"]["DRINK_WATER"]
        d["visibility"] = True
        d["highlight"] = True
        if not rt["water_warned"]:
            rt["water_warned"] = True
            SAY("It's been %d minutes since you last drank water. Drink within the next "
                "%d minutes or you'll get a migraine." % (gap, max(1, WATER_DEADLINE - gap)))


def _update_medication_schedule(state, now):
    rt = _RT
    t = state["tasks"]["TAKE_MEDS"]
    due = rt["last_dose"] + MED_INTERVAL
    rt["med_overdue"] = now >= due + MED_GRACE_MIN
    if rt["med_overdue"]:
        t["visibility"] = True
        t["highlight"] = True
        if not rt["med_overdue_announced"]:
            rt["med_overdue_announced"] = True
            SAY("You feel nauseous and light-sensitive. You were supposed to take your "
                "medication at %s." % _fmt(due))


def _start_headache(state, now, cause):
    rt = _RT
    rt["headache"] = True
    rt["headache_minutes"] = 0
    rt["headache_cause"] = cause
    if cause == "dehydration":
        SAY("A migraine hits. You went too long without water.")
    else:
        SAY("A migraine is starting. Energy will drain faster the longer it lasts.")
    # Rescue dose becomes visible if enough time has passed since the last one.
    if now - rt["last_dose"] >= MED_MIN_INTERVAL:
        state["tasks"]["TAKE_MEDS"]["visibility"] = True
        if rt["meds_supply"] <= 0:
            SAY("You have no medication on hand. The Health & Biological Sciences "
                "Complex has more. Sleeping 60+ minutes also works.")
        else:
            SAY("Medication or an hour of sleep will clear it.")
    else:
        SAY("You took medication recently, so another dose isn't safe yet. Sleep helps.")


def _clear_headache(state, how):
    rt = _RT
    rt["headache"] = False
    rt["headache_minutes"] = 0
    rt["headache_cause"] = None
    if not rt["med_overdue"]:
        state["tasks"]["TAKE_MEDS"]["visibility"] = False
        state["tasks"]["TAKE_MEDS"]["highlight"] = False
    SAY("Your migraine has cleared (%s)." % how)


def _update_headache(state, now):
    rt = _RT
    sleeping = "SLEEP" in state["active_task_set"]
    if rt["headache"]:
        rt["headache_minutes"] += 1
        if rt["headache_minutes"] % HEADACHE_REMINDER_EVERY == 0:
            SAY("Your migraine has lasted %d minutes. It's draining your energy "
                "much faster." % rt["headache_minutes"])
        return
    if sleeping:
        return                                      # no new migraines while asleep

    # Guaranteed: no water for WATER_DEADLINE minutes.
    if now - rt["water_last"] >= WATER_DEADLINE:
        _start_headache(state, now, "dehydration")
        return

    # Random onset: baseline x walking x missed-medication multipliers.
    p = BASE_HEADACHE_PROB_PER_MIN
    if _is_walking():
        p *= WALK_HEADACHE_MULT
    if rt["med_overdue"]:
        p *= MED_MISSED_HEADACHE_MULT
    if random.random() < p:
        _start_headache(state, now, "random")


# =============================================================================
# SECTION 11: BURN RATES, HIGHLIGHTS, CLAMPS
# =============================================================================
def _update_burn_rates(state, now):
    rt = _RT
    if "SLEEP" in state["active_task_set"]:
        state["energy_burn_rate"] = 0.0             # energy is being restored instead
        state["water_burn_rate"] = BASE_WATER_BURN * SLEEP_BURN_MULT
        state["food_burn_rate"] = BASE_FOOD_BURN * SLEEP_BURN_MULT
        return

    mult = 1.0
    if rt["headache"]:
        mult *= min(HEADACHE_MAX_MULT, 1.0 + HEADACHE_ESCALATION_PER_MIN * rt["headache_minutes"])
    if state["food"] <= 0:
        mult *= HUNGER_EMPTY_ENERGY_MULT
    elif state["food"] < FOOD_LOW_THRESHOLD:
        mult *= HUNGER_LOW_ENERGY_MULT
    if state["water"] <= 0:
        mult *= DEHYDRATION_ENERGY_MULT

    rate = BASE_ENERGY_BURN * mult
    if _is_walking():
        rate += WALK_EXTRA_ENERGY_BURN
    state["energy_burn_rate"] = rate
    state["water_burn_rate"] = BASE_WATER_BURN
    state["food_burn_rate"] = BASE_FOOD_BURN


def _update_highlights(state, now):
    rt = _RT
    tasks = state["tasks"]
    active = state["active_task_set"]
    # Scheduled commitments blink shortly before they start and until they end.
    for tid in SCHEDULED_IDS:
        if tid in rt["evaluated"]:
            continue
        t = tasks[tid]
        t["highlight"] = (tid not in active
                          and t["timeblockstart"] - HIGHLIGHT_LEAD_MIN <= now < t["timeblockend"])
    # Rehearsal reminder before OC225B.
    r = tasks["REHEARSE_OC225B"]
    if not rt["rehearsal_done"]:
        r["highlight"] = (now >= OC225B_START - 120 and now < OC225B_START
                          and "REHEARSE_OC225B" not in active)
    # Make-up study reminder as the day winds down.
    if "STUDY_CS216" in tasks and not rt["study_resolved"]:
        s = tasks["STUDY_CS216"]
        s["highlight"] = (now >= s["deadline"] - STUDY_HIGHLIGHT_LEAD
                          and "STUDY_CS216" not in active)


def _clamp_and_warn(state):
    rt = _RT
    state["water"] = max(0.0, min(100.0, state["water"]))
    state["food"] = max(0.0, min(100.0, state["food"]))
    state["energy"] = min(100.0, state["energy"])
    for level in ENERGY_WARN_LEVELS:
        if state["energy"] < level and level not in rt["energy_warned"]:
            rt["energy_warned"].add(level)
            SAY("Your energy is down to %d. You are at risk of fainting." % round(state["energy"]))
        elif state["energy"] >= level + 10:
            rt["energy_warned"].discard(level)
    if state["gpa"] < GPA_SCHOLARSHIP_WARNING and not rt["gpa_warned"]:
        rt["gpa_warned"] = True
        SAY("Your GPA is dangerously close to the 2.5 scholarship cutoff.")


# =============================================================================
# SECTION 12: THE TICK HANDLER
# =============================================================================
def handle_minute(current_state):
    """Called by the engine once per in-game minute. Returns the updated GAME_STATE.

    Never touches current_minute, never adds to active_task_set, and never
    modifies awaiting_task_set. It may remove tasks from the active set.
    """
    global _RT
    state = current_state
    now = state["current_minute"]

    # (Re)initialize bookkeeping at the start of every new game.
    if _RT is None or _RT["last_minute"] is None or now < _RT["last_minute"]:
        _RT = _new_runtime(now)
    _RT["last_minute"] = now

    if not _RT["intro_done"]:
        _RT["intro_done"] = True
        SAY("Good morning. You slept 9 hours. EE244 starts at 9:00, and you have a "
            "full day of classes and lab. Keep an eye on your water and your head.")

    _handle_travel(state, now)                  # location changes
    _track_presence_and_quizzes(state, now)     # quizzes, CS216 context, study task
    _handle_lab(state, now)                     # no-drink rule, lab completion
    _handle_simple_tasks(state, now)            # drink/eat/sleep/meds/errands
    _evaluate_deadlines(state, now)             # class/lab/study outcomes
    _update_water_clock(state, now)
    _update_medication_schedule(state, now)
    _update_headache(state, now)
    _update_burn_rates(state, now)
    _update_highlights(state, now)
    _clamp_and_warn(state)
    return state


# =============================================================================
# SECTION 13: MOCK ENGINE + SMOKE TEST
# =============================================================================
def _in_block(t, minute):
    """Mock-engine helper: either bound of a time block may be None (open-ended)."""
    return ((t["timeblockstart"] is None or t["timeblockstart"] <= minute) and
            (t["timeblockend"] is None or minute < t["timeblockend"]))


def _smoke_test(seed, verbose=False):
    """Run a full day with a random-ish player and a mock engine."""
    global _RT
    random.seed(seed)
    _RT = None
    messages = []
    globals()["SAY"] = lambda m: messages.append(m)
    state = make_game_state_start()

    end_reason = "survived"
    for minute in range(START_MINUTE, 1440):
        state["current_minute"] = minute
        state = handle_minute(state)

        # mock engine: increments, burns, enforces timeblock/location/mutex
        for tid in list(state["active_task_set"]):
            state["tasks"][tid]["time_spent"] += 1
        state["energy"] -= state["energy_burn_rate"]
        state["water"] -= state["water_burn_rate"]
        state["food"] -= state["food_burn_rate"]
        if state["energy"] <= 0:
            end_reason = "fainted at %s" % _fmt(minute)
            break
        if state["gpa"] < 2.5:
            end_reason = "lost scholarship at %s" % _fmt(minute)
            break

        for tid in list(state["active_task_set"]):
            t = state["tasks"][tid]
            if t["location"] is not None and t["location"] != state["location"]:
                state["active_task_set"].remove(tid)
            elif not _in_block(t, minute):
                state["active_task_set"].remove(tid)

        # random-ish player
        if random.random() < 0.3:
            choices = [k for k, v in state["tasks"].items()
                       if v["visibility"] and k not in state["active_task_set"]]
            if choices:
                pick = random.choice(choices)
                t = state["tasks"][pick]
                ok = (t["location"] in (None, state["location"]) and
                      _in_block(t, minute))
                groups = set()
                for a in state["active_task_set"]:
                    groups.update(state["tasks"][a]["mutex_groups"])
                if ok and not groups.intersection(t["mutex_groups"]):
                    state["active_task_set"].append(pick)
        if random.random() < 0.02 and state["active_task_set"]:
            tid = random.choice(state["active_task_set"])
            if state["tasks"][tid]["can_cancel"]:
                state["active_task_set"].remove(tid)

    if verbose:
        print("\n".join(messages))
    return end_reason, state["gpa"], round(state["energy"], 1), len(messages)


if __name__ == "__main__":
    for s in range(30):
        print(s, _smoke_test(s))