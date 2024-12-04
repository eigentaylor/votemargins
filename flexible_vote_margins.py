import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import time

# this is the same as calc_vote_margins.py but we can opt to flip states that are not the winner's states
# this gives a more efficient flip number in 1912 for example, where flippingh GA, UT, and VT (the latter two won by Taft instead of wilson) gives the same number of electoral votes as flipping LA and AL (states won by Wilson) but with less votes to flip
# overall, this makes 1912, 1944, and 1964 more efficient flips

# Set the dark theme for all plots
plt.style.use('dark_background')

# We want to find the minimum number of votes needed to flip the result of the election for each year
# We will take all the states that the overall winner won and find the optimal combination of states to flip which will push the loser to 270+ electoral votes

def get_flip_results(election_results_df, print_results=False):
    # Initialize a dictionary to store the results for each year
    flip_results = {}

    # open a text file flip_resuults.txt to store the results
    with open(f'results/flip_results_{start_year}-{end_year}.txt', 'w') as f:
        f.write('')
    # loop through the years in the election results data
    for year in election_results_df['year'].unique():
        # get the election results for the year
        election_results = election_results_df[election_results_df['year'] == year]
        # get the total electoral votes
        total_electoral_votes = election_results['total_electoral_votes'].iloc[0]
        # get the number of votes needed to win
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
        # get the states that the loser lost
        lost_states = election_results[election_results['party_win'] != loser]
        if lost_states.empty:
            print(f'Year: {year} No winner states')
        # create a dict to store the name, electoral votes, and votes to flip for each state
        winner_states_dict = {}
        for index, row in lost_states.iterrows():
            state = row['state']
            electoral_votes = row['electoral_votes']
            state_winner_votes = row[row['party_win'] + '_votes']
            runner_up_votes = row[loser + '_votes']
            votes_to_flip = (state_winner_votes - runner_up_votes) // 2 + 1
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
        # set the color to be blue for democrat and red for republican
        color = 'blue' if election_results['D_votes'].sum() > election_results['R_votes'].sum() else 'red'
        if year == 1960:
            # this year was f'd up. WTF ALABAMA AND MISSISSIPPI
            total_votes_winner = 34220984
            total_votes_loser = 34108157
            color = 'blue'
        popular_vote_margin = total_votes_winner - total_votes_loser
        abs_popular_vote_margin = abs(popular_vote_margin)
        total_votes_in_year = election_results['totalvotes'].sum()
        total_electoral_votes_in_year = election_results['electoral_votes'].sum()
        electoral_college_votes_to_win = total_electoral_votes_in_year // 2 + 1
        number_of_flipped_states = len(flipped_states)
        
        # Store the result for the year
        flip_results[year] = {
            'min_votes_to_flip': min_votes_to_flip,
            'flipped_states': flipped_states,
            'number_of_flipped_states': number_of_flipped_states,
            'electoral_votes_flipped': best_v,
            'total_electoral_votes': total_electoral_votes_in_year,
            'electoral_votes_to_win': electoral_college_votes_to_win,
            'popular_vote_margin': popular_vote_margin,
            'color': color, # color for the popular vote margin plot
            'flip_margin_ratio': 100 * min_votes_to_flip / total_votes_in_year,
            'popular_margin_ratio': 100 * popular_vote_margin / total_votes_in_year
        }
        generate_year_results(year, winner_name, winner, winner_electoral_votes, loser_name, loser, loser_electoral_votes, total_votes_winner, total_votes_loser, popular_vote_margin, electoral_college_votes_to_win, flipped_states_votes_dict, min_votes_to_flip, number_of_flipped_states, abs_popular_vote_margin, total_votes_in_year, best_v, print_results=print_results)

    # Output the results
    flip_results_df = pd.DataFrame.from_dict(flip_results, orient='index')
    flip_results_df.to_csv(f'results/flip_results-{start_year}-{end_year}.csv')

    # copy the input data to the results folder
    election_results_df.to_csv(f'results/election_results-{start_year}-{end_year}.csv', index=False)
    return flip_results_df, flip_results
        
