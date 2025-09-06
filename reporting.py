import os


def generate_year_results(year, winner_name, winner, winner_electoral_votes, loser_name, loser, loser_electoral_votes, total_votes_winner, total_votes_loser, popular_vote_margin, electoral_college_votes_to_win, flipped_states_votes_dict, min_votes_to_flip, number_of_flipped_states, abs_popular_vote_margin, total_votes_in_year, best_v, start_year, end_year, print_results=True):
    """Print and persist per-year summary details."""
    popular_vote_margin = total_votes_winner - total_votes_loser
    if print_results:
        print(f'Year: {year}')
        print(f'Original Winner: {winner_name} ({winner}) with {winner_electoral_votes} electoral votes vs {loser_name} ({loser}) with {loser_electoral_votes} electoral votes ({electoral_college_votes_to_win} needed)')
        # Format flipped states dict for nicer printing (commas for large numbers, % formatting)
        def _format_flipped(d):
            if not isinstance(d, dict):
                return str(d)
            parts = []
            for state, info in d.items():
                ec = info.get('EC', '')
                fv = info.get('flipped votes', info.get('flipped_votes', ''))
                pct = info.get('% flipped', '')
                try:
                    fv_str = f"{int(fv):,}"
                except Exception:
                    fv_str = str(fv)
                try:
                    pct_str = f"{float(pct):.3f}%" if pct != '' else ''
                except Exception:
                    pct_str = str(pct)
                parts.append(f"{state}: EC={ec}, flipped votes={fv_str}, % flipped={pct_str}")
            return "; ".join(parts)

        flipped_states_str = _format_flipped(flipped_states_votes_dict)
        print(f'Flipped states: {flipped_states_str}')
        print(f'Total number of flipped votes: {min_votes_to_flip} across {number_of_flipped_states} states, Ratio to Popular Vote Margin: {100 * min_votes_to_flip / abs_popular_vote_margin:.5f}%, Ratio to Total Votes in Year: {100 * min_votes_to_flip / total_votes_in_year:.5f}%')
        print(f'New Winner:{loser_name} ({loser}) with {best_v+loser_electoral_votes} electoral votes vs {winner_name} ({winner}) with {winner_electoral_votes-best_v} electoral votes\n')

    # Ensure results directory exists
    if not os.path.exists('results'):
        os.makedirs('results')

    # Append to the text summary file
    with open(f'results/flip_results_{start_year}-{end_year}.txt', 'a') as f:
        f.write(f'Year: {year}\n')
        f.write(f'\tOriginal Winner:\n\t\t{winner_name} ({winner}) with {winner_electoral_votes} electoral votes ({electoral_college_votes_to_win} needed)\n\t\t\tvs {loser_name} ({loser}) with {loser_electoral_votes} electoral votes \n')
        popular_vote_winner = winner_name if popular_vote_margin > 0 else loser_name
        f.write(f'\tPopular Vote Margin: {popular_vote_margin:<,}  for {popular_vote_winner}\n')
        # write a nicely formatted flipped states string (with thousands separators and percent formatting)
        def _format_flipped_for_write(d):
            # reuse same formatting logic as printing
            if not isinstance(d, dict):
                return str(d)
            parts = []
            for state, info in d.items():
                ec = info.get('EC', '')
                fv = info.get('flipped votes', info.get('flipped_votes', ''))
                pct = info.get('% flipped', '')
                try:
                    fv_str = f"{int(fv):,}"
                except Exception:
                    fv_str = str(fv)
                try:
                    pct_str = f"{float(pct):.3f}%" if pct != '' else ''
                except Exception:
                    pct_str = str(pct)
                parts.append(f"\n\t\t{state:<15} ({ec:>2} EVs):{fv_str:>10} ({pct_str:>7}) flipped votes")
            return "; ".join(parts)

        flipped_states_str = _format_flipped_for_write(flipped_states_votes_dict)
        f.write(f'\tFlipped states: {flipped_states_str}\n')
        f.write(f'\tTotal number of flipped votes: {min_votes_to_flip:,} across {number_of_flipped_states} states\n\tRatio to Popular Vote Margin: {100 * min_votes_to_flip / abs_popular_vote_margin:.5f}%\n\tRatio to Total Votes in Year: {100 * min_votes_to_flip / total_votes_in_year:.5f}%\n')
        f.write(f'\tNew Winner:\n\t\t{loser_name} ({loser}) with {best_v+loser_electoral_votes} electoral votes ({electoral_college_votes_to_win} needed)\n\t\t\tvs {winner_name} ({winner}) with {winner_electoral_votes-best_v} electoral votes\n\n')
