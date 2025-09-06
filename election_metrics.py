import os
import math
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from plotting import make_plot, make_bar_plot

from analysis import compute_flip_for_year


plt.style.use('dark_background')


def _safe_int(x, default: int = 0) -> int:
    try:
        if pd.isna(x):
            return default
        return int(x)
    except Exception:
        try:
            v = pd.to_numeric(x, errors='coerce')
            return default if pd.isna(v) else int(v)
        except Exception:
            return default


def _get_num(row: pd.Series, col: str) -> int:
    try:
        v = row[col]
    except Exception:
        return 0
    try:
        v = pd.to_numeric(v, errors='coerce')
    except Exception:
        v = np.nan
    return 0 if pd.isna(v) else int(v)


def _two_party_totals(df: pd.DataFrame) -> Tuple[int, int, int]:
    D_total = pd.to_numeric(df['D_votes'], errors='coerce').fillna(0).astype(int).sum()
    R_total = pd.to_numeric(df['R_votes'], errors='coerce').fillna(0).astype(int).sum()
    S = D_total + R_total
    return D_total, R_total, S


def _state_two_party(row: pd.Series) -> int:
    d = _get_num(row, 'D_votes')
    r = _get_num(row, 'R_votes')
    return int(d + r)


def _state_margin_votes(row: pd.Series) -> int:
    d = _get_num(row, 'D_votes')
    r = _get_num(row, 'R_votes')
    return abs(d - r)


def _votes_to_flip_state(row: pd.Series) -> int:
    # Minimum integer votes to change outcome under a symmetric shift assumption
    margin = _state_margin_votes(row)
    return margin // 2 + 1 if margin > 0 else 0


def _uniform_swing_sigma(year_df: pd.DataFrame, loser: str, votes_needed_ev: int) -> float:
    if votes_needed_ev <= 0:
        return 0.0

    # States the loser lost (i.e., states currently won by the other party)
    lost_states = year_df[year_df['party_win'] != loser].copy()

    # threshold to flip state i under a uniform two-party swing = f_i / (D_i + R_i)
    thresholds: List[Tuple[float, int]] = []  # (threshold_i, electoral_votes)
    for _, row in lost_states.iterrows():
        two_party = _state_two_party(row)
        if two_party <= 0:
            continue
        f_i = _votes_to_flip_state(row)
        thr = f_i / two_party
        ev = _get_num(row, 'electoral_votes')
        thresholds.append((thr, ev))

    thresholds.sort(key=lambda x: x[0])

    acc_ev = 0
    sigma = math.nan
    for thr, ev in thresholds:
        acc_ev += ev
        if acc_ev >= votes_needed_ev:
            sigma = thr
            break
    return float(sigma)


def _state_concentration_risk(flipped_states: List[str], winner_states_dict: Dict[str, Dict[str, int]], f: int) -> float:
    if f <= 0 or not flipped_states:
        return 0.0
    sum_sq = 0
    for st in flipped_states:
        f_i = int(winner_states_dict[st]['votes_to_flip'])
        sum_sq += f_i * f_i
    if sum_sq == 0:
        return 0.0
    # R = f^2 / sum(f_i^2); lower means more concentrated reliance
    return (f * f) / sum_sq


from typing import Union

