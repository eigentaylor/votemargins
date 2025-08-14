import os
import numpy as np
import matplotlib.pyplot as plt

# Always use dark theme here. The caller can override if desired before import.
plt.style.use('dark_background')


def make_plot(flip_results_df, start_year, end_year, plot_count, key, ylabel, title, filename, folder_path='results/', show_plot=False, use_log_scale=False, subplot_dual_log=False):
    """Make a line plot. If subplot_dual_log is True, create a 2-row subplot where
    the top row is the regular plot and the bottom row is the same plot in log (or symlog) scale.
    """
    data = flip_results_df[key].astype(float)

    # Check if all values are integers
    all_integers = data.apply(lambda x: float(x).is_integer()).all()

    # readability settings
    title_fs = 20
    label_fs = 14
    tick_fs = 12
    data_label_fs = 10
    data_bbox = dict(facecolor='black', alpha=0.6, pad=2, edgecolor='none')
    # vibrant styling for dark background
    line_color = '#00d1ff'  # bright cyan
    line_width = 2.6
    marker_style = dict(marker='o', markersize=6, markeredgecolor='black', markeredgewidth=0.6)
    bar_color = '#ff6b6b'  # coral/salmon
    bar_edge = dict(edgecolor='black', linewidth=0.6)

    if subplot_dual_log:
        # Create two-row subplot: top regular, bottom log/symlog
        fig, (ax_top, ax_bottom) = plt.subplots(2, 1, figsize=(18, 12), sharex=True)

        # Top (regular)
        ax_top.plot(flip_results_df.index, data, color=line_color, linewidth=line_width, **marker_style)
        ax_top.set_ylabel(ylabel, fontsize=label_fs)
        ax_top.grid(True, linestyle='--', alpha=0.5)
        ax_top.set_title(title, fontsize=title_fs)
        ax_top.tick_params(axis='both', which='major', labelsize=tick_fs)

        # Compute small vertical offset so labels sit above/below the line
        y_range = data.max() - data.min()
        if y_range == 0:
            y_offset = abs(data.max()) * 0.01 if abs(data.max()) > 0 else 1.0
        else:
            y_offset = y_range * 0.03

        # Put labels on top
        for i in range(len(flip_results_df)):
            y = data.iloc[i]
            formatted = f'{int(y):,}' if all_integers else f'{y:.5f}'
            y_text = y + y_offset if y >= 0 else y - y_offset
            ax_top.text(flip_results_df.index[i], y_text, formatted, ha='center', va='bottom' if y >= 0 else 'top', fontsize=data_label_fs, color='white', bbox=data_bbox)

        # Bottom (log or symlog depending on data)
        ax_bottom.plot(flip_results_df.index, data, color=line_color, linewidth=line_width, alpha=0.9, **marker_style)

        # Choose log vs symlog if non-positive values exist
        if (data <= 0).any():
            # use symmetric log so negative values are represented; small linthresh avoids collapse
            ax_bottom.set_yscale('symlog', linthresh=1e-6)
            bottom_label = ylabel + ' (symlog)'
        else:
            ax_bottom.set_yscale('log')
            bottom_label = ylabel + ' (log)'

        ax_bottom.set_ylabel(bottom_label, fontsize=label_fs)
        ax_bottom.grid(True, linestyle='--', alpha=0.5)
        ax_bottom.tick_params(axis='both', which='major', labelsize=tick_fs)

        # Put labels on bottom
        for i in range(len(flip_results_df)):
            y = data.iloc[i]
            formatted = f'{int(y):,}' if all_integers else f'{y:.2e}'
            # place slightly above for positive, below for negative
            y_text = y + y_offset if y >= 0 else y - y_offset
            va = 'bottom' if y >= 0 else 'top'
            ax_bottom.text(flip_results_df.index[i], y_text, formatted, ha='center', va=va, fontsize=data_label_fs, color='white', bbox=data_bbox)

        # X ticks on shared axis
        ax_bottom.set_xlabel('Year', fontsize=label_fs)
        ax_bottom.set_xticks(flip_results_df.index)
        for label in ax_bottom.get_xticklabels():
            label.set_rotation(45)
            label.set_ha('right')
            label.set_fontsize(tick_fs)

        # Credit
        fig.text(0.5, 0.01, 'By: eigentaylor', ha='center', va='bottom')
        fig.tight_layout()

        os.makedirs(folder_path, exist_ok=True)
        fig.savefig(os.path.join(folder_path, f'{plot_count}-{filename}.png'))
        if show_plot:
            plt.show()
        plt.close(fig)
        return

    # Default single-axes behavior
    plt.figure(figsize=(18, 8))
    plt.plot(flip_results_df.index, data, color=line_color, linewidth=line_width, **marker_style)
    plt.xlabel('Year', fontsize=label_fs)
    plt.xticks(flip_results_df.index, rotation=45, ha='right', fontsize=tick_fs)
    plt.ylabel(ylabel, fontsize=label_fs)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.title(title, fontsize=title_fs)
    plt.gca().tick_params(axis='both', which='major', labelsize=tick_fs)

    # Put labels with offset and bbox for readability
    y_range = data.max() - data.min()
    if y_range == 0:
        y_offset = abs(data.max()) * 0.01 if abs(data.max()) > 0 else 1.0
    else:
        y_offset = y_range * 0.03

    for i in range(len(flip_results_df)):
        ratio = data.iloc[i]
        formatted_ratio = f'{int(ratio):,}' if all_integers else f'{ratio:.5f}'
        y_text = ratio + y_offset if ratio >= 0 else ratio - y_offset
        plt.text(flip_results_df.index[i], y_text, formatted_ratio, ha='center', va='bottom' if ratio>=0 else 'top', fontsize=data_label_fs, color='white', bbox=data_bbox)

    if use_log_scale:
        plt.yscale('log')
    plt.tight_layout()

    # add credit
    plt.text(0.5, 0.01, 'By: eigentaylor', ha='center', va='bottom', transform=plt.gca().transAxes, fontsize=10)

    os.makedirs(folder_path, exist_ok=True)
    plt.savefig(os.path.join(folder_path, f'{plot_count}-{filename}.png'))
    if show_plot:
        plt.show()


