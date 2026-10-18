"""
ask.py - a blocking question dialog with any number of buttons.

    from ask import ask

    answer = ask("Are you sure?", ["Yes", "No"])
    if answer == "Yes":
        ...

Like input(), ask() blocks until the user answers, then returns the label of
the button they chose. If the window is closed (or Escape is pressed) it
returns `cancel`, which defaults to None.

Standalone: uses only tkinter from the standard library.

Keyboard: Left/Right/Tab move between buttons, Enter/Space presses the
focused one, 1-9 press the matching button, Escape cancels.
"""

import tkinter as tk
from tkinter import ttk

__all__ = ["ask"]


def ask(question, options=("OK",), *, title="", default=0, cancel=None,
        max_per_row=4, wraplength=360):
    """Show a modal dialog and return the label of the clicked button.

    question     -- text to display (may be multi-line)
    options      -- sequence of button labels, shown left to right
    title        -- window title (default: empty)
    default      -- index of the button that starts focused (Enter presses it)
    cancel       -- value returned if the dialog is closed or Escape is hit
    max_per_row  -- buttons wrap onto additional rows after this many
    wraplength   -- pixel width at which the question text wraps
    """
    labels = [str(o) for o in options]
    if not labels:
        raise ValueError("ask() needs at least one option")
    if not 0 <= default < len(labels):
        default = 0

    # Reuse an existing Tk app if there is one; otherwise make our own window.
    parent = tk._default_root
    win = tk.Toplevel(parent) if parent else tk.Tk()
    win.title(title)
    win.resizable(False, False)

    result = [cancel]

    def choose(value):
        result[0] = value
        win.destroy()

    frame = ttk.Frame(win, padding=20)
    frame.grid(sticky="nsew")

    ttk.Label(frame, text=str(question), wraplength=wraplength,
              justify="left").grid(row=0, column=0, pady=(0, 16), sticky="w")

    button_area = ttk.Frame(frame)
    button_area.grid(row=1, column=0)

    buttons = []
    for i, label in enumerate(labels):
        btn = ttk.Button(button_area, text=label,
                         command=lambda lab=label: choose(lab))
        btn.grid(row=i // max_per_row, column=i % max_per_row,
                 padx=4, pady=3, sticky="ew")
        buttons.append(btn)

    def move_focus(step):
        current = win.focus_get()
        idx = buttons.index(current) if current in buttons else default
        buttons[(idx + step) % len(buttons)].focus_set()

    def press_focused(_event=None):
        current = win.focus_get()
        if current in buttons:
            current.invoke()
        return "break"

    win.bind("<Left>", lambda e: move_focus(-1))
    win.bind("<Right>", lambda e: move_focus(1))
    win.bind("<Return>", press_focused)
    win.bind("<KP_Enter>", press_focused)
    win.bind("<Escape>", lambda e: choose(cancel))
    win.protocol("WM_DELETE_WINDOW", lambda: choose(cancel))
    for i in range(min(9, len(buttons))):
        win.bind(str(i + 1), lambda e, b=buttons[i]: b.invoke())

    # Center on screen, bring to front, focus the default button.
    win.update_idletasks()
    w, h = win.winfo_reqwidth(), win.winfo_reqheight()
    x = (win.winfo_screenwidth() - w) // 2
    y = (win.winfo_screenheight() - h) // 3
    win.geometry(f"+{x}+{y}")
    win.lift()
    win.attributes("-topmost", True)
    win.after(200, lambda: win.attributes("-topmost", False))
    buttons[default].focus_force()

    if parent:
        win.transient(parent)
        win.grab_set()

    win.wait_window(win)  # blocks until the dialog is destroyed
    return result[0]

