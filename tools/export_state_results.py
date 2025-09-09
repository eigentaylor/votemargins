#!/usr/bin/env python3
"""Export state-year party winners into a copy-friendly JS object.

Creates `state_results.js` by default with the shape:

export default {
  states: {
    'California': { 1900: 'R', 1904: 'R', ... },
    ...
  }
};

The script looks for common header names (state, year, party_win) and is
robust to simple variations. Run with --csv and --out to override defaults.
"""
import argparse
import csv
import os
import sys
from collections import defaultdict


def detect_fieldnames(fieldnames):
    low = {f.lower(): f for f in fieldnames}
    mapping = {}
    # state
    for cand in ("state", "state_name", "state/territory"):
        if cand in low:
            mapping['state'] = low[cand]
            break
    # year
    for cand in ("year", "election_year"):
        if cand in low:
            mapping['year'] = low[cand]
            break
    # party win
    for cand in ("party_win", "party", "winner_party", "party_affiliation"):
        if cand in low:
            mapping['party'] = low[cand]
            break
    return mapping


def map_party_to_letter(party_raw):
    if party_raw is None:
        return ''
    p = party_raw.strip()
    if not p:
        return ''
    pl = p.lower()
    if pl in ('d', 'dem', 'democrat', 'democratic', 'democratic-party') or pl.startswith('dem'):
        return 'D'
    if pl in ('r', 'rep', 'republican', 'republican-party') or pl.startswith('rep') or 'gop' in pl:
        return 'R'
    # fallback: return first letter uppercased
    return pl[0].upper()


def build_states_dict(csv_path):
    states = defaultdict(dict)
    with open(csv_path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        mapping = detect_fieldnames(reader.fieldnames or [])
        if 'state' not in mapping or 'year' not in mapping or 'party' not in mapping:
            sys.stderr.write(
                "Could not find required columns automatically. Found: %s\n" % (reader.fieldnames,)
            )
            raise SystemExit(2)
        for row in reader:
            state = row.get(mapping['state'], '').strip()
            year_raw = row.get(mapping['year'], '').strip()
            party_raw = row.get(mapping['party'], '').strip()
            if not state or not year_raw:
                continue
            try:
                year = int(year_raw)
            except Exception:
                # skip rows with non-integer year
                continue
            letter = map_party_to_letter(party_raw)
            if not letter:
                continue
            states[state][year] = letter
    return states


def format_js(states_dict):
    # sort states and years for deterministic output
    lines = []
    lines.append("export default {")
    lines.append("  states: {")
    for i, state in enumerate(sorted(states_dict.keys())):
        if '-' in state:
            # skip congressional districts
            continue
        years = sorted(states_dict[state].keys())
        # title case states for consistency
        lines.append(f"    '{state.title()}': {{")
        # pack year entries, keep line length readable
        parts = [f"{y}: '{states_dict[state][y]}'" for y in years]
        # group by 8 per line
        chunk_size = 8
        for start in range(0, len(parts), chunk_size):
            chunk = parts[start:start+chunk_size]
            comma = ',' if start + chunk_size < len(parts) else ''
            lines.append('      ' + ', '.join(chunk) + (',' if comma else ','))
        # remove the trailing comma on last line of the state's object
        # but keep a comma after the object itself for valid JS
        # (we'll tidy by ensuring a single comma after the closing brace)
        lines.append("    },")
    lines.append("  }")
    lines.append("};")
    return '\n'.join(lines) + '\n'


def main():
    ap = argparse.ArgumentParser(description="Export state-year party winners into JS object")
    ap.add_argument('--csv', default=os.path.join(os.path.dirname(__file__), '..', '1900_2024_election_results.fixed.csv'))
    ap.add_argument('--out', default=os.path.join(os.path.dirname(__file__), '..', 'state_results.js'))
    args = ap.parse_args()

    csv_path = os.path.abspath(args.csv)
    out_path = os.path.abspath(args.out)

    if not os.path.exists(csv_path):
        sys.stderr.write(f"CSV file not found: {csv_path}\n")
        raise SystemExit(2)

    states = build_states_dict(csv_path)
    if not states:
        sys.stderr.write("No state/year/party rows found.\n")
        raise SystemExit(1)

    js = format_js(states)
    with open(out_path, 'w', encoding='utf-8') as fh:
        fh.write(js)

    print(f"Wrote {out_path} ({len(states)} states, years per state may vary)")


if __name__ == '__main__':
    main()
