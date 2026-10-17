init python:
    def unseen_background(filename, tint):
        """Use a supplied background, or a solid-color placeholder."""
        path = "images/" + filename
        if renpy.loadable(path):
            return Transform(Image(path), xysize=(1920, 1080))
        return Solid(tint)

    def unseen_portrait(filename, tint):
        """Use a supplied character portrait, or a colored placeholder."""
        path = "images/" + filename
        if renpy.loadable(path):
            return Transform(Image(path), fit="contain", xysize=(480, 720))
        return Solid(tint, xysize=(420, 640))

    def change_stats(minutes=0, energy=0, water=0, food=0, grades=0, friends=0):
        store.clock += minutes
        for key, delta in (("energy", energy), ("water", water),
            ("food", food), ("grades", grades),
            ("friends", friends)):
            setattr(store, key, max(0, min(100, getattr(store, key) + delta)))
        # Immediately route to an ending whenever a threshold is crossed.
        # These are fictional gameplay thresholds, not medical or university rules.
        if store.energy <= 0:
            renpy.jump("ending_ambulance")
        if store.grades < 65:
            renpy.jump("ending_dismissal")
        if store.friends <= 0:
            renpy.jump("ending_isolation")

    def clock_label():
        hour = (store.clock // 60) % 24
        minute = store.clock % 60
        return "%d:%02d %s" % (hour % 12 or 12, minute, "AM" if hour < 12 else "PM")

image bg dorm = unseen_background("dorm.png", "#EEE6F7")
image bg campus = unseen_background("campus.png", "#E1ECF4")
image bg classroom = unseen_background("classroom.png", "#F2EAF4")
image bg cafe = unseen_background("cafe.png", "#F6E9DC")
image bg library = unseen_background("library.png", "#E6E7F2")
image bg evening = unseen_background("evening.png", "#DCD9F0")
image avatar one = unseen_portrait("avatar1.png", "#D7B8EC")
image avatar two = unseen_portrait("avatar2.png", "#B8DDEB")
image avatar three = unseen_portrait("avatar3.png", "#F3C9C7")
image avatar four = unseen_portrait("avatar4.png", "#D2E6CC")

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
default homework_submitted = 0
default homework_assigned = 0
default test_correct = 0
default test_total = 0
default missed_labs = 0
default late_projects = 0
default campus_support = False
default club_task = False
default conflict_resolved = False
default monday_promise = False
default thursday_deadline = False

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

# Make the default text box readable, without editing screens.rpy.
style window:
    background Solid("#211B2DEB")
    xpadding 68
    ypadding 35

style say_dialogue:
    color "#FFFFFF"
    size 32

style say_label:
    color "#F0CFFF"
    size 31

style choice_button_text:
    color "#FFFFFF"
    hover_color "#F5D6FF"
    size 30

style choice_button:
    background Solid("#352842F2")
    hover_background Solid("#644A7CF2")
    xpadding 32
    ypadding 20



# ========================= UNSEEN: WEEK ONE =========================
# Fictional gameplay: the three loss thresholds are narrative mechanics.
# The Tuesday/Thursday ENEE222 and CMSC216 overlaps in the reference
# calendar are handled as scheduling conflicts, not simultaneous attendance.

label start:
    # Reset the entire run, including when replaying from a game-over screen.
    $ energy = 75
    $ water = 60
    $ food = 80
    $ grades = 85
    $ friends = 50
    $ club_name = "None"
    $ homework_submitted = 0
    $ test_correct = 0
    $ test_total = 0
    $ class_attendance = 0
    $ missed_classes = 0
    $ missed_labs = 0
    $ late_projects = 0
    $ accommodations_requested = False
    $ honest_conversation = False
    $ campus_support = False
    $ club_commitment = 0
    $ club_task = False
    $ monday_promise = False
    $ thursday_deadline = False
    scene bg dorm
    $ day = 1
    $ clock = 480
    "UNSEEN — WEEK ONE"
    "You're starting another week at the University of Maryland while managing POTS, classes, friendships, and the pressure to keep up."
    "Every choice matters. You cannot do everything, and sometimes a reasonable decision has an unexpected cost."
    $ player_name = renpy.input("What is your name?", length=24).strip() or "Alex"
    "Choose a portrait. Your appearance doesn't change your disability or your options."
    menu:
        "Portrait 1":
            $ avatar_choice = 1
        "Portrait 2":
            $ avatar_choice = 2
        "Portrait 3":
            $ avatar_choice = 3
        "Portrait 4":
            $ avatar_choice = 4
    if avatar_choice == 1:
        show avatar one at right
    elif avatar_choice == 2:
        show avatar two at right
    elif avatar_choice == 3:
        show avatar three at right
    else:
        show avatar four at right
    p "Let's see what this week brings."
    hide avatar one
    hide avatar two
    hide avatar three
    hide avatar four
    show screen unseen_hud
    "Your Grades begin at 85. Energy begins at 75, and Friends at 50."
    "GAME RULES: Energy at 0, Grades below 65, or Friends at 0 immediately ends the run."
    "Food and Water influence your energy through choices. They are resources, not medical measurements."
    jump monday

label monday:
    $ day = 1
    $ clock = 480
    scene bg dorm
    "MONDAY — 8:00 AM"
    "Your schedule: CMSC216 discussion at 10; CPBE225 at 11; ENEE222 at 12:30; PHYS161 at 2; and CPBE200 at 6:30."
    "A CMSC216 programming assignment is due tonight. Mira has been trying to make plans with you."
    menu:
        "Finish debugging before breakfast so the assignment is ready.":
            $ change_stats(minutes=85, energy=-13, food=-12, water=-9, grades=4)
            $ homework_submitted += 1
            "The program finally compiles. You leave in a rush."
        "Eat, fill your water bottle, and plan to finish the assignment after class.":
            $ change_stats(minutes=85, energy=7, food=19, water=20, grades=-2)
            $ monday_promise = True
            "You feel more prepared for the morning, but the deadline hasn't moved."
        "Email the TA about a bug, then work for forty minutes and eat something.":
            $ change_stats(minutes=85, energy=-4, food=9, water=10, grades=1)
            $ accommodations_requested = True
            $ monday_promise = True
            "You ask for help. A reply might come before the deadline."
    scene bg classroom
    $ clock = 600
    "10:00 AM — CMSC216 Discussion, ESJ 1309"
    "The TA explains pointers and memory. Your professor expects you to know this for the next assessment."
    menu:
        "Stay for discussion and ask a question afterward.":
            $ class_attendance += 1
            $ change_stats(minutes=55, energy=-12, water=-6, grades=2)
            "The explanation clicks, but you're already running low on time."
        "Take a brief break outside and return for the second half.":
            $ class_attendance += 1
            $ change_stats(minutes=55, energy=-4, grades=0)
            "You miss the first example but stay for the rest."
        "Skip discussion to finish the programming assignment.":
            $ missed_classes += 1
            $ homework_submitted += 1
            $ change_stats(minutes=55, energy=-9, grades=1)
            "The assignment is submitted. You missed the TA's warning about a common exam mistake."
    scene bg campus
    $ clock = 660
    "11:00 AM — CPBE225 Lecture, TWS 0236. ENEE222 begins at 12:30 in KEB 1110."
    "You have fifteen minutes between them, including the trip across campus."
    menu:
        "Attend both lectures and grab food afterward.":
            $ class_attendance += 2
            $ change_stats(minutes=165, energy=-23, food=-15, water=-12, grades=3)
            "You get both sets of notes. You don't get a real lunch break."
        "Attend CPBE225, then eat and arrive late to ENEE222.":
            $ class_attendance += 1
            $ missed_classes += 1
            $ change_stats(minutes=165, energy=-8, food=19, water=12, grades=-3)
            "You miss a key circuit-analysis example."
        "Attend ENEE222 after taking a rest break; miss CPBE225.":
            $ class_attendance += 1
            $ missed_classes += 1
            $ change_stats(minutes=165, energy=8, food=9, water=10, grades=-4)
            "You have energy for circuits but need to catch up on CPBE225."
    scene bg classroom
    $ clock = 840
    "2:00 PM — PHYS161 Lecture, PHY 1410"
    "The professor introduces forces and free-body diagrams."
    menu:
        "Attend and take notes even though you're tired.":
            $ class_attendance += 1
            $ change_stats(minutes=55, energy=-12, grades=2)
        "Sit out the lecture, rest, and request notes from a classmate.":
            $ missed_classes += 1
            $ change_stats(minutes=55, energy=12, friends=2, grades=-3)
            "Your classmate agrees to share notes later."
    scene bg cafe
    $ clock = 960
    "4:00 PM — Mira asks if you can meet before your 6:30 CPBE200 lecture."
    menu:
        "Meet Mira for an hour and talk about the week.":
            $ change_stats(minutes=70, energy=-9, food=9, friends=16)
            "Mira tells you she's been worried you've stopped wanting to hang out."
        "Tell Mira you're overwhelmed and offer a specific time on Friday.":
            $ honest_conversation = True
            $ change_stats(minutes=15, energy=5, friends=7)
            "Mira replies: 'Friday works. Thanks for telling me.'"
        "Ignore the message and focus on the assignment.":
            $ change_stats(minutes=90, energy=-13, friends=-17, grades=3)
            "You make progress. Mira stops texting."
    scene bg classroom
    $ clock = 1110
    "6:30 PM — CPBE200 Lecture, ESJ 1202"
    menu:
        "Attend the evening lecture and take the late trip home.":
            $ class_attendance += 1
            $ change_stats(minutes=75, energy=-15, food=-8, water=-7, grades=2)
        "Go home and review the posted slides tomorrow.":
            $ missed_classes += 1
            $ change_stats(minutes=75, energy=10, grades=-4)
    if monday_promise:
        scene bg dorm
        $ clock = 1260
        "9:00 PM — The CMSC216 assignment is still due."
        menu:
            "Stay up to finish and submit it.":
                $ homework_submitted += 1
                $ change_stats(minutes=150, energy=-23, grades=5)
                "The submission confirmation arrives just before midnight."
            "Submit what you have and get some sleep.":
                $ change_stats(minutes=25, energy=14, grades=-7)
                $ late_projects += 1
                "The assignment is incomplete, but you preserve time for recovery."
            "Ask for a late submission and accept the possibility of a penalty.":
                $ accommodations_requested = True
                $ change_stats(minutes=20, energy=11, grades=-3)
                $ late_projects += 1
                "You send the email. The outcome is uncertain."
    jump tuesday

label tuesday:
    $ day = 2
    $ clock = 540
    scene bg dorm
    "TUESDAY — 9:00 AM"
    "ENEE222 appears at 10:00, overlapping with CMSC216 lecture at 11:00. ENEE244 starts at 2:00, followed by PHYS161 discussion at 4:00."
    "The overlap means you can't fully attend both morning classes."
    menu:
        "Prioritize CMSC216 lecture and ask for ENEE222 notes.":
            $ class_attendance += 1
            $ missed_classes += 1
            $ change_stats(minutes=165, energy=-15, grades=1, friends=2)
            "You keep up with programming, but circuits is harder to follow tonight."
        "Attend ENEE222, leave early, and catch the second half of CMSC216.":
            $ class_attendance += 1
            $ missed_classes += 1
            $ change_stats(minutes=165, energy=-23, grades=2)
            "You cover parts of both, but travel makes it exhausting."
        "Contact both instructors about the conflict and arrange an alternative.":
            $ accommodations_requested = True
            $ campus_support = True
            $ change_stats(minutes=165, energy=-9, grades=0)
            "You begin sorting out the conflict. Not everything is resolved today."
    scene bg classroom
    $ clock = 840
    "2:00 PM — ENEE244 Lecture, CHE 2108"
    "A Boolean-logic exercise appears on the board: What is 1 AND 0?"
    menu:
        "0":
            $ test_correct += 1
            $ change_stats(energy=-7, grades=2)
            "Correct. AND is true only when both inputs are true."
        "1":
            $ change_stats(energy=-7, grades=-2)
            "Not quite. Both inputs must be 1 for AND to output 1."
        "Ask a classmate to explain the truth table.":
            $ change_stats(energy=-7, friends=5, grades=0)
            "You understand it after talking through the table."
    $ test_total += 1
    $ class_attendance += 1
    scene bg classroom
    $ clock = 960
    "4:00 PM — PHYS161 Discussion, PHY 1402"
    "You still have an ENEE222 problem set to complete."
    menu:
        "Attend discussion, then finish the problem set late tonight.":
            $ class_attendance += 1
            $ change_stats(minutes=160, energy=-26, grades=5, food=-11)
            $ homework_submitted += 1
            "You complete both, but it's been a very long day."
        "Attend discussion, then study with Rowan and submit partial work.":
            $ class_attendance += 1
            $ change_stats(minutes=160, energy=-14, grades=-4, friends=13)
            "Rowan helps you understand the formulas. Some answers remain unfinished."
        "Skip discussion and use the time to finish the problem set and rest.":
            $ missed_classes += 1
            $ homework_submitted += 1
            $ change_stats(minutes=160, energy=8, grades=1)
            "You finish the assignment, but need to review the physics problems later."
    scene bg campus
    $ clock = 1140
    "7:00 PM — Rowan invites you to explore student clubs."
    menu:
        "Go to the club fair together.":
            $ change_stats(minutes=60, energy=-11, friends=8)
            jump club_fair
        "Browse clubs online and ask Rowan for recommendations.":
            $ change_stats(minutes=20, energy=6, friends=3)
            jump club_fair
        "Skip clubs for now and catch up on classwork.":
            $ change_stats(minutes=90, energy=-10, grades=3, friends=-7)
            $ club_name = "None"
            jump wednesday

label club_fair:
    "Pick a UMD organization for this week's club storyline. Meeting times are fictionalized for gameplay."
    menu:
        "Technica — organize a technology event.":
            $ club_name = "Technica"
        "Robotics at Maryland — build and test a robot.":
            $ club_name = "Robotics at Maryland"
        "Hack4Impact — build technology for community partners.":
            $ club_name = "Hack4Impact"
        "Terps Racing — collaborate on an engineering build.":
            $ club_name = "Terps Racing"
    $ club_commitment = 1
    $ change_stats(friends=8)
    "You join [club_name]. Your team has a Wednesday meeting and a Friday deliverable."
    jump wednesday

label wednesday:
    $ day = 3
    $ clock = 480
    scene bg dorm
    "WEDNESDAY — 8:00 AM"
    "ENEE244 discussion at 9; CMSC216 discussion at 10; CPBE225 at 11; ENEE222 at 12:30; PHYS161 at 2; and CPBE225 lab at 5."
    "It's the most packed day of your week."
    menu:
        "Prepare food, water, and a plan for breaks before leaving.":
            $ change_stats(minutes=50, energy=8, food=16, water=18, grades=-1)
            "Preparation takes time, but you know where your breaks might fit."
        "Review ENEE244 logic notes until you have to leave.":
            $ change_stats(minutes=50, energy=-9, food=-9, grades=3)
            "You feel ready for discussion but have less room for anything unexpected."
        "Ask a classmate to share notes for one morning session.":
            $ change_stats(minutes=50, energy=5, friends=5, grades=-2)
            $ accommodations_requested = True
            "Your classmate agrees. You'll owe them a favor later."
    scene bg classroom
    $ clock = 540
    "9:00 AM — ENEE244 Discussion, EGR 1110"
    "The TA asks: What is NOT(1)?"
    menu:
        "0":
            $ test_correct += 1
            $ change_stats(energy=-6, grades=2)
            "Correct. NOT flips a Boolean value."
        "1":
            $ change_stats(energy=-6, grades=-2)
            "Not quite. NOT(1) equals 0."
    $ test_total += 1
    $ class_attendance += 1
    scene bg campus
    $ clock = 600
    "10:00 AM — CMSC216 discussion, followed immediately by CPBE225 lecture."
    menu:
        "Attend both and use the short transition to get across campus.":
            $ class_attendance += 2
            $ change_stats(minutes=135, energy=-23, water=-13, grades=3)
            "You get there, but the morning feels relentless."
        "Attend CMSC216 and take a proper break instead of CPBE225.":
            $ class_attendance += 1
            $ missed_classes += 1
            $ change_stats(minutes=135, energy=12, food=10, water=12, grades=-5)
            "You feel more capable afterward, but CPBE225 notes are missing."
        "Skip CMSC216, attend CPBE225, and use the first hour to recover.":
            $ missed_classes += 1
            $ class_attendance += 1
            $ change_stats(minutes=135, energy=9, food=7, grades=-3)
            "You make the later class and plan to catch up on programming."
    scene bg classroom
    $ clock = 750
    "12:30 PM — ENEE222 Lecture, KEB 1110; PHYS161 follows at 2:00."
    "You have a short window to eat, and Mira wants to know if Friday plans are still happening."
    menu:
        "Attend both classes and postpone lunch.":
            $ class_attendance += 2
            $ change_stats(minutes=150, energy=-23, food=-19, water=-14, grades=4, friends=-5)
            "You keep up academically. Mira's message remains unanswered."
        "Eat with Mira, attend physics, and miss circuits.":
            $ class_attendance += 1
            $ missed_classes += 1
            $ change_stats(minutes=150, energy=-7, food=18, water=12, grades=-6, friends=13)
            "Mira seems relieved. You need to catch up on ENEE222."
        "Attend circuits, then take a recovery break instead of physics.":
            $ class_attendance += 1
            $ missed_classes += 1
            $ change_stats(minutes=150, energy=8, food=7, water=10, grades=-4)
            "You preserve some capacity for the evening lab."
    scene bg classroom
    $ clock = 1020
    "5:00 PM — CPBE225 Lab, TWS 0320"
    "Your lab partner is counting on you to help collect data."
    menu:
        "Stay for the full lab and finish the analysis tonight.":
            $ class_attendance += 1
            $ homework_submitted += 1
            $ change_stats(minutes=140, energy=-25, grades=7, friends=3)
            "You complete the lab report, but the late finish costs you."
        "Ask your partner to divide the work and complete your portion later.":
            $ class_attendance += 1
            $ change_stats(minutes=100, energy=-13, grades=2, friends=7)
            $ thursday_deadline = True
            "Your partner agrees, but expects your section by tomorrow."
        "Leave early without discussing it with your partner.":
            $ missed_labs += 1
            $ change_stats(minutes=50, energy=12, grades=-12, friends=-15)
            "Your partner is upset and the lab grade takes a serious hit."
    if club_name != "None":
        scene bg campus
        $ clock = 1200
        "8:00 PM — Your [club_name] team has a meeting."
        menu:
            "Attend and promise to deliver a substantial task by Friday.":
                $ club_task = True
                $ club_commitment += 2
                $ change_stats(minutes=90, energy=-20, friends=12)
                "Your team is excited. Your to-do list grows."
            "Join remotely for a short check-in and accept a smaller task.":
                $ club_task = True
                $ club_commitment += 1
                $ change_stats(minutes=35, energy=-6, friends=6)
                "You contribute without staying for the full meeting."
            "Explain that today's lab ran late and decline this meeting.":
                $ change_stats(minutes=10, energy=6, friends=-4)
                "The organizer understands, though you miss the team discussion."
    jump thursday

label thursday:
    $ day = 4
    $ clock = 540
    scene bg dorm
    "THURSDAY — 9:00 AM"
    "ENEE222 lab at 10:00 overlaps with CMSC216 lecture at 11:00. ENEE244 lecture begins at 2:00."
    "Tomorrow brings a PHYS161 quiz and project deadlines."
    if thursday_deadline:
        "Your CPBE225 lab partner messages: 'Can you send your part of the analysis this morning?'"
        menu:
            "Finish your section before class, even if you're rushed.":
                $ homework_submitted += 1
                $ change_stats(minutes=75, energy=-16, grades=5, friends=5)
                "Your partner thanks you."
            "Explain that you need an extra day and offer to revise their section too.":
                $ change_stats(minutes=15, grades=-4, friends=2)
                "Your partner reluctantly agrees."
            "Leave the message unanswered and focus on the morning lab.":
                $ change_stats(minutes=10, grades=-7, friends=-16)
                "Your partner submits without your section."
    scene bg classroom
    $ clock = 600
    "10:00 AM — ENEE222 Lab, KEB 2107"
    "You cannot fully attend this lab and the overlapping CMSC216 lecture."
    menu:
        "Complete the lab and arrange to catch up on CMSC216.":
            $ class_attendance += 1
            $ missed_classes += 1
            $ change_stats(minutes=115, energy=-23, grades=6)
            "Your lab results are submitted, but you miss lecture examples."
        "Attend CMSC216 and accept the missed ENEE222 lab penalty.":
            $ class_attendance += 1
            $ missed_labs += 1
            $ change_stats(minutes=115, energy=-15, grades=-13)
            "You understand the programming lecture. The lab penalty is substantial."
        "Contact the instructors about the overlap and request a makeup arrangement.":
            $ campus_support = True
            $ accommodations_requested = True
            $ change_stats(minutes=115, energy=-9, grades=-2)
            "The request is documented, but approval is not automatic."
    scene bg classroom
    $ clock = 840
    "2:00 PM — ENEE244 Lecture, CHE 2108"
    "You have a digital-logic quiz coming up."
    menu:
        "Attend and work through the examples with a classmate.":
            $ class_attendance += 1
            $ change_stats(minutes=75, energy=-13, grades=3, friends=4)
        "Attend, then leave promptly for a break.":
            $ class_attendance += 1
            $ change_stats(minutes=75, energy=-8, grades=1)
        "Miss lecture to prepare for tomorrow's physics quiz.":
            $ missed_classes += 1
            $ change_stats(minutes=75, energy=-7, grades=-5)
            $ friday_test_preparation += 3
    scene bg library
    $ clock = 1080
    "6:00 PM — Rowan invites you to a study group. Mira has also asked whether you're free for dinner."
    menu:
        "Study with Rowan and turn down dinner with an explanation.":
            $ honest_conversation = True
            $ friday_test_preparation += 4
            $ change_stats(minutes=110, energy=-14, grades=3, friends=1)
            "Mira wishes you luck on the quiz."
        "Go to dinner with Mira and study briefly afterward.":
            $ friday_test_preparation += 1
            $ change_stats(minutes=120, energy=-12, food=17, friends=17)
            "You feel connected, but less prepared for tomorrow."
        "Study alone and ignore both messages.":
            $ friday_test_preparation += 5
            $ change_stats(minutes=130, energy=-20, grades=4, friends=-19)
            "You cover the most material. Both friends feel pushed away."
        "Take a restorative evening and send honest updates to both friends.":
            $ honest_conversation = True
            $ change_stats(minutes=80, energy=19, food=11, water=12, friends=4, grades=-2)
            "You won't finish all the review, but you make a plan for tomorrow."
    jump friday

label friday:
    $ day = 5
    $ clock = 540
    scene bg dorm
    "FRIDAY — 9:00 AM"
    "Your only scheduled class is PHYS161 lecture at 2:00 PM, but you have a physics quiz and looming project responsibilities."
    "Mira asks whether you still want to meet."
    menu:
        "Spend the morning preparing for physics and skip breakfast with Mira.":
            $ friday_test_preparation += 4
            $ change_stats(minutes=130, energy=-18, food=-13, friends=-8, grades=2)
            "Your review is thorough. Mira sounds disappointed."
        "Meet Mira for breakfast and review notes afterward.":
            $ friday_test_preparation += 1
            $ change_stats(minutes=130, energy=-6, food=18, water=12, friends=15)
            "You laugh together, then rush through the final practice problems."
        "Take a quiet morning, eat, and prepare for the quiz in shorter blocks.":
            $ friday_test_preparation += 2
            $ change_stats(minutes=130, energy=11, food=15, water=15, friends=0)
            "You don't review everything, but you arrive with a workable plan."
    scene bg classroom
    $ clock = 840
    "2:00 PM — PHYS161 Lecture, PHY 1410"
    "Your quiz begins. These questions count toward your Grades score."
    $ class_attendance += 1
    $ change_stats(minutes=45, energy=-9)
    "Question 1: A 2 kg object accelerates at 3 m/s². What is the net force?"
    menu:
        "6 N":
            $ test_correct += 1
            $ change_stats(grades=5)
            "Correct. F = ma = 6 N."
        "1.5 N":
            $ change_stats(grades=-7)
            "Not quite. Multiply mass by acceleration."
        "9 N":
            $ change_stats(grades=-7)
            "Not quite. F = ma."
    $ test_total += 1
    "Question 2: A car moves at constant velocity. What is its net force?"
    menu:
        "Zero":
            $ test_correct += 1
            $ change_stats(grades=5)
            "Correct. Constant velocity means zero acceleration."
        "Equal to its mass":
            $ change_stats(grades=-7)
            "Not quite. Mass and force are different quantities."
        "Increasing over time":
            $ change_stats(grades=-7)
            "Not quite. Constant velocity requires no net force."
    $ test_total += 1
    "Question 3: A 10 N force acts right and a 4 N force acts left. What is the net force?"
    menu:
        "6 N right":
            $ test_correct += 1
            $ change_stats(grades=5)
            "Correct. The opposing forces subtract."
        "14 N right":
            $ change_stats(grades=-7)
            "Not quite. The forces point in opposite directions."
        "6 N left":
            $ change_stats(grades=-7)
            "The magnitude is right, but the larger force points right."
    $ test_total += 1
    "The quiz ends. You leave class wondering how the week added up."
    if club_task:
        scene bg campus
        $ clock = 990
        "4:30 PM — Your [club_name] organizer asks for the task you promised."
        menu:
            "Finish it now, even if you miss plans with Mira.":
                $ club_commitment += 2
                $ change_stats(minutes=130, energy=-23, grades=1, friends=-12)
                "Your team appreciates the work. Mira waited for you."
            "Ask the organizer to share the task and offer a partial deliverable.":
                $ club_commitment += 1
                $ change_stats(minutes=75, energy=-10, friends=6)
                "The team adapts. You still have some work to do."
            "Disappear and leave the task unfinished.":
                $ change_stats(minutes=10, energy=6, friends=-21)
                "The organizer has to scramble to cover your commitment."
    scene bg evening
    $ clock = 1140
    "7:00 PM — The week is finally over."
    "The choices you made shaped more than your calendar."
    jump weekly_reflection

label weekly_reflection:
    scene bg dorm
    "WEEK ONE — REFLECTION"
    "Classes attended: [class_attendance]. Missed class sessions: [missed_classes]. Missed labs: [missed_labs]."
    "Assignments completed or submitted: [homework_submitted]. Quiz questions answered correctly: [test_correct] out of [test_total]."
    if club_name != "None":
        "You joined [club_name] and earned [club_commitment] club contribution points."
    else:
        "You didn't join a club this week. You used that time for other priorities."
    if honest_conversation:
        "You had an honest conversation about your limits. Someone understood more than they did before."
    else:
        "Some of your friends still don't know what you're managing. That may shape next week's relationships."
    if campus_support:
        "You asked for help with a real scheduling conflict. Advocating for yourself was part of your academic work."
    if energy < 25:
        "You're ending the week with very little energy. Your next chapter would need to account for that."
    "Final Grades: [grades]/100. Final Friends: [friends]/100. Energy: [energy]/100."
    "You made it through Week One. That doesn't mean every choice was easy or every outcome was fair."
    "WEEK ONE COMPLETE — This is the successful ending for the prototype."
    menu:
        "Replay and make different choices":
            jump start
        "Return to the main menu":
            return

label ending_ambulance:
    hide screen unseen_hud
    scene bg evening
    "The sounds around you blur. You lose consciousness."
    "When you open your eyes, you're in an ambulance. A bystander called 911 after you fainted."
    "A paramedic tells you that you're being evaluated. You think about the demands of the week and how difficult it was to find room for recovery."
    "GAME OVER — AMBULANCE ENDING"
    "In this fictional game, Energy reaching zero triggers this ending. Real fainting cannot be predicted by a game meter."
    menu:
        "Try again":
            jump start
        "Main menu":
            return

label ending_dismissal:
    hide screen unseen_hud
    scene bg dorm
    "A university notice arrives. Your academic standing has fallen below the threshold used in this game's fictional rules."
    "The notice says that you have been academically dismissed. You stare at the screen, thinking about missed labs, deadlines, and impossible overlaps."
    "GAME OVER — ACADEMIC DISMISSAL"
    "This is a fictional rule for Unseen, not UMD's real academic dismissal policy."
    menu:
        "Try again":
            jump start
        "Main menu":
            return

label ending_isolation:
    hide screen unseen_hud
    scene bg dorm
    "Messages have stopped coming. You feel painfully isolated, and your mood has worsened over the week."
    "You find it difficult to get out of bed or face another day on campus. You decide you cannot continue the semester as things are."
    "The chapter ends here, but the character's story does not have to. Reaching out for support and reconnecting are possible next steps."
    "GAME OVER — ISOLATION ENDING"
    "The Friends score is a fictional relationship mechanic, not a measure of depression or a person's worth."
    menu:
        "Try again":
            jump start
        "Main menu":
            return
