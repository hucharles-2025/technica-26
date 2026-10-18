import time
import remote_comms as ios
from time_manipulations import *
import json
import compiled_rules 
from pprint import pprint
import keyboard
import os

GAME_REAL_LIFE_MINUTES = 48
GAME_MINS_PER_REAL_MIN = int(1440 / GAME_REAL_LIFE_MINUTES)
REAL_SECS_BETWEEN_GAME_MINS = 1 / GAME_MINS_PER_REAL_MIN * 60
DEBUG_MODE = True

GAME_STATE = compiled_rules.GAME_STATE_START

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
    for active_task_name in GAME_STATE["active_task_set"]:
        GAME_STATE["tasks"][active_task_name]["time_spent"] += 1

    # 3. Run all custom logic then tx data
    GAME_STATE["current_minute"] += 1
    compiled_rules.handle_minute(GAME_STATE)
    #ios.send_message("SEND_STATE", json.dumps(GAME_STATE))
    time.sleep(REAL_SECS_BETWEEN_GAME_MINS)

    # 4. Check if we meet any stop conds
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

    # 5a. Define method for adding to the active task set 
    # without violating mutex group rules and respecting
    # timeblockstart, timeblockend
    def lists_share_elems(list1, list2):
        return (not set(list1).isdisjoint(list2))
    def lists_share_mutex_groups(taskid1, taskid2):
        return lists_share_elems(
            GAME_STATE["tasks"][taskid1]["mutex_groups"],
            GAME_STATE["tasks"][taskid2]["mutex_groups"]
        )
    def add_to_task_set(taskid):
        tba_task_data = GAME_STATE["tasks"][taskid]

        # 1. If this task is already in the active set, reject
        if (taskid in GAME_STATE["active_task_set"]):
            return 1, "This task is already underway." 

        # 2. Check time: if it's too late, reject. Too early, place it in queue. Just right, 
        # add it to active if it doesn't violate any mutexes
        curr_time = GAME_STATE["current_minute"]
        if (tba_task_data["timeblockstart"] is not None and curr_time > tba_task_data["timeblockend"]):
            return 3, "It is too late to do this task."
        elif (tba_task_data["timeblockend"] is not None and curr_time < tba_task_data["timeblockstart"]):
            # Put it on the queue.
            if taskid not in GAME_STATE["awaiting_task_set"]:
                GAME_STATE["awaiting_task_set"].append(taskid)
                return 4, "It is too early for this task, but it has been saved for later."
            else:
                return 5, "This task has already been queued for later."
        else:
            # Check mutex groups on the active set
            for k in GAME_STATE["active_task_set"]:
                if lists_share_mutex_groups(taskid, k):
                    return 2, f"Can't do this task at the same time as {GAME_STATE['tasks'][k]['shortdesc']}"
            
            # Add it to the current tasks
            GAME_STATE["active_task_set"].append(taskid)
            return 0, "OK"

    # 5b. If anything is in the queue, try to slide it in now.
    # If it's still too early then nothing will happen, otherwise
    # it will work.
    awaiting_task_set_rewrite = []
    for taskid in GAME_STATE["awaiting_task_set"]:
        retcode, msg = add_to_task_set(taskid)
        if retcode in [4,5]: 
            # ONLY keep it on queue if it's still too early -- if there's 
            # a mutex violation, it's too late somehow, etc., then remove it
            awaiting_task_set_rewrite.append(taskid)
        else:
            input(msg)
    GAME_STATE["awaiting_task_set"] = awaiting_task_set_rewrite
        
    # 6. Draw the command line testing utility, if enabled
    if DEBUG_MODE:
        os.system("cls")
        print(f"TIME: {get_time_string(GAME_STATE['current_minute'])}\n")
        print(f"ENERGY: {GAME_STATE['energy']}")
        print(f"WATER: {GAME_STATE['water']}")
        print(f"FOOD: {GAME_STATE['food']}\n")
        print(f"ENERGY BURN RATE: {GAME_STATE['energy_burn_rate']}")
        print(f"WATER BURN RATE: {GAME_STATE['water_burn_rate']}")
        print(f"FOOD BURN RATE: {GAME_STATE['food_burn_rate']}\n")
        print(f"GPA: {GAME_STATE['gpa']}\n")
        print("TASKS:")
        for v in GAME_STATE["tasks"].values():
            if not v["visibility"]: 
                continue
            print(f"  * {v['shortdesc']}: {v['longdesc']} ")
        print(f"\n(SELECTED TASKS: {GAME_STATE['active_task_set']})")
        print(f"\n(AWAITING TASKS: {GAME_STATE['awaiting_task_set']})")

        