def generate_year_results(year, winner_name, winner, winner_electoral_votes, loser_name, loser, loser_electoral_votes, total_votes_winner, total_votes_loser, popular_vote_margin, electoral_college_votes_to_win, flipped_states_votes_dict, min_votes_to_flip, number_of_flipped_states, abs_popular_vote_margin, total_votes_in_year, best_v, print_results=True):
    popular_vote_margin = total_votes_winner - total_votes_loser
    if print_results:
        # Print the results
        print(f'Year: {year}')
        print(f'Original Winner: {winner_name} ({winner}) with {winner_electoral_votes} electoral votes vs {loser_name} ({loser}) with {loser_electoral_votes} electoral votes ({electoral_college_votes_to_win} needed)')
        print(f'Flipped states: {flipped_states_votes_dict}')
        print(f'Total number of flipped votes: {min_votes_to_flip} across {number_of_flipped_states} states, Ratio to Popular Vote Margin: {100 * min_votes_to_flip / abs_popular_vote_margin:.5f}%, Ratio to Total Votes in Year: {100 * min_votes_to_flip / total_votes_in_year:.5f}%')
        print(f'New Winner: {loser_name} ({loser}) with {best_v+loser_electoral_votes} electoral votes vs {winner_name} ({winner}) with {winner_electoral_votes-best_v} electoral votes\n')
    # save the results to a text file in the /results folder
    # check if the folder exists, if not create it
    if not os.path.exists('results'):
        os.makedirs('results')
    # open the file and write the results
    with open(f'results/flip_results_{start_year}-{end_year}.txt', 'a') as f:
        f.write(f'Year: {year}\n')
        f.write(f'Original Winner: {winner_name} ({winner}) with {winner_electoral_votes} electoral votes vs {loser_name} ({loser}) with {loser_electoral_votes} electoral votes ({electoral_college_votes_to_win} needed)\n')
        popular_vote_winner = winner_name if popular_vote_margin > 0 else loser_name
        f.write(f'Popular Vote Margin: {popular_vote_margin}  for {popular_vote_winner}\n')
        f.write(f'Flipped states: {flipped_states_votes_dict}\n')
        f.write(f'Total number of flipped votes: {min_votes_to_flip} across {number_of_flipped_states} states, Ratio to Popular Vote Margin: {100 * min_votes_to_flip / abs_popular_vote_margin:.5f}%, Ratio to Total Votes in Year: {100 * min_votes_to_flip / total_votes_in_year:.5f}%\n')
        f.write(f'New Winner: {loser_name} ({loser}) with {best_v+loser_electoral_votes} electoral votes vs {winner_name} ({winner}) with {winner_electoral_votes-best_v} electoral votes\n\n')

def make_plot(flip_results_df, start_year, end_year, plot_count, key, ylabel, title, filename, folder_path='results/', show_plot=False, use_log_scale=False):
    plt.figure(figsize=(18, 8))
    plt.plot(flip_results_df.index, flip_results_df[key])
    plt.xlabel('Year')
    plt.xticks(flip_results_df.index, rotation=45, ha='right')
    plt.ylabel(ylabel)
    plt.title(title)
    
    # Check if all values are integers
    all_integers = flip_results_df[key].apply(lambda x: float(x).is_integer()).all()
    
    # Put labels
    for i in range(len(flip_results_df)):
        ratio = flip_results_df[key][flip_results_df.index[i]]
        if all_integers:
            formatted_ratio = f'{int(ratio):,}'
        else:
            formatted_ratio = f'{ratio:.5f}'
        plt.text(flip_results_df.index[i], ratio, formatted_ratio, ha='center', va='bottom')
    
    if use_log_scale:
        plt.yscale('log')
    plt.tight_layout()
    
    # add my name
    plt.text(0.5, 0.01, 'By: eigentaylor', ha='center', va='bottom', transform=plt.gca().transAxes)
    
    plt.savefig(os.path.join(folder_path, f'{plot_count}-{filename}.png'))
    print(f'Saved plot to {os.path.join(folder_path, f"{plot_count}-{filename}.png")}')
    if show_plot:
        plt.show()
        
def make_bar_plot(flip_results_df, start_year, end_year, plot_count, key, ylabel, title, filename, folder_path='results/', show_plot=False):
    # Check if all values are integers
    all_integers = flip_results_df[key].apply(lambda x: float(x).is_integer()).all()
    plt.figure(figsize=(18, 8))
    if key == 'popular_vote_margin' or key == 'popular_margin_ratio':
        plt.bar(flip_results_df.index, flip_results_df[key], color=flip_results_df['color'])
        # plot a horizontal dashed line at 0
        plt.axhline(y=0, color='white', linewidth=1, linestyle='dashed')
        # put the margin on top of each bar
        for i in range(len(flip_results_df)):
            margin = flip_results_df[key][flip_results_df.index[i]]
            #formatted_margin = f'{margin:,}'
            if all_integers:
                formatted_margin = f'{int(margin):,}'
            else:
                formatted_margin = f'{margin:.5f}'
            # if the margin is negative, put the text below the bar
            if margin < 0:
                plt.text(flip_results_df.index[i], margin, formatted_margin, ha='center', va='top')
            else:
                plt.text(flip_results_df.index[i], margin, formatted_margin, ha='center', va='bottom')
    else:
        plt.bar(flip_results_df.index, flip_results_df[key])
        
        # Check if all values are integers
        all_integers = flip_results_df[key].apply(lambda x: float(x).is_integer()).all()
        
        # Put labels
        for i in range(len(flip_results_df)):
            ratio = flip_results_df[key][flip_results_df.index[i]]
            if all_integers:
                formatted_ratio = f'{int(ratio):,}'
            else:
                formatted_ratio = f'{ratio:.5f}'
            # Place the label above or below the bar based on its value
            va = 'bottom' if ratio >= 0 else 'top'
            plt.text(flip_results_df.index[i], ratio, formatted_ratio, ha='center', va=va)
    
    plt.xlabel('Year')
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(flip_results_df.index, rotation=45, ha='right')
    plt.tight_layout()
    # add my name (since this is a bar plot, put it at the top)
    plt.text(0.5, 0.99, 'By: eigentaylor', ha='center', va='top', transform=plt.gca().transAxes)
    plt.savefig(os.path.join(folder_path, f'{plot_count}-{filename}.png'))
    print(f'Saved plot to {os.path.join(folder_path, f"{plot_count}-{filename}.png")}')
    if show_plot:
        plt.show()
        
