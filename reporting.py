import os


def generate_year_results(year, winner_name, winner, winner_electoral_votes, loser_name, loser, loser_electoral_votes, total_votes_winner, total_votes_loser, popular_vote_margin, electoral_college_votes_to_win, flipped_states_votes_dict, min_votes_to_flip, number_of_flipped_states, abs_popular_vote_margin, total_votes_in_year, best_v, start_year, end_year, print_results=True):
    """Print and persist per-year summary details."""
    popular_vote_margin = total_votes_winner - total_votes_loser
    if print_results:
        print(f'Year: {year}')
        print(f'Original Winner: {winner_name} ({winner}) with {winner_electoral_votes} electoral votes vs {loser_name} ({loser}) with {loser_electoral_votes} electoral votes ({electoral_college_votes_to_win} needed)')
        print(f'Flipped states: {flipped_states_votes_dict}')
        print(f'Total number of flipped votes: {min_votes_to_flip} across {number_of_flipped_states} states, Ratio to Popular Vote Margin: {100 * min_votes_to_flip / abs_popular_vote_margin:.5f}%, Ratio to Total Votes in Year: {100 * min_votes_to_flip / total_votes_in_year:.5f}%')
        print(f'New Winner: {loser_name} ({loser}) with {best_v+loser_electoral_votes} electoral votes vs {winner_name} ({winner}) with {winner_electoral_votes-best_v} electoral votes\n')

    # Ensure results directory exists
    if not os.path.exists('results'):
        os.makedirs('results')

    # Append to the text summary file
    with open(f'results/flip_results_{start_year}-{end_year}.txt', 'a') as f:
        f.write(f'Year: {year}\n')
        f.write(f'Original Winner: {winner_name} ({winner}) with {winner_electoral_votes} electoral votes vs {loser_name} ({loser}) with {loser_electoral_votes} electoral votes ({electoral_college_votes_to_win} needed)\n')
        popular_vote_winner = winner_name if popular_vote_margin > 0 else loser_name
        f.write(f'Popular Vote Margin: {popular_vote_margin}  for {popular_vote_winner}\n')
        f.write(f'Flipped states: {flipped_states_votes_dict}\n')
        f.write(f'Total number of flipped votes: {min_votes_to_flip} across {number_of_flipped_states} states, Ratio to Popular Vote Margin: {100 * min_votes_to_flip / abs_popular_vote_margin:.5f}%, Ratio to Total Votes in Year: {100 * min_votes_to_flip / total_votes_in_year:.5f}%\n')
        f.write(f'New Winner: {loser_name} ({loser}) with {best_v+loser_electoral_votes} electoral votes vs {winner_name} ({winner}) with {winner_electoral_votes-best_v} electoral votes\n\n')
