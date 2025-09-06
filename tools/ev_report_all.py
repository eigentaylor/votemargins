#!/usr/bin/env python3
"""
Scan the fixed CSV and compute per-year electoral vote totals for each candidate
by summing the state's `electoral_votes` assigned to the state's `party_win`.
Falls back to the highest vote among D/R/T if `party_win` is missing.

Usage:
  python tools\ev_report_all.py [YEAR]
If YEAR is provided, prints only that year.
"""
import csv
import sys
from collections import defaultdict

CSV = "1900_2024_election_results.fixed.csv"

def choose_winner_by_votes(row):
    # row keys: D_votes,R_votes,T_votes may be empty
    try:
        d = int(row.get('D_votes') or 0)
    except ValueError:
        d = 0
    try:
        r = int(row.get('R_votes') or 0)
    except ValueError:
        r = 0
    try:
        t = int(row.get('T_votes') or 0)
    except ValueError:
        t = 0
    maxv = max(d,r,t)
    if maxv == d:
        return row.get('D_name','').strip()
    if maxv == r:
        return row.get('R_name','').strip()
    return row.get('T_name','').strip()


def main():
    filter_year = None
    if len(sys.argv) > 1:
        try:
            filter_year = int(sys.argv[1])
        except ValueError:
            print('Invalid year argument; ignoring filter')
            filter_year = None

    totals = defaultdict(lambda: defaultdict(int))

    with open(CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                year = int(row.get('year'))
            except Exception:
                continue
            if filter_year and year != filter_year:
                continue
            try:
                ev = int(row.get('electoral_votes') or 0)
            except ValueError:
                ev = 0
            pw = (row.get('party_win') or '').strip()
            if pw == 'D':
                name = (row.get('D_name') or '').strip()
            elif pw == 'R':
                name = (row.get('R_name') or '').strip()
            elif pw == 'T':
                name = (row.get('T_name') or '').strip()
            else:
                # fallback to vote-based winner
                name = choose_winner_by_votes(row)
            if not name:
                # if we still don't have a name, skip
                continue
            totals[year][name] += ev

    years = sorted(totals.keys())
    for y in years:
        print(f"Year: {y}")
        items = sorted(totals[y].items(), key=lambda kv: kv[1], reverse=True)
        for name, ev in items:
            print(f"  {name}: {ev} EVs")
        print()

if __name__ == '__main__':
    main()
