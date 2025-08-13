import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import time

from analysis import compute_flip_for_year
from reporting import generate_year_results
from plotting import make_plot, make_bar_plot, make_state_frequency_plot, make_all_plots

# Set the dark theme for all plots
plt.style.use('dark_background')


def get_flip_results(election_results_df, start_year, end_year, print_results=False):
    # Initialize a dictionary to store the results for each year
    flip_results = {}

    # Ensure results directory exists and initialize summary file
    os.makedirs('results', exist_ok=True)
    with open(f'results/flip_results_{start_year}-{end_year}.txt', 'w') as f:
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
        electoral_votes_to_flip = votes_to_win - loser_electoral_votes

        flipped_states, min_votes_to_flip, best_v, winner_states_dict = compute_flip_for_year(
            election_results, loser, electoral_votes_to_flip
        )

        flipped_states_votes_dict = {}
        for state in flipped_states:
            flipped_states_votes_dict[state] = {
                'EC': winner_states_dict[state]['electoral_votes'],
                'flipped votes': winner_states_dict[state]['votes_to_flip'],
                '% flipped': round(
                    winner_states_dict[state]['votes_to_flip'] / winner_states_dict[state]['total_votes'] * 100, 3
                ),
            }

        flipped_states_votes_dict = {
            k: v for k, v in sorted(
                flipped_states_votes_dict.items(), key=lambda item: item[1]['flipped votes']
            )
        }

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
        number_of_flipped_states = len(flipped_states)

        flip_results[year] = {
            'min_votes_to_flip': min_votes_to_flip,
            'flipped_states': flipped_states,
            'number_of_flipped_states': number_of_flipped_states,
            'electoral_votes_flipped': best_v,
            'total_electoral_votes': total_electoral_votes_in_year,
            'electoral_votes_to_win': electoral_college_votes_to_win,
            'popular_vote_margin': popular_vote_margin,
            'color': color,
            'flip_margin_ratio': 100 * min_votes_to_flip / total_votes_in_year,
            'popular_margin_ratio': 100 * popular_vote_margin / total_votes_in_year,
        }

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
        )

    # Output the results
    flip_results_df = pd.DataFrame.from_dict(flip_results, orient='index')
    flip_results_df.to_csv(f'results/flip_results-{start_year}-{end_year}.csv')

    # copy the input data to the results folder
    election_results_df.to_csv(f'results/election_results-{start_year}-{end_year}.csv', index=False)
    return flip_results_df, flip_results


def main():
    start_year = 1900
    end_year = 2024
    election_results_df = pd.read_csv('1900_2024_election_results.csv')

    flip_results_df, flip_results = get_flip_results(election_results_df, start_year, end_year, print_results=True)
    make_all_plots(flip_results_df, start_year, end_year, folder_path='results/', show_plot=False)


if __name__ == '__main__':
    main()