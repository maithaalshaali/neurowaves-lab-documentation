# Trigger count sanity check
# This script should take as input a csv file that contains:
# - the code of the trigger for each channel
# - the trigger count number per type
# - directory of the base to do the sanity check
# It will do the following:
# - load the directory find subjects and sessions
# - load the .con files for each subject and session if found
# - count the triggers
# save a logfile for each subject for each session
# - if the subject data session is already sanity checked it should skip

import os
import re


BASE_DIR = r"test_sanity_check_dir"


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



if __name__ == "__main__":

    main()