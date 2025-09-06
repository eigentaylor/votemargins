import csv
import sys
from collections import defaultdict

def scan(path, year_filter=None):
    by_year = defaultdict(lambda: defaultdict(int))
    with open(path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            year = r.get('year')
            if year_filter and str(year_filter) != str(year):
                continue
            try:
                ev = int(float(r.get('electoral_votes') or 0))
            except Exception:
                ev = 0
            # assign to party names in D_name/R_name/T_name columns only if corresponding *_electoral > 0
            for col_prefix in ('D', 'R', 'T'):
                name_col = f'{col_prefix}_name'
                ev_col = f'{col_prefix}_electoral'
                name = r.get(name_col) or ''
                try:
                    ev_assigned = int(float(r.get(ev_col) or 0))
                except Exception:
                    ev_assigned = 0
                if ev_assigned > 0 and name:
                    by_year[year][name] += ev_assigned
    return by_year

def main():
    if len(sys.argv) < 2:
        print('Usage: ev_scan.py <year>')
        sys.exit(1)
    year = sys.argv[1]
    path = '1900_2024_election_results.fixed.csv'
    data = scan(path, year_filter=year)
    if not data or year not in data:
        print(f'No data for year {year}')
        return
    items = sorted(data[year].items(), key=lambda x: -x[1])
    print(f'Year: {year}')
    for name, ev in items:
        print(f'  {name}: {ev} EVs')

if __name__ == '__main__':
    main()
