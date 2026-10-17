import time
import remote_comms as ios
from time_manipulations import *

GAME_REAL_LIFE_MINUTES = 24
GAME_MINS_PER_REAL_MIN = int(1440 / GAME_REAL_LIFE_MINUTES)
REAL_SECS_BETWEEN_GAME_MINS = 1 / GAME_MINS_PER_REAL_MIN * 60
AI_ASSESS_PERIOD = 60 # in-game minutes
MANUALLY_INIT_AI_ASSESS = False

GAME_STATE = {
    "current_minute": get_minutes(7, 0),
    "minutes_slept_last_night": 425,
    "energy": 100,
    "energy_burn_rate": 0.01, # per minute 
    "water": 60, 
    "water_burn_rate": 0.01, # per minute
    "food": 40, 
    "food_burn_rate": 0.01,
    "gpa": 3.2, 
    "active_task": None,
    "tasks": {

    }
    # Each task dict entry is referred to by a unique alphanumeric ID. Under it should be a dict
    # with a short description (shortdesc), a long description (longdesc), a visibility marker (visible) 
    # a marker for time spent (time_spent), whether the task can be cancelled midway (can_cancel), 
    # and how many minutes the task takes (requiredmins). Optional:
    #   * (taskinitcmd) A command sent to the render engine when the task is initiated, 
    #        mostly used to display
    #        interactive tasks which require the user to play additional mind/dexterity games while
    #        under the influence of pain, visual impairment, etc. If set to None then no command
    #        is sent to the render engine when the task is started.
    #   * (timeblockstart, timeblockend) A tuple containing the minute times 
    #        during which that task must be done. If set to None, then the task can be started/worked on
    #        at any time. This is mostly used for tasks like going to class, going to pharmacy to 
    #        refill meds, etc. where there are certain hours where you can do it.
    #   * (deadline) The minute timestamp where if you cross it, the AI will take note and start
    #        applying consequences. 
}

# Handle all one time init steps
if not ios.init_comms():
    # Accept cx to game client, abort on failure
    print("[Main] Failed to init comms, aborting.")
    exit()

while True: 
    # Handle the passing of one 
    # minute using deterministic rules:
    
    # 1. Consume a certain amount of food, water and energy according to the burn rate
    # set by the AI
    GAME_STATE["energy"] -= GAME_STATE["energy_burn_rate"]
    GAME_STATE["water"] -= GAME_STATE["water_burn_rate"]
    GAME_STATE["food"] -= GAME_STATE["food_burn_rate"]

    # 2. For whatever task that the user has selected as active, give them one more minute
    # of completion time on that task.
    active_task_name = GAME_STATE["active_task"]
    if active_task_name in GAME_STATE["tasks"]:
        GAME_STATE["tasks"][active_task_name]["time_spent"] += 1

    # 3. Check if we meet any of the conditions for a check up by the AI game master
    if GAME_STATE["current_minute"] % AI_ASSESS_PERIOD == 0:
        pass # Carry out a routine check of stats
    elif active_task_name in GAME_STATE["tasks"]:
        current_task_data = GAME_STATE["tasks"][active_task_name]
        if current_task_data["time_spent"] >= current_task_data["requiredmins"]:
            pass # Carry out an AI assessment of task performance and positive/negative consequences


    # 4. Transmit current pretend time to client and add one minute to game time
    GAME_STATE["current_minute"] += 1
    ios.send_message("SET_PRETEND_TIME", get_time_string(GAME_STATE["current_minute"]))
    time.sleep(REAL_SECS_BETWEEN_GAME_MINS)

    # 5. Check if we meet any stop conds
    if (GAME_STATE["energy"] <= 0):
        ios.send_message("STOP_COND", "ENERGY")
        break
    elif (GAME_STATE["water"] <= 0):
        ios.send_message("STOP_COND", "WATER")
        break
    elif (GAME_STATE["food"] <= 0):
        ios.send_message("STOP_COND", "FOOD")
        break
    elif (GAME_STATE["gpa"] < 2.5):
        ios.send_message("STOP_COND", "GPA")
        break