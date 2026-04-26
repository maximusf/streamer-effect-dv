# clean_trends.py
# by Maximus Fernandez
#
# Cleans the four Google Trends CSV exports for the case study games.
# Google Trends data is the cleanest of the three sources used in this
# project: dates are already in ISO format, scores are integers in the
# 0-100 range, and there are no Excel-induced formatting issues. The
# only real cleaning needed is to normalize the column names, since
# Google Trends names the score column after whatever search term was
# used (e.g. "Among Us", "Fall Guys: Ultimate Knockout"), and to tag
# each row with its game name for the eventual concatenation.
#
# Important caveat for downstream analysis: Google Trends scores are
# normalized per search term, where 100 represents the peak interest
# for that specific term over its time range. Scores are NOT comparable
# in absolute terms across games. They should only be used to identify
# the timing of public-awareness spikes within a single game, not to
# compare popularity magnitudes between games.

import pandas as pd
from pathlib import Path

IN_DIR = Path("data/raw")
OUT_DIR = Path("data/clean")
OUT_DIR.mkdir(parents=True, exist_ok=True)

GAMES = ["among_us", "fall_guys", "vampire_survivors", "lethal_company"]


def clean_one(game: str) -> pd.DataFrame:
    """
    Loads, cleans, and returns the DataFrame for a single game's Google
    Trends export.
    """
    in_path = IN_DIR / f"google_{game}.csv"

    # Read the file. The column names from Google Trends are "Time" and
    # the search term; we overwrite both positionally so every game's
    # output has identical schema regardless of how the search term was
    # phrased on the website.
    df = pd.read_csv(in_path, header=0)
    df.columns = ["month", "trends_score"]

    # Date column is already in ISO format ("2019-01-01"), so pandas
    # parses it directly with no format string needed.
    df["month"] = pd.to_datetime(df["month"], errors="coerce")

    # Trends scores are integers 0 to 100. Cast to nullable Int64 so any
    # parsing failures land as NaN rather than 0.
    df["trends_score"] = pd.to_numeric(df["trends_score"], errors="coerce").astype("Int64")

    # Sort oldest to newest, even though Google Trends already exports in
    # this order. Defensive consistency with the other two cleaners.
    df = df.sort_values("month").reset_index(drop=True)

    # Tag with game name so the combined long-format file carries source
    # information for every row.
    df.insert(1, "game", game)

    return df


def main():
    all_games = []
    for game in GAMES:
        print(f"Cleaning {game}...")
        df = clean_one(game)
        out = OUT_DIR / f"trends_{game}_clean.csv"
        df.to_csv(out, index=False)
        print(f"  Wrote {len(df)} rows to {out}")
        all_games.append(df)

    master = pd.concat(all_games, ignore_index=True)
    master_out = OUT_DIR / "trends_all_clean.csv"
    master.to_csv(master_out, index=False)
    print(f"\nCombined: {len(master)} rows to {master_out}")

    print("\nNon-null counts in combined dataset:")
    print(master.notna().sum().to_string())


if __name__ == "__main__":
    main()
