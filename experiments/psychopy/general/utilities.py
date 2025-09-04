from pypixxlib._libdpx import DPxOpen, DPxClose, DPxWriteRegCache, DPxUpdateRegCache, DPxGetTime, DPxStopDinLog, DPxGetDinValue


trigger_channels_dictionary = {
    224: 4,
    225: 16,
    226: 64,
    227: 256,
    228: 1024,
    229: 4096,
    230: 16384,
    231: 65536
}

def decimal_to_binary(decimal_number):
    """
    Converts a decimal number to its binary representation.

    Parameters:
        decimal_number (int): The decimal number to convert.

    Returns:
        str: A string representing the binary equivalent of the decimal number.
    """
    if decimal_number < 0:
        raise ValueError("The number should be non-negative.")
    return bin(decimal_number)[2:]




# --- mapping (all lowercase), now with DISTINCT whites per box ---
# NOTE: Update the integers below to match your actual hardware wiring.
#       The example uses:
#         - right white  -> response=5,  listen_to=5
#         - left  white  -> response=10, listen_to=10
button_mapping = {
    "right box": {
        "red":    {"response": 9,  "listen_to": 1},
        "green":  {"response": 7,  "listen_to": 3},
        "blue":   {"response": 6,  "listen_to": 4},
        "yellow": {"response": 8,  "listen_to": 2},
        "white":  {"response": 5,  "listen_to": 5},   # <- set per your wiring
    },
    "left box": {
        "red":    {"response": 4,  "listen_to": 6},
        "green":  {"response": 2,  "listen_to": 8},
        "blue":   {"response": 1,  "listen_to": 9},
        "yellow": {"response": 3,  "listen_to": 7},
        "white":  {"response": 10, "listen_to": 10},  # <- set per your wiring
    }
}

from collections import defaultdict

# --- internal helpers built from the mapping ---
# (box,color) -> listen_to code
_PAIR_TO_LISTEN = {
    (box, color): info["listen_to"]
    for box, colors in button_mapping.items()
    for color, info in colors.items()
}
# response code -> list of (box,color) pairs (handles any shared lines, if any)
_RESP_TO_PAIRS = defaultdict(list)
for _box, _colors in button_mapping.items():
    for _color, _info in _colors.items():
        _RESP_TO_PAIRS[_info["response"]].append((_box, _color))
_RESP_TO_PAIRS = dict(_RESP_TO_PAIRS)

# sets of valid codes from the mapping
_ALL_RESPONSE_CODES = sorted(_RESP_TO_PAIRS.keys())                 # e.g. [1,2,3,4,5,6,7,8,9,10]
_ALL_LISTEN_CODES   = sorted({_PAIR_TO_LISTEN[p] for p in _PAIR_TO_LISTEN})  # may differ from responses
_VPIXX_REGISTER_SIZE     = 24


def _norm_box(s: str) -> str:
    """Normalize and validate a box name.

    Args:
      s: Raw box string (e.g., 'Right Box', 'left box').

    Returns:
      str: Normalized box string (lowercase).

    Raises:
      ValueError: If the box name is unknown.
    """
    s = s.strip().lower()
    if s not in button_mapping:
        raise ValueError(f"Unknown box: {s!r}. Use 'right box' or 'left box'.")
    return s


def _norm_color(box: str, c: str) -> str:
    """Normalize and validate a color for a given box.

    Args:
      box: Normalized box name ('right box' or 'left box').
      c: Raw color string (e.g., 'Green', 'blue', 'WHITE').

    Returns:
      str: Normalized color string (lowercase).

    Raises:
      ValueError: If the color is not defined for the given box.
    """
    c = c.strip().lower()
    if c not in button_mapping[box]:
        raise ValueError(f"Unknown color for {box}: {c!r}.")
    return c


def _normalize_selection(selection: dict | None):
    """Normalize the grouped selection into pairs and listen codes.

    Args:
      selection: Grouped selection dict like:
        {
          "right box": ["green", "blue", "yellow"],
          "left box":  ["white", "blue", "red"]
        }
        If None, listens to all defined buttons.

    Returns:
      tuple[list[tuple[str, str]], list[int]]: A tuple (listen_pairs, listen_codes) where:
        * listen_pairs: list of normalized (box, color) tuples.
        * listen_codes: sorted list of hardware listen_to integers.
    """
    if selection is None:
        listen_pairs = list(_PAIR_TO_LISTEN.keys())
    else:
        listen_pairs = []
        for raw_box, colors in selection.items():
            box = _norm_box(raw_box)
            if not colors:
                continue
            for c in colors:
                color = _norm_color(box, c)
                listen_pairs.append((box, color))

    # Deduplicate while preserving order and build codes.
    listen_pairs = list(dict.fromkeys(listen_pairs))
    listen_codes = sorted({_PAIR_TO_LISTEN[p] for p in listen_pairs})
    return listen_pairs, listen_codes