def make_bar_plot(flip_results_df, start_year, end_year, plot_count, key, ylabel, title, filename, folder_path='results/', show_plot=False, subplot_dual_log=False):
    """Make a bar plot. If subplot_dual_log is True, create a 2-row subplot where
    the top row is the regular bar chart and the bottom row is the same data in log (or symlog) scale.
    """
    data = flip_results_df[key].astype(float)
    all_integers = data.apply(lambda x: float(x).is_integer()).all()

    # readability and styling (match line plots)
    title_fs = 20
    label_fs = 14
    tick_fs = 12
    data_label_fs = 10
    data_bbox = dict(facecolor='black', alpha=0.6, pad=2, edgecolor='none')
    bar_color_default = '#ff6b6b'
    bar_edge = dict(edgecolor='black', linewidth=0.6)

    # party colors (vibrant)
    party_colors = {
        'D': 'deepskyblue',  # '#2b83ba',
        'R': 'red',  # '#ff4d4d',
    }

    # Keys that should use the electoral-college loser color
    ec_loser_keys = {'min_votes_to_flip', 'number_of_flipped_states', 'flip_margin_ratio'}

    # compute per-row colors when requested
    def _compute_ec_loser_colors(df):
        #  flip colors from the color column
        if 'color' in df.columns:
            colors = df['color'].apply(lambda c: party_colors['D'] if str(c).strip() == 'red' else party_colors['R']).copy()
            # Force 2000 and 2016 to use party_colors['D']
            for year in [2000, 2016]:
                if year in df.index:
                    colors.loc[year] = party_colors['D']
            return colors
        # try overall_winner or winner_party columns to infer loser
        if 'overall_winner' in df.columns:
            return df['overall_winner'].apply(lambda w: party_colors['D'] if str(w).strip() == 'R' else party_colors['R'])
        if 'winner_party' in df.columns:
            return df['winner_party'].apply(lambda w: party_colors['D'] if str(w).strip() == 'R' else party_colors['R'])
        # fallback: uniform default
        return [bar_color_default] * len(df)
    
    # choose default colors per row; for some keys use EC-loser colors
    default_colors = flip_results_df['color'] if 'color' in flip_results_df.columns else bar_color_default
    if key in ec_loser_keys:
        #default_colors = flip_results_df['color'] if 'color' in flip_results_df.columns else bar_color_default#
        default_colors = _compute_ec_loser_colors(flip_results_df)
        # flip the colors for 2000 and 2016
        # if 2000 in flip_results_df.index:
        #     default_colors[2000] = party_colors['D']
        # if 2016 in flip_results_df.index:
        #     default_colors[2016] = party_colors['D']
    else:
        default_colors = flip_results_df['color'] if 'color' in flip_results_df.columns else bar_color_default

    if subplot_dual_log:
        fig, (ax_top, ax_bottom) = plt.subplots(2, 1, figsize=(18, 12), sharex=True)

        # Top
        top_colors = default_colors
        if key in ('popular_vote_margin', 'popular_margin_ratio'):
            ax_top.bar(flip_results_df.index, data, color=top_colors, **bar_edge)
            ax_top.axhline(y=0, color='white', linewidth=1, linestyle='dashed')
        else:
            ax_top.bar(flip_results_df.index, data, color=top_colors, **bar_edge)

        # Title/labels/fonts
        ax_top.set_ylabel(ylabel, fontsize=label_fs)
        ax_top.set_title(title, fontsize=title_fs)
        ax_top.grid(True, linestyle='--', alpha=0.5)
        ax_top.tick_params(axis='both', which='major', labelsize=tick_fs)

        # Compute vertical offset for bar labels
        y_max = data.max()
        y_min = data.min()
        y_range = y_max - y_min
        if y_range == 0:
            y_offset = abs(y_max) * 0.01 if abs(y_max) > 0 else 1.0
        else:
            y_offset = y_range * 0.03

        # Labels on top
        for i in range(len(flip_results_df)):
            y = data.iloc[i]
            formatted = f'{int(y):,}' if all_integers else f'{y:.5f}'
            y_text = y + y_offset if y >= 0 else y - y_offset
            va = 'bottom' if y >= 0 else 'top'
            ax_top.text(flip_results_df.index[i], y_text, formatted, ha='center', va=va, fontsize=data_label_fs, color='white', bbox=data_bbox)

        # Bottom (log or symlog depending on data)
        bottom_colors = default_colors
        if key in ('popular_vote_margin', 'popular_margin_ratio'):
            ax_bottom.bar(flip_results_df.index, data, color=bottom_colors, **bar_edge)
            ax_bottom.axhline(y=0, color='white', linewidth=1, linestyle='dashed')
        else:
            ax_bottom.bar(flip_results_df.index, data, color=bottom_colors, **bar_edge)

        if (data <= 0).any():
            ax_bottom.set_yscale('symlog', linthresh=1e-6)
            bottom_label = ylabel + ' (symlog)'
        else:
            ax_bottom.set_yscale('log')
            bottom_label = ylabel + ' (log)'

        ax_bottom.set_ylabel(bottom_label, fontsize=label_fs)
        ax_bottom.grid(True, linestyle='--', alpha=0.5)
        ax_bottom.tick_params(axis='both', which='major', labelsize=tick_fs)

        # Labels on bottom
        for i in range(len(flip_results_df)):
            y = data.iloc[i]
            formatted = f'{int(y):,}' if all_integers else f'{y:.5f}'
            y_text = y + y_offset if y >= 0 else y - y_offset
            va = 'bottom' if y >= 0 else 'top'
            ax_bottom.text(flip_results_df.index[i], y_text, formatted, ha='center', va=va, fontsize=data_label_fs, color='white', bbox=data_bbox)

        ax_bottom.set_xlabel('Year', fontsize=label_fs)
        ax_bottom.set_xticks(flip_results_df.index)
        for label in ax_bottom.get_xticklabels():
            label.set_rotation(45)
            label.set_ha('right')
            label.set_fontsize(tick_fs)

        fig.text(0.5, 0.99, 'By: eigentaylor', ha='center', va='top')
        fig.tight_layout()
        os.makedirs(folder_path, exist_ok=True)
        fig.savefig(os.path.join(folder_path, f'{plot_count}-{filename}.png'))
        if show_plot:
            plt.show()
        plt.close(fig)
        return

    # Default single-axes behavior
    plt.figure(figsize=(18, 8))
    
    plt.bar(flip_results_df.index, flip_results_df[key], color=default_colors, **bar_edge)
    if key in ('popular_vote_margin', 'popular_margin_ratio'):
        plt.axhline(y=0, color='white', linewidth=1, linestyle='dashed')

    # label fonts and title
    plt.xlabel('Year', fontsize=label_fs)
    plt.ylabel(ylabel, fontsize=label_fs)
    plt.title(title, fontsize=title_fs)
    plt.xticks(flip_results_df.index, rotation=45, ha='right', fontsize=tick_fs)
    plt.grid(True, linestyle='--', alpha=0.5)

    # Add readable data labels with bbox and offset
    y_max = data.max()
    y_min = data.min()
    y_range = y_max - y_min
    if y_range == 0:
        y_offset = abs(y_max) * 0.01 if abs(y_max) > 0 else 1.0
    else:
        y_offset = y_range * 0.03

    for i in range(len(flip_results_df)):
        y = data.iloc[i]
        formatted = f'{int(y):,}' if all_integers else f'{y:.5f}'
        y_text = y + y_offset if y >= 0 else y - y_offset
        va = 'bottom' if y >= 0 else 'top'
        plt.text(flip_results_df.index[i], y_text, formatted, ha='center', va=va, fontsize=data_label_fs, color='white', bbox=data_bbox)

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


