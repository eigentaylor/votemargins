import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from csveditinggeneral import generate_election_results_df

start_year = 1912
end_year = 1976
years = list(range(start_year, end_year + 1, 4))
recreate_csv = True  # Set this flag to True if you want to regenerate the CSV file every time

electoral_college_df = pd.read_csv('electoral_college.csv')

if not recreate_csv and os.path.exists(f'election_results_{start_year}_{end_year}.csv'):
    print(f'File election_results_{start_year}_{end_year}.csv exists')
    election_results_df = pd.read_csv(f'election_results_{start_year}_{end_year}.csv')
else:
    if recreate_csv:
        print(f'Recreating the file election_results_{start_year}_{end_year}.csv')
    else:
        print(f'File election_results_{start_year}_{end_year}.csv does not exist')
    # Load electoral college data and generate the results
    election_results_df = generate_election_results_df(years, electoral_college_df)
    # Save the generated results to a CSV file
    election_results_df.to_csv(f'election_results_{start_year}_{end_year}.csv', index=False)

# We want to find the minimum number of votes needed to flip the result of the election for each year
# We will take all the states that the overall winner won and find the optimal combination of states to flip which will push the loser to 270+ electoral votes

# Initialize a dictionary to store the results for each year
flip_results = {}

# open a text file flip_resuults.txt to store the results
with open('flip_results_{start_year}-{end_year}.txt', 'w') as f:
    f.write('')

