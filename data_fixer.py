#!/usr/bin/env python3
"""Fixer for election results CSV.

Usage:
  python data_fixer.py --infile 1900_2024_election_results.csv --out 1900_2024_election_results.fixed.csv

It applies explicit corrections from `corrections.json` (list of corrections keyed by year and state or state_po),
then recomputes winner/runner-up and D_electoral/R_electoral/T_electoral from vote totals.
"""
import csv
import json
import argparse
from typing import Dict, Any


def parse_int(s: str) -> int:
    try:
        return int(float(s))
    except Exception:
        return 0


def load_corrections(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def match_correction(corr: Dict[str, Any], row: Dict[str, str]) -> bool:
    # corr may contain year and state or state_po
    if "year" in corr and str(corr["year"]) != row.get("year"):
        return False
    if "state" in corr and corr["state"].upper() != row.get("state", "").upper():
        return False
    if "state_po" in corr and corr["state_po"].upper() != row.get("state_po", "").upper():
        return False
    return True


def apply_changes(row: Dict[str, str], changes: Dict[str, Any]):
    for k, v in changes.items():
        # write values as strings to keep CSV consistent
        row[k] = str(v)


def recompute_electorals(row: Dict[str, str]):
    # Allocate electoral votes according to `party_win` when present,
    # otherwise fall back to highest vote totals.
    electoral_votes = parse_int(row.get("electoral_votes", "0"))

    party_win = (row.get("party_win") or "").strip()
    # normalize single-letter party codes if full names provided
    if party_win.upper() in ("D", "R", "T"):
        winner_party = party_win.upper()
    else:
        # fallback: determine from votes
        D_votes = parse_int(row.get("D_votes", "0"))
        R_votes = parse_int(row.get("R_votes", "0"))
        T_votes = parse_int(row.get("T_votes", "0"))
        votes = [("D", D_votes), ("R", R_votes), ("T", T_votes)]
        votes_sorted = sorted(votes, key=lambda x: x[1], reverse=True)
        winner_party = votes_sorted[0][0]
        # keep party_win in sync if it was blank
        if not party_win:
            row["party_win"] = winner_party

    # Strictly set overall_winner from party_win-derived winner_party
    row["overall_winner"] = winner_party

    # Determine runner-up and vote counts from vote totals (for winner_votes/loser_votes and overall_runner_up)
    D_votes = parse_int(row.get("D_votes", "0"))
    R_votes = parse_int(row.get("R_votes", "0"))
    T_votes = parse_int(row.get("T_votes", "0"))
    votes = {"D": D_votes, "R": R_votes, "T": T_votes}

    # Runner-up is the highest vote among the other parties
    others = [(p, v) for p, v in votes.items() if p != winner_party]
    others_sorted = sorted(others, key=lambda x: x[1], reverse=True)
    runner = others_sorted[0][0] if others_sorted else "R"

    row["overall_runner_up"] = runner
    row["winner_votes"] = str(votes.get(winner_party, 0))
    row["loser_votes"] = str(others_sorted[0][1] if others_sorted else 0)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--infile", default="1900_2024_election_results.csv")
    p.add_argument("--out", default="1900_2024_election_results.fixed.csv")
    p.add_argument("--corrections", default="corrections.json")
    p.add_argument("--inplace", action="store_true", help="overwrite infile")
    p.add_argument("--dry-run", action="store_true", help="print affected rows and exit")
    args = p.parse_args()

    corrections = load_corrections(args.corrections)

    with open(args.infile, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        fieldnames = reader.fieldnames

    if not fieldnames:
        print("No headers found in CSV")
        return

    modified_count = 0
    affected = []

    for row in rows:
        matched = False
        for corr in corrections:
            if match_correction(corr, row):
                changes = corr.get("changes", {})
                apply_changes(row, changes)
                matched = True
        # after explicit corrections, recompute electorals and winners from votes
        recompute_electorals(row)
        if matched:
            modified_count += 1
            affected.append((row.get("year"), row.get("state"), row.get("state_po")))

    if args.dry_run:
        print(f"Would modify {modified_count} rows")
        for y, s, sp in affected:
            print(y, s, sp)
        return

    outpath = args.out
    if args.inplace:
        outpath = args.infile

    # Compute per-year national electoral totals by party_win (for reporting)
    year_party_totals = {}
    for row in rows:
        year = row.get("year")
        party = (row.get("party_win") or "").strip().upper()
        ev = parse_int(row.get("electoral_votes", "0"))
        ytot = year_party_totals.setdefault(year, {"D": 0, "R": 0, "T": 0, "total": 0})
        ytot["total"] += ev
        if party in ("D", "R", "T"):
            ytot[party] += ev
        else:
            raise ValueError(f"Unexpected party_win '{party}' in year {year}")
            # if unknown party_win, fall back to highest vote
            Dv = parse_int(row.get("D_votes", "0"))
            Rv = parse_int(row.get("R_votes", "0"))
            Tv = parse_int(row.get("T_votes", "0"))
            winner = max((("D", Dv), ("R", Rv), ("T", Tv)), key=lambda x: x[1])[0]
            ytot[winner] += ev

    # Assign per-row state-level electoral allocations: each state's EV goes to its winner (party_win)
    for row in rows:
        year = row.get("year")
        # set D_electoral, R_electoral, T_electoral from year_party_totals
        row["D_electoral"] = str(year_party_totals[year]["D"])
        row["R_electoral"] = str(year_party_totals[year]["R"])
        row["T_electoral"] = str(year_party_totals[year]["T"])
        overall_winner = 'D' if year_party_totals[year]['D'] > year_party_totals[year]['R'] else 'R'
        # get runner up as 2nd highest of D, R, T
        parties = ['D', 'R', 'T']
        runner_up = sorted(parties, key=lambda p: year_party_totals[year][p], reverse=True)[1]
        row["overall_winner"] = overall_winner
        row["overall_runner_up"] = runner_up
        # check if winner_state (party_win matches overall_winner)
        if row.get("party_win") == overall_winner:
            row["winner_state"] = "True"
        else:
            row["winner_state"] = "False"
        if year == '1960':
            row["T_name"] = "Harry F. Byrd"

    with open(outpath, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    # Post-write: verify per-year D/R/T electoral totals
    totals_by_year = {}
    for row in rows:
        year = row.get("year")
        totals = totals_by_year.setdefault(year, {"D": 0, "R": 0, "T": 0, "total": 0})
        ev = parse_int(row.get("electoral_votes", "0"))
        totals["D"] += parse_int(row.get("D_electoral", "0"))
        totals["R"] += parse_int(row.get("R_electoral", "0"))
        totals["T"] += parse_int(row.get("T_electoral", "0"))
        totals["total"] += ev

    print(f"Wrote {len(rows)} rows to {outpath}. Applied corrections to {modified_count} rows.")
    # Print summary lines for each year where sums don't match
    bad_years = []
    for year, t in sorted(totals_by_year.items()):
        allocated = t["D"] + t["R"] + t["T"]
        expected = t["total"]
        if allocated != expected:
            bad_years.append((year, allocated, expected, t["D"], t["R"], t["T"]))

    if bad_years:
        print("\nPer-year electoral allocation mismatches (allocated != expected):")
        for y, allocated, expected, d, r, te in bad_years:
            print(f"{y}: allocated={allocated} expected={expected} (D={d} R={r} T={te})")
    else:
        print("All years: allocated electoral votes match expected totals.")


if __name__ == "__main__":
    main()
