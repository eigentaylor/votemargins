import os
import numpy as np
import matplotlib.pyplot as plt

# Always use dark theme here. The caller can override if desired before import.
plt.style.use('dark_background')


def make_plot(flip_results_df, start_year, end_year, plot_count, key, ylabel, title, filename, folder_path='results/', show_plot=False, use_log_scale=False):
    plt.figure(figsize=(18, 8))
    plt.plot(flip_results_df.index, flip_results_df[key])
    plt.xlabel('Year')
    plt.xticks(flip_results_df.index, rotation=45, ha='right')
    plt.ylabel(ylabel)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.title(title)

    # Check if all values are integers
    all_integers = flip_results_df[key].apply(lambda x: float(x).is_integer()).all()

    # Put labels
    for i in range(len(flip_results_df)):
        ratio = flip_results_df[key][flip_results_df.index[i]]
        formatted_ratio = f'{int(ratio):,}' if all_integers else f'{ratio:.5f}'
        plt.text(flip_results_df.index[i], ratio, formatted_ratio, ha='center', va='bottom')

    if use_log_scale:
        plt.yscale('log')
    plt.tight_layout()

    # add credit
    plt.text(0.5, 0.01, 'By: eigentaylor', ha='center', va='bottom', transform=plt.gca().transAxes)

    os.makedirs(folder_path, exist_ok=True)
    plt.savefig(os.path.join(folder_path, f'{plot_count}-{filename}.png'))
    if show_plot:
        plt.show()


def make_bar_plot(flip_results_df, start_year, end_year, plot_count, key, ylabel, title, filename, folder_path='results/', show_plot=False):
    all_integers = flip_results_df[key].apply(lambda x: float(x).is_integer()).all()
    plt.figure(figsize=(18, 8))
    if key in ('popular_vote_margin', 'popular_margin_ratio'):
        plt.bar(flip_results_df.index, flip_results_df[key], color=flip_results_df['color'])
        plt.axhline(y=0, color='white', linewidth=1, linestyle='dashed')
        for i in range(len(flip_results_df)):
            margin = flip_results_df[key][flip_results_df.index[i]]
            formatted_margin = f'{int(margin):,}' if all_integers else f'{margin:.5f}'
            va = 'top' if margin < 0 else 'bottom'
            plt.text(flip_results_df.index[i], margin, formatted_margin, ha='center', va=va)
    else:
        plt.bar(flip_results_df.index, flip_results_df[key])
        for i in range(len(flip_results_df)):
            ratio = flip_results_df[key][flip_results_df.index[i]]
            formatted_ratio = f'{int(ratio):,}' if all_integers else f'{ratio:.5f}'
            va = 'bottom' if ratio >= 0 else 'top'
            plt.text(flip_results_df.index[i], ratio, formatted_ratio, ha='center', va=va)

    plt.xlabel('Year')
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(flip_results_df.index, rotation=45, ha='right')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.text(0.5, 0.99, 'By: eigentaylor', ha='center', va='top', transform=plt.gca().transAxes)

    os.makedirs(folder_path, exist_ok=True)
    plt.savefig(os.path.join(folder_path, f'{plot_count}-{filename}.png'))
    if show_plot:
        plt.show()


def make_state_frequency_plot(flip_results_df, start_year, end_year, plot_count, folder_path='results/', show_plot=False):
    flipped_states_count = {}
    for _, row in flip_results_df.iterrows():
        for state in row['flipped_states']:
            flipped_states_count[state] = flipped_states_count.get(state, 0) + 1

    flipped_states_count = dict(sorted(flipped_states_count.items(), key=lambda item: item[1], reverse=True))

    plt.figure(figsize=(18, 8))
    plt.bar(flipped_states_count.keys(), flipped_states_count.values())
    plt.xlabel('State')
    plt.ylabel('Frequency of Flipping')
    plt.title(f'Frequency of Flipping by State ({start_year}-{end_year})')

    for i, v in enumerate(flipped_states_count.values()):
        plt.text(i, v, v, ha='center', va='bottom')

    plt.xticks(rotation=90)
    plt.yticks(np.arange(0, max(flipped_states_count.values()) + 1, 1))
    plt.tight_layout()
    plt.text(0.5, 0.99, 'By: eigentaylor', ha='center', va='top', transform=plt.gca().transAxes)

    os.makedirs(folder_path, exist_ok=True)
    plt.savefig(os.path.join(folder_path, f'{plot_count}-flipped_states_frequency.png'))
    if show_plot:
        plt.show()


def make_all_plots(flip_results_df, start_year, end_year, folder_path='results/', show_plot=False):
    os.makedirs(folder_path, exist_ok=True)
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
