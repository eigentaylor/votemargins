import numpy as np


def compute_flip_for_year(election_results, loser, votes_to_win):
    """Compute dynamic-programming table to flip enough states to give loser >= votes_to_win.

    Returns:
        flipped_states (list[str]): states to flip
        min_votes_to_flip (int): minimal popular votes to flip across selected states
        best_v (int): electoral votes flipped
        winner_states_dict (dict): per-state data used in DP
    """
    # States the loser lost
    lost_states = election_results[election_results['party_win'] != loser]

    winner_states_dict = {}
    for _, row in lost_states.iterrows():
        state = row['state']
        electoral_votes = row['electoral_votes']
        state_winner_votes = row[row['party_win'] + '_votes']
        runner_up_votes = row[loser + '_votes']
        votes_to_flip = (state_winner_votes - runner_up_votes) // 2 + 1
        winner_states_dict[state] = {
            'electoral_votes': electoral_votes,
            'votes_to_flip': votes_to_flip,
            'total_votes': row['totalvotes']
        }

    # Sort by efficiency
    winner_states_dict = {
        k: v for k, v in sorted(
            winner_states_dict.items(),
            key=lambda item: item[1]['votes_to_flip'] / item[1]['electoral_votes']
        )
    }

    max_electoral_votes = sum([d['electoral_votes'] for d in winner_states_dict.values()])
    dp = [np.inf] * (max_electoral_votes + 1)
    dp[0] = 0
    state_used = [None] * (max_electoral_votes + 1)

    for state, data in winner_states_dict.items():
        ev = data['electoral_votes']
        vt = data['votes_to_flip']
        for v in range(max_electoral_votes, ev - 1, -1):
            if dp[v - ev] + vt < dp[v]:
                dp[v] = dp[v - ev] + vt
                state_used[v] = state

    min_dp = np.inf
    best_v = 0
    for v in range(votes_to_win, max_electoral_votes + 1):
        if dp[v] < min_dp:
            min_dp = dp[v]
            best_v = v

    flipped_states = []
    v_current = best_v
    min_votes_to_flip = 0
    while v_current > 0:
        state = state_used[v_current]
        if state is None:
            break
        min_votes_to_flip += winner_states_dict[state]['votes_to_flip']
        flipped_states.append(state)
        v_current -= winner_states_dict[state]['electoral_votes']

    return flipped_states, min_votes_to_flip, best_v, winner_states_dict
