Data fixer helper

This small tool applies targeted corrections from `corrections.json` and recomputes electoral allocations.

Run (PowerShell):

```powershell
# dry run to see which rows would be changed
python .\data_fixer.py --infile .\1900_2024_election_results.csv --corrections .\corrections.json --dry-run

# write to a new file
python .\data_fixer.py --infile .\1900_2024_election_results.csv --out .\1900_2024_election_results.fixed.csv --corrections .\corrections.json

# overwrite original (use with care)
python .\data_fixer.py --infile .\1900_2024_election_results.csv --inplace --corrections .\corrections.json
```

Notes:
- `corrections.json` is a list of corrections; each correction should include `year` and `state` or `state_po`, and a `changes` object mapping column names to corrected values.
- After applying explicit changes the script recomputes `overall_winner`, `overall_runner_up`, `winner_votes`, `loser_votes`, and `D_electoral`/`R_electoral`/`T_electoral` based on the vote columns and the `electoral_votes` field.