def compute_year_metrics(year_df: pd.DataFrame, alpha: float = 0.5,
                          recount_threshold: float = 0.005,
                          brittleness_threshold: float = 0.02) -> Dict[str, Union[int, float, str]]:
    year = int(year_df['year'].iloc[0])

    # Winner/loser parties for the year
    winner_party = str(year_df['overall_winner'].iloc[0]).strip()
    loser_party = 'D' if winner_party == 'R' else 'R'

    # Two-party totals
    D_total, R_total, S = _two_party_totals(year_df)
    m = abs(D_total - R_total) / S if S > 0 else float('nan')

    # Electoral tallies
    total_ec = _safe_int(year_df['total_electoral_votes'].iloc[0])
    ev_to_win = _safe_int(year_df['electoral_votes_to_win'].iloc[0])

    D_ec = _safe_int(year_df['D_electoral'].iloc[0])
    R_ec = _safe_int(year_df['R_electoral'].iloc[0])

    winner_ec = D_ec if winner_party == 'D' else R_ec
    loser_ec = R_ec if winner_party == 'D' else D_ec

    votes_needed_ev = max(ev_to_win - loser_ec, 0)

    # Flip computation for f and flipped set
    flipped_states, f, best_v, winner_states_dict = compute_flip_for_year(year_df, loser_party, votes_needed_ev)

    # Derived shares
    winner_pop_two_party = D_total if winner_party == 'D' else R_total
    PV_share = winner_pop_two_party / S if S > 0 else float('nan')
    EC_share = (winner_ec / total_ec) if total_ec > 0 else float('nan')

    # Combined closeness metrics
    f_over_S = f / S if S > 0 else float('nan')
    C1 = math.sqrt((m * m) + (f_over_S * f_over_S)) if (not math.isnan(m) and not math.isnan(f_over_S)) else float('nan')
    C2 = max(m, f_over_S) if (not math.isnan(m) and not math.isnan(f_over_S)) else float('nan')
    # Given formula: 2*m*f / (S + m*f)
    denom_C3 = (S + (m * f)) if (S > 0) else float('nan')
    C3 = (2 * m * f) / denom_C3 if denom_C3 and denom_C3 > 0 else float('nan')
    C4 = (m ** alpha) * (f_over_S ** (1 - alpha)) if (not math.isnan(m) and not math.isnan(f_over_S)) else float('nan')
    C5 = f / (m * S) if (S > 0 and m > 0) else float('inf') if (S > 0 and m == 0) else float('nan')

    # Chaos/distortion metrics
    popular_vote_safety = m
    electoral_college_safety = f_over_S

    R_concentration = _state_concentration_risk(flipped_states, winner_states_dict, f)
    sigma = _uniform_swing_sigma(year_df, loser_party, votes_needed_ev)

    # Vote Efficiency Gap
    if PV_share == 0.5:
        eta = float('inf')
    else:
        denom = (PV_share - 0.5)
        def transform(x):
            # Normalize to [-1, 1]
            return np.arctan(x / 5) / (np.pi / 2)
        eta = transform((EC_share - 0.5) / denom - 1 if denom != 0 else float('inf'))

    # Recount Vulnerability
    close_states_ev = 0
    for _, row in year_df.iterrows():
        tp = _state_two_party(row)
        if tp <= 0:
            continue
        margin_share = _state_margin_votes(row) / tp
        if margin_share < recount_threshold:
            close_states_ev += _get_num(row, 'electoral_votes')
    V_recount = close_states_ev / total_ec if total_ec > 0 else float('nan')

    # Coalition Brittleness: count of winner-won states with margin < 2%
    brittleness = 0
    for _, row in year_df.iterrows():
        if str(row['party_win']).strip() != winner_party:
            continue
        tp = _state_two_party(row)
        if tp <= 0:
            continue
        margin_share = _state_margin_votes(row) / tp
        if margin_share < brittleness_threshold:
            brittleness += 1

    # Institutional Distortion Index
    if m == 0 or math.isnan(m) or math.isnan(f_over_S):
        distortion = float('nan')
    else:
        distortion = abs(f_over_S - m) / m

    return {
        'year': year,
        'winner_party': winner_party,
        'loser_party': loser_party,
        'D_total': D_total,
        'R_total': R_total,
        'S_two_party': S,
        'winner_EC': winner_ec,
        'loser_EC': loser_ec,
        'total_EC': total_ec,
        'PV_share': PV_share,
        'EC_share': EC_share,
        'm': m,
        'f': int(f),
        'f_over_S': f_over_S,
        'alpha': alpha,
        'C1_euclidean': C1,
        'C2_max': C2,
        'C3_harmonic_like': C3,
        'C4_weighted_geom': C4,
        'C5_efficiency_ratio': C5,
        'popular_vote_safety': popular_vote_safety,
        'electoral_college_safety': electoral_college_safety,
        'state_concentration_R': R_concentration,
        'margin_sensitivity_sigma': sigma,
        'vote_efficiency_gap_eta': eta,
        'recount_vulnerability_V': V_recount,
        'coalition_brittleness_count': brittleness,
        'institutional_distortion_D': distortion,
    }


def compute_metrics_for_all_years(csv_path: str = '1900_2024_election_results.csv',
                                  alpha: float = 0.5,
                                  recount_threshold: float = 0.005,
                                  brittleness_threshold: float = 0.02) -> pd.DataFrame:
    # Handle leading file path comment lines in CSV
    df = pd.read_csv(csv_path, comment='/', engine='python')

    # Clean expected columns to numeric where needed
    for col in ['D_votes', 'R_votes', 'electoral_votes', 'totalvotes', 'D_electoral', 'R_electoral',
                'total_electoral_votes', 'electoral_votes_to_win']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    metrics: List[Dict[str, Union[int, float, str]]] = []
    for year, year_df in df.groupby('year'):
        metrics.append(compute_year_metrics(year_df.copy(), alpha=alpha,
                                            recount_threshold=recount_threshold,
                                            brittleness_threshold=brittleness_threshold))

    metrics_df = pd.DataFrame(metrics).sort_values('year').reset_index(drop=True)
    return metrics_df


