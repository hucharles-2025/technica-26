init python:
    def unseen_background(filename, tint):
        """Find artwork in game/images, game/backgrounds, or directly in game."""
        for path in ("images/" + filename, "backgrounds/" + filename, filename):
            if renpy.loadable(path):
                return Transform(Image(path), fit="cover", xysize=(1920, 1080))
        renpy.log("UNSEEN: Missing background PNG: " + filename +
            " (checked game/images/, game/backgrounds/, and game/)")
        return Solid(tint, xysize=(1920, 1080))

    def unseen_portrait(filename, tint):
        """Use a supplied character portrait, or a colored placeholder."""
        # Portrait filenames may be inside game/characters/ or game/images/.
        path = filename if filename.startswith("characters/") else "images/" + filename
        if renpy.loadable(path):
            return Transform(Image(path), fit="contain", xysize=(810, 755))
        return Solid(tint, xysize=(810, 755))

    def change_stats(minutes=0, energy=0, water=0, food=0, grades=0, friends=0):
        store.clock += minutes
        for key, delta in (("energy", energy), ("water", water),
            ("food", food), ("grades", grades),
            ("friends", friends)):
            setattr(store, key, max(0, min(100, getattr(store, key) + delta)))

    def clock_label():
        hour = (store.clock // 60) % 24
        minute = store.clock % 60
        return "%d:%02d %s" % (hour % 12 or 12, minute, "AM" if hour < 12 else "PM")

# Custom backgrounds: place PNGs directly in game/images/.
# Keep these scene names so the existing story uses the new artwork.
image bg dorm = unseen_background("dorm_room_bg.png", "#EEE6F7")
image bg campus = unseen_background("walking_bg.png", "#E1ECF4")
image bg classroom = unseen_background("classroom_bg.png", "#F2EAF4")
image bg bathroom = unseen_background("bathroom_bg.png", "#F6E9DC")
image bg jw = unseen_background("jw_bg.png", "#E6E7F2")
# Existing scene names retained as aliases for story compatibility.
image bg cafe = unseen_background("walking_bg.png", "#E1ECF4")
image bg library = unseen_background("jw_bg.png", "#E6E7F2")
image bg evening = unseen_background("dorm_room_bg.png", "#EEE6F7")
image avatar one = unseen_portrait("characters/Person 1/p1_neutral.png", "#D7B8EC")
image avatar two = unseen_portrait("avatar2.png", "#B8DDEB")
image avatar three = unseen_portrait("avatar3.png", "#F3C9C7")
image avatar four = unseen_portrait("avatar4.png", "#D2E6CC")

# Character 1 expression sprites. Names must match files exactly.
# Folder: game/characters/Person 1/
image p1 happy = "characters/Person 1/p1_happy.png"
image p1 neutral = "characters/Person 1/p1_neutral.png"
image p1 pain = "characters/Person 1/p1_pain.png"
image p1 stressed = "characters/Person 1/p1_stressed.png"
image p1 tired = "characters/Person 1/p1_tired.png"

# During gameplay, use '$ unseen_mood_override = "tired"' to force a mood.
# Reset with '$ unseen_mood_override = ""' for automatic mood selection.
# The avatar choice remains independent from the disability selection.

# The player's name is supplied at the start of each New Game.
define p = Character("[player_name]", color="#E7B9FF")
define mira = Character("Mira", color="#A5E9DF")
define rowan = Character("Rowan", color="#FFD0AA")
define professor = Character("Professor Ellis", color="#F2C2DA")

default player_name = "Alex"
default avatar_choice = 1
default day = 1
default clock = 480
default energy = 75
default water = 60
default food = 80
default grades = 85
default friends = 50
default asked_for_help = False

default took_break = False
default club_name = "None"
default assignments_done = 0
default assignments_total = 0
default quiz_points = 0
default quiz_total = 0
default class_attendance = 0
default missed_classes = 0
default accommodations_requested = False
default honest_conversation = False
default club_commitment = 0
default rested_today = False
default friday_test_preparation = 0
default academic_notes = []
default social_notes = []


# Appearance and condition are separate selections.
default selected_condition = 0
default symptom_load = 0
default care_completed = []
default routine_day = 0
default unseen_mood_override = ""

init python:
    def unseen_sprite_mood(dialogue=""):
        """Match the current line's emotion; avoid permanent stressed faces."""
        line = (dialogue or "").lower()
        if any(word in line for word in (
            "migraine", "headache", "pain", "cramp", "spasm",
            "vomit", "nausea", "aching", "hurts", "flare")):
            return "pain"
        if any(word in line for word in (
            "exhaust", "fatigue", "tired", "sleep", "rest",
            "drained", "worn out")):
            return "tired"
        if any(word in line for word in (
            "panic", "stress", "anxious", "exam", "deadline",
            "overwhelm", "worried", "quiz", "failing", "late")):
            return "stressed"
        if any(word in line for word in (
            "laugh", "smile", "happy", "celebrat", "excited",
            "proud", "relieved", "thanks", "great news", "fun")):
            return "happy"
        # Event-specific override can be set in a scene if desired.
        if store.unseen_mood_override:
            return store.unseen_mood_override
        if store.energy <= 18:
            return "tired"
        if store.symptom_load >= 18:
            return "pain"
        # Normal narration should be neutral, not stressed all day.
        return "neutral"

    unseen_avatars = [
        ("Person 1", "characters/Person 1/p1_neutral.png", "#D7B8EC"),
        ("Sage", "avatar2.png", "#B8DDEB"),
        ("Ember", "avatar3.png", "#F3C9C7"),
        ("Juniper", "avatar4.png", "#D2E6CC"),
    ]
    unseen_conditions = [
        {
            "name": "POTS",
            "about": "A form of autonomic dysfunction that can involve rapid heart rate on standing, dizziness, fatigue and brain fog. Symptoms vary.",
            "symptoms": ["Dizziness, vertigo or unsteadiness", "Visual dimming or muffled hearing during presyncope", "Fatigue, concentration problems and sometimes fainting"],
            "needs": ["Plan fluid intake and any extra salt with a clinician", "Compression garments if recommended", "Check heart rate or blood pressure when useful", "Sit or lie down if feeling faint; rise gradually", "Use a shower chair or mobility support if helpful"],
            "schedule": ["8:00 AM - breakfast and morning check-in", "Before leaving - pack water and any prescribed supplies", "Between classes - hydration and seated breaks", "Evening - check symptoms and prepare tomorrow's supplies"],
            "challenge": "Standing in line, long walks, heat, and packed class days can increase symptoms.",
        },
        {
            "name": "Chronic Daily Migraines",
            "about": "Frequent headache days may affect light sensitivity, nausea, fatigue and concentration. Not every attack involves every symptom.",
            "symptoms": ["Head pain and impaired concentration", "Nausea, sometimes vomiting", "Light, sound or smell sensitivity", "Some people experience dizziness or other neurological symptoms"],
            "needs": ["Follow an individually prescribed acute/preventive medication plan", "Use a quieter, darker space during attacks when helpful", "Manage triggers and maintain regular food and fluids", "Build breaks into prolonged concentration", "Track patterns without assuming every attack is preventable"],
            "schedule": ["8:00 AM - breakfast and symptom check", "Before class - pack prescribed medication if applicable", "Midday - meal, fluids, sensory break", "Evening - record symptoms and prepare a quiet rest option"],
            "challenge": "A flare may begin unpredictably and complicate class attendance or exams.",
        },
        {
            "name": "Tourette Syndrome",
            "about": "A neurological condition involving involuntary motor and/or vocal tics. Coprolalia (involuntary obscene words) occurs in a minority of people.",
            "symptoms": ["Motor and vocal tics", "Sometimes painful or exhausting tic episodes", "Premonitory urges for some tics", "Communication challenges and social misunderstandings"],
            "needs": ["Take breaks when tics are exhausting", "Find a comfortable place to let tics occur safely", "Use CBIT skills if trained and helpful; they are not a requirement", "Request class or testing accommodations as needed", "Communicate with trusted people when comfortable"],
            "schedule": ["8:00 AM - check how you are feeling", "Before class - identify break and accommodation options", "Between classes - decompress if needed", "Evening - rest and prepare for tomorrow"],
            "challenge": "A tic episode during a quiet exam can cause stress and misunderstanding.",
        },
        {
            "name": "Fibromyalgia",
            "about": "A chronic condition associated with widespread pain, fatigue, unrefreshing sleep and cognitive difficulties. Severity varies.",
            "symptoms": ["Widespread pain or stiffness", "Significant fatigue", "Sleep disruption", "Brain fog and sometimes headaches"],
            "needs": ["Pace activities and plan recovery breaks", "Use gentle movement or stretching if tolerated", "Choose supportive seating and accessible routes", "Use reminders or notes for cognitive fatigue", "Keep a flexible sleep routine"],
            "schedule": ["8:00 AM - gentle start and breakfast", "Before class - plan transport and seating", "Midday - paced movement and rest break", "Evening - organize reminders and allow recovery"],
            "challenge": "A poor night of sleep may make a full day of labs and lectures harder.",
        },
        {
            "name": "Multiple Sclerosis",
            "about": "MS is an immune-mediated condition affecting the central nervous system. Symptoms are diverse, and not everyone experiences the same impairments.",
            "symptoms": ["Numbness, tingling, weakness or spasticity", "Visual changes or pain with eye movement", "Fatigue, dizziness and balance problems", "Bladder, speech, swallowing or thinking difficulties in some people"],
            "needs": ["Use prescribed treatments and mobility aids as appropriate", "Take breaks for neurological fatigue", "Record new or worsening symptoms and contact the care team", "Use reminders and accessible class arrangements", "Seek urgent assessment for sudden major neurological changes"],
            "schedule": ["8:00 AM - check symptoms and mobility needs", "Before class - plan accessible transport", "Midday - neurological fatigue break", "Evening - review changes and follow prescribed care plan"],
            "challenge": "Unexpected changes in fatigue or mobility can disrupt travel between buildings.",
        },
        {
            "name": "Type 1 Diabetes",
            "about": "Type 1 diabetes requires insulin and glucose management. Insulin doses and glucose-check frequency are individualized; this game does not prescribe them.",
            "symptoms": ["Low or high glucose may affect concentration and energy", "High glucose can cause thirst and frequent urination", "Low glucose may cause shakiness, sweating or confusion", "Vomiting, abdominal pain, fruity breath or deep breathing can signal an emergency"],
            "needs": ["Check glucose using your prescribed meter/CGM plan", "Take insulin as prescribed; never guess a dose", "Carry rapid-acting glucose and emergency supplies", "For a low, follow your personal treatment plan and recheck as directed (often after 15 minutes)", "Seek emergency help for severe low glucose, suspected DKA, or inability to swallow safely"],
            "schedule": ["8:00 AM - glucose check and breakfast plan", "Meals - account for food and insulin per prescribed plan", "Between classes - check alerts and carry supplies", "Evening - review glucose and prepare supplies"],
            "challenge": "A glucose alert during an exam can force a choice between privacy and immediate care.",
        },
    ]

    def unseen_care_step(step):
        if step not in store.care_completed:
            store.care_completed.append(step)
            store.energy = min(100, store.energy + 5)
            store.water = min(100, store.water + 3)

    def unseen_daily_load():
        # Fictional variability, not a physiological simulation.
        return 5 + ((store.day * 7 + store.selected_condition * 3) % 9)

# Ren'Py screen language. The game uses a 1920 x 1080 design resolution.
# Adjust the resolution in game/gui.rpy if your project uses a different one.
screen unseen_hud():
    zorder 90
    frame:
        xalign 0.5
        yalign 0.0
        xsize 1860
        ysize 164
        top_margin 22
        background Solid("#292236F4")
        xpadding 26
        ypadding 18

        hbox:
            xfill True
            yalign 0.5
            spacing 22

            vbox:
                xsize 230
                spacing 7
                text "✦ UNSEEN" size 32 bold True color "#F2D6FF"
                text "[player_name]" size 23 bold True color "#FFFFFF"
                text "DAY [day]  •  [clock_label()]" size 20 color "#FFFFFF"

            vbox:
                xsize 310
                spacing 11
                hbox:
                    xfill True
                    text "ENERGY" size 25 bold True color "#FFFFFF"
                    text "[energy]/100" size 24 color "#F0C5FF" xalign 1.0
                bar:
                    value AnimatedValue(energy, 100, delay=0.4)
                    xsize 310
                    ysize 28
                    left_bar Solid("#D5A2F0")
                    right_bar Solid("#51425F")
                    thumb None

            vbox:
                xsize 280
                spacing 11
                hbox:
                    xfill True
                    text "WATER" size 25 bold True color "#FFFFFF"
                    text "[water]%" size 24 color "#A6E8FF" xalign 1.0
                bar:
                    value AnimatedValue(water, 100, delay=0.4)
                    xsize 280
                    ysize 28
                    left_bar Solid("#8BD9F3")
                    right_bar Solid("#51425F")
                    thumb None

            vbox:
                xsize 280
                spacing 11
                hbox:
                    xfill True
                    text "FOOD" size 25 bold True color "#FFFFFF"
                    text "[food]%" size 24 color "#FFD1DF" xalign 1.0
                bar:
                    value AnimatedValue(food, 100, delay=0.4)
                    xsize 280
                    ysize 28
                    left_bar Solid("#F4ADC7")
                    right_bar Solid("#51425F")
                    thumb None

            vbox:
                xsize 280
                spacing 11
                hbox:
                    xfill True
                    text "GRADES" size 25 bold True color "#FFFFFF"
                    text "[grades]/100" size 24 color "#E5D6FF" xalign 1.0
                bar:
                    value AnimatedValue(grades, 100, delay=0.4)
                    xsize 280
                    ysize 28
                    left_bar Solid("#B9A7F1")
                    right_bar Solid("#51425F")
                    thumb None

            vbox:
                xsize 280
                spacing 11
                hbox:
                    xfill True
                    text "FRIENDS" size 25 bold True color "#FFFFFF"
                    text "[friends]/100" size 24 color "#FFC8DE" xalign 1.0
                bar:
                    value AnimatedValue(friends, 100, delay=0.4)
                    xsize 280
                    ysize 28
                    left_bar Solid("#F5B2D1")
                    right_bar Solid("#51425F")
                    thumb None


# Carousel-style screens. Large portrait area is reserved for supplied artwork.
screen unseen_avatar_picker():
    modal True
    zorder 100
    default index = 0
    add Solid("#24182F")

    fixed:
        xfill True
        yfill True

        text "CHOOSE YOUR CHARACTER":
            xalign 0.5
            ypos 35
            size 52
            bold True
            color "#F5D9FF"

        text "Use the arrows to browse":
            xalign 0.5
            ypos 110
            size 24
            color "#E7D4F4"

        # The sprite itself is enlarged, not just its empty image canvas.
        add Transform(unseen_portrait(unseen_avatars[index][1], unseen_avatars[index][2]), zoom=0.84):
            xalign 0.5
            ycenter 498

        textbutton "❮":
            xalign 0.10
            ycenter 520
            action SetScreenVariable("index", (index - 1) % len(unseen_avatars))
            text_size 75

        textbutton "❯":
            xalign 0.90
            ycenter 520
            action SetScreenVariable("index", (index + 1) % len(unseen_avatars))
            text_size 75

        text unseen_avatars[index][0]:
            xalign 0.5
            ypos 810
            size 30
            bold True
            color "#FFFFFF"

        frame:
            xalign 0.5
            ypos 864
            xsize 405
            ysize 85
            background Solid("#76539D")
            xpadding 8
            ypadding 8
            textbutton "SELECT CHARACTER":
                xalign 0.5
                yalign 0.5
                action Return(index + 1)
                text_size 29
                text_color "#FFFFFF"
                text_hover_color "#FFE7FF"

screen unseen_condition_picker():
    modal True
    default index = 0
    add Solid("#1E172BF8")
    frame:
        xalign 0.5
        yalign 0.5
        xsize 1560
        ysize 960
        background Solid("#30243F")
        xpadding 38
        ypadding 22
        vbox:
            spacing 15
            text "CHOOSE AN EXPERIENCE" xalign 0.5 size 43 bold True color "#F5D9FF"
            fixed:
                xfill True
                ysize 74
                textbutton "❮":
                    xalign 0.18
                    yalign 0.5
                    action SetScreenVariable("index", (index - 1) % len(unseen_conditions))
                    text_size 52
                text unseen_conditions[index]["name"]:
                    xalign 0.5
                    yalign 0.5
                    xsize 850
                    text_align 0.5
                    size 38
                    bold True
                    color "#FFFFFF"
                textbutton "❯":
                    xalign 0.82
                    yalign 0.5
                    action SetScreenVariable("index", (index + 1) % len(unseen_conditions))
                    text_size 52
            text unseen_conditions[index]["about"] xalign 0.5 xmaximum 1430 text_align 0.5 size 23 color "#EADFF0"
            viewport:
                xsize 1450
                ysize 610
                mousewheel True
                draggable True
                scrollbars "vertical"
                vbox:
                    spacing 15
                    frame:
                        xfill True
                        background Solid("#483857")
                        xpadding 25
                        ypadding 15
                        vbox:
                            spacing 8
                            text "POSSIBLE SYMPTOMS" size 28 bold True color "#F0C8FF"
                            for item in unseen_conditions[index]["symptoms"]:
                                text "• " + item size 22 color "#FFFFFF"
                    frame:
                        xfill True
                        background Solid("#483857")
                        xpadding 25
                        ypadding 15
                        vbox:
                            spacing 8
                            text "SELF-CARE AND SUPPORT OPTIONS" size 28 bold True color "#BFEAFF"
                            for item in unseen_conditions[index]["needs"]:
                                text "• " + item size 22 color "#FFFFFF"
                    frame:
                        xfill True
                        background Solid("#483857")
                        xpadding 25
                        ypadding 15
                        vbox:
                            spacing 8
                            text "SAMPLE DAILY TASK LIST" size 28 bold True color "#FFD2E3"
                            for item in unseen_conditions[index]["schedule"]:
                                text "□ " + item size 22 color "#FFFFFF"
                    text "GAMEPLAY CHALLENGE: " + unseen_conditions[index]["challenge"] size 22 color "#FFFFFF"
            text "Schedules are examples, not medical instructions. Follow your own clinician's plan." xalign 0.5 size 19 color "#E5C9E8"
            textbutton "PLAY THIS EXPERIENCE" xalign 0.5 action Return(index) text_size 29

# The character rises from behind the dialogue panel at the lower-right.
# Only Person 1 has completed art so far. Other selections do not show
# Person 1's face by mistake.
screen unseen_story_sprite():
    # Above the dialogue background. Character rises out of its top edge.
    zorder 120
    if avatar_choice == 1:
        $ mood = unseen_sprite_mood()
        $ sprite_file = "characters/Person 1/p1_" + mood + ".png"
        if renpy.loadable(sprite_file):
            add Transform(sprite_file, fit="contain", xysize=(450, 450)):
                xalign 0.975
                yalign 1.0
                yoffset -155

screen unseen_daily_tasks():
    modal True
    add Solid("#1E172BEF")
    frame:
        xalign 0.5
        yalign 0.5
        xsize 1360
        ysize 830
        background Solid("#30243F")
        xpadding 45
        ypadding 35
        vbox:
            spacing 18
            text "DAY [day] — DAILY CARE PLAN" size 42 bold True color "#F4D4FF"
            text unseen_conditions[selected_condition]["name"] size 30 color "#BCEAFF"
            text "Choose a task to plan for today. Completing one costs time but helps your game resources." size 23 color "#FFFFFF"
            for i, task in enumerate(unseen_conditions[selected_condition]["schedule"]):
                hbox:
                    spacing 20
                    if i in care_completed:
                        text "✓" size 28 color "#A8EAC6"
                        text task size 23 color "#D9CFE2"
                    else:
                        textbutton "□  " + task action [Function(unseen_care_step, i), SetVariable("clock", clock + 15)] text_size 23
            text "Other tasks can be completed later through story decisions." size 20 color "#CFC3D7"
            textbutton "START THE DAY" xalign 0.5 action Return() text_size 30

# Custom dialogue panel: text starts in the TOP-LEFT, with sensible
# wrapping, and the chosen sprite peeks out above the panel at the right.
# This overrides the default say screen from screens.rpy.
screen say(who, what):
    zorder 100
    window:
        id "window"
        xalign 0.5
        yalign 1.0
        xsize 1920
        ysize 250
        background Solid("#241B32EE")
        left_padding 40
        right_padding 400
        top_padding 20
        bottom_padding 20

        vbox:
            xalign 0.0
            yalign 0.0
            spacing 8
            if who is not None:
                text who id "who":
                    size 30
                    bold True
                    color "#F0CFFF"
            text what id "what":
                size (35 if len(what) < 95 else 31 if len(what) < 190 else 27)
                color "#FFFFFF"
                xalign 0.0
                text_align 0.0
                line_spacing 3

    # Dialogue-only portrait: rises out of the panel's right corner.
    if avatar_choice == 1:
        $ dialogue_mood = unseen_sprite_mood(what)
        $ dialogue_sprite = "characters/Person 1/p1_" + dialogue_mood + ".png"
        if renpy.loadable(dialogue_sprite):
            add Transform(dialogue_sprite, fit="contain", xysize=(475, 475)):
                xalign 0.965
                yalign 1.0
                yoffset -115

style choice_button_text:
    color "#FFFFFF"
    hover_color "#F5D6FF"
    size 30

style choice_button:
    background Solid("#352842F2")
    hover_background Solid("#644A7CF2")
    xpadding 32
    ypadding 20

# -------------------- MAIN STORY --------------------
# This is a complete five-day playable prototype.
# All scores are game mechanics, not medical advice or predictions.

label start:
    scene bg dorm
    $ day = 1
    $ clock = 480
    "UNSEEN"
    "College can be exciting, exhausting, unpredictable, and full of competing priorities."
    "Choose your character and then choose which disability experience to explore."
    $ player_name = renpy.input("What should everyone call you?", length=24).strip()
    if not player_name:
        $ player_name = "Alex"
    $ quick_menu = False
    window hide
    $ avatar_choice = renpy.call_screen("unseen_avatar_picker")
    $ selected_condition = renpy.call_screen("unseen_condition_picker")
    $ quick_menu = True
    window auto
    "You selected [unseen_conditions[selected_condition]['name']]. This story portrays one fictional experience, not everyone with the condition."
    "Self-care and symptom patterns differ between people. The task list is a game mechanic, not a treatment plan."
    show screen unseen_hud
    "Grades begin at 85. Classes, exams, relationships and self-care compete for your time."
    jump monday

label monday:
    $ unseen_mood_override = ""
    $ day = 1
    $ clock = 480
    scene bg dorm
    $ care_completed = []
    $ symptom_load = unseen_daily_load()
    $ change_stats(energy=-symptom_load)
    $ renpy.call_screen("unseen_daily_tasks")
    "MONDAY — 8:00 AM"
    call unseen_incident
    "Your CMSC216 discussion begins at 10:00. An ENEE222 assessment is coming up, and your CMSC216 programming assignment is due tonight."
    "You also promised Mira you'd get lunch together."
    menu:
        "Eat breakfast and pack water; leave less time to review code.":
            $ change_stats(minutes=65, food=18, water=17, energy=3)
            $ friday_test_preparation += 1
            "You leave feeling more prepared for the physical demands of the morning, but your code review is rushed."
        "Review your code before leaving; skip the slower morning routine.":
            $ change_stats(minutes=65, food=-13, water=-10, energy=-9)
            $ friday_test_preparation += 3
            "You catch a tricky bug. The morning feels harder than you hoped."
        "Ask your teaching assistant for an extension and take a measured morning.":
            $ change_stats(minutes=65, food=10, water=10, energy=5)
            $ accommodations_requested = True
            "You send a message. Whether an extension is granted is not guaranteed, but you've communicated early."
    scene bg campus
    $ clock = 590
    "9:50 AM — The Iribe Center"
    "The campus is busy. Your first lecture is about arrays and indexes."
    menu:
        "Attend CMSC216 and take notes, even though you feel worn down.":
            $ class_attendance += 1
            $ change_stats(minutes=55, energy=-13, water=-8)
            "You understand the examples, but the long morning takes energy."
        "Attend with a brief break and ask for the lecture notes afterward.":
            $ class_attendance += 1
            $ accommodations_requested = True
            $ change_stats(minutes=55, energy=-7, water=-5)
            "You miss a few minutes, then catch up using the notes."
        "Return to your dorm and work through the lecture material later.":
            $ missed_classes += 1
            $ change_stats(minutes=55, energy=8)
            $ friday_test_preparation -= 1
            "Rest helps. Now you have an additional lecture to catch up on."
    "11:00 AM — You have a discussion section, travel to circuits, and lunch to fit in."
    menu:
        "Go to discussion, take paratransit, and arrive at circuits on time.":
            $ class_attendance += 2
            $ change_stats(minutes=120, energy=-23, food=-13, water=-10)
            $ friday_test_preparation += 2
            "You make both classes. Mira texts: 'Still doing lunch?'"
        "Go to discussion, eat with Mira, and arrive late to circuits.":
            $ class_attendance += 1
            $ missed_classes += 1
            $ change_stats(minutes=120, energy=-9, food=20, water=9, friends=9)
            "Lunch is wonderful. You miss the start of the circuits example."
        "Take a break and eat before circuits; miss discussion.":
            $ missed_classes += 1
            $ class_attendance += 1
            $ change_stats(minutes=120, energy=8, food=17, water=12, friends=-3)
            "You arrive at circuits steadier, but your discussion notes are missing."
    scene bg jw
    $ clock = 900
    "3:00 PM — Your CMSC216 assignment is due tonight. Mira has invited you to study together."
    $ assignments_total += 1
    menu:
        "Finish the assignment alone while you still have momentum.":
            $ assignments_done += 1
            $ change_stats(minutes=120, energy=-18, food=-8, grades=2)
            $ friday_test_preparation += 1
            "You submit your work. Mira ends up studying with someone else."
        "Study with Mira; ask for help, but submit a partially finished assignment.":
            $ change_stats(minutes=120, energy=-11, food=-7, friends=10, grades=-2)
            $ friday_test_preparation += 2
            "You understand the material better, but some assignment points are left on the table."
        "Request help and take a recovery break before finishing.":
            $ assignments_done += 1
            $ accommodations_requested = True
            $ change_stats(minutes=150, energy=2, food=-6, grades=1, friends=-2)
            "You work in shorter blocks and submit later in the evening."
    scene bg dorm
    $ clock = 1260
    "9:00 PM — Tomorrow brings circuits discussion and a policy seminar."
    menu:
        "Sleep early and leave tomorrow's preparation unfinished.":
            $ change_stats(energy=17, food=-5)
            "You choose rest, knowing you'll need to prepare between classes."
        "Prepare for tomorrow's circuits discussion.":
            $ friday_test_preparation += 2
            $ change_stats(energy=-12, water=-5)
            "You feel more confident about circuits, but it's a late night."
        "Call a friend you've barely seen this week.":
            $ change_stats(energy=-7, friends=10)
            "You reconnect. The conversation runs longer than expected."
    $ unseen_mood_override = ""
    if energy <= 0:
        jump unseen_ambulance
    if grades < 65:
        jump unseen_dismissal
    if friends <= 0:
        jump unseen_isolation
    jump tuesday

label tuesday:
    $ unseen_mood_override = ""
    $ day = 2
    $ clock = 540
    scene bg dorm
    $ care_completed = []
    $ symptom_load = unseen_daily_load()
    $ change_stats(energy=-symptom_load)
    $ renpy.call_screen("unseen_daily_tasks")
    "TUESDAY — 9:00 AM"
    call unseen_incident
    "Today includes ENEE222 discussion and CPBE225. There's a short circuits problem set due."
    $ assignments_total += 1
    menu:
        "Complete the problem set before discussion.":
            $ assignments_done += 1
            $ change_stats(minutes=110, energy=-14, grades=2, food=-9)
            $ friday_test_preparation += 2
            "The answers take longer than expected. You head out without much downtime."
        "Eat and hydrate, then submit what you already finished.":
            $ change_stats(minutes=110, energy=6, food=18, water=15, grades=-2)
            "You make it to class feeling more prepared physically, but the assignment is incomplete."
        "Go to office hours for the hardest problems and submit afterward.":
            $ assignments_done += 1
            $ change_stats(minutes=130, energy=-8, grades=2, water=-5)
            $ friday_test_preparation += 3
            "You understand why your original method didn't work."
    scene bg classroom
    $ clock = 750
    "12:30 PM — ENEE222 Discussion"
    "Your TA writes: 'Find the derivative of f(x) = x² sin(x).'"
    menu:
        "2x sin(x) + x² cos(x)":
            $ quiz_points += 1
            $ friday_test_preparation += 2
            "Correct. The product rule differentiates one factor at a time."
        "2x cos(x)":
            $ friday_test_preparation += 0
            "Not quite. You differentiated the two factors together instead of using the product rule."
        "x² cos(x)":
            "Not quite. You forgot the derivative of x² in the first product-rule term."
    $ quiz_total += 1
    "The TA moves on to the next example."
    menu:
        "Stay for the full discussion and CPBE225 afterward.":
            $ class_attendance += 2
            $ change_stats(minutes=155, energy=-21, food=-12, water=-12)
            $ friday_test_preparation += 1
            "You take solid notes. You're drained by the end."
        "Take a break between classes and arrive late to policy.":
            $ class_attendance += 1
            $ missed_classes += 1
            $ change_stats(minutes=155, energy=-4, food=8, water=8)
            "You catch the policy discussion halfway through."
        "Ask for notes and skip policy to recover.":
            $ class_attendance += 1
            $ missed_classes += 1
            $ accommodations_requested = True
            $ change_stats(minutes=155, energy=14, food=9)
            "You recover, but will need to catch up on the assigned debate."
    scene bg campus
    $ clock = 1080
    "6:00 PM — Rowan texts: 'Come to the club fair with me? I don't want to go alone.'"
    "You want to find your community, but your week is already full."
    menu:
        "Go to the club fair and choose a group.":
            $ change_stats(minutes=75, energy=-11, friends=6)
            jump club_fair
        "Ask Rowan to send you the club list so you can choose from home.":
            $ change_stats(minutes=20, energy=5, friends=1)
            "Rowan sends photos of the tables and tells you about the conversations."
            jump club_fair
        "Decline for now and spend the evening catching up.":
            $ change_stats(minutes=90, energy=-8, grades=1, friends=-5)
            $ friday_test_preparation += 2
            "You make academic progress, but you haven't found a club yet."
            $ club_name = "None"
    if energy <= 0:
        jump unseen_ambulance
    if grades < 65:
        jump unseen_dismissal
    if friends <= 0:
        jump unseen_isolation
    jump wednesday

label club_fair:
    "You can commit to one campus organization. Its meeting will become part of your week."
    "These are examples inspired by UMD student organizations; confirm current membership and meeting details through UMD's official student organization directory."
    menu:
        "Technica — event organizing and technology":
            $ club_name = "Technica"
        "Robotics at Maryland — engineering projects":
            $ club_name = "Robotics at Maryland"
        "Hack4Impact — technology for social impact":
            $ club_name = "Hack4Impact"
        "Terps Racing — engineering and team builds":
            $ club_name = "Terps Racing"
    $ club_commitment = 1
    $ change_stats(friends=6)
    "You join [club_name]. Your first meeting is Wednesday evening."
    if energy <= 0:
        jump unseen_ambulance
    if grades < 65:
        jump unseen_dismissal
    if friends <= 0:
        jump unseen_isolation
    jump wednesday

label wednesday:
    $ unseen_mood_override = ""
    $ day = 3
    $ clock = 480
    scene bg dorm
    $ care_completed = []
    $ symptom_load = unseen_daily_load()
    $ change_stats(energy=-symptom_load)
    $ renpy.call_screen("unseen_daily_tasks")
    "WEDNESDAY — 8:00 AM"
    call unseen_incident
    "CMSC216 lecture and discussion are followed by circuits at noon. Your club meets this evening."
    "A friend texts: 'You've been distant lately. Are we okay?'"
    menu:
        "Explain that managing symptoms and deadlines has been difficult.":
            $ honest_conversation = True
            $ change_stats(minutes=15, friends=11, energy=-2)
            "Your friend replies: 'I didn't know. We can plan something low-key.'"
        "Say everything is fine so you don't worry them.":
            $ change_stats(minutes=5, friends=-5)
            "The conversation ends, but the misunderstanding remains."
        "Promise to hang out tonight, even though you're not sure you can.":
            $ change_stats(minutes=5, friends=3)
            "Your friend is excited. Now you have another commitment."
            $ social_notes.append("Promised a Wednesday hangout")
    scene bg classroom
    $ clock = 600
    "10:00 AM — CMSC216"
    "The professor asks what the array expression arr[2] accesses in a zero-indexed array."
    menu:
        "The third element":
            $ quiz_points += 1
            $ friday_test_preparation += 2
            "Correct. Index zero refers to the first element."
        "The second element":
            "Not quite. Index two is the third element."
        "The array's length":
            "Not quite. That would require a length operation or property."
    $ quiz_total += 1
    menu:
        "Attend lecture, discussion, and circuits; eat afterward.":
            $ class_attendance += 3
            $ change_stats(minutes=210, energy=-29, food=-18, water=-17)
            $ friday_test_preparation += 3
            "You make every class. The afternoon feels long."
        "Attend CMSC216 and circuits, but use discussion time for a break.":
            $ class_attendance += 2
            $ missed_classes += 1
            $ change_stats(minutes=210, energy=-11, food=9, water=12)
            $ friday_test_preparation += 1
            "You preserve some energy, but must get discussion notes later."
        "Attend discussion and circuits; review the lecture recording later.":
            $ class_attendance += 2
            $ missed_classes += 1
            $ change_stats(minutes=210, energy=-13, food=7, water=8)
            $ friday_test_preparation += 2
            "You trade live lecture time for a more manageable morning."
    scene bg jw
    $ clock = 960
    "4:00 PM — You have a programming quiz to prepare for, and the club meeting is approaching."
    $ assignments_total += 1
    menu:
        "Finish the coding practice assignment before the meeting.":
            $ assignments_done += 1
            $ change_stats(minutes=90, energy=-17, grades=2)
            $ friday_test_preparation += 3
            "You finish, but the club meeting now feels like a lot."
        "Take a structured rest break, then finish part of the assignment.":
            $ rested_today = True
            $ change_stats(minutes=90, energy=15, grades=-1)
            $ friday_test_preparation += 1
            "You feel more able to focus, though some practice remains undone."
        "Study with Rowan and trade help on difficult questions.":
            $ assignments_done += 1
            $ change_stats(minutes=90, energy=-11, friends=8, grades=1)
            $ friday_test_preparation += 2
            "You both learn something. It takes longer than studying alone."
    if club_name != "None":
        scene bg campus
        $ clock = 1110
        "6:30 PM — [club_name] meeting"
        menu:
            "Attend the full meeting and volunteer for a task.":
                $ club_commitment += 2
                $ change_stats(minutes=100, energy=-20, friends=13)
                "You leave with a new responsibility and a few new contacts."
            "Attend briefly, introduce yourself, then head home.":
                $ club_commitment += 1
                $ change_stats(minutes=45, energy=-7, friends=7)
                "You connect with people while respecting your limits."
            "Message the organizer and ask for a recap instead.":
                $ change_stats(minutes=15, energy=7, friends=-2)
                "You stay involved remotely, but miss the informal conversations."
    else:
        "6:30 PM — Other students are heading to club meetings."
        menu:
            "Spend the evening reviewing circuits.":
                $ friday_test_preparation += 3
                $ change_stats(minutes=85, energy=-13)
            "Take a longer break and reach out to a friend.":
                $ change_stats(minutes=85, energy=15, friends=5)
    if "Promised a Wednesday hangout" in social_notes:
        "Your friend texts: 'Are we still hanging out?'"
        menu:
            "Be upfront and suggest a shorter meetup tomorrow.":
                $ honest_conversation = True
                $ change_stats(friends=5)
                "Your friend appreciates having a concrete alternative."
            "Go out tonight, even though your schedule is packed.":
                $ change_stats(minutes=90, energy=-17, friends=10)
                "You have fun. Tomorrow morning may be harder."
            "Don't reply until tomorrow.":
                $ change_stats(friends=-9)
                "The unread message weighs on you."
    if energy <= 0:
        jump unseen_ambulance
    if grades < 65:
        jump unseen_dismissal
    if friends <= 0:
        jump unseen_isolation
    jump thursday

label thursday:
    $ unseen_mood_override = ""
    $ day = 4
    $ clock = 540
    scene bg dorm
    $ care_completed = []
    $ symptom_load = unseen_daily_load()
    $ change_stats(energy=-symptom_load)
    $ renpy.call_screen("unseen_daily_tasks")
    "THURSDAY — 9:00 AM"
    call unseen_incident
    "ENEE222 discussion and CPBE225 are on your calendar. Your professor also has office hours."
    "The circuits quiz is tomorrow. Mira asks you to help prepare for a presentation."
    menu:
        "Go to office hours before class and skip breakfast with Mira.":
            $ change_stats(minutes=100, energy=-10, food=-9, friends=-3)
            $ friday_test_preparation += 4
            "Your professor helps you untangle a derivative problem."
        "Eat with Mira and study together; miss office hours.":
            $ change_stats(minutes=100, food=16, water=12, friends=12, energy=-5)
            $ friday_test_preparation += 2
            "You support each other, but your hardest question remains unresolved."
        "Take a slower morning and email your professor a question.":
            $ accommodations_requested = True
            $ change_stats(minutes=100, energy=12, food=9, water=8)
            $ friday_test_preparation += 1
            "You send a specific question and wait for a reply."
    scene bg classroom
    $ clock = 750
    "12:30 PM — ENEE222 discussion"
    "A related-rates question asks: a 10-foot ladder leans against a wall. If its base is 6 feet from the wall, how high is the top?"
    menu:
        "8 feet":
            $ quiz_points += 1
            $ friday_test_preparation += 2
            "Correct: 6² + 8² = 10²."
        "4 feet":
            "Not quite. Use the Pythagorean theorem with the ladder as the hypotenuse."
        "16 feet":
            "Not quite. The height cannot exceed the 10-foot ladder."
    $ quiz_total += 1
    menu:
        "Attend discussion and policy, then rest afterward.":
            $ class_attendance += 2
            $ change_stats(minutes=160, energy=-17, water=-10, food=-10)
            "You make both classes and plan a quieter evening."
        "Attend discussion but use policy time to recover and catch up later.":
            $ class_attendance += 1
            $ missed_classes += 1
            $ change_stats(minutes=160, energy=8, food=10, water=10)
            "You will need to review the policy discussion."
        "Ask for notes, rest now, and prepare for the quiz tonight.":
            $ missed_classes += 2
            $ change_stats(minutes=160, energy=15, food=8, water=10)
            $ friday_test_preparation += 2
            "You gain study time but miss both in-person sessions."
    scene bg dorm
    $ clock = 1140
    "7:00 PM — Your friend has a birthday dinner tonight. Tomorrow is the circuits quiz."
    menu:
        "Go to the whole dinner, even if you study less.":
            $ change_stats(minutes=160, energy=-22, friends=17, food=15)
            $ friday_test_preparation -= 2
            "You laugh more than you have all week. You get home late."
        "Go for dessert and tell your friend why you need to leave early.":
            $ change_stats(minutes=70, energy=-8, friends=10, food=5)
            $ friday_test_preparation += 1
            $ honest_conversation = True
            "Your friend appreciates seeing you, even briefly."
        "Stay home and study; send a thoughtful birthday message.":
            $ change_stats(minutes=120, energy=-15, friends=-5)
            $ friday_test_preparation += 4
            "You feel prepared, but you miss celebrating in person."
    if energy <= 0:
        jump unseen_ambulance
    if grades < 65:
        jump unseen_dismissal
    if friends <= 0:
        jump unseen_isolation
    jump friday

label friday:
    $ unseen_mood_override = ""
    $ day = 5
    $ clock = 510
    scene bg dorm
    $ care_completed = []
    $ symptom_load = unseen_daily_load()
    $ change_stats(energy=-symptom_load)
    $ renpy.call_screen("unseen_daily_tasks")
    "FRIDAY — 8:30 AM"
    call unseen_incident
    "Today is the CMSC216 lecture, circuits lecture, and your ENEE222 quiz."
    "You have also promised your club organizer an update, if you joined a club."
    menu:
        "Eat, hydrate, and review one page of notes.":
            $ change_stats(minutes=70, energy=4, food=16, water=17)
            $ friday_test_preparation += 1
            "You arrive with a little less review time but a steadier routine."
        "Use every minute for last-minute studying.":
            $ change_stats(minutes=70, energy=-12, food=-9, water=-10)
            $ friday_test_preparation += 3
            "You cover more material, but the morning feels intense."
        "Ask for a quieter testing arrangement and take time to prepare.":
            $ accommodations_requested = True
            $ change_stats(minutes=70, energy=6, water=12)
            $ friday_test_preparation += 1
            "You confirm your testing arrangements. Planning ahead helps reduce uncertainty."
    scene bg classroom
    $ clock = 600
    "10:00 AM — CMSC216"
    menu:
        "Attend the lecture and review quiz material afterward.":
            $ class_attendance += 1
            $ change_stats(minutes=60, energy=-10, water=-5)
            $ friday_test_preparation += 1
        "Use lecture time to prepare for circuits, and catch up later.":
            $ missed_classes += 1
            $ change_stats(minutes=60, energy=-8)
            $ friday_test_preparation += 2
    scene bg classroom
    $ clock = 720
    "12:00 PM — ENEE222"
    "It's time for the quiz. Your preparation matters, but so does what you've learned along the way."
    $ quiz_total += 1
    "Question 1: What is the derivative of f(x) = x³ + 2x?"
    menu:
        "3x² + 2":
            $ quiz_points += 1
            "Correct."
        "x² + 2":
            "Not quite. The derivative of x³ is 3x²."
        "3x + 2":
            "Not quite. The exponent on x decreases by one."
    $ quiz_total += 1
    "Question 2: For f(x) = x² - 2 and x₀ = 1, what is the first Newton's Method approximation?"
    menu:
        "3/2":
            $ quiz_points += 1
            "Correct. x₁ = 1 - (-1)/2 = 3/2."
        "1/2":
            "Not quite. Subtract the entire fraction f(x₀)/f'(x₀)."
        "2":
            "Not quite. Newton's Method gives 3/2 after one step."
    $ quiz_total += 1
    "Question 3: Use linear approximation at x = 16 to estimate sqrt(17)."
    menu:
        "33/8":
            $ quiz_points += 1
            "Correct: 4 + (1/8)(1) = 33/8."
        "17/4":
            "Not quite. The slope at x = 16 is 1/8."
        "4":
            "Not quite. Four is the value at the base point, not the estimate."
    $ quiz_total += 1
    "Question 4: A 10-foot ladder has its base 6 feet from the wall. If the base moves outward at 2 ft/s, what is dy/dt?"
    menu:
        "-3/2 ft/s":
            $ quiz_points += 1
            "Correct. At y = 8, dy/dt = -(6/8)(2) = -3/2."
        "3/2 ft/s":
            "The magnitude is right, but the top is moving down, so the rate is negative."
        "-2 ft/s":
            "Not quite. Differentiate x² + y² = 100 with respect to time."
    $ quiz_total += 1
    "The quiz is over. You have done what you could with the time and resources available."
    if club_name != "None":
        "Your [club_name] organizer asks if you can help with a weekend task."
        menu:
            "Take the task and rearrange your weekend plans.":
                $ club_commitment += 2
                $ change_stats(energy=-10, friends=7)
                "You accept. You will need to manage the added commitment."
            "Offer a smaller task with a realistic deadline.":
                $ club_commitment += 1
                $ change_stats(friends=5)
                "The organizer agrees. You have a manageable contribution."
            "Decline this weekend and explain your workload.":
                $ change_stats(energy=5, friends=-1)
                "You communicate your limits clearly."
    scene bg evening
    $ clock = 1080
    "FRIDAY — 6:00 PM"
    "The week is ending. Not every decision worked out exactly as you hoped."
    if energy <= 0:
        jump unseen_ambulance
    if grades < 65:
        jump unseen_dismissal
    if friends <= 0:
        jump unseen_isolation
    jump weekly_reflection

label weekly_reflection:
    # A transparent prototype grade model: the player begins at 85.
    # Homework completion, practice quizzes, and preparation all contribute.
    $ homework_fraction = float(assignments_done) / max(1, assignments_total)
    $ quiz_fraction = float(quiz_points) / max(1, quiz_total)
    $ earned = int(round((homework_fraction - 0.5) * 8 + (quiz_fraction - 0.5) * 10 + max(-3, min(5, friday_test_preparation // 3)) - missed_classes))
    $ grades = max(0, min(100, grades + earned))
    "WEEK ONE — REFLECTION"
    "Assignments completed: [assignments_done] out of [assignments_total]."
    "Practice and quiz questions correct: [quiz_points] out of [quiz_total]."
    "Classes attended: [class_attendance]. Class sessions missed: [missed_classes]."
    "Your current Grades score is [grades]/100, and your Friends score is [friends]/100."
    if club_name != "None":
        "You joined [club_name] and built [club_commitment] club commitment points."
    else:
        "You did not join a club this week. That choice left room for other priorities."
    if accommodations_requested:
        "You reached out for support or used a strategy to make the academic week more accessible."
    else:
        "You navigated the week without requesting additional support. That remains an option in future chapters."
    if honest_conversation:
        "At least once, you were honest about what you needed. That opened the door to a more understanding relationship."
    else:
        "Some people may not yet understand why your plans changed. A conversation could help in a future chapter."
    if energy < 25:
        "Your energy is low. The next chapter would begin with choices about recovery and commitments."
    elif energy > 65:
        "You end the week with some energy available, though that doesn't mean the week was easy."
    else:
        "You end the week somewhere in the middle: proud of some decisions and still thinking about others."
    "There is no perfect score for living a full life. Grades and friendships matter, but neither tells the whole story."
    "END OF WEEK ONE — Thank you for playing UNSEEN."
    menu:
        "Replay the week with different decisions":
            jump start
        "Return to the main menu":
            return

label unseen_incident:
    $ unseen_mood_override = ""
    if selected_condition == 0:
        "You experience dizziness and visual dimming after standing. You sit down and ask someone nearby to stay with you."
    elif selected_condition == 1:
        "A headache flare makes light and sound difficult to tolerate. You consider the quiet room and your prescribed plan."
    elif selected_condition == 2:
        "A sudden tic episode interrupts a quiet room. You can step out, ask for accommodations, or explain it to a classmate."
    elif selected_condition == 3:
        "Widespread pain and fatigue make the next walk across campus feel overwhelming."
    elif selected_condition == 4:
        "Your balance feels less reliable today. You plan an accessible route and consider contacting your care team about changes."
    else:
        "Your glucose device alerts you to a reading that needs attention. You follow your own diabetes care plan."
    menu:
        "Pause and address your immediate needs.":
            $ change_stats(minutes=25, energy=8, water=5)
            "You take time to respond. You may need to adjust the rest of your schedule."
        "Ask a friend or staff member for help with logistics.":
            $ change_stats(minutes=15, energy=5, friends=5)
            "Someone helps you find a quieter place or rearrange your plans."
        "Keep going and try to deal with it after class.":
            $ change_stats(minutes=5, energy=-17, grades=1)
            "You save time now, but your symptoms make the next part of the day harder."
    if energy <= 0:
        jump unseen_ambulance
    if grades < 65:
        jump unseen_dismissal
    if friends <= 0:
        jump unseen_isolation
    return

label unseen_ambulance:
    hide screen unseen_hud
    hide screen unseen_story_sprite
    scene bg evening
    "Your vision fades. When you become aware of your surroundings again, you are in an ambulance."
    "A bystander called 911 after you collapsed. The paramedics are checking on you."
    "GAME OVER — A medical emergency interrupted your semester."
    "In real life, fainting or new severe symptoms deserve appropriate medical evaluation; game energy is not a medical predictor."
    jump unseen_restart

label unseen_dismissal:
    hide screen unseen_hud
    hide screen unseen_story_sprite
    scene bg dorm
    "An academic notice arrives. Under this game's fictional rules, your Grades score fell below 65."
    "GAME OVER — Academic dismissal."
    "Real UMD academic standing follows university policies, not this game's 65-point threshold."
    jump unseen_restart

label unseen_isolation:
    hide screen unseen_hud
    hide screen unseen_story_sprite
    scene bg dorm
    "The messages have stopped. You feel isolated and overwhelmed, and decide you cannot continue the semester as it is."
    "GAME OVER — You withdraw from the semester to seek support and a different path forward."
    "This is a fictional ending. Friendship scores do not determine depression, and support can be found even during isolation."
    jump unseen_restart

label unseen_restart:
    menu:
        "Try again":
            jump start
        "Return to main menu":
            return

# Dialogue positioning: begin text near the top-left, not vertically centered.
init 2 python:
    gui.dialogue_xpos = 38
    gui.dialogue_ypos = 25
