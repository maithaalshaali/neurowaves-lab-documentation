import os
import re

import mne
import pandas as pd
import numpy as np

# ----------------------------------------------------------------------------
# 1) CONFIGURATION
# ----------------------------------------------------------------------------

import sys

class Tee(object):
    def __init__(self, *files):
        self.files = files

    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()  # optional: ensure real-time writing

    def flush(self):
        for f in self.files:
            f.flush()




BASE_DIR = r"C:\Users\hz3752\Box\MEG\Data\masked-priming-english"

# Threshold for detecting an analog pulse in the MISC channels
TRIGGER_THRESHOLD = 0.2

# Desired intervals (seconds)
EXPECTED_MASK_TO_PRIME = 0.5
EXPECTED_PRIME_TO_TARGET = 0.05
# If you want to check target duration, see below

# Tolerances around the expected intervals (e.g. ±50 ms, ±10 ms, etc.)
TOL_MASK_TO_PRIME = 0.01  # ±10 ms tolerance
TOL_PRIME_TO_TARGET = 0.01  # ±10 ms tolerance

def find_sessions(base_dir):
    """
    Recursively walks the base directory to find MEG sessions and
    returns a list of dictionaries containing session info:
      {
        'subject': <subject directory name>,
        'session': <session directory name>,
        'con_file': <path to .con file>,
        'csv_file': <path to the main CSV file>,
      }
    """
    session_info_list = []

    # We’ll match sub-* / ses-*/ type paths, but you can adapt if your naming differs:
    # e.g., sub-pilot_testing, ses-001_squid, etc.
    subject_pattern = re.compile(r"^sub-(.+)$")
    session_pattern = re.compile(r"^ses-(.+)$")

    for root, dirs, files in os.walk(base_dir):
        # Identify the subject folder name (sub-XXX) and session folder name (ses-XXX) in the path
        path_parts = root.split(os.sep)

        # We only care if there's at least a subject and session in the path
        if len(path_parts) < 2:
            continue

        # Try to find "sub-xxx" / "ses-xxx" in path
        subject_match = None
        session_match = None

        # We'll look for sub- and ses- in the path
        for part in path_parts:
            if subject_pattern.match(part):
                subject_match = part
            elif session_pattern.match(part):
                session_match = part

        if not (subject_match and session_match):
            # Not in a BIDS-like sub-*/ses-* directory
            continue

        # We know we are inside a sub-.../ses-... path, but
        # we only want to capture the correct files:
        #   1) <something>.con in a 'meg-kit' folder
        #   2) <something>.csv in 'sourcedata' folder (with minimal suffix if multiple)
        con_file = None
        csv_file = None

        # If this root is the 'meg-kit' folder, see if we have a .con file
        if os.path.basename(root) == 'meg-kit':
            con_candidates = [f for f in files if f.lower().endswith('.con')]
            if con_candidates:
                # Take the first .con we find or refine the logic if needed
                con_file = os.path.join(root, con_candidates[0])

        # If this root is the 'sourcedata' folder, see if we have the main .csv
        # (In your example, you mention you only need the one that has no extra suffix.)
        if os.path.basename(root) == 'sourcedata':
            csv_candidates = [
                f for f in files
                if f.lower().endswith('.csv')
                # You might also need extra checks if you want to skip files with suffixes
                # For example:
                # and not re.match(r".*_\d{4}-\d{2}-\d{2}_\d{2}h\d{2}\.\d{2}\.\d{3}\.csv", f)
            ]
            # Filter to keep only "one" CSV if multiple are found, e.g. the earliest or by naming:
            # For demonstration, let's pick the first sorted candidate or refine as needed
            if csv_candidates:
                csv_candidates.sort()
                csv_file = os.path.join(root, csv_candidates[0])

        if con_file or csv_file:
            # See if we already have an entry for this subject/session
            # (since the walk might find 'meg-kit' and 'sourcedata' in different passes)
            existing = next((s for s in session_info_list
                             if s["subject"] == subject_match and s["session"] == session_match), None)
            if not existing:
                entry = {
                    "subject": subject_match,
                    "session": session_match,
                    "con_file": con_file,
                    "csv_file": csv_file
                }
                session_info_list.append(entry)
            else:
                # Update the existing dict with whichever file we found now
                if con_file:
                    existing["con_file"] = con_file
                if csv_file:
                    existing["csv_file"] = csv_file

    # Filter out sessions that might be incomplete
    # e.g., we only keep those that have both a con_file and a csv_file
    session_info_list = [
        s for s in session_info_list
        if s["con_file"] is not None and s["csv_file"] is not None
    ]

    return session_info_list


