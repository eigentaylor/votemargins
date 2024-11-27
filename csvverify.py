import pandas as pd
import numpy as np

# Load the dataset
election_results_df = pd.read_csv('summary_results_split_verify.csv')

# 2016 seems off, let's check the data
# print total democrat electoral votes in 2016
print(election_results_df[(election_results_df['year'] == 2016) & (election_results_df['party_win'] == 'D')]['electoral_votes'].sum())
# print all states that gave their electoral college votes to the democratic candidate in 2016
print(election_results_df[(election_results_df['year'] == 2016) & (election_results_df['winner_state'] == False)])