# loop through the years in the election results data
for year in election_results_df['year'].unique():
    # get the election results for the year
    election_results = election_results_df[election_results_df['year'] == year]
    # get the total electoral votes
    total_electoral_votes = election_results['total_electoral_votes'].iloc[0]
    # get the number of votes needed to win
    #votes_to_win = total_electoral_votes // 2 + 1
    votes_to_win = election_results['electoral_votes_to_win'].iloc[0]
    # get the winner of the election
    winner = election_results['overall_winner'].iloc[0]
    # get the number of electoral votes the winner won
    winner_electoral_votes = election_results[winner + '_electoral'].iloc[0]
    # get the number of electoral votes the loser won
    loser = election_results['overall_runner_up'].iloc[0]
    winner_name = election_results[winner + '_name'].iloc[0]
    loser_name = election_results[loser + '_name'].iloc[0]
    loser_electoral_votes = election_results[loser + '_electoral'].iloc[0]
    # get the number of electoral votes to flip
    electoral_votes_to_flip = votes_to_win - loser_electoral_votes
    # get the states that the overall winner won
    winner_states = election_results[election_results['winner_state'] == True]
    if winner_states.empty:
        print(f'Year: {year} No winner states')
    # create a dict to store the name, electoral votes, and votes to flip for each state
    winner_states_dict = {}
    for index, row in winner_states.iterrows():
        state = row['state']
        electoral_votes = row['electoral_votes']
        votes_to_flip = row['votes_to_flip']
        winner_states_dict[state] = {'electoral_votes': electoral_votes, 'votes_to_flip': votes_to_flip, 'total_votes': row['totalvotes']}
    
    # sort the winner states by efficiencu (votes to flip / electoral votes)
    winner_states_dict = {k: v for k, v in sorted(winner_states_dict.items(), key=lambda item: item[1]['votes_to_flip'] / item[1]['electoral_votes'])}
    # Implement the DP table
    max_electoral_votes = sum([data['electoral_votes'] for data in winner_states_dict.values()])
    dp = [np.inf] * (max_electoral_votes + 1)
    dp[0] = 0
    
    # State tracking for backtracking later
    state_used = [None] * (max_electoral_votes + 1)
    
    # Process each state
    for state, data in winner_states_dict.items():
        electoral_votes = data['electoral_votes']
        votes_to_flip = data['votes_to_flip']
        for v in range(max_electoral_votes, electoral_votes - 1, -1):
            if dp[v - electoral_votes] + votes_to_flip < dp[v]:
                dp[v] = dp[v - electoral_votes] + votes_to_flip
                state_used[v] = state
    
    # Find the minimum votes needed to flip while ensuring 270 EC votes
    # do this by disregarding v < electoral_votes_to_flip
    # find the minimum dp[v] where v >= electoral_votes_to_flip
    min_dp = np.inf
    best_v = 0
    for v in range(electoral_votes_to_flip, max_electoral_votes + 1):
        if dp[v] < min_dp:
            min_dp = dp[v]
            best_v = v
    # Get the states that were flipped
    flipped_states = []
    v_current = best_v
    min_votes_to_flip = 0
    #print(f'best_v: {best_v}')
    
    while v_current > 0:
        state = state_used[v_current]
        min_votes_to_flip += winner_states_dict[state]['votes_to_flip']
        if state is not None:
            flipped_states.append(state)
            v_current -= winner_states_dict[state]['electoral_votes']
    
    # create dict for each flipped state along with the votes to flip
    flipped_states_votes_dict = {}
    for state in flipped_states:
        # add dict of EC votes and votes to flip
        flipped_states_votes_dict[state] = {'EC': winner_states_dict[state]['electoral_votes'], 'flipped votes': winner_states_dict[state]['votes_to_flip'], '% flipped': round(winner_states_dict[state]['votes_to_flip'] / winner_states_dict[state]['total_votes'] * 100, 3)}
    if flipped_states_votes_dict == {}:
        print(f'Year: {year} No states flipped')
    # sort the flipped states by flipped votes
    flipped_states_votes_dict = {k: v for k, v in sorted(flipped_states_votes_dict.items(), key=lambda item: item[1]['flipped votes'], reverse=False)}
    
    # get the total votes for the winner and loser
    total_votes_winner = election_results[winner + '_votes'].sum()
    total_votes_loser = election_results[loser + '_votes'].sum()
    popular_vote_margin = total_votes_winner - total_votes_loser
    abs_popular_vote_margin = abs(popular_vote_margin)
    # set the color to be blue for democrat and red for republican
    color = 'blue' if election_results['D_votes'].sum() > election_results['R_votes'].sum() else 'red'
    #pop_vote_dict[year] = {'margin': popular_vote_margin, 'color': color}
    if year == 2024:
        print(f'Pop Vote Margin: {popular_vote_margin}')
    
    # Store the result for the year
    flip_results[year] = {
        'min_votes_to_flip': min_votes_to_flip,
        'flipped_states': flipped_states,
        'electoral_votes_flipped': best_v,
        'margin': popular_vote_margin,
        'color': color, # color for the popular vote margin plot
        'flip_margin_ratio': 100 * min_votes_to_flip / abs_popular_vote_margin
    }
    # Print the results
    print(f'Year: {year}')
    print(f'Original Winner: {winner_name} ({winner}) with {winner_electoral_votes} electoral votes vs {loser_name} ({loser}) with {loser_electoral_votes} electoral votes')
    #print(f'Original Loser: {loser_name} ({loser}) with {loser_votes} electoral votes')
    print(f'Flipped states: {flipped_states_votes_dict} with {min_votes_to_flip} total flipped votes')
    #print(f'Flipped States: {flipped_states} with {min_votes_to_flip} total flipped votes')
    print(f'New Winner: {loser_name} ({loser}) with {best_v+loser_electoral_votes} electoral votes vs {winner_name} ({winner}) with {winner_electoral_votes-best_v} electoral votes')
    # save the results to a text file
    with open('flip_results.txt', 'a') as f:
        f.write(f'Year: {year}\n')
        f.write(f'Original Winner: {winner_name} ({winner}) with {winner_electoral_votes} electoral votes vs {loser_name} ({loser}) with {loser_electoral_votes} electoral votes\n')
        f.write(f'Flipped states: {flipped_states_votes_dict} with {min_votes_to_flip} total flipped votes\n')
        f.write(f'New Winner: {loser_name} ({loser}) with {best_v+loser_electoral_votes} electoral votes vs {winner_name} ({winner}) with {winner_electoral_votes-best_v} electoral votes\n\n')

# Output the results
flip_results_df = pd.DataFrame.from_dict(flip_results, orient='index')
flip_results_df.to_csv('flip_results.csv', index=True)

