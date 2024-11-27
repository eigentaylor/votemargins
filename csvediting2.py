import pandas as pd
import numpy as np

# Load the dataset
election_results_df = pd.read_csv('summary_results.csv')

# We want to add the 2024 election results to the dataset
# We will use the 2020 election results as a template
# Get the 2020 election results
election_results_2020 = election_results_df[election_results_df['year'] == 2020]

# Change the year of each row to 2024
election_results_2024 = election_results_2020.copy()
election_results_2024['year'] = 2024

# update the number of electoral votes for the states that changed from the 2020 census: TX, FL, CO, MT, NC, OR gained electoral votes (TX got 2, the rest got 1)
# CA, IL, MI, NY, OH, PA, WV lost electoral 1 vote each
electoral_votes_changes = { 'TX': 2, 'FL': 1, 'CO': 1, 'MT': 1, 'NC': 1, 'OR': 1, 'CA': -1, 'IL': -1, 'MI': -1, 'NY': -1, 'OH': -1, 'PA': -1, 'WV': -1 }
# update the electoral votes for each state
for state, votes in electoral_votes_changes.items():
    election_results_2024.loc[election_results_2024['state_po'] == state, 'electoral_votes']   += votes
    
# to check, print the electoral votes for each of the states that changed from 2020 and 2024
print(election_results_2020[election_results_2020['state_po'].isin(electoral_votes_changes.keys())][['state', 'electoral_votes']])
print(election_results_2024[election_results_2024['state_po'].isin(electoral_votes_changes.keys())][['state', 'electoral_votes']])

# update the candidate names to the 2024 election results 
# change D_name from BIDEN, JOSEPH R. JR. to HARRIS, KAMALA D. in every state
election_results_2024['D_name'] = 'HARRIS, KAMALA D.'

# we update D_electotral, R_electoral, and overall_winner to 226, 312, and R respectively
election_results_2024['D_electoral'] = 226
election_results_2024['R_electoral'] = 312
election_results_2024['overall_winner'] = 'R'

# dictionary with D_votes and R_votes for each state
votes_2024 = {
    'AL': {'D_votes': 769391, 'R_votes': 1457704},
    'AK': {'D_votes': 139812, 'R_votes': 184204},
    'AZ': {'D_votes': 1582860, 'R_votes': 1770242},
    'AR': {'D_votes': 396905, 'R_votes': 759241},
    'CA': {'D_votes': 9183800, 'R_votes': 5988823},
    'CO': {'D_votes': 1727603, 'R_votes': 1377078},
    'CT': {'D_votes': 994494, 'R_votes': 739472},
    'DE': {'D_votes': 289758, 'R_votes': 214351},
    'DC': {'D_votes': 289244, 'R_votes': 20874},
    'FL': {'D_votes': 4683038, 'R_votes': 6110125},
    'GA': {'D_votes': 2548017, 'R_votes': 2663117},
    'HI': {'D_votes': 312384, 'R_votes': 193169},
    'ID': {'D_votes': 274956, 'R_votes': 605144},
    'IL': {'D_votes': 3056201, 'R_votes': 2444517},
    'IN': {'D_votes': 1163657, 'R_votes': 1727624},
    'IA': {'D_votes': 706556, 'R_votes': 927734},
    'KS': {'D_votes': 531989, 'R_votes': 741464},
    'KY': {'D_votes': 701407, 'R_votes': 1338161},
    'LA': {'D_votes': 766870, 'R_votes': 1208505},
    'ME': {'D_votes': 430795, 'R_votes': 374972},
    'MD': {'D_votes': 1860918, 'R_votes': 1026549},
    'MA': {'D_votes': 2072571, 'R_votes': 1234961},
    'MI': {'D_votes': 2736533, 'R_votes': 2816636},
    'MN': {'D_votes': 1656979, 'R_votes': 1519032},
    'MS': {'D_votes': 465357, 'R_votes': 746305},
    'MO': {'D_votes': 1190823, 'R_votes': 1739047},
    'MT': {'D_votes': 231856, 'R_votes': 352001},
    'NE': {'D_votes': 362300, 'R_votes': 558389},
    'NV': {'D_votes': 705197, 'R_votes': 751205},
    'NH': {'D_votes': 418496, 'R_votes': 395531},
    'NJ': {'D_votes': 2218078, 'R_votes': 1966571},
    'NM': {'D_votes': 478727, 'R_votes': 423327},
    'NY': {'D_votes': 4404111, 'R_votes': 3478782},
    'NC': {'D_votes': 2715380, 'R_votes': 2898428},
    'ND': {'D_votes': 112327, 'R_votes': 246505},
    'OH': {'D_votes': 2476003, 'R_votes': 3116579},
    'OK': {'D_votes': 499599, 'R_votes': 1036213},
    'OR': {'D_votes': 1226991, 'R_votes': 909576},
    'PA': {'D_votes': 3421088, 'R_votes': 3542505},
    'RI': {'D_votes': 285156, 'R_votes': 214406},
    'SC': {'D_votes': 1028452, 'R_votes': 1483747},
    'SD': {'D_votes': 146859, 'R_votes': 272081},
    'TN': {'D_votes': 1055039, 'R_votes': 1964499},
    'TX': {'D_votes': 4806474, 'R_votes': 6375376},
    'UT': {'D_votes': 562560, 'R_votes': 883799},
    'VT': {'D_votes': 242235, 'R_votes': 119395},
    'VA': {'D_votes': 2335367, 'R_votes': 2075061},
    'WA': {'D_votes': 2241465, 'R_votes': 1526471},
    'WV': {'D_votes': 214309, 'R_votes': 533556},
    'WI': {'D_votes': 1668229, 'R_votes': 1697626},
    'WY': {'D_votes': 69527, 'R_votes': 192633}
}

