import pandas as pd
import numpy as np

# Load the dataset
election_results_df = pd.read_csv('summary_results_updated.csv')

# We want to split the states ME and NE into their respective districts
# in 2008, 2016, 2020, and 2024, at least one of the districts in ME and NE voted differently from the state
# NE-02 voted for the democratic candidate in 2008, 2020 and 2024
# ME-02 voted for the republican candidate in 2016, 2020, and 2024
# they had the same electoral votes in all elections

# to fix this, we will split the states into two rows when they split their electoral votes
# we will subtract 1 electoral vote from the state in its original row and add another row with 1 electoral vote for the district that split its votes
# we will also have to update the D_votes, R_votes, winner_votes, loser_votes, votes_to_flip, party_win, and winner_state columns

# we create a dictionary for NE and ME with the years they split their votes and the popular vote data for the defecting district. then we will subtract D_votes and R_votes from the state and add a new row with the defecting district data

NE_split = {
    2008: {'D_votes': 138892, 'R_votes': 135567},
    2020: {'D_votes': 171517, 'R_votes': 149880},
    2024: {'D_votes': 163298, 'R_votes': 148621}
}

ME_split = {
    2016: {'D_votes': 143952, 'R_votes': 180665},
    2020: {'D_votes': 167182, 'R_votes': 196771},
    2024: {'D_votes': 174225, 'R_votes': 209650}
}

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

# function to calculate the required columns and split the state into two rows
def split_state(state_po, votes, election_results_df):
    # loop through the years the state split its votes
    for year, data in votes.items():
        # get the row for the year and state
        row_index = election_results_df[(election_results_df['year'] == year) & (election_results_df['state_po'] == state_po)].index
        row = election_results_df.loc[row_index]
        
        # add a new row with the defecting district
        new_row = row.copy()
        new_row['state_po'] = state_po + '-02'
        new_row['state'] = state_po + '-02'
        new_row['electoral_votes'] = 1
        new_row['D_votes'] = data['D_votes']
        new_row['R_votes'] = data['R_votes']
        new_row = recalculate_votes(new_row)
        
        # subtract the votes for the defecting district from the state in row
        election_results_df.loc[row_index, 'electoral_votes'] -= 1
        election_results_df.loc[row_index, 'D_votes'] -= data['D_votes']
        election_results_df.loc[row_index, 'R_votes'] -= data['R_votes']
        election_results_df.loc[row_index] = recalculate_votes(election_results_df.loc[row_index])
        
        # Insert the new row right after the original row but keep the original row in the same place and update the index
        election_results_df = pd.concat([election_results_df.iloc[:row_index[0] + 1], new_row, election_results_df.iloc[row_index[0] + 1:]]).reset_index(drop=True)
        
    return election_results_df

# Split the states ME and NE
election_results_df = split_state('NE', NE_split, election_results_df)
election_results_df = split_state('ME', ME_split, election_results_df)

# go through all the rows and recalculate just in case
election_results_df = election_results_df.groupby(['year', 'state_po'], group_keys=False).apply(recalculate_votes)

# recalculate total_electoral_votes,D_electoral,R_electoral,overall_winner,winner_state
def recalculate_electoral_winner(results_df, year):
    # get the total electoral votes for the year
    total_electoral_votes = results_df[results_df['year'] == year]['electoral_votes'].sum()
    # get the total electoral votes for each party
    D_electoral = results_df[(results_df['year'] == year) & (results_df['party_win'] == 'D')]['electoral_votes'].sum()
    R_electoral = results_df[(results_df['year'] == year) & (results_df['party_win'] == 'R')]['electoral_votes'].sum()
    # get the overall winner
    overall_winner = 'D' if D_electoral > R_electoral else 'R'
    # update the rows with the new values
    results_df.loc[results_df['year'] == year, 'total_electoral_votes'] = total_electoral_votes
    results_df.loc[results_df['year'] == year, 'D_electoral'] = D_electoral
    results_df.loc[results_df['year'] == year, 'R_electoral'] = R_electoral
    results_df.loc[results_df['year'] == year, 'overall_winner'] = overall_winner
    # we set winner state to True if the overall winner won the state
    for state in results_df[results_df['year'] == year]['state_po'].unique():
        # check if party_win == overall_winner
        winner_state = results_df[(results_df['year'] == year) & (results_df['state_po'] == state)]['party_win'].iloc[0] == overall_winner
    return results_df

# recalculate total_electoral_votes,D_electoral,R_electoral,overall_winner,winner_state for each year
for year in election_results_df['year'].unique():
    election_results_df = recalculate_electoral_winner(election_results_df, year)

# ensure numerical columns are saved as integers
election_results_df['electoral_votes'] = election_results_df['electoral_votes'].astype(int)
election_results_df['total_electoral_votes'] = election_results_df['total_electoral_votes'].astype(int)
election_results_df['D_electoral'] = election_results_df['D_electoral'].astype(int)
election_results_df['R_electoral'] = election_results_df['R_electoral'].astype(int)
election_results_df['winner_votes'] = election_results_df['winner_votes'].astype(int)
election_results_df['loser_votes'] = election_results_df['loser_votes'].astype(int)
election_results_df['votes_to_flip'] = election_results_df['votes_to_flip'].astype(int)

# Save the updated election results data
election_results_df.to_csv('summary_results_split_verify.csv', index=False)
print('Done')