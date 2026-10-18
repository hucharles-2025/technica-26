import pygame
import pygame_gui
import copy
from pygame_gui.elements import (
    UIButton,
    UILabel,
    UIPanel,
    UIProgressBar,
    UISelectionList,
)
import time
from time_manipulations import *
import json
import compiled_rules 
from pprint import pprint
import keyboard
import os
import dialogs

pygame.init()

CHARACTER_NUMBER = dialogs.ask("Choose a character.", ["1", "2", "3", "4"])

# --------------------------------------------------------------------------
# Layout constants
# --------------------------------------------------------------------------
BACKDROP_W, BACKDROP_H = int(1920/2), int(1080/2.5)
CONTROL_H = 260
WINDOW_W, WINDOW_H = BACKDROP_W, BACKDROP_H + CONTROL_H

PAD = 5
LABEL_H = 24
BUTTON_H = 36
COLUMN_COUNT = 4

FPS = 60

FONT = pygame.font.SysFont("Calibri", 30) 

LOC_DORM = "Dorm"
LOC_EE = "Electrical Engineering Building"
LOC_CS = "Computer Science Building"
LOC_ARTS = "Arts Building"
LOC_PHYS = "Physics Building"
LOC_HEALTH = "Health & Biological Sciences Complex"
LOC_DINING = "North Dining Hall"
LOC_PARATRANSIT = "In Paratransit Van"
LOC_WALKING = "Walking Outside"

IMAGE_FILENAMES = {
    LOC_DORM: "dorm_room_bg.png",
    LOC_EE: "classroom_bg.png",
    LOC_CS: "classroom_bg.png",
    LOC_ARTS: "classroom_bg.png",
    LOC_PHYS: "classroom_bg.png",
    LOC_HEALTH: "healthcenter_bg.png",
    LOC_DINING: "jw_bg.png",
    LOC_PARATRANSIT: "transit_bg.png",
    LOC_WALKING: "walking_bg.png"
}

ui = None

# --------------------------------------------------------------------------
# GLOBAL GAME STATE SETUP AND METHODS
# --------------------------------------------------------------------------
GAME_STATE = copy.deepcopy(compiled_rules.GAME_STATE_START)
GAME_STATE["energy"]=100
GAME_STATE["gpa"]=4.0
GAME_STATE["current_minute"]=21*60
# Helpers
GAME_OVER_REASON = None
GPA_FAIL_THRESHOLD = 2.0
END_TIME = 21* 60

def check_game_over():
    global GAME_OVER_REASON
    if GAME_OVER_REASON is not None:
        return
    GAME_STATE["energy"] = max(0, GAME_STATE["energy"])

    if GAME_STATE["energy"] <= 0:
        GAME_OVER_REASON = "fainted"
    elif GAME_STATE["gpa"] < GPA_FAIL_THRESHOLD:
        GAME_OVER_REASON = "flunked"
    elif GAME_STATE["current_minute"] >= END_TIME:
        GAME_OVER_REASON = "success"



def lists_share_elems(list1, list2):
        return (not set(list1).isdisjoint(list2))
def lists_share_mutex_groups(taskid1, taskid2):
    return lists_share_elems(
        GAME_STATE["tasks"][taskid1]["mutex_groups"],
        GAME_STATE["tasks"][taskid2]["mutex_groups"]
    )
# Activate / queue a task on a state object
def add_to_task_set(state, taskid):
    tba_task_data = state["tasks"][taskid]

    # 1. If this task is already in the active set, reject
    if (taskid in state["active_task_set"]):
        return 1, "You're already working on this item!" 

    # 2. Check time: if it's too late, reject. Too early, place it in queue. Just right, 
    # add it to active if it doesn't violate any mutexes
    print(f"Current location: {state['location']}, needed location: {tba_task_data['location']}")
    curr_time = state["current_minute"]
    if (tba_task_data["timeblockend"] is not None and curr_time > tba_task_data["timeblockend"]):
        return 3, "The time window for doing this has already passed."
    elif tba_task_data["location"] is not None and state["location"] != tba_task_data["location"]:
        # If we're not in the right location, have it wait until we are
        if taskid not in state["awaiting_task_set"]:
            state["awaiting_task_set"].append(taskid)
            return 6, f"You are not in the correct location for this task. You need to be at {tba_task_data['location']}."
        else:
            return 5, "This task is already on your to-do list for later."
    elif (tba_task_data["timeblockstart"] is not None and curr_time < tba_task_data["timeblockstart"]):
        # Put it on the queue.
        if taskid not in state["awaiting_task_set"]:
            state["awaiting_task_set"].append(taskid)
            return 4, "It is too early to do this, but it is on your to-do list later."
        else:
            return 5, "This task is already on your to-do list for later."
    else:            
        # Check mutex groups on the active set
        for k in state["active_task_set"]:
            if lists_share_mutex_groups(taskid, k):
                return 2, f"You can't do this at the same time as: {state['tasks'][k]['shortdesc']}"

        # Add it to the current tasks
        state["active_task_set"].append(taskid)
        return 0, "OK"

