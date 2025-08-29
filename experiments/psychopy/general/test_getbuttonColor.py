"""
PsychoPy hardware test harness for getbuttonColor()

This script opens a PsychoPy window and runs multiple scenarios against your
real hardware-backed getbuttonColor() function. It shows on-screen instructions,
waits for a press, reports the result, and proceeds between trials.

Requirements:
  - PsychoPy installed:  pip install psychopy
  - Your module must export:
      - button_mapping: dict
      - getbuttonColor(selection: dict | None) -> tuple[str, str]
  - Your module handles hardware polling internally (DPx* + decimal_to_binary).

Controls:
  - Press ESC anytime to abort the current trial or exit at prompts.
  - Press SPACE to advance after each result screen.

Usage:
  python test_getbutton_psychopy_hardware.py
"""

from psychopy import visual, event
import time
import importlib

# ------------------- CONFIG -------------------
MODULE_NAME = "your_module_name"  # e.g., "buttons" if buttons.py has your function
TRIAL_TIMEOUT_SEC = 30.0          # Per-trial timeout; set to None to wait indefinitely
WINDOW_SIZE = (1000, 700)
BG_COLOR = "black"
TEXT_COLOR = "white"
TEXT_HEIGHT = 0.05
WRAP_WIDTH = 1.6
# ----------------------------------------------


def load_module(name: str):
    """Import and validate the user module."""
    mod = importlib.import_module(name)
    if not hasattr(mod, "button_mapping") or not hasattr(mod, "getbuttonColor"):
        raise ImportError(
            f"Module '{name}' must export 'button_mapping' and 'getbuttonColor'."
        )
    return mod


def show_text(win, lines, wait_keys=None, allow_esc=True):
    """Render lines of text and optionally wait for keys.

    Args:
        win: PsychoPy Window.
        lines: List of strings to display (one per line).
        wait_keys: Optional list of keys to wait for (e.g., ['space']).
        allow_esc: If True, returns 'escape' when ESC is pressed while waiting.

    Returns:
        List of keys pressed if waiting; otherwise None.
    """
    txt = "\n".join(lines)
    stim = visual.TextStim(
        win, text=txt, height=TEXT_HEIGHT, wrapWidth=WRAP_WIDTH, color=TEXT_COLOR
    )
    stim.draw()
    win.flip()
    if wait_keys is not None:
        while True:
            keys = event.waitKeys(keyList=wait_keys + (["escape"] if allow_esc else []))
            if "escape" in keys:
                return ["escape"]
            return keys


def run_trial(win, mod, title, selection, timeout=TRIAL_TIMEOUT_SEC):
    """Run a single listening trial using real hardware.

    Args:
        win: PsychoPy Window.
        mod: Imported user module (with getbuttonColor).
        title: Title text shown on screen.
        selection: Dict selection for getbuttonColor, e.g.:
            {"right box": ["green", "blue"], "left box": ["red"]}
            or None to listen to all.
        timeout: Seconds to wait before aborting the trial (None waits forever).

    Returns:
        tuple[str, str] on success, or None on timeout/abort.
    """
    start_lines = [
        f"[{title}]",
        "",
        "The system is now listening on the real hardware.",
        "Press a configured button. ESC to abort this trial.",
    ]
    show_text(win, start_lines)

    t0 = time.time()
    while True:
        # Abort on ESC (non-blocking)
        if "escape" in event.getKeys(keyList=["escape"]):
            return None

        try:
            # Your function blocks internally until a valid press is detected.
            # If you want a hard timeout, enforce it externally with elapsed time.
            if timeout is not None and (time.time() - t0) > timeout:
                return None

            result = mod.getbuttonColor(selection)
            if result:
                return result
        except Exception as e:
            # Show error and halt this trial
            show_text(
                win,
                [f"Error: {e}", "", "Press SPACE to continue to the next trial, ESC to quit."],
            )
            keys = show_text(win, ["Press SPACE to continue, ESC to quit."], wait_keys=["space"], allow_esc=True)
            if keys and "escape" in keys:
                return None
            return None  # proceed to next scenario


def main():
    """Open PsychoPy window and run several hardware scenarios."""
    mod = load_module(MODULE_NAME)
    win = visual.Window(size=WINDOW_SIZE, color=BG_COLOR, units="norm")

    # Intro
    keys = show_text(
        win,
        [
            "getbuttonColor() — Hardware Test",
            "",
            f"Module: {MODULE_NAME}",
            f"Timeout per trial: {TRIAL_TIMEOUT_SEC if TRIAL_TIMEOUT_SEC else '∞'} sec",
            "",
            "Press SPACE to start, ESC to quit.",
        ],
        wait_keys=["space"],
        allow_esc=True,
    )
    if keys and "escape" in keys:
        win.close()
        return

    # Define scenarios
    scenarios = [
        (
            "Right only — green, blue, yellow",
            {"right box": ["green", "blue", "yellow"]},
        ),
        (
            "Left only — white, blue, red",
            {"left box": ["white", "blue", "red"]},
        ),
        (
            "Both boxes — right(red, green) + left(blue, yellow)",
            {"right box": ["red", "green"], "left box": ["blue", "yellow"]},
        ),
        (
            "All buttons — both boxes (incl. white)",
            {
                "right box": ["red", "green", "blue", "yellow", "white"],
                "left box":  ["red", "green", "blue", "yellow", "white"],
            },
        ),
    ]

    # Run scenarios
    for title, selection in scenarios:
        result = run_trial(win, mod, title, selection, timeout=TRIAL_TIMEOUT_SEC)
        if result is None:
            # Trial aborted or timed out
            keys = show_text(
                win,
                [
                    f"[{title}]",
                    "",
                    "No button detected (aborted or timed out).",
                    "Press SPACE for next trial, ESC to quit.",
                ],
                wait_keys=["space"],
                allow_esc=True,
            )
            if keys and "escape" in keys:
                break
            continue

        box_side, color = result
        keys = show_text(
            win,
            [
                f"[{title}]",
                "",
                f"Detected: {color} on {box_side}",
                "",
                "Press SPACE for next trial, ESC to quit.",
            ],
            wait_keys=["space"],
            allow_esc=True,
        )
        if keys and "escape" in keys:
            break

    # Outro
    show_text(win, ["Done. Press ESC to exit."], wait_keys=["escape"])
    win.close()


if __name__ == "__main__":
    main()