def make_state_frequency_plot(flip_results_df, start_year, end_year, plot_count, folder_path='results/', show_plot=False):
    # make flipped_states_count dict
    flipped_states_count = {}
    for index, row in flip_results_df.iterrows():
        for state in row['flipped_states']:
            if state not in flipped_states_count:
                flipped_states_count[state] = 1
            else:
                flipped_states_count[state] += 1
    # sort the dict by frequency
    flipped_states_count = {k: v for k, v in sorted(flipped_states_count.items(), key=lambda item: item[1], reverse=True)}
    plt.figure(figsize=(18, 8))
    plt.bar(flipped_states_count.keys(), flipped_states_count.values())
    plt.xlabel('State')
    plt.ylabel('Frequency of Flipping')
    plt.title(f'Frequency of Flipping by State ({start_year}-{end_year})')
    # put the numbers above the bars
    for i in range(len(flipped_states_count)):
        plt.text(i, list(flipped_states_count.values())[i], list(flipped_states_count.values())[i], ha='center', va='bottom')
    plt.xticks(rotation=90)
    plt.yticks(np.arange(0, max(flipped_states_count.values()) + 1, 1))
    plt.tight_layout()
    # add my name (since this is a bar plot, put it at the top)
    plt.text(0.5, 0.99, 'By: eigentaylor', ha='center', va='top', transform=plt.gca().transAxes)
    plt.savefig(os.path.join(folder_path, f'{plot_count}-flipped_states_frequency.png'))
    print(f'Saved plot to {os.path.join(folder_path, f"{plot_count}-flipped_states_frequency.png")}')
    if show_plot:
        plt.show()
    
def make_all_plots(flip_results_df, start_year, end_year, folder_path='results/', show_plot=False):
    # clean up the folder
    for file in os.listdir(folder_path):
        if file.endswith('.png'):
            os.remove(os.path.join(folder_path, file))
    plot_count = 1
    make_plot(flip_results_df, start_year, end_year, plot_count, 'min_votes_to_flip', 'Minimum Votes to Flip', f'Minimum Votes to Flip Election Result by Year ({start_year}-{end_year})', 'flip_results', folder_path, show_plot)
    plot_count += 1
    make_plot(flip_results_df, start_year, end_year, plot_count, 'flip_margin_ratio', 'Minimum Votes to Flip / Total Votes Cast in Year (%)', f'Percentage Minimum Votes to Flip / Total Votes Cast in Year ({start_year}-{end_year})', 'flip_margin_ratio_log', folder_path, show_plot, use_log_scale=True)
    plot_count += 1
    make_plot(flip_results_df, start_year, end_year, plot_count, 'flip_margin_ratio', 'Minimum Votes to Flip / Total Votes Cast in Year (%)', f'Percentage Minimum Votes to Flip / Total Votes Cast in Year ({start_year}-{end_year})', 'flip_margin_ratio', folder_path, show_plot, use_log_scale=False)
    plot_count += 1
    make_bar_plot(flip_results_df, start_year, end_year, plot_count, 'number_of_flipped_states', 'Number of Flipped States', f'Number of Flipped States by Year ({start_year}-{end_year})', 'number_of_flipped_states', folder_path, show_plot)
    plot_count += 1
    make_bar_plot(flip_results_df, start_year, end_year, plot_count, 'popular_vote_margin', 'Popular Vote Margin', f'Popular Vote Margin by Year ({start_year}-{end_year})', 'pop_vote_margin', folder_path, show_plot)
    plot_count += 1
    make_bar_plot(flip_results_df, start_year, end_year, plot_count, 'popular_margin_ratio', 'Popular Vote Margin / Total Votes Cast in Year (%)', f'Percentage Popular Vote Margin / Total Votes Cast in Year ({start_year}-{end_year})', 'pop_margin_ratio', folder_path, show_plot)
    plot_count += 1
    make_state_frequency_plot(flip_results_df, start_year, end_year, plot_count, folder_path, show_plot)
    
start_year = 1900
end_year = 2024
election_results_df = pd.read_csv('1900_2024_election_results.csv')

flip_results_df, flip_results = get_flip_results(election_results_df, print_results=True)
make_all_plots(flip_results_df, start_year, end_year, folder_path='results/', show_plot=False)