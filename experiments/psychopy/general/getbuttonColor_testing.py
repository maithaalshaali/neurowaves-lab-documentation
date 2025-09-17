"""
PsychoPy hardware test harness for getbuttonColor()

- Live DIN monitor (SPACE to start trials, ESC to quit)
- Responsive UI while hardware waits (worker thread for getbuttonColor)
- In-trial HUD shows raw DIN value + bits in real time
- Robust logging and safe DPx open/close

Requirements:
  pip install psychopy
  pypixxlib installed with your DPx drivers
"""

import sys, os, time, importlib, logging, traceback, threading, queue
from psychopy import visual, event, core
from pypixxlib import _libdpx as dp

# ------------------- LOGGING -------------------
logging.basicConfig(
    level=logging.DEBUG,  # switch to INFO for less verbosity
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("hardware_debug.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
# -----------------------------------------------

# ------------------- CONFIG --------------------
MODULE_NAME = "utilities"      # your module exposing button_mapping + getbuttonColor
TRIAL_TIMEOUT_SEC = 30.0       # set None for infinite
WINDOW_SIZE = (1000, 700)
BG_COLOR = "black"
TEXT_COLOR = "white"
TEXT_HEIGHT = 0.05
WRAP_WIDTH = 1.6
DPX_OPEN_RETRIES = 3
DPX_OPEN_DELAY_S = 1.0
# -----------------------------------------------


# ================== DPx SAFE OPEN/CLOSE ==================
def safe_dpx_open(timeout_s=5.0):
    """Open DPx device with timeout, clear diagnostics, and pre-checks."""
    try:
        logging.info("pypixxlib module: %s", dp.__file__)
        libdir = os.path.dirname(dp.__file__)
        logging.info("DPx DLL directory: %s", libdir)
    except Exception:
        pass

    # If already open, don't open again
    try:
        if hasattr(dp, "DPxIsOpen"):
            is_open = dp.DPxIsOpen()
            logging.info("DPxIsOpen() -> %r", is_open)
            if is_open:
                logging.info("Device already open; skipping DPxOpen()")
                return True
    except Exception as e:
        logging.warning("DPxIsOpen() check failed: %s", e)

    # Run DPxOpen in a worker thread so we can timeout
    q = queue.Queue(maxsize=1)
    def _open():
        try:
            ret = dp.DPxOpen()
            q.put(("ok", ret))
        except Exception as e:
            q.put(("err", e))

    t = threading.Thread(target=_open, daemon=True)
    t.start()

    t0 = time.time()
    while True:
        try:
            status, payload = q.get_nowait()
            if status == "ok":
                logging.info("DPxOpen() OK (ret=%r)", payload)
                return True
            else:
                logging.error("DPxOpen() raised: %s", payload)
                raise RuntimeError(f"DPxOpen failed: {payload}")
        except queue.Empty:
            if time.time() - t0 > timeout_s:
                # Timed out: give actionable advice
                msg = (
                    f"DPxOpen() did not return within {timeout_s:.1f}s.\n"
                    "Tips:\n"
                    "  • Close any other apps using the device (MATLAB, PyPixx, prior Python runs)\n"
                    "  • Power-cycle the DPx box and replug USB (try a direct motherboard port)\n"
                    "  • Reboot Windows if the endpoint is stuck\n"
                    "  • Ensure pypixxlib/driver versions match your firmware\n"
                    "  • If it persists, try a minimal open script to isolate the issue"
                )
                logging.critical(msg)
                raise TimeoutError(msg)
            core.wait(0.05)



def safe_dpx_close():
    try:
        dp.DPxClose()
        logging.info("DPxClose() OK")
    except Exception as e:
        logging.warning("DPxClose() raised: %s", e)


# ================== MODULE LOADING ==================
def load_module(name: str):
    """Import and validate the user module."""
    logging.info("Importing module %s", name)
    # Ensure sibling module is importable even if cwd differs
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    mod = importlib.import_module(name)

    missing = [x for x in ("button_mapping", "getbuttonColor") if not hasattr(mod, x)]
    if missing:
        raise ImportError(f"Module '{name}' missing required exports: {', '.join(missing)}")

    logging.info("Module %s loaded OK", name)
    return mod


# ================== UI HELPERS ==================
def show_text(win, lines, wait_keys=None, allow_esc=True):
    """Render text (multi-line) and optionally wait for keys."""
    if win is None:
        raise RuntimeError("show_text called before a PsychoPy Window was created.")
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


# ================== LIVE DIN MONITOR ==================
def live_monitor(win, decimal_to_binary=None):
    """
    Live DIN viewer before trials. Press SPACE to start, ESC to quit.
    Updates every frame; shows raw decimal and bit string.
    """
    event.clearEvents()
    txt = visual.TextStim(win, height=TEXT_HEIGHT, wrapWidth=WRAP_WIDTH, color=TEXT_COLOR)
    info = visual.TextStim(win, pos=(0, -0.85), height=TEXT_HEIGHT*0.8, color=TEXT_COLOR)
    info.text = "LIVE DIN MONITOR — press SPACE to start trials, ESC to quit"
    while True:
        # Read hardware
        try:
            dp.DPxUpdateRegCache()
            raw = dp.DPxGetDinValue()
            bits = decimal_to_binary(raw) if decimal_to_binary else bin(raw)[2:]
        except Exception as e:
            raw, bits = -1, f"<read error: {e}>"

        # Draw
        txt.text = f"raw: {raw}\nbits: {bits}"
        txt.draw()
        info.draw()
        win.flip()

        keys = event.getKeys(keyList=["space", "escape"])
        if "space" in keys:
            return "start"
        if "escape" in keys:
            return "quit"

        core.wait(0.03)  # ~33 FPS; keeps UI responsive


# ================== WORKER THREAD FOR getbuttonColor ==================
def _spawn_getbutton(mod, selection):
    """Run getbuttonColor(selection) in a worker thread and return a Queue for results."""
    q = queue.Queue(maxsize=1)

    def _target():
        try:
            res = mod.getbuttonColor(selection)
            q.put(("ok", res))
        except Exception as e:
            q.put(("err", e))

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    return q


# ================== TRIAL RUNNER (with HUD) ==================
def run_trial(win, mod, title, selection, timeout=TRIAL_TIMEOUT_SEC):
    event.clearEvents()

    header = visual.TextStim(win, height=TEXT_HEIGHT, color=TEXT_COLOR, wrapWidth=WRAP_WIDTH)
    hud    = visual.TextStim(win, pos=(0, -0.85), height=TEXT_HEIGHT*0.8, color=TEXT_COLOR)
    header.text = f"[{title}]\n\nListening on real hardware…\nPress ESC to abort this trial."

    q = _spawn_getbutton(mod, selection)
    t0 = time.time()
    last_hud = 0.0

    while True:
        # ESC to abort
        if "escape" in event.getKeys(keyList=["escape"]):
            logging.info("Trial '%s' aborted by ESC", title)
            return None

        # Non-blocking result check
        try:
            status, payload = q.get_nowait()
            if status == "ok" and payload:
                logging.info("Detected press: %r", payload)
                return payload  # (box_side, color)
            elif status == "err":
                logging.error("getbuttonColor() raised: %s", payload)
                logging.debug("Traceback (if any) above.")
                show_text(win, [f"Error: {payload}", "", "Press SPACE to continue, ESC to quit."])
                keys = show_text(win, ["Press SPACE to continue, ESC to quit."],
                                 wait_keys=["space"], allow_esc=True)
                if keys and "escape" in keys:
                    return None
                return None
        except queue.Empty:
            pass

        # Timeout
        if timeout is not None and (time.time() - t0) > timeout:
            logging.info("Trial '%s' timed out after %.2fs", title, timeout)
            return None

        # Update HUD ~10 Hz
        now = time.time()
        if now - last_hud > 0.1:
            try:
                dp.DPxUpdateRegCache()
                raw = dp.DPxGetDinValue()
                # Use module's converter if available
                if hasattr(mod, "decimal_to_binary"):
                    bits = mod.decimal_to_binary(raw)
                else:
                    bits = bin(raw)[2:]
                hud.text = f"raw: {raw}   bits: {bits}"
            except Exception as e:
                hud.text = f"<read error: {e}>"
            last_hud = now

        # Draw frame
        header.draw()
        hud.draw()
        win.flip()

        core.wait(0.01)  # smooth events


# ================== MAIN ==================
def main():
    win = None
    try:
        # 1) Open hardware early; fail fast if unavailable
        safe_dpx_open()

        # 2) Load user module (must export button_mapping + getbuttonColor)
        mod = load_module(MODULE_NAME)

        # 3) PsychoPy window
        win = visual.Window(size=WINDOW_SIZE, color=BG_COLOR, units="norm")
        event.clearEvents()

        # 4) Live DIN monitor (real-time). SPACE to start trials, ESC to quit.
        mode = live_monitor(win, decimal_to_binary=getattr(mod, "decimal_to_binary", None))
        if mode == "quit":
            show_text(win, ["Exiting. Press ESC to close."], wait_keys=["escape"])
            return

        # 5) Intro
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
            return

        # 6) Scenarios
        scenarios = [
            ("Right only — green, blue, yellow", {"right box": ["green", "blue", "yellow"]}),
            ("Left only — white, blue, red", {"left box": ["white", "blue", "red"]}),
            ("Both boxes — right(red, green) + left(blue, yellow)",
             {"right box": ["red", "green"], "left box": ["blue", "yellow"]}),
            ("All buttons — both boxes (incl. white)", {
                "right box": ["red", "green", "blue", "yellow", "white"],
                "left box":  ["red", "green", "blue", "yellow", "white"],
            }),
        ]

        # 7) Trials
        for title, selection in scenarios:
            result = run_trial(win, mod, title, selection, timeout=TRIAL_TIMEOUT_SEC)

            if result is None:
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

        # 8) Outro
        show_text(win, ["Done. Press ESC to exit."], wait_keys=["escape"])

    except Exception as e:
        # Fatal error: show it onscreen and log details
        logging.critical("Fatal error: %s", e)
        logging.debug("Traceback:\n%s", traceback.format_exc())
        try:
            if win is None:
                win = visual.Window(size=(800, 400), color=BG_COLOR, units="norm")
            show_text(
                win,
                [
                    "Fatal error — see hardware_debug.log",
                    "",
                    str(e),
                    "",
                    "Press ESC to exit.",
                ],
                wait_keys=["escape"],
                allow_esc=True,
            )
        except Exception:
            pass
    finally:
        if win is not None:
            try:
                win.close()
            except Exception:
                pass
        safe_dpx_close()


if __name__ == "__main__":
    main()