def make_all_plots(flip_results_df, start_year, end_year, folder_path='results/', show_plot=False, clear_files=False):
    os.makedirs(folder_path, exist_ok=True)
    if clear_files:
        # Remove all .png files in folder_path and its subfolders
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.png'):
                    os.remove(os.path.join(root, file))

    plot_count = 1
    # create a dual-subplot version: top regular, bottom log/symlog
    make_bar_plot(flip_results_df, start_year, end_year, plot_count, 'flip_margin_ratio', 'Minimum Votes to Flip / Total Votes Cast in Year (%)', f'Percentage Minimum Votes to Flip / Total Votes Cast in Year ({start_year}-{end_year})', 'min_votes_to_flip_ratio', folder_path, show_plot, subplot_dual_log=True)
    plot_count += 1
    # make_plot(flip_results_df, start_year, end_year, plot_count, 'flip_margin_ratio', 'Minimum Votes to Flip / Total Votes Cast in Year (%)', f'Percentage Minimum Votes to Flip / Total Votes Cast in Year ({start_year}-{end_year})', 'flip_margin_ratio', folder_path, show_plot, use_log_scale=False)
    # plot_count += 1
    make_bar_plot(flip_results_df, start_year, end_year, plot_count, 'popular_margin_ratio', 'Popular Vote Margin / Total Votes Cast in Year (%)', f'Percentage Popular Vote Margin / Total Votes Cast in Year ({start_year}-{end_year})', 'pop_margin_ratio', folder_path, show_plot, subplot_dual_log=False)
    plot_count += 1
    make_bar_plot(flip_results_df, start_year, end_year, plot_count, 'min_votes_to_flip', 'Minimum Votes to Flip', f'Minimum Votes to Flip Election Result by Year ({start_year}-{end_year})', 'min_votes_to_flip_raw', folder_path, show_plot, subplot_dual_log=True)
    plot_count += 1
    make_bar_plot(flip_results_df, start_year, end_year, plot_count, 'popular_vote_margin', 'Popular Vote Margin', f'Popular Vote Margin by Year ({start_year}-{end_year})', 'pop_vote_margin_raw', folder_path, show_plot, subplot_dual_log=False)
    plot_count += 1
    make_bar_plot(flip_results_df, start_year, end_year, plot_count, 'number_of_flipped_states', 'Number of Flipped States', f'Number of Flipped States by Year ({start_year}-{end_year})', 'number_of_flipped_states', folder_path, show_plot)
    plot_count += 1
    make_state_frequency_plot(flip_results_df, start_year, end_year, plot_count, folder_path, show_plot)
