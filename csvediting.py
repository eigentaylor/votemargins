import pandas as pd
import numpy as np

# Load the datasets
election_results_df = pd.read_csv('summary_election_results.csv')
electoral_college_df = pd.read_csv('filtered_electoral_college.csv')

# we need to add the electoral college data to the election results data
# first we loop through the electoral college data to get the total electoral votes for all states, how many votes are necessary to win and the winner of each election
# loop through the years in filtered_electoral_college.csv
for year in electoral_college_df['year'].unique():
    # get the electoral votes for the year
    electoral_votes = electoral_college_df[electoral_college_df['year'] == year]
    # get the total electoral votes
    total_electoral_votes = electoral_votes['electoral_votes'].sum()
    # get the number of votes needed to win
    votes_to_win = total_electoral_votes // 2 + 1
    # get the winner of the election by counting the number of electoral votes the republican won and see if it is greater than the votes needed to win
    winner = 'R' if electoral_votes[electoral_votes['party'] == 'R']['electoral_votes'].sum() >= votes_to_win else 'D'
    # get number of republican electoral votes for the year
    republican_votes = electoral_votes[electoral_votes['party'] == 'R']['electoral_votes'].sum()
    democrat_votes = electoral_votes[electoral_votes['party'] == 'D']['electoral_votes'].sum()
    # convert all the values to integers
    total_electoral_votes = int(total_electoral_votes)
    votes_to_win = int(votes_to_win)
    republican_votes = int(republican_votes)
    democrat_votes = int(democrat_votes)
    #print(f'{year} - Total Electoral Votes: {total_electoral_votes}, Votes to Win: {votes_to_win}, Winner: {winner}')
    # now we loop through the states and add the electoral votes to the election results data
    for index, row in electoral_votes.iterrows():
        # get the state abbreviation
        state = row['state']
        # get the electoral votes for the state
        electoral_votes = row['electoral_votes']
        #convert to integer
        electoral_votes = int(electoral_votes)
        # add the electoral votes to the election results data
        # find the row in the election results data for the year and state
        summary_results_row = election_results_df.loc[(election_results_df['year'] == year) & (election_results_df['state'] == state)]
        # set the electoral votes for the state
        election_results_df.loc[(election_results_df['year'] == year) & (election_results_df['state'] == state), 'electoral_votes'] = electoral_votes
        # set the total electoral votes for the year and votes to win
        election_results_df.loc[(election_results_df['year'] == year), 'total_electoral_votes'] = total_electoral_votes
        election_results_df.loc[(election_results_df['year'] == year), 'D_electoral'] = democrat_votes
        election_results_df.loc[(election_results_df['year'] == year), 'R_electoral'] = republican_votes
        election_results_df.loc[(election_results_df['year'] == year), 'overall_winner'] = winner
    
# Ensure numerical columns are saved as integers
election_results_df['electoral_votes'] = election_results_df['electoral_votes'].astype(int)
election_results_df['total_electoral_votes'] = election_results_df['total_electoral_votes'].astype(int)
election_results_df['D_electoral'] = election_results_df['D_electoral'].astype(int)
election_results_df['R_electoral'] = election_results_df['R_electoral'].astype(int)

# Save the updated election results data
election_results_df.to_csv('summary_election_results_updated.csv', index=False)