def plot_results(flip_results_df, flip_results, start_year, end_year, skip_reagan=False, path='img/', show_plot=True):
    prefix = 'noreg-' if skip_reagan else 'reg-'
    
    if skip_reagan:
        if 1980 in flip_results_df.index:
            flip_results_df = flip_results_df.drop(1980)
        if 1984 in flip_results_df.index:
            flip_results_df = flip_results_df.drop(1984)
    
    # create directory for images if it doesn't exist
    if not os.path.exists(path):
        os.makedirs(path)
    
    # min votes to flip plot
    plt.figure(figsize=(14, 6))

    plt.plot(flip_results_df.index, flip_results_df['min_votes_to_flip'])
    plt.xlabel('Year')
    # x ticks for each year
    plt.xticks(flip_results_df.index)
    plt.ylabel('Minimum Votes to Flip')
    # plot (x,y) labels for each point
    for i in range(len(flip_results_df)):
        min_votes_to_flip = flip_results_df['min_votes_to_flip'][flip_results_df.index[i]]
        formatted_votes = f'{min_votes_to_flip:,}'
        plt.text(flip_results_df.index[i], min_votes_to_flip, formatted_votes)
    plt.title(f'Minimum Votes to Flip Election Result by Year ({start_year}-{end_year})')

    # save plot to file
    plt.savefig(os.path.join(path, f'{prefix}flip_results.png'))
    if show_plot:
        plt.show()

    # plot the popular vote margin
    plt.figure(figsize=(14, 6))
    pop_vote_df = pd.DataFrame.from_dict(flip_results, orient='index')
    plt.bar(pop_vote_df.index, pop_vote_df['margin'], color=pop_vote_df['color'])
    # x ticks for each year
    plt.xticks(pop_vote_df.index)
    # plot a horizontal line at 0
    plt.axhline(y=0, color='black', linewidth=1)
    # put the margin on top of each bar
    for i in range(len(pop_vote_df)):
        margin = pop_vote_df['margin'][pop_vote_df.index[i]]
        formatted_margin = f'{margin:,}'
        # if the margin is negative, put the text below the bar
        if margin < 0:
            plt.text(pop_vote_df.index[i], margin, formatted_margin, ha='center', va='top')
        else:
            plt.text(pop_vote_df.index[i], margin, formatted_margin, ha='center')
    plt.xlabel('Year')
    plt.ylabel('Popular Vote Margin')
    plt.title(f'Popular Vote Margin by Year ({start_year}-{end_year})')
    #save plot to file
    plt.savefig(os.path.join(path, f'{prefix}pop_vote_margin.png'))
    if show_plot:
        plt.show()

    # Ratio of votes to flip vs popular vote margin
    plt.figure(figsize=(14, 6))

    # Plot the data
    plt.plot(flip_results_df.index, flip_results_df['flip_margin_ratio'])
    plt.xlabel('Year')
    plt.xticks(flip_results_df.index)
    plt.ylabel('Minimum Votes to Flip / Popular Vote Margin (%)')
    plt.title(f'Percentage Minimum Votes to Flip / Popular Vote Margin by Year ({start_year}-{end_year})')

    # Add text annotations for each point
    for i in range(len(flip_results_df)):
        ratio = flip_results_df['flip_margin_ratio'][flip_results_df.index[i]]
        formatted_ratio = f'{ratio:.5f}'
        plt.text(flip_results_df.index[i], ratio, formatted_ratio)

    # Save the figure
    plt.savefig(os.path.join(path, f'{prefix}flip_margin_ratio.png'))

    # Show the plot
    if show_plot:
        plt.show()

    # count up the frequency of flipped states
    flipped_states_count = {}
    for year in flip_results_df.index:
        for state in flip_results[year]['flipped_states']:
            if state in flipped_states_count:
                flipped_states_count[state] += 1
            else:
                flipped_states_count[state] = 1

    # sort the states by frequency
    flipped_states_count = {k: v for k, v in sorted(flipped_states_count.items(), key=lambda item: item[1], reverse=True)}
    # plot a bar chart of the frequency of flipped states
    plt.figure(figsize=(14, 6))
    plt.bar(flipped_states_count.keys(), flipped_states_count.values())
    plt.xlabel('State')
    plt.ylabel('Frequency of Flipping')
    plt.title(f'Frequency of Flipping by State ({start_year}-{end_year})')
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(os.path.join(path, f'{prefix}flipped_states_frequency.png'))
    if show_plot:
        plt.show()

plot_results(flip_results_df, flip_results, start_year, end_year, skip_reagan=False, show_plot=False)
if end_year > 1984:
    plot_results(flip_results_df, flip_results, start_year, end_year, skip_reagan=True, show_plot=False)