def _plot_series(years: List[int], values: List[float], ylabel: str, title: str, out_path: str,
                 is_percentage: bool = False, bar: bool = False):
    """Deprecated internal plotting (kept for compatibility). Election metrics now uses
    plotting.make_plot/make_bar_plot for consistent styling. This function is unused.
    """
    df_tmp = pd.DataFrame({"series": values}, index=years)
    folder = os.path.dirname(out_path)
    base = os.path.basename(out_path)
    if base.lower().endswith('.png'):
        base = base[:-4]
    # try to split like '01-C1_euclidean'
    if '-' in base:
        plot_count, filename = base.split('-', 1)
    else:
        plot_count, filename = '00', base
    if bar:
        make_bar_plot(df_tmp, years[0], years[-1], plot_count, 'series', ylabel, title, filename, folder_path=folder, show_plot=False)
    else:
        make_bar_plot(df_tmp, years[0], years[-1], plot_count, 'series', ylabel, title, filename, folder_path=folder, show_plot=False)


def write_outputs(metrics_df: pd.DataFrame, results_dir: str = 'results') -> None:
    os.makedirs(results_dir, exist_ok=True)

    first_year = int(metrics_df['year'].min())
    last_year = int(metrics_df['year'].max())

    csv_out = os.path.join(results_dir, f'election_metrics-{first_year}-{last_year}.csv')
    metrics_df.to_csv(csv_out, index=False)

    plots_dir = os.path.join(results_dir, 'election_metrics')
    os.makedirs(plots_dir, exist_ok=True)

    # Define plotting order and labels
    plot_specs = [
        ('C1_euclidean', 'C1 (Euclidean Distance)', 'Combined Closeness C1'),
        ('C2_max', 'C2 (Max Metric)', 'Combined Closeness C2'),
        ('C3_harmonic_like', 'C3 (Harmonic-like)', 'Combined Closeness C3'),
        ('C4_weighted_geom', 'C4 (Weighted Geometric Mean)', 'Combined Closeness C4'),
        ('C5_efficiency_ratio', 'C5 (Electoral Efficiency Ratio)', 'Combined Closeness C5'),
        ('popular_vote_safety', 'Popular Vote Safety (m)', 'Popular Vote Safety'),
        ('electoral_college_safety', 'Electoral College Safety (f/S)', 'Electoral College Safety'),
        ('state_concentration_R', 'State Concentration Risk (R)', 'State Concentration Risk'),
        ('margin_sensitivity_sigma', 'Margin Sensitivity (sigma)', 'Margin Sensitivity'),
        ('vote_efficiency_gap_eta', 'Vote Efficiency Gap (eta)', 'Vote Efficiency Gap'),
        ('recount_vulnerability_V', 'Recount Vulnerability (V)', 'Recount Vulnerability'),
        ('coalition_brittleness_count', 'Coalition Brittleness (count)', 'Coalition Brittleness'),
        ('institutional_distortion_D', 'Institutional Distortion (D)', 'Institutional Distortion Index'),
    ]

    years = metrics_df['year'].tolist()

    for idx, (col, ylabel, title) in enumerate(plot_specs, start=1):
        values = metrics_df[col].tolist()
        # Construct a small DataFrame with index=years and the series as a single column
        df_plot = pd.DataFrame({col: values}, index=years)
        # Use plotting helpers for consistent style; save as 2-digit prefix like before
        plot_count = f"{idx:02d}"
        filename = col
        full_title = f"{title} ({first_year}-{last_year})"
        if col == 'coalition_brittleness_count':
            make_bar_plot(df_plot, first_year, last_year, plot_count, col, ylabel, full_title, filename, folder_path=plots_dir, show_plot=False)
        else:
            make_bar_plot(df_plot, first_year, last_year, plot_count, col, ylabel, full_title, filename, folder_path=plots_dir, show_plot=False, subplot_dual_log=True)


if __name__ == '__main__':
    try:
        print("Starting election_metrics computation...")
        metrics = compute_metrics_for_all_years()
        print(f"Computed metrics dataframe with shape: {metrics.shape}")
        write_outputs(metrics)
        print(f"Wrote metrics for {len(metrics)} elections to results and plots.")
    except Exception as e:
        os.makedirs('results', exist_ok=True)
        with open(os.path.join('results', 'election_metrics_error.log'), 'w', encoding='utf-8') as logf:
            import traceback
            logf.write('Election metrics run failed:\n')
            logf.write(str(e) + '\n')
            logf.write(traceback.format_exc())
        raise
