import os


def generate_year_results(year, winner_name, winner, winner_electoral_votes, loser_name, loser, loser_electoral_votes, total_votes_winner, total_votes_loser, popular_vote_margin, electoral_college_votes_to_win, flipped_states_votes_dict, min_votes_to_flip, number_of_flipped_states, abs_popular_vote_margin, total_votes_in_year, best_v, start_year, end_year, print_results=True, mode='classic', other_parties=None, skip_majority=False):
    """Print and persist per-year summary details."""
    if best_v + loser_electoral_votes >= electoral_college_votes_to_win and mode == 'no_majority' and skip_majority:
        return
    popular_vote_margin = total_votes_winner - total_votes_loser
    if print_results:
        print(f'Year: {year}')
        print(f'Original Winner: {winner_name} ({winner}) with {winner_electoral_votes} electoral votes vs {loser_name} ({loser}) with {loser_electoral_votes} electoral votes ({electoral_college_votes_to_win} needed)')
        # include the single other party/candidate with the least EVs (if any)
        other_candidate = None
        if other_parties:
            try:
                parsed = []
                for code, info in other_parties.items():
                    name = ''
                    ev = 0
                    if isinstance(info, (list, tuple)) and len(info) >= 2:
                        name, ev = info[0], int(info[1])
                    elif isinstance(info, dict):
                        name = info.get('name') or info.get('candidate') or ''
                        ev = int(info.get('electoral_votes', 0))
                    else:
                        name = str(code)
                        if isinstance(info, (int, float)):
                            ev = int(info)
                        else:
                            try:
                                ev = int(str(info))
                            except Exception:
                                ev = 0
                    parsed.append((code, (name or str(code)), ev))
                # choose the candidate with the smallest non-zero EVs
                # exclude the primary winner and runner-up from consideration
                parsed = [p for p in parsed if p[2] > 0 and p[1] not in (winner_name, loser_name)]
                if parsed:
                    other_candidate = min(parsed, key=lambda x: x[2])
                    code, name, ev = other_candidate[0], other_candidate[1], other_candidate[2]
                    print(f'Other party/candidate: {name} ({code}) with {ev} electoral votes')
            except Exception:
                other_candidate = None
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
                # compute original and adjusted tuples if original_votes present
                orig = info.get('original_votes') or {}
                state_winner = info.get('state_winner') or ''
                # orig tuple ordering: D, R, T (T may be zero)
                try:
                    D_orig = int(orig.get('D', 0))
                except Exception:
                    D_orig = 0
                try:
                    R_orig = int(orig.get('R', 0))
                except Exception:
                    R_orig = 0
                try:
                    T_orig = int(orig.get('T', 0))
                except Exception:
                    T_orig = 0

                # default adjusted = original
                D_adj, R_adj, T_adj = D_orig, R_orig, T_orig
                try:
                    fv_int = int(fv)
                except Exception:
                    fv_int = None

                if fv_int is not None and state_winner in ('D', 'R'):
                    # flipped votes are removed from the original winner and added to the runner-up (loser arg of generate_year_results)
                    if state_winner == 'D':
                        # D was winner, so subtract fv from D and add to R
                        D_adj = max(0, D_orig - fv_int)
                        R_adj = R_orig + fv_int
                    else:
                        R_adj = max(0, R_orig - fv_int)
                        D_adj = D_orig + fv_int

                # format tuples; include T only if non-zero
                def tuple_str(d, r, t):
                    if t:
                        return f"(D: {d:,}, R: {r:,}, T: {t:,})"
                    else:
                        return f"(D: {d:,}, R: {r:,})"

                orig_tuple = tuple_str(D_orig, R_orig, T_orig)
                adj_tuple = tuple_str(D_adj, R_adj, T_adj)

                parts.append(f"{state}: EC={ec}, flipped votes={fv_str}, % flipped={pct_str}, {orig_tuple} -> {adj_tuple}")
            return "; ".join(parts)

        # compute popular vote winner and percentage of total votes (for printing)
        popular_vote_winner = winner_name if popular_vote_margin > 0 else loser_name
        try:
            pop_pct_of_total = 100 * abs(popular_vote_margin) / total_votes_in_year if total_votes_in_year else None
        except Exception:
            pop_pct_of_total = None

        flipped_states_str = _format_flipped(flipped_states_votes_dict)
        # Print popular vote margin with total votes and percentage of total votes
        if pop_pct_of_total is None:
            print(f'Popular Vote Margin: {abs(popular_vote_margin):,}  for {popular_vote_winner} (Total votes: {total_votes_in_year})')
        else:
            print(f'Popular Vote Margin: {abs(popular_vote_margin):,}  for {popular_vote_winner} (Total votes: {total_votes_in_year:,}; Ratio to Total Votes in Year: {pop_pct_of_total:.5f}%)')
        print(f'Flipped states: {flipped_states_str}')
        print(f'Total number of flipped votes: {min_votes_to_flip} across {number_of_flipped_states} states, Ratio to Popular Vote Margin: {100 * min_votes_to_flip / abs_popular_vote_margin:.5f}%, Ratio to Total Votes in Year: {100 * min_votes_to_flip / total_votes_in_year:.5f}%')
        print(f'New Winner:{loser_name} ({loser}) with {best_v+loser_electoral_votes} electoral votes vs {winner_name} ({winner}) with {winner_electoral_votes-best_v} electoral votes\n')

    # Map modes to output folders (user preference):
    # classic -> results/, no_majority -> no_majority/
    folder_map = {
        'classic': 'results',
        'no_majority': 'no_majority'
    }
    folder = folder_map.get(mode, os.path.join('results', mode))
    os.makedirs(folder, exist_ok=True)
    # Choose the correct filename depending on mode
    txt_name = f'no_majority_results_{start_year}-{end_year}.txt' if mode == 'no_majority' else f'flip_results_{start_year}-{end_year}.txt'
    # Append to the text summary file for the selected mode
    with open(os.path.join(folder, txt_name), 'a') as f:
        f.write(f'Year: {year}\n')
        f.write(f'\tOriginal Winner:\n\t\t{winner_name} ({winner}) with {winner_electoral_votes} electoral votes ({electoral_college_votes_to_win} needed)\n\t\t\tvs {loser_name} ({loser}) with {loser_electoral_votes} electoral votes \n')
        # include the single other party/candidate with the least EVs in the text output
        if other_parties:
            try:
                # reuse logic above if available
                if 'other_candidate' in locals() and other_candidate:
                    code, name, ev = other_candidate[0], other_candidate[1], other_candidate[2]
                else:
                    # fallback parse
                    parsed = []
                    for code, info in other_parties.items():
                        name = ''
                        ev = 0
                        if isinstance(info, (list, tuple)) and len(info) >= 2:
                            name, ev = info[0], int(info[1])
                        elif isinstance(info, dict):
                            name = info.get('name') or info.get('candidate') or ''
                            ev = int(info.get('electoral_votes', 0))
                        else:
                            name = str(code)
                            if isinstance(info, (int, float)):
                                ev = int(info)
                            else:
                                try:
                                    ev = int(str(info))
                                except Exception:
                                    ev = 0
                        parsed.append((code, (name or str(code)), ev))
                    # exclude primary winner/runner-up when choosing the small contender
                    parsed = [p for p in parsed if p[2] > 0 and p[1] not in (winner_name, loser_name)]
                    if parsed:
                        code, name, ev = min(parsed, key=lambda x: x[2])
                    else:
                        code, name, ev = None, None, 0
                if ev > 0:
                    f.write(f'\t\t\t\tvs {name} ({code}) with {ev} electoral votes\n')
            except Exception:
                pass
        # if T_electoral > 0, include in original winner line
        popular_vote_winner = winner_name if popular_vote_margin > 0 else loser_name
        # write popular vote margin with total votes in year and percentage of total votes
        try:
            pop_pct_of_total = 100 * abs(popular_vote_margin) / total_votes_in_year if total_votes_in_year else None
        except Exception:
            pop_pct_of_total = None

        if pop_pct_of_total is None:
            f.write(f"\tPopular Vote Margin: {abs(popular_vote_margin):<,}  for {popular_vote_winner}\n\tTotal votes in year: {total_votes_in_year}\n")
        else:
            f.write(f"\tPopular Vote Margin: {abs(popular_vote_margin):<,} ({pop_pct_of_total:<.5f}% of total)  for {popular_vote_winner}\n\tTotal votes in year: {total_votes_in_year:,}\n")
        # write a nicely formatted flipped states string (with thousands separators and percent formatting)
        total_flipped_EVs = sum(info.get('EC', 0) for info in flipped_states_votes_dict.values())
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
                # compute original and adjusted tuples
                orig = info.get('original_votes') or {}
                state_winner = info.get('state_winner') or ''
                try:
                    D_orig = int(orig.get('D', 0))
                except Exception:
                    D_orig = 0
                try:
                    R_orig = int(orig.get('R', 0))
                except Exception:
                    R_orig = 0
                try:
                    T_orig = int(orig.get('T', 0))
                except Exception:
                    T_orig = 0

                D_adj, R_adj, T_adj = D_orig, R_orig, T_orig
                try:
                    fv_int = int(fv)
                except Exception:
                    fv_int = None

                if fv_int is not None and state_winner in ('D', 'R'):
                    if state_winner == 'D':
                        D_adj = max(0, D_orig - fv_int)
                        R_adj = R_orig + fv_int
                    else:
                        R_adj = max(0, R_orig - fv_int)
                        D_adj = D_orig + fv_int

                if T_orig:
                    orig_tuple = f"(D{'*' if state_winner == 'D' else ' '}: {D_orig:>10,}, R{'*' if state_winner == 'R' else ' '}: {R_orig:>10,}, T: {T_orig:>10,})"
                    adj_tuple = f"(D{'*' if D_adj > R_adj else ' '}: {D_adj:>10,}, R{'*' if R_adj > D_adj else ' '}: {R_adj:>10,}, T: {T_adj:>10,})"
                else:
                    orig_tuple = f"(D{'*' if state_winner == 'D' else ' '}: {D_orig:>10,}, R{'*' if state_winner == 'R' else ' '}: {R_orig:>10,})"
                    adj_tuple = f"(D{'*' if D_adj > R_adj else ' '}: {D_adj:>10,}, R{'*' if R_adj > D_adj else ' '}: {R_adj:>10,})"

                parts.append(f"\n\t\t{state:<15} ({ec:>2} EVs):{fv_str:>10} ({pct_str:>7}) flipped votes\n\t\t\t   {orig_tuple} \n\t\t\t-> {adj_tuple}")
            return "; ".join(parts)

        flipped_states_str = _format_flipped_for_write(flipped_states_votes_dict)
        f.write(f'\tFlipped states: {flipped_states_str}\n')
        f.write(f'\tTotal number of flipped votes: {min_votes_to_flip:,} ({total_flipped_EVs} EVs) across {number_of_flipped_states} states\n\tRatio to Popular Vote Margin: {100 * min_votes_to_flip / abs_popular_vote_margin:.5f}% ({popular_vote_margin:<,})\n\tRatio to Total Votes in Year: {100 * min_votes_to_flip / total_votes_in_year:.5f}% ({total_votes_in_year:,})\n')
        # Write New Winner block or NO MAJORITY. Also include the small other contender if present.
        if best_v + loser_electoral_votes >= electoral_college_votes_to_win:
            f.write(f'\tNew Winner:\n')
            f.write(f'\t\t{loser_name} ({loser}) with {best_v+loser_electoral_votes} electoral votes ({electoral_college_votes_to_win} needed)\n')
            f.write(f'\t\t\tvs {winner_name} ({winner}) with {winner_electoral_votes-best_v} electoral votes\n')
            # append the other contender if we have one
            try:
                if other_parties:
                    if 'other_candidate' in locals() and other_candidate:
                        code, name, ev = other_candidate[0], other_candidate[1], other_candidate[2]
                    else:
                        # pick smallest
                        parsed = []
                        for code, info in other_parties.items():
                            if isinstance(info, (list, tuple)) and len(info) >= 2:
                                n, e = info[0], int(info[1])
                            elif isinstance(info, dict):
                                n = info.get('name') or info.get('candidate') or ''
                                e = int(info.get('electoral_votes', 0))
                            else:
                                n = str(code)
                                try:
                                    e = int(info)
                                except Exception:
                                    try:
                                        e = int(str(info))
                                    except Exception:
                                        e = 0
                            parsed.append((code, (n or str(code)), e))
                        # exclude primary winner/runner-up when picking the small contender
                        parsed = [p for p in parsed if p[2] > 0 and p[1] not in (winner_name, loser_name)]
                        if parsed:
                            code, name, ev = min(parsed, key=lambda x: x[2])
                        else:
                            code, name, ev = None, None, 0
                    if ev > 0:
                        f.write(f'\t\t\tvs {name} ({code}) with {ev} electoral votes\n')
            except Exception:
                pass
            f.write('\n')
        else:
            # NO MAJORITY: show adjusted EV totals after flipping and include the small other contender (if any)
            f.write('\tNO MAJORITY\n')
            try:
                # adjusted totals after flipping `best_v` from the winner to the loser
                adjusted_loser_ev = best_v + loser_electoral_votes
                adjusted_winner_ev = winner_electoral_votes - best_v
                f.write(f"\t\t{winner_name} ({winner}) with {adjusted_winner_ev} electoral votes ({electoral_college_votes_to_win} needed)\n")
                f.write(f"\t\t\tvs {loser_name} ({loser}) with {adjusted_loser_ev} electoral votes\n")

                # include the small other contender if present (exclude primary winner/runner-up)
                other_code = other_name = None
                other_ev = 0
                if other_parties:
                    if 'other_candidate' in locals() and other_candidate:
                        other_code, other_name, other_ev = other_candidate[0], other_candidate[1], other_candidate[2]
                    else:
                        parsed = []
                        for code, info in other_parties.items():
                            name = ''
                            ev = 0
                            if isinstance(info, (list, tuple)) and len(info) >= 2:
                                name, ev = info[0], int(info[1])
                            elif isinstance(info, dict):
                                name = info.get('name') or info.get('candidate') or ''
                                ev = int(info.get('electoral_votes', 0))
                            else:
                                name = str(code)
                                try:
                                    ev = int(info)
                                except Exception:
                                    try:
                                        ev = int(str(info))
                                    except Exception:
                                        ev = 0
                            parsed.append((code, (name or str(code)), ev))
                        # exclude primary winner/runner-up
                        parsed = [p for p in parsed if p[2] > 0 and p[1] not in (winner_name, loser_name)]
                        if parsed:
                            other_code, other_name, other_ev = min(parsed, key=lambda x: x[2])

                if other_ev and other_name:
                    f.write(f"\t\t\t\tvs {other_name} ({other_code}) with {other_ev} electoral votes\n")
            except Exception:
                # fallback to previous simple line if something goes wrong
                f.write('\tNO MAJORITY\n')
            f.write('\n')
