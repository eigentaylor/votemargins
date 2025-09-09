import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import time

from analysis import compute_flip_for_year
from reporting import generate_year_results
from plotting import make_all_plots
from election_metrics import compute_metrics_for_all_years, write_outputs

# Set the dark theme for all plots
plt.style.use('dark_background')


def get_flip_results(election_results_df, start_year, end_year, print_results=False, flip_mode='classic'):
    """Compute flip results.

    flip_mode: 'classic' (runner-up becomes outright winner),
               'no_majority' (original winner ends up with strictly less than ECs_to_win),
               'both' (produce both modes)
    Returns a dict mapping mode->(flip_results_df, flip_results_dict)
    """
    modes = [flip_mode] if flip_mode in ('classic', 'no_majority') else ['classic', 'no_majority']

    # Initialize containers for each mode
    all_flip_results = {m: {} for m in modes}

    # Map modes to output folders (user preference): classic -> results/, no_majority -> no_majority/
    folder_map = {
        'classic': 'results',
        'no_majority': 'no_majority'
    }

    # Ensure results directories and initialize summary files per mode
    for m in modes:
        folder = folder_map.get(m, os.path.join('results', m))
        os.makedirs(folder, exist_ok=True)
        # name the text summary file depending on mode
        txt_name = f'no_majority_results_{start_year}-{end_year}.txt' if m == 'no_majority' else f'flip_results_{start_year}-{end_year}.txt'
        with open(os.path.join(folder, txt_name), 'w') as f:
            f.write('')

    # loop through the years in the election results data
    for year in election_results_df['year'].unique():
        election_results = election_results_df[election_results_df['year'] == year]
        total_electoral_votes = election_results['total_electoral_votes'].iloc[0]
        votes_to_win = election_results['electoral_votes_to_win'].iloc[0]
        winner = election_results['overall_winner'].iloc[0]
        winner_electoral_votes = election_results[winner + '_electoral'].iloc[0]
        loser = election_results['overall_runner_up'].iloc[0]
        winner_name = election_results[winner + '_name'].iloc[0]
        loser_name = election_results[loser + '_name'].iloc[0]
        loser_electoral_votes = election_results[loser + '_electoral'].iloc[0]

        # common per-year values
        total_votes_winner = election_results[winner + '_votes'].sum()
        total_votes_loser = election_results[loser + '_votes'].sum()
        color = 'deepskyblue' if election_results['D_votes'].sum() > election_results['R_votes'].sum() else 'red'
        if year == 1960:
            total_votes_winner = 34220984
            total_votes_loser = 34108157
            color = 'deepskyblue'
        popular_vote_margin = total_votes_winner - total_votes_loser
        abs_popular_vote_margin = abs(popular_vote_margin)
        total_votes_in_year = election_results['totalvotes'].sum()
        total_electoral_votes_in_year = election_results['electoral_votes'].sum()
        electoral_college_votes_to_win = total_electoral_votes_in_year // 2 + 1

        # compute for requested modes
        for m in modes:
            if m == 'classic':
                electoral_votes_to_flip = votes_to_win - loser_electoral_votes
            elif m == 'no_majority':
                # flip enough EVs away from the original winner so winner ends up with strictly less than needed to win
                # i.e., original_winner_ECs_after = winner_electoral_votes - flipped_ev < electoral_college_votes_to_win
                # So need flipped_ev > winner_electoral_votes - (electoral_college_votes_to_win - 1)
                flipped_ev_needed = max(0, winner_electoral_votes - (electoral_college_votes_to_win - 1))
                electoral_votes_to_flip = flipped_ev_needed
            else:
                continue

            # If no electoral votes need flipping, set empty results
            if electoral_votes_to_flip <= 0:
                flipped_states = []
                min_votes_to_flip = 0
                best_v = 0
                winner_states_dict = {}
            else:
                flipped_states, min_votes_to_flip, best_v, winner_states_dict = compute_flip_for_year(
                    election_results, loser, electoral_votes_to_flip
                )

            flipped_states_votes_dict = {}
            for state in flipped_states:
                # attempt to capture original per-party vote totals for the state so we can
                # show original -> adjusted tuples in reports
                try:
                    prow = election_results[election_results['state'] == state].iloc[0]
                except Exception:
                    prow = None

                d_votes = r_votes = t_votes = 0
                state_winner = ''
                if prow is not None:
                    try:
                        d_votes = int(prow.get('D_votes') or 0)
                    except Exception:
                        d_votes = 0
                    try:
                        r_votes = int(prow.get('R_votes') or 0)
                    except Exception:
                        r_votes = 0
                    try:
                        t_votes = int(prow.get('T_votes') or 0)
                    except Exception:
                        t_votes = 0

                    state_winner = (prow.get('party_win') or '').strip()
                    if state_winner not in ('D', 'R', 'T'):
                        # fallback: infer by comparing vote totals in the row
                        if d_votes >= r_votes and d_votes >= t_votes:
                            state_winner = 'D'
                        elif r_votes >= d_votes and r_votes >= t_votes:
                            state_winner = 'R'
                        else:
                            state_winner = 'T'

                flipped_states_votes_dict[state] = {
                    'EC': winner_states_dict[state]['electoral_votes'],
                    'flipped votes': winner_states_dict[state]['votes_to_flip'],
                    '% flipped': round(
                        winner_states_dict[state]['votes_to_flip'] / winner_states_dict[state]['total_votes'] * 100, 3
                    ),
                    'original_votes': {'D': d_votes, 'R': r_votes, 'T': t_votes},
                    'state_winner': state_winner,
                }

            flipped_states_votes_dict = {
                k: v for k, v in sorted(
                    flipped_states_votes_dict.items(), key=lambda item: item[1]['flipped votes']
                )
            }

            number_of_flipped_states = len(flipped_states)

            all_flip_results[m][year] = {
                'min_votes_to_flip': min_votes_to_flip,
                'flipped_states': flipped_states,
                'number_of_flipped_states': number_of_flipped_states,
                'electoral_votes_flipped': best_v,
                'total_electoral_votes': total_electoral_votes_in_year,
                'electoral_votes_to_win': electoral_college_votes_to_win,
                'popular_vote_margin': popular_vote_margin,
                'color': color,
                'flip_margin_ratio': 100 * (min_votes_to_flip / total_votes_in_year if total_votes_in_year else 0),
                'popular_margin_ratio': 100 * (popular_vote_margin / total_votes_in_year if total_votes_in_year else 0),
            }

            # Build other_parties: sum each state's `electoral_votes` once, assigned to the state's `party_win` candidate.
            # Some files store per-party totals repeated on every row; summing those repeats multiplies totals.
            # Instead iterate states and add that state's `electoral_votes` once to the candidate indicated by `party_win`.
            # Build other_parties keyed by party code ('D','R','T').
            # Sum each state's `electoral_votes` once and attribute to the state's `party_win`.
            ev_totals = {'D': 0, 'R': 0, 'T': 0}
            name_map = {'D': '', 'R': '', 'T': ''}
            for _, prow in election_results.iterrows():
                pw = (prow.get('party_win') or '').strip()
                # normalize pw to D/R/T; if missing determine by vote counts
                if pw not in ('D', 'R', 'T'):
                    try:
                        d_votes = int(prow.get('D_votes') or 0)
                    except Exception:
                        d_votes = 0
                    try:
                        r_votes = int(prow.get('R_votes') or 0)
                    except Exception:
                        r_votes = 0
                    try:
                        t_votes = int(prow.get('T_votes') or 0)
                    except Exception:
                        t_votes = 0
                    if d_votes >= r_votes and d_votes >= t_votes:
                        pw = 'D'
                    elif r_votes >= d_votes and r_votes >= t_votes:
                        pw = 'R'
                    else:
                        pw = 'T'

                try:
                    ev = int(prow.get('electoral_votes') or 0)
                except Exception:
                    ev = 0

                if ev <= 0:
                    continue

                # record candidate name for this party if not set
                if not name_map.get(pw):
                    name_col = f"{pw}_name"
                    try:
                        name_map[pw] = (prow.get(name_col) or '').strip()
                    except Exception:
                        name_map[pw] = ''

                ev_totals[pw] = ev_totals.get(pw, 0) + ev

            # Build final other_parties dict using codes as keys
            other_parties = {}
            for code in ('D', 'R', 'T'):
                ev = ev_totals.get(code, 0)
                if ev > 0:
                    # fallback: try to get a name from the election_results frame if not found in name_map
                    name = name_map.get(code) or ''
                    if not name and f"{code}_name" in election_results.columns:
                        try:
                            # take the first non-empty name in that column
                            nonempty = election_results[f"{code}_name"].dropna().astype(str)
                            if len(nonempty) > 0:
                                name = nonempty.iloc[0].strip()
                        except Exception:
                            name = name_map.get(code) or ''
                    other_parties[code] = (name, ev)

            # Remove the primary winner/runner-up from other_parties to avoid duplication in the "Other" list
            other_parties.pop(winner_name, None)
            other_parties.pop(loser_name, None)

            # For no_majority mode only produce a TXT entry when the flip produces NO MAJORITY
            if m == 'no_majority':
                # after flipping best_v to the loser, does the original winner end up below the threshold?
                adjusted_loser_ev = best_v + loser_electoral_votes
                adjusted_winner_ev = winner_electoral_votes - best_v
                if adjusted_winner_ev < electoral_college_votes_to_win:
                    generate_year_results(
                        year,
                        winner_name,
                        winner,
                        winner_electoral_votes,
                        loser_name,
                        loser,
                        loser_electoral_votes,
                        total_votes_winner,
                        total_votes_loser,
                        popular_vote_margin,
                        electoral_college_votes_to_win,
                        flipped_states_votes_dict,
                        min_votes_to_flip,
                        number_of_flipped_states,
                        abs_popular_vote_margin,
                        total_votes_in_year,
                        best_v,
                        start_year,
                        end_year,
                        print_results=print_results,
                        mode=m,
                        other_parties=other_parties,
                    )
                    # also save to a separate ONLY file with just these years
                    generate_year_results(
                        year,
                        winner_name,
                        winner,
                        winner_electoral_votes,
                        loser_name,
                        loser,
                        loser_electoral_votes,
                        total_votes_winner,
                        total_votes_loser,
                        popular_vote_margin,
                        electoral_college_votes_to_win,
                        flipped_states_votes_dict,
                        min_votes_to_flip,
                        number_of_flipped_states,
                        abs_popular_vote_margin,
                        total_votes_in_year,
                        best_v,
                        start_year,
                        end_year,
                        print_results=print_results,
                        mode=m,
                        other_parties=other_parties,
                        filename='no_majority_ONLY_results',
                        skip_majority=True,
                    )
            else:
                generate_year_results(
                    year,
                    winner_name,
                    winner,
                    winner_electoral_votes,
                    loser_name,
                    loser,
                    loser_electoral_votes,
                    total_votes_winner,
                    total_votes_loser,
                    popular_vote_margin,
                    electoral_college_votes_to_win,
                    flipped_states_votes_dict,
                    min_votes_to_flip,
                    number_of_flipped_states,
                    abs_popular_vote_margin,
                    total_votes_in_year,
                    best_v,
                    start_year,
                    end_year,
                    print_results=print_results,
                    mode=m,
                    other_parties=other_parties,
                )

    # Output the results per mode
    output = {}
    for m in modes:
        flip_results_df = pd.DataFrame.from_dict(all_flip_results[m], orient='index')
        csv_folder = folder_map.get(m, os.path.join('results', m))
        os.makedirs(csv_folder, exist_ok=True)
        flip_results_df.to_csv(os.path.join(csv_folder, f'flip_results-{start_year}-{end_year}.csv'))
        # copy the input data to the results folder for this mode
        election_results_df.to_csv(os.path.join(csv_folder, f'election_results-{start_year}-{end_year}.csv'), index=False)
        output[m] = (flip_results_df, all_flip_results[m])

    return output


def main():
    start_year = 1900
    end_year = 2024
    election_results_df = pd.read_csv('1900_2024_election_results.fixed.csv')

    # produce both modes and save outputs/plots for each
    results_by_mode = get_flip_results(election_results_df, start_year, end_year, print_results=True, flip_mode='both')
    for mode, (flip_results_df, _) in results_by_mode.items():
        folder_path = 'results' if mode == 'classic' else mode
        make_all_plots(flip_results_df, start_year, end_year, folder_path=os.path.join(folder_path), show_plot=False, mode=mode, clear_files=True)
        
    # run the sorting script to produce sorted versions of the results files
    import tools.sort_flip_results
    # run the file
    tools.sort_flip_results.main()

    metrics = compute_metrics_for_all_years()
    write_outputs(metrics)


if __name__ == '__main__':
    # delete folders if they exist
    for folder in ['results', 'no_majority', 'election_metrics']:
        if os.path.exists(folder):
            import shutil
            shutil.rmtree(folder)
    main()