# Cancel a task on a state object
def cancel_task(state, taskid):
    # 1. See if the task is active, queued or not in either relevant set
    target_list = None
    active = False
    if (taskid in state["active_task_set"]):
        target_list = state["active_task_set"]
        active = True
    elif (taskid in state["awaiting_task_set"]):
        target_list = state["awaiting_task_set"]
    else:
        return 1, "This task is not actively being done nor is it in the queue."

    # 2. Check to see if this is the type of task that can be interrupted after 
    # it has been entered into the active zone
    if active and not state["tasks"][taskid]["can_cancel"]:
        return 2, "You cannot stop this task once you've started."
    else:
        target_list.remove(taskid)
        return 0,f"OK (removal was from active task set? {active})"

# --------------------------------------------------------------------------
# UI
# --------------------------------------------------------------------------
class Banner:
    """Flashes a message over the backdrop, holds it, then fades it out (frame-based).
    Long messages are word-wrapped so the banner always stays on screen."""
    def __init__(self, font_size: int = 20, y: int = BACKDROP_H // 5,
                 max_width_frac: float = 0.8):
        self.font = pygame.font.Font(None, font_size)
        self.y = y
        # Widest the *text* may be; the box adds padding on top of this
        self.pad_x, self.pad_y = 20, 10
        self.max_text_w = int(BACKDROP_W * max_width_frac) - 2 * self.pad_x
        self.surface = None
        self.total_frames = 0
        self.hold_frames = 0
        self.frames_left = 0

    def _wrap(self, text: str) -> list:
        """Split text into lines no wider than max_text_w, honoring existing newlines."""
        lines = []
        for paragraph in text.split("\n"):
            current = ""
            for word in paragraph.split(" "):
                candidate = word if not current else f"{current} {word}"
                if self.font.size(candidate)[0] <= self.max_text_w:
                    current = candidate
                    continue

                # Candidate is too wide: flush the current line first
                if current:
                    lines.append(current)
                    current = ""

                # A single word wider than the banner gets broken by character
                while self.font.size(word)[0] > self.max_text_w and len(word) > 1:
                    cut = len(word) - 1
                    while cut > 1 and self.font.size(word[:cut])[0] > self.max_text_w:
                        cut -= 1
                    lines.append(word[:cut])
                    word = word[cut:]
                current = word
            lines.append(current)
        return lines

    def show(self, text: str):
        frames = int(len(text) * 1.5)
        hold = frames - 5

        """Display `text` for `frames` frames total; the last (frames - hold) are the fade."""
        lines = self._wrap(text)
        line_surfs = [self.font.render(line, True, (255, 255, 255)) for line in lines]
        line_h = self.font.get_linesize()

        text_w = max((s.get_width() for s in line_surfs), default=0)
        text_h = line_h * len(line_surfs)

        surf = pygame.Surface(
            (text_w + 2 * self.pad_x, text_h + 2 * self.pad_y),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(surf, (0, 0, 0, 180), surf.get_rect(), border_radius=8)

        # Center each line within the box
        for i, line_surf in enumerate(line_surfs):
            x = (surf.get_width() - line_surf.get_width()) // 2
            surf.blit(line_surf, (x, self.pad_y + i * line_h))

        self.surface = surf
        self.total_frames = max(frames, 1)
        self.hold_frames = min(max(hold, 0), self.total_frames - 1)
        self.frames_left = self.total_frames

    def update(self):
        """Call once per frame."""
        if self.frames_left > 0:
            self.frames_left -= 1

    def draw(self, target: pygame.Surface):
        if self.surface is None or self.frames_left <= 0:
            return
        elapsed = self.total_frames - self.frames_left
        if elapsed < self.hold_frames:
            alpha = 255
        else:
            fade_len = self.total_frames - self.hold_frames
            alpha = int(255 * self.frames_left / fade_len)
        self.surface.set_alpha(alpha)
        target.blit(self.surface, self.surface.get_rect(midtop=(BACKDROP_W // 2, self.y)))
class MigraineUI:
    def __init__(self, manager: pygame_gui.UIManager, state: dict):
        self.manager = manager
        self.state = state

        self.panel = UIPanel(
            relative_rect=pygame.Rect(0, BACKDROP_H, WINDOW_W, CONTROL_H),
            manager=manager,
            starting_height=1,
        )

        inner_w = WINDOW_W - 2 * PAD
        self.col_w = (inner_w - (COLUMN_COUNT - 1) * PAD) // COLUMN_COUNT
        self.inner_h = CONTROL_H - 2 * PAD
        self.list_h = self.inner_h - LABEL_H - BUTTON_H - 2 * PAD

        self._build_all_tasks_column(self._col_x(0))
        self._build_active_tasks_column(self._col_x(1))
        self._build_queued_tasks_column(self._col_x(2))
        self._build_gauges_column(self._col_x(3))

        self.banner = Banner()

        self.refresh()

    # ----- layout helpers -------------------------------------------------
    def _col_x(self, index: int) -> int:
        return PAD + index * (self.col_w + PAD)

    def _header(self, x: int, text: str) -> UILabel:
        return UILabel(
            pygame.Rect(x, PAD, self.col_w, LABEL_H), text,
            self.manager, container=self.panel,
        )

    def _list(self, x: int) -> UISelectionList:
        return UISelectionList(
            pygame.Rect(x, PAD + LABEL_H, self.col_w, self.list_h),
            item_list=[], manager=self.manager, container=self.panel,
            allow_multi_select=False,
        )

    def _button(self, x: int, text: str) -> UIButton:
        return UIButton(
            pygame.Rect(x, PAD + LABEL_H + self.list_h + PAD, self.col_w, BUTTON_H),
            text, self.manager, container=self.panel,
        )

    # ----- columns --------------------------------------------------------
    def _build_all_tasks_column(self, x: int):
        self._header(x, "All Tasks")
        self.all_list = self._list(x)
        self.queue_btn = self._button(x, "Queue Selected")
        self.queue_btn.disable()

    def _build_active_tasks_column(self, x: int):
        self._header(x, "Active Tasks")
        self.active_list = self._list(x)
        self.cancel_btn = self._button(x, "Cancel Selected")
        self.cancel_btn.disable()

    def _build_queued_tasks_column(self, x: int):
        self._header(x, "Queued Tasks")
        self.queued_list = self._list(x)
        self.unqueue_btn = self._button(x, "Unqueue Selected")
        self.unqueue_btn.disable()

    def _build_gauges_column(self, x: int):
        self._header(x, "Status")
        names = ["Energy", "Food", "Water", "GPA"]
        row_h = (self.inner_h - LABEL_H) // len(names)
        name_w = 110
        value_w = 70
        bar_w = self.col_w - name_w - 2 * PAD

        self.gauge_bars = {}
        self.gauge_values = {}
        for i, name in enumerate(names):
            y = PAD + LABEL_H + i * row_h
            UILabel(pygame.Rect(x, y, name_w, row_h - 6), name,
                    self.manager, container=self.panel)
            bar = UIProgressBar(
                pygame.Rect(x + name_w + PAD, y + 4, bar_w, row_h - 14),
                manager=self.manager, container=self.panel,
            )
            value = UILabel(
                pygame.Rect(x + name_w + bar_w + 2 * PAD, y, value_w, row_h - 6),
                "", self.manager, container=self.panel,
            )
            self.gauge_bars[name.lower()] = bar
            self.gauge_values[name.lower()] = value

    # ----- state -> widgets -----------------------------------------------
    def refresh(self):
        print("[Debug MigraineUI refresh()] Full refresh requested")
        s = self.state
        """Re-sync every widget with the game state. Call after any state change."""
        alltasks = s["tasks"]
        self.all_list.set_item_list([alltasks[t]['shortdesc'] for t in s["tasks"]])
        self.active_list.set_item_list([alltasks[t]['shortdesc'] for t in s["active_task_set"]])
        self.queued_list.set_item_list([alltasks[t]['shortdesc'] for t in s["awaiting_task_set"]])
        # Rebuilding a list clears its selection, so buttons go back to disabled
        self.queue_btn.disable()
        self.cancel_btn.disable()
        self.unqueue_btn.disable()
        self.refresh_gauges()

    def refresh_gauges(self):
        s = self.state
        self.gauge_bars["energy"].set_current_progress(s["energy"])
        self.gauge_bars["food"].set_current_progress(s["food"])
        self.gauge_bars["water"].set_current_progress(s["water"])
        self.gauge_bars["gpa"].set_current_progress(s["gpa"] / 4.0 * 100.0)

        self.gauge_values["energy"].set_text(f"")
        self.gauge_values["food"].set_text(f"")
        self.gauge_values["water"].set_text(f"")
        self.gauge_values["gpa"].set_text(f"")

    # ----- selection lookups ----------------------------------------------
    @staticmethod
    def _selected_index(sel_list: UISelectionList, tasks: list):
        label = sel_list.get_single_selection()
        if label is None:
            return None
        for i, t in enumerate(tasks):
            #print("[Debug _selected_index] ", i,t, label)
            if t == label:
                #print("[Debug _selected_index] Selected: ",t)
                return t
        #print("[Debug _selected_index] No select.")
        return None

    # _selected_index returns the short description of a task; however, 
    # tasks are referenced by a separate ID so this looks up a task 
    # short description and turns it back into the task ID so the 
    # individual task dict can be returned in the ternary statement
    # without a KeyError
    def _shortdesc_to_task_id(self, short_desc):
        taskdict = self.state["tasks"]
        for k, v in taskdict.items():
            if v["shortdesc"] == short_desc:
                return k
        return None

    def selected_all(self):
        # This method matches based on what's directly on the button, so the 
        # list of task IDs in each category (all, active, awaiting) needs to be converted
        # to short descriptions (which is what goes on the button)
        i = self._selected_index(self.all_list, [self.state["tasks"][i]["shortdesc"] for i in self.state["tasks"]])
        return None if i is None else self._shortdesc_to_task_id(i)
        pass

    def selected_active(self):
        i = self._selected_index(self.active_list, [self.state["tasks"][i]["shortdesc"] for i in self.state["active_task_set"]])
        return None if i is None else self._shortdesc_to_task_id(i)
        pass

    def selected_queued(self):
        i = self._selected_index(self.queued_list, [self.state["tasks"][i]["shortdesc"] for i in self.state["awaiting_task_set"]])
        return None if i is None else self._shortdesc_to_task_id(i)
        pass

    # ----- event handling --------------------------------------------------
    def handle_event(self, event: pygame.event.Event):
        """Handles UI events. Returns True if the event was consumed."""
        # s = self.state

        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element is self.all_list:
                self.queue_btn.enable()
            elif event.ui_element is self.active_list:
                task = self.selected_active()
                # Only cancellable tasks can be removed
                if self.state["tasks"][task]["can_cancel"]:
                    self.cancel_btn.enable()
                else:
                    self.cancel_btn.disable()
            elif event.ui_element is self.queued_list:
                self.unqueue_btn.enable()
            return True

        #if event.type == pygame_gui.UI_SELECTION_LIST_DROPPED_SELECTION:
        #    if event.ui_element is self.all_list:
        #        self.queue_btn.disable()
        #    elif event.ui_element is self.active_list:
        #        self.cancel_btn.disable()
        #    elif event.ui_element is self.queued_list:
        #        self.unqueue_btn.disable()
        #    return True

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element is self.queue_btn:
                task = self.selected_all()
                if task:
                    retcode, msg = add_to_task_set(self.state, task)
                    print("[Task Mgmt] Result of activate/queue task op: ", 
                        retcode, msg)
                    if retcode != 0: 
                        ui.banner.show(msg)
                    self.refresh()
                return True

            if event.ui_element is self.cancel_btn:
                task = self.selected_active()
                if task:
                    retcode, msg = cancel_task(self.state, task)
                    print("[Task Mgmt] Result of cancel task op: ", 
                        retcode, msg)
                    if retcode != 0:
                        ui.banner.show(msg)
                    self.refresh()
                return True

            if event.ui_element is self.unqueue_btn:
                task = self.selected_queued()
                if task:
                    retcode, msg = cancel_task(self.state, task)
                    print("[Task Mgmt] Result of cancel task op: ", 
                        retcode, msg)
                    if retcode != 0:
                        ui.banner.show(msg)
                    self.refresh()
                return True

        return False


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def draw_backdrop(surface: pygame.Surface):
    """Placeholder for the 1920x1080 backdrop. Replace with your image/scene."""
    backdrop_rect = pygame.Rect(0, 0, BACKDROP_W, BACKDROP_H)
    backdrop_image = pygame.image.load(f"./assets/Sprites/{IMAGE_FILENAMES[GAME_STATE['location']]}")
    scaled_image = pygame.transform.scale(backdrop_image, (BACKDROP_W, BACKDROP_H))
    surface.blit(scaled_image, (0, 0))

def draw_game_over(surface):
    endings = {
        "fainted": (
            "ambulance_bg.png",
            "Pain",
            "YOIU FAINTED",
            [
                "Your energy reached zero, and yoiu lost conciousness.",
                "A bystander saw you collapse and called 911.",
                "You slowly wake up in the back of an ambulance.",
                "Your day has come to an unexpected end."
            ]
        ),
        "flunked": (
            "flunked_bg (1).png",
            "Tired",
            "YOU FLUNKED OUT",
            [
                "Your grades fell below the required GPA threshold.",
                "You lost your scholarship and flunked out of school.",
                "Managing your health and academics became overwhelming."
            ]
        ),
        "success": (
            "dorm_room_bg.png",
            "Happy",
            "YOU MADE IT THROUGH THE DAY!",
            [
                "You made it to 9:00 PM!",
                "Living with a chronic illness means facing challenges",
                "that others may never see.",
                "You experienced just one day with one condition.",
                "We hope you now have a greater appreciation for the",
                "unseen struggles of people with chronic illnesses."
            ]
        )
    }
    if GAME_OVER_REASON is None:
        return
    background, emotion, title, lines = endings[GAME_OVER_REASON]

    bg = pygame.image.load(f"./assets/Sprites/{background}").convert()
    bg = pygame.transform.scale(bg, (WINDOW_W, WINDOW_H)) 
    surface.blit(bg, (0, 0))
    person = pygame.image.load(f"./assets/Sprites/P{CHARACTER_NUMBER}_{emotion}.PNG").convert_alpha()
    person = pygame.transform.scale_by(person, 0.28)
    person_rect = person.get_rect(bottomright=(WINDOW_W - 10, WINDOW_H + 15))
    surface.blit(person, person_rect)

    panel_h = 210
    panel = pygame.Surface(
        (WINDOW_W-30, panel_h), pygame.SRCALPHA
    )

    pygame.draw.rect(panel, (15, 17, 30, 225), panel.get_rect(), border_radius=15)

    panel_x = 15
    panel_y = WINDOW_H - panel_h - 15
    surface.blit(panel, (panel_x, panel_y))
    title_font = pygame.font.SysFont("Calibri", 28, bold=True)
    body_font = pygame.font.SysFont("Calibri", 19)

    title_surface = title_font.render(title, True, (255, 255, 170))
    surface.blit(title_surface, (panel_x + 22, panel_y + 16))

    for i, line in enumerate(lines):
        text_surface = body_font.render(line, True, (255, 255, 255))
        surface.blit(text_surface, (panel_x + 22, panel_y + 57 + i * 23))

def main():
    global ui
    pygame.display.set_caption("Unseen")

    # SCALED lets the 1920x1340 logical window shrink to fit smaller monitors
    window = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.SCALED | pygame.RESIZABLE)
    clock = pygame.time.Clock()

    manager = pygame_gui.UIManager((WINDOW_W, WINDOW_H), "theme.json")
    frame_count = 0
    ui = MigraineUI(manager, GAME_STATE)
    ui.refresh()

    # --------------------------------------------------------------------------
    # COMPILED RULES UNIT: allow it to print messages and 
    # request refreshes of task lists by passing in handlers
    # --------------------------------------------------------------------------
    def handle_CRU_say(msg):
        print(f"[Compiled Rules Unit Interface] CRU relayed message: {msg}")
        ui.banner.show(msg)
    compiled_rules.SAY = handle_CRU_say
    compiled_rules.ASK = dialogs.ask

    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0
        check_game_over()
        if GAME_OVER_REASON is not None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            if running:
                draw_game_over(window)
                pygame.display.update()
            continue
        # ---- input ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            manager.process_events(event)
            ui.handle_event(event)

        # ---- advance time in simulation ----
        manager.update(dt)
        
        if frame_count % 15 == 0:            
            # 1. Consume a certain amount of food, water and energy according to the burn rate
            # set by the AI
            GAME_STATE["energy"] = max(0, GAME_STATE["energy"] - GAME_STATE["energy_burn_rate"])
            GAME_STATE["water"] -= GAME_STATE["water_burn_rate"]
            GAME_STATE["food"] -= GAME_STATE["food_burn_rate"]

            # 2. For whatever task that the user has selected as active, give them one more minute
            # of completion time on that task.
            for active_task_name in GAME_STATE["active_task_set"]:
                GAME_STATE["tasks"][active_task_name]["time_spent"] += 1

            # 3. Run all custom logic then tx data
            GAME_STATE["current_minute"] += 1
            # print(GAME_STATE["current_minute"])
            def _pluck_dict_keys(di, keys):
                return {k: di[k] for k in keys if k in di}
            game_state_before = copy.deepcopy(_pluck_dict_keys(GAME_STATE, ["tasks", "active_task_set", "awaiting_task_set"]))
            compiled_rules.handle_minute(GAME_STATE)
            print("DEBUG ENERGY:", GAME_STATE["energy"])
            print("DEBUG GPA:", GAME_STATE["gpa"])
            print("DEBUG TIME:", GAME_STATE["current_minute"])

            check_game_over()
            print("DEBUG GAME OVER REASON:", GAME_OVER_REASON)
            
            if _pluck_dict_keys(GAME_STATE, ["tasks", "active_task_set", "awaiting_task_set"]) != game_state_before:
                # The CRU changed the state, need to refresh the task list 
                print("[Compiled Rules Unit Interface] CRU handle_minute() changed task list, requesting task list redraw.")
                ui.refresh()
            # time.sleep(REAL_SECS_BETWEEN_GAME_MINS)

            # 4. See if any queued tasks can be initiated because they arrived
            if GAME_OVER_REASON is None:
                awaiting_task_set_rewrite = []
                for taskid in GAME_STATE["awaiting_task_set"]:
                    retcode, msg = add_to_task_set(GAME_STATE, taskid)
                    if retcode == 0:
                        ui.refresh()
                    elif retcode in [4,5,6]: 
                        # ONLY keep it on queue if it's still too early or not the right place -- if there's 
                        # a mutex violation, it's too late somehow, etc., then remove it
                        awaiting_task_set_rewrite.append(taskid)
                    else:
                        print(f"[Task Mgmt] Tried to unload task {taskid}" f"from queue but got msg {retcode, msg}")

                GAME_STATE["awaiting_task_set"] = awaiting_task_set_rewrite
            check_game_over()

            if GAME_OVER_REASON is not None:
                draw_game_over(window)
                pygame.display.update()
                frame_count += 1
                continue

        # ---- draw ----
        # (DO NOT CHANGE THE ORDER THESE ARE RENDERED! For instance, 
        # drawing backdrop second and banner first breaks the banner)
        ui.refresh_gauges()
        ui.banner.update()
        draw_backdrop(window)
        text_surface = FONT.render(f"Time: {get_time_string(GAME_STATE['current_minute'])}", True, (255, 255, 255), (0, 0, 0))
        window.blit(text_surface, (PAD , PAD))
        if GAME_STATE["energy"] <= 40:
            emotion = "Pain"
        elif GAME_STATE["energy"] > 40 and GAME_STATE["energy"] < 60:
            emotion = "Tired"
        elif GAME_STATE["gpa"] < 2.8:
            emotion = "Stressed"
        elif GAME_STATE["energy"] > 85:
            emotion = "Happy"
        else:
            emotion = "Neutral"
        # print(emotion)
        person_image = pygame.image.load(f"./assets/Sprites/P{CHARACTER_NUMBER}_{emotion}.PNG")
        person_image = pygame.transform.scale_by(person_image, 0.25)
        window.blit(person_image, (WINDOW_W - 550, 10))
        ui.banner.draw(window)
        manager.draw_ui(window)


        

        # advance frame counter 
        frame_count += 1

        pygame.display.update()

    pygame.quit()


if __name__ == "__main__":
    main()