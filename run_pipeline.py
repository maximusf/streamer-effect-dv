# run_pipeline.py
# by Maximus Fernandez

# Runs the full raw-to-master data pipeline end to end:

#   1. clean_twitch.py    cleans manually-collected TwitchTracker CSVs
#   2. clean_steam.py     cleans the SteamDB monthly CSV exports
#   3. clean_google.py    cleans the Google Trends CSV exports
#   4. merge_data.py      joins the three cleaned sources into master.csv
#                         and computes lag_summary.csv + growth_summary.csv

# Each underlying script is self-contained and can be run on its own.
# This orchestrator exists so the entire pipeline can be regenerated
# with a single command. Each step runs as a subprocess so each
# script's main() side effects (file I/O, console output) stay
# isolated and global state cannot leak between steps.

# Order matters here, unlike in the cleaners-only version: merge_data
# reads the cleaned CSVs, so it must run after all three cleaners
# finish. We run them in sequence rather than in parallel for that
# reason and because the console output is easier to follow when
# each step prints in order.

import subprocess
import sys
from pathlib import Path

# Order matters: cleaners first (independent of each other), then merge.
SCRIPTS = [
    "clean_twitch.py",
    "clean_steam.py",
    "clean_google.py",
    "merge_data.py",
]


def run_script(script: str) -> bool:
    # Runs a single script as a subprocess and streams its output to the
    # console. Returns True if the script exited with code 0, False
    # otherwise.

    # We use sys.executable rather than a hardcoded "python" so whichever
    # Python interpreter is running this orchestrator (whether "python",
    # "python3", or a virtualenv binary) is reused for the child process.
    # Avoids the common pitfall of the orchestrator succeeding under one
    # interpreter while a child fails under a different one with missing
    # dependencies.
    
    print(f"\n{'=' * 60}")
    print(f"Running {script}")
    print(f"{'=' * 60}")

    # check=False so we can report each failure explicitly. With
    # check=True, a failed cleaner would crash the orchestrator before
    # we got the chance to skip the merge step (which would have failed
    # anyway because its inputs would be missing or stale).
    result = subprocess.run([sys.executable, script], check=False)
    return result.returncode == 0


def main():
    # Verify every script exists in the current directory before
    # running anything, so the user gets a clear error up front rather
    # than a confusing "File not found" partway through.
    missing = [s for s in SCRIPTS if not Path(s).exists()]
    if missing:
        print("ERROR: Missing script(s) in current directory:")
        for s in missing:
            print(f"  {s}")
        print("\nMake sure you are running this from the project root and "
              "that all four scripts are present.")
        sys.exit(1)

    # Run each script in sequence. If a cleaner fails, skip the merge
    # step, since merge_data would either crash or silently produce a
    # stale master.csv. The cleaners are independent of each other so
    # we keep going even if one fails, to surface as many issues as
    # possible in a single run.
    failed = []
    for script in SCRIPTS:
        if script == "merge_data.py" and failed:
            print(f"\n{'=' * 60}")
            print("Skipping merge_data.py because one or more cleaners failed.")
            print(f"{'=' * 60}")
            failed.append(script)
            continue
        if not run_script(script):
            failed.append(script)

    # Final summary so the result of the full pipeline is visible at
    # the bottom of the terminal even after lots of intermediate output.
    print(f"\n{'=' * 60}")
    print("Pipeline summary")
    print(f"{'=' * 60}")
    if failed:
        print(f"FAILED: {len(failed)} script(s) did not complete successfully:")
        for s in failed:
            print(f"  {s}")
        sys.exit(1)
    else:
        print(f"All {len(SCRIPTS)} scripts completed successfully.")
        print("Cleaned data and master files are in data/clean/")


if __name__ == "__main__":
    main()