# Function to calculate the required columns
def calculate_election_results(row, votes):
    D_votes = votes[row['state_po']]['D_votes']
    R_votes = votes[row['state_po']]['R_votes']
    
    if D_votes > R_votes:
        winner_votes = D_votes
        loser_votes = R_votes
        party_win = 'D'
    else:
        winner_votes = R_votes
        loser_votes = D_votes
        party_win = 'R'
    
    votes_to_flip = (winner_votes - loser_votes) // 2 + 1
    # winner state is true if party_win == 'R'. otherwise, it is false
    winner_state = party_win == 'R'
    
    return pd.Series([D_votes, R_votes, winner_votes, loser_votes, votes_to_flip, party_win, winner_state])

# Apply the function to each row in the DataFrame
election_results_2024[['D_votes', 'R_votes', 'winner_votes', 'loser_votes', 'votes_to_flip', 'party_win', 'winner_state']] = election_results_2024.apply(calculate_election_results, axis=1, votes=votes_2024)

# check if the winner is the same as the overall winner by adding the electoral votes for states with party_win == 'R' and seeing if we get 312
# if not, i made a mistake
if election_results_2024[election_results_2024['party_win'] == 'R']['electoral_votes'].sum() != 312:
    #print(election_results_2024[election_results_2024['party_win'] == 'R']['electoral_votes'].sum())
    print(f'R_electoral: {election_results_2024[election_results_2024["party_win"] == "R"]["electoral_votes"].sum()}\n D_electoral: {election_results_2024[election_results_2024["party_win"] == "D"]["electoral_votes"].sum()}')
    # print which states have party_win == 'D' sorted alphabetically and also how many electoral votes they have
    print(election_results_2024[election_results_2024['party_win'] == 'D'].sort_values(by='state')['electoral_votes'])
    #print(election_results_2024[election_results_2024['party_win'] == 'D']['state'])
    raise ValueError('Error in calculation of winner')

# create merged data frame which adds 2024 election results to the end of the summary_results.csv
election_results_df = pd.concat([election_results_df, election_results_2024], ignore_index=True)

# ensure numerical columns are saved as integers
election_results_df['electoral_votes'] = election_results_df['electoral_votes'].astype(int)
election_results_df['total_electoral_votes'] = election_results_df['total_electoral_votes'].astype(int)
election_results_df['D_electoral'] = election_results_df['D_electoral'].astype(int)
election_results_df['R_electoral'] = election_results_df['R_electoral'].astype(int)
election_results_df['winner_votes'] = election_results_df['winner_votes'].astype(int)
election_results_df['loser_votes'] = election_results_df['loser_votes'].astype(int)
election_results_df['votes_to_flip'] = election_results_df['votes_to_flip'].astype(int)


# Save the updated election results data
election_results_df.to_csv('summary_results_updated.csv', index=False)

# print the total R_votes and D_votes from all the states and DC in votes_2024
print(f'R_votes: {sum([data["R_votes"] for data in votes_2024.values()])}')
print(f'D_votes: {sum([data["D_votes"] for data in votes_2024.values()])}')