def getbuttonColor(selection: dict | None = None):
    """
    Poll the inputs like `getbutton`, but return (box, color).
    Honors the mapping (including distinct whites) and an optional grouped
    `selection` filter of the form:
        {
          "right box": ["green", "blue"],
          "left box":  ["red"]
        }
    """
    listen_pairs, _listen_codes = _normalize_selection(selection)  # keep selection, ignore listen codes

    while True:
        DPxUpdateRegCache()
        raw = DPxGetDinValue()
        bits = decimal_to_binary(raw)

        # Ensure we can index up to the largest response bit (handles short strings)
        # if len(bits) < _VPIXX_REGISTER_SIZE:
        #     bits = bits.zfill(_VPIXX_REGISTER_SIZE)

        # --- replicate getbutton logic over the full response range ---
        # Build an array for codes 1.._MAX_BIT_NEEDED where index 0 -> code 1 (LSB)
        button_box = [int(bit) for bit in bits[-10:]]

        # Only consider response codes that exist in the mapping
        resp_codes = [i + 1 for i, state in enumerate(button_box)
                      if state == 1 and (i + 1) in _ALL_RESPONSE_CODES]

        # Return only when a single response line is high, matching getbutton semantics
        if len(resp_codes) == 1:
            resp = resp_codes[0]

            # Map response code -> (box,color) candidates from the mapping
            candidates = _RESP_TO_PAIRS.get(resp, [])

            # If a selection was provided, intersect with it
            if selection is not None:
                candidates = [p for p in candidates if p in listen_pairs]

            if len(candidates) == 1:
                # Same return shape as before: (box_side, color)
                return candidates[0]

            if len(candidates) > 1:
                # This mirrors the "single line pressed" assumption—if hardware lines are shared,
                # the selection filter should disambiguate; otherwise we raise.
                raise RuntimeError(
                    "Ambiguous press: multiple (box,color) share this hardware line: "
                    + ", ".join(f"{b}/{c}" for b, c in candidates)
                )
        # else: 0 or >1 responses high → keep polling






def getbutton(buttons=None):
    # buttons is an array or None
    # if buttons is an array it contains the code number of the button we want
    # Updated table 13-01-2025 tested

    # RIGHT BOX

        # Red button:
            # return response = 9   (this is the value returned by the getbutton or listenbutton function)
            # buttons array set to = 1     (add this number to the buttons array in order to listen to it)

        # Green button:
            # return response = 7
            # listen to = 3

        # Blue button:
            # return response = 6
            # listen to = 4

        # Yellow button:
            # return response = 8
            # listen to = 2


    # Left Box

        # Red button:
            # return response = 4
            # listen to = 6

        # Green button:
            # return response = 2
            # listen to = 8

        # Blue button:
            # return response = 1
            # listen to = 9

        # Yellow button:
            # return response = 3
            # listen to = 7

    if buttons == None:

        while True:
            DPxUpdateRegCache()
            value = DPxGetDinValue()
            #print(decimal_to_binary(value))
            value = decimal_to_binary(value)
            # The final 8 values should correspond to the button presses

            # Check if any relevant button is pressed
            if (value[-1] == '1' or value[-2] == '1' or value[-3] == '1' or
                    value[-4] == '1' or value[-6] == '1' or value[-7] == '1' or
                    value[-8] == '1' or value[-9] == '1'):

                # Extract button box states
                button_box = [
                    int(value[-9 + i_but]) for i_but in range(9)
                ]

                # Find which button was pressed
                resp = [i + 1 for i, state in enumerate(button_box) if state == 1]



                # If only one button is pressed, return the result
                if len(resp) == 1:
                    return resp[0]
    else:

        neg_buttons = [-x for x in buttons]
        print(neg_buttons)
        while True:

            DPxUpdateRegCache()
            value = DPxGetDinValue()
            # print(decimal_to_binary(value))
            value = decimal_to_binary(value)
            # The final 8 values should correspond to the button presses
            #print(value)
            if any(value[x] == '1' for x in neg_buttons):

                # Extract button box states
                button_box = [
                    int(value[-9 + i_but]) for i_but in range(9)
                ]

                # Find which button was pressed
                resp = [i + 1 for i, state in enumerate(button_box) if state == 1]

                # If only one button is pressed, return the result
                if len(resp) == 1:
                    return resp[0]



def listenbutton(keycode):

    # Updated table 21-11-2024 tested
    # RIGHT BOX
    # 9  RED
    # 7  GREEN
    # 6 BLUE
    # 8 Yellow

    # Left Box
    # 4 RED
    # 2 Green
    # 1 Blue
    # 3 Yellow

    # Keycode is one of the above numbers that correspond to the button we want to listen to

    while True:
        DPxUpdateRegCache()
        value = DPxGetDinValue()
        #print(decimal_to_binary(value))
        value = decimal_to_binary(value)
        # The final 8 values should correspond to the button presses

        # Check if any relevant button is pressed
        if (value[-1] == '1' or value[-2] == '1' or value[-3] == '1' or
                value[-4] == '1' or value[-6] == '1' or value[-7] == '1' or
                value[-8] == '1' or value[-9] == '1'):

            # Extract button box states
            button_box = [
                int(value[-9 + i_but]) for i_but in range(9)
            ]

            # Find which button was pressed
            resp = [i + 1 for i, state in enumerate(button_box) if state == 1]

            # If only one button is pressed, return the result
            if len(resp) == 1 and resp[0]==keycode:
                return resp[0]

