import pandas as pd
import numpy as np

# Load the dataset
election_results_df = pd.read_csv('summary_results_split_verify.csv')

def recalculate_votes(row):
    # using D_votes and R_votes, recalculate totalvotes, winner_votes, loser_votes, votes_to_flip, party_win, and winner_state
    D_votes = int(row['D_votes'].iloc[0])
    R_votes = int(row['R_votes'].iloc[0])
    totalvotes = D_votes + R_votes
    winner_votes = max(D_votes, R_votes)
    loser_votes = min(D_votes, R_votes)
    votes_to_flip = (winner_votes - loser_votes) // 2 + 1
    party_win = 'D' if D_votes > R_votes else 'R'
    winner_state = party_win == row['overall_winner']
    # update the row with the new values
    row['totalvotes'] = int(totalvotes)
    row['winner_votes'] = int(winner_votes)
    row['loser_votes'] = int(loser_votes)
    row['votes_to_flip'] = int(votes_to_flip)
    row['party_win'] = party_win
    row['winner_state'] = winner_state
    return row