def main():

    sessions = find_sessions(BASE_DIR)
    if not sessions:
        print("No valid MEG sessions found!")
        return

    # Display all sessions to the user
    print("Found the following sessions:")
    for idx, s in enumerate(sessions, start=1):
        print(f"{idx}. {s['subject']}/{s['session']}")
        print(f"   CON: {s['con_file']}")
        print(f"   CSV: {s['csv_file']}\n")

    # Let the user pick a session
    choice = input("Select a session number to process (or press Enter to exit): ")
    if not choice.strip():
        print("No session selected. Exiting.")
        return
    choice_index = int(choice) - 1
    if choice_index < 0 or choice_index >= len(sessions):
        print("Invalid choice. Exiting.")
        return

    selected_session = sessions[choice_index]
    print("You selected:")
    print(f"Subject: {selected_session['subject']}")
    print(f"Session: {selected_session['session']}")
    print(f"CON File: {selected_session['con_file']}")
    print(f"CSV File: {selected_session['csv_file']}")

    # Add your processing code here
    # For example, parse the .con file or read the CSV file.

    con_file = selected_session['con_file']
    csv_file = selected_session['csv_file']

    # Open a log file in append or write mode
    logfile = open(con_file+'_output_log.txt', 'w', encoding='utf-8')

    # Redirect stdout (and optionally stderr)
    sys.stdout = Tee(sys.stdout, logfile)
    sys.stderr = Tee(sys.stderr, logfile)  # Optional: to also mirror errors



    channel_map = {
        224: "MISC 001",  # mask channel
        225: "MISC 002",  # prime channel #1
        226: "MISC 003",
        227: "MISC 004",
        228: "MISC 005",
        229: "MISC 006",
        230: "MISC 007",  # prime channel #6
        231: "MISC 008",  # instruction + target
    }

    mask_channel_code = 224
    target_channel_code = 231
    prime_codes = [225, 226, 227, 228, 229, 230]



    # ----------------------------------------------------------------------------
    # 2) LOAD AND FILTER THE CSV
    # ----------------------------------------------------------------------------
    df = pd.read_csv(csv_file, sep=",", engine="python")

    # Filter out practice rows AND rows with empty PRIME or TARGET columns
    df_filtered = df[
        (df["CONDITION"] != "PRACTICE") &
        (df["PRIME"].notna()) & (df["PRIME"] != "") &
        (df["TARGET"].notna()) & (df["TARGET"] != "")
    ]

    # Count unique trials (assuming 'thisTrialN' is a unique trial index)
    n_real_trials = df_filtered["thisTrialN"].nunique()
    print(f"Number of valid real trials (non-practice, prime/target not empty): {n_real_trials}")

    # ----------------------------------------------------------------------------
    # 3) BUILD EXPECTED TRIGGER COUNTS
    # ----------------------------------------------------------------------------
    expected_triggers_dict = {ch_name: 0 for ch_name in channel_map.values()}

    # Add 1 for the instruction trigger at the start (on target channel = 231)
    expected_triggers_dict[channel_map[target_channel_code]] += 1

    # For each real trial:
    #   1 mask trigger (ch 224)
    #   1 prime trigger (on channel in prime_codes)
    #   1 target trigger (ch 231)
    for _, row in df_filtered.iterrows():
        # Mask
        expected_triggers_dict[channel_map[mask_channel_code]] += 1

        # Prime
        code = row["triggerCode"]
        if code in prime_codes:
            ch_name = channel_map[code]
            expected_triggers_dict[ch_name] += 1
        # else: Possibly a warning, but we'll pass

        # Target
        expected_triggers_dict[channel_map[target_channel_code]] += 1

    # Summarize total expected
    expected_total = sum(expected_triggers_dict.values())

    print("\nEXPECTED TRIGGERS (PER CHANNEL):")
    for ch_name, exp_count in expected_triggers_dict.items():
        print(f"  {ch_name} => {exp_count}")
    print(f"TOTAL EXPECTED ACROSS ALL CHANNELS = {expected_total}\n")

    # ----------------------------------------------------------------------------
    # 4) READ THE .con FILE WITH MNE
    # ----------------------------------------------------------------------------
    raw = mne.io.read_raw_kit(con_file, preload=True)
    sfreq = raw.info["sfreq"]
    print("MNE thinks the sampling frequency is:", raw.info["sfreq"])
    # ----------------------------------------------------------------------------
    # 5) TRIGGER DETECTION FUNCTION
    # ----------------------------------------------------------------------------
    def find_trigger_rising_edges(signal, threshold=TRIGGER_THRESHOLD):
        """
        Return sample indices where the signal transitions from below 'threshold'
        to above 'threshold' (simple 0->1).
        """
        above = signal > threshold
        rising_edges = np.where(np.diff(above.astype(int)) == 1)[0]
        return rising_edges

    # ----------------------------------------------------------------------------
    # 6) DETECT ACTUAL TRIGGERS ON EACH CHANNEL
    # ----------------------------------------------------------------------------
    actual_triggers_dict = {}
    actual_total = 0

    # We'll also build a single list of all triggers as (time_s, code) to check intervals
    all_triggers = []

    for code, ch_name in channel_map.items():
        if ch_name not in raw.ch_names:
            print(f"WARNING: {ch_name} not found in raw data. Setting actual=0.")
            actual_triggers_dict[ch_name] = 0
            continue

        ch_idx = raw.ch_names.index(ch_name)
        signal = raw.get_data(picks=[ch_idx])[0]  # shape: (n_samples,)

        rising_samples = find_trigger_rising_edges(signal, threshold=TRIGGER_THRESHOLD)
        trigger_times = rising_samples / sfreq  # in seconds

        actual_count = len(trigger_times)
        actual_triggers_dict[ch_name] = actual_count
        actual_total += actual_count

        # Store each trigger with the numeric code for easy pattern-checking
        for t in trigger_times:
            all_triggers.append((t, code))

        # Print debug info
        print(f"\nChannel: {ch_name} (CSV code={code})")
        print(f"  Found {actual_count} triggers at times (s): {np.round(trigger_times, 4)}")
        if actual_count > 1:
            inter_trigger_durations = np.diff(trigger_times)
            print(f"  Durations between triggers (s): {np.round(inter_trigger_durations, 4)}")

    # ----------------------------------------------------------------------------
    # 7) COMPARE ACTUAL VS. EXPECTED COUNTS
    # ----------------------------------------------------------------------------
    print("\nACTUAL TRIGGERS (PER CHANNEL):")
    for ch_name, cnt in actual_triggers_dict.items():
        print(f"  {ch_name} => {cnt}")
    print(f"TOTAL ACTUAL ACROSS ALL CHANNELS = {actual_total}\n")

    print("--------------------------------------------------------------")
    print("Comparing expected vs. actual triggers:\n")

    for ch_name in sorted(expected_triggers_dict.keys()):
        exp_cnt = expected_triggers_dict[ch_name]
        act_cnt = actual_triggers_dict.get(ch_name, 0)
        status = "OK" if exp_cnt == act_cnt else "MISMATCH"
        print(f"Channel {ch_name:8s} | expected={exp_cnt:3d}, actual={act_cnt:3d} => {status}")

    print("\nOVERALL TOTAL:")
    print(f"  Expected total triggers = {expected_total}")
    print(f"  Actual total triggers   = {actual_total}")
    if expected_total == actual_total:
        print("  ==> Overall trigger count matches expected.")
    else:
        print("  ==> WARNING: Overall trigger count does NOT match!")
    print("--------------------------------------------------------------\n")


    trigger_count_is_valid = (expected_total == actual_total)

    # ----------------------------------------------------------------------------
    # 8) CHECK TIMING BETWEEN MASK -> PRIME -> TARGET
    # ----------------------------------------------------------------------------

    # 2) Initialize a duration check flag before looping over intervals:
    duration_is_valid = True

    # Sort all triggers by time
    all_triggers.sort(key=lambda x: x[0])

    mask_prime_target_intervals = []
    i = 0
    n = len(all_triggers)

    # We'll do a simple pattern-based parsing:
    # - Look for a trigger with code 224 (MASK)
    # - The next in time should be code in prime_codes (PRIME)
    # - The next after that should be code 231 (TARGET)
    #
    # We measure the intervals between them.
    # If the pattern doesn't match, skip or break as appropriate.

    while i < n - 2:
        t0, c0 = all_triggers[i]
        t1, c1 = all_triggers[i+1]
        t2, c2 = all_triggers[i+2]

        # Check if we have (224 -> prime_codes -> 231)
        if c0 == 224 and c1 in prime_codes and c2 == 231:
            dt_mask_prime = t1 - t0
            dt_prime_target = t2 - t1

            mask_prime_target_intervals.append((t0, t1, t2, c1, dt_mask_prime, dt_prime_target))
            i += 3  # move past this group
        else:
            # If this doesn't match the pattern, just move to the next trigger
            # Or we could try a more robust approach. But for simplicity:
            i += 1

    # Print a summary
    print("Checking timing for each (Mask -> Prime -> Target) triplet:\n")
    for idx, (t_mask, t_prime, t_targ, prime_code,
              dt_mp, dt_pt) in enumerate(mask_prime_target_intervals, start=1):

        # Compare dt_mp to expected 0.5 and dt_pt to expected 0.05
        mask_prime_ok = (abs(dt_mp - EXPECTED_MASK_TO_PRIME) <= TOL_MASK_TO_PRIME)
        prime_target_ok = (abs(dt_pt - EXPECTED_PRIME_TO_TARGET) <= TOL_PRIME_TO_TARGET)

        print(f"Trial-like group #{idx}:")
        print(f"  Found mask at  t = {t_mask:.3f}s, code=224")
        print(f"  Found prime at t = {t_prime:.3f}s, code={prime_code}")
        print(f"  Found target at t = {t_targ:.3f}s, code=231")

        print(f"  --> Mask->Prime:  {dt_mp:.3f}s ", end="")
        print("OK" if mask_prime_ok else f"(WARNING: expected ~{EXPECTED_MASK_TO_PRIME}s)")

        print(f"  --> Prime->Target: {dt_pt:.3f}s ", end="")
        print("OK" if prime_target_ok else f"(WARNING: expected ~{EXPECTED_PRIME_TO_TARGET}s)")

        # (Optional) check how long target is "on" by seeing when the next mask appears:
        # If you want to see if the target stayed for ~0.3s, you can look ahead to the
        # next group's mask time (if any) and check that difference. For example:
        if idx < len(mask_prime_target_intervals):
            # next triplet's mask time
            next_mask_time = mask_prime_target_intervals[idx][0]  # t_mask of the next group
            dt_target_offset = next_mask_time - t_targ
            # check if dt_target_offset >= 0.3 or around 0.3
            # for now we just print it:
            print(f"  --> Target->NextMask: {dt_target_offset:.3f}s (approx. for target duration)")

        if not mask_prime_ok or not prime_target_ok:
            duration_is_valid = False

        print()

    print(f"Total valid (Mask->Prime->Target) groups found: {len(mask_prime_target_intervals)}")
    print("Done.")



    print('Summary ----------------')

    if trigger_count_is_valid and duration_is_valid:
        print("ALL CHECKS PASSED: Trigger counts and durations are valid!")
    else:
        print("CHECKS FAILED: ")
        if not trigger_count_is_valid:
            print("  - Trigger count mismatch")

        if not duration_is_valid:
            print("  - One or more inter-trigger durations (Mask→Prime or Prime→Target) are invalid")

        if trigger_count_is_valid or duration_is_valid:
            print("CHECKS that have PASSED")
            if trigger_count_is_valid:
                print("  - Trigger count is valid")

            if duration_is_valid:
                print("  - All inter-trigger durations are valid")

if __name__ == "__main__":

    main()