import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import math
import re

# Load the dataset
election_results_df = pd.read_csv('summary_results_split_verify.csv')
electoral_college_df = pd.read_csv('electoral_college.csv')

# We want to generalize the data to be able to handle elections where more than two parties win electoral votes

# print the current columns
#print(election_results_df.columns)

def get_election_data(year):
    base_url = f"https://en.wikipedia.org/wiki/{year}_United_States_presidential_election"
    vote_data = {year: {}}

    # Fetch the main page
    response = requests.get(base_url)
    if response.status_code != 200:
        print(f"Failed to fetch data for {year}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Find state links
    state_links = [
        a['href'] for a in soup.find_all('a', href=True)
        if f"{year}_United_States_presidential_election_in_" in a['href']
    ]

    # Remove duplicates and sort the links alphabetically by state name
    state_links = list(set(state_links))
    state_links.sort()

    for link in state_links:
        state_url = f"https://en.wikipedia.org{link}"
        state_name = link.split("_in_")[-1].replace("_", " ").upper()
        
        if state_name == "WASHINGTON (STATE)":  # Handle special case for Washington state
            state_name = "WASHINGTON"
        if state_name == "THE DISTRICT OF COLUMBIA":
            state_name = "D.C."
        if state_name == "MASSACHUSETTS":
            my = 0
        try:
            state_response = requests.get(state_url)
            state_soup = BeautifulSoup(state_response.text, "html.parser")

            # Try to find the infobox
            infobox = state_soup.find("table", {"class": "infobox"})

            nominees, parties, vote_counts = [], [], []

            if infobox:
                rows = infobox.find_all("tr")

                # Extract nominees, parties, and popular vote data from infobox
                for row in rows:
                    headers = row.find_all("th")
                    data = row.find_all("td")

                    if not headers or not data:
                        continue

                    header_text = headers[0].get_text(strip=True)

                    if header_text == "Nominee":
                        nominees_added = [td.get_text(strip=True) for td in data]
                        nominees.extend(nominees_added)
                    elif header_text == "Party":
                        parties_added = [td.get_text(strip=True) for td in data]
                        parties.extend(parties_added)
                    elif header_text == "Popular\xa0vote":
                        if state_name == "ARIZONA" and year == 1912:
                            # Handle special case for Arkansas in 1912
                            vote_counts = vote_counts
                        vote_counts_added = [
                            int(re.sub(r'\D', '', td.get_text(strip=True)))
                            for td in data
                            if re.sub(r'\D', '', td.get_text(strip=True)).isdigit()
                        ]
                        vote_counts.extend(vote_counts_added)

            # If infobox data is incomplete, fall back to vote breakdown table
            if not nominees or len(vote_counts) < 2:  # Check if infobox lacks third-party data
                print(f"Infobox incomplete for {state_name} in year {year}. Falling back to table.")
                table = state_soup.find("table", {"class": "wikitable"})
                if table:
                    rows = table.find_all("tr")
                    for row in rows[1:]:  # Skip the header row
                        cols = row.find_all("td")
                        if len(cols) < 3:
                            continue

                        # Extract candidate, party, and votes from table
                        candidate = cols[0].get_text(strip=True)
                        party = cols[1].get_text(strip=True)
                        votes = cols[2].get_text(strip=True).replace(",", "")

                        try:
                            votes = int(votes)
                            if "Democrat" in party:
                                nominees.append(candidate)
                                parties.append("Democratic")
                                vote_counts.append(votes)
                            elif "Republican" in party:
                                nominees.append(candidate)
                                parties.append("Republican")
                                vote_counts.append(votes)
                            else:  # Third-party or independent
                                nominees.append(candidate)
                                parties.append("Third")
                                vote_counts.append(votes)
                        except ValueError:
                            continue

            # Map the vote counts to D_votes, R_votes, and T_votes
            state_results = {"D_votes": 0, "R_votes": 0, "T_votes": 0}
            for i, party in enumerate(parties):
                if party == "Democratic":
                    state_results["D_votes"] = vote_counts[i]
                elif party == "Republican":
                    state_results["R_votes"] = vote_counts[i]
                else:
                    state_results["T_votes"] = max(vote_counts[i], state_results["T_votes"])
            if state_results["D_votes"] == 0 and state_results["R_votes"] == 0:
                print(f"Error processing {state_name} in {year}: Missing data for D or R. D_votes: {state_results['D_votes']}, R_votes: {state_results['R_votes']}")

            vote_data[year][state_name] = state_results
            #print(f"Processed {state_name} in {year}: {state_results}")

        except Exception as e:
            print(f"Error processing {state_name}: {e}")

    return vote_data

def get_candidate_names(year, state):
    if year == 1912:
        return {"R_name": "William Howard Taft", "D_name": "Woodrow Wilson", "T_name": "Theodore Roosevelt"}
    if year == 1916:
        return {"R_name": "Charles Evans Hughes", "D_name": "Woodrow Wilson", "T_name": ""}
    if year == 1920:
        return {"R_name": "Warren G. Harding", "D_name": "James M. Cox", "T_name": ""}
    if year == 1924:
        return {"R_name": "Calvin Coolidge", "D_name": "John W. Davis", "T_name": "Robert M. La Follette"}
    if year == 1944:
        return {"R_name": "Thomas E. Dewey", "D_name": "Franklin D. Roosevelt", "T_name": ""}
    if year == 1948:
        return {"R_name": "Thomas E. Dewey", "D_name": "Harry S. Truman", "T_name": "Strom Thurmond"}
    if year == 1952:
        return {"R_name": "Dwight D. Eisenhower", "D_name": "Adlai Stevenson", "T_name": ""}
    if year == 1956:
        return {"R_name": "Dwight D. Eisenhower", "D_name": "Adlai Stevenson", "T_name": ""}
    if year == 1960:
        return {"R_name": "Richard Nixon", "D_name": "John F. Kennedy", "T_name": ""}
    if year == 1964:
        return {"R_name": "Barry Goldwater", "D_name": "Lyndon B. Johnson", "T_name": ""}
    if year == 1968:
        return {"R_name": "Richard Nixon", "D_name": "Hubert Humphrey", "T_name": "George Wallace"}
    if year == 1972:
        return {"R_name": "Richard Nixon", "D_name": "George McGovern", "T_name": ""}
    
    state_name = state.replace(" ", "_")
    # currently it is uppercase, so we need to make it capital case (both words if it is two words)
    state_name = state_name.title()
    
    state_url = f"https://en.wikipedia.org/wiki/{year}_United_States_presidential_election_in_{state_name}"
    
    try:
        response = requests.get(state_url)
        if response.status_code != 200:
            print(f"Failed to fetch data for {state} in {year}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # Locate the infobox
        infobox = soup.find("table", {"class": "infobox"})
        if not infobox:
            print(f"No infobox found for {state} in {year}")
            return {"R_name": "", "D_name": "", "T_name": ""}

        # Variables to store candidate names
        R_name = ""
        D_name = ""

        # Parse rows for Nominee and Popular vote
        nominees, parties, popular_votes = [], [], []
        rows = infobox.find_all("tr")
        for row in rows:
            headers = row.find_all("th")
            data = row.find_all("td")

            if not headers or not data:
                continue

            header_text = headers[0].get_text(strip=True)

            # Collect nominee names
            if header_text == "Nominee":
                nominees = [td.get_text(strip=True) for td in data]

            # Collect party affiliations
            elif header_text == "Party":
                parties = [td.get_text(strip=True) for td in data]

        # Match candidates to parties
        for i in range(len(parties)):
            if parties[i] == "Democratic" or parties[i] == "National Democratic":
                D_name = nominees[i]
            elif parties[i] == "Republican":
                R_name = nominees[i]
        
        # check to make sure D_name and R_name are not empty
        if not D_name or not R_name:
            print(f"Error processing {state} in {year}: Missing data for D or R. D_name: {D_name}, R_name: {R_name}")

        return {"R_name": R_name, "D_name": D_name, "T_name": ''}

    except Exception as e:
        print(f"Error processing {state} in {year}: {e}")
        return {"R_name": "", "D_name": "", "T_name": ""}


# Example Usage
print(get_candidate_names(1912, "Arizona"))
print(get_candidate_names(1916, "Arizona"))
print(get_candidate_names(1860, "Missouri"))


# Example Usage
#print(get_names(1968))
#print(get_names(1956))

def get_electoral_votes(year, electoral_college_df=electoral_college_df):

    # Get the electoral college data for the specified year
    # get rows where 'year' == year
    electoral_votes = electoral_college_df[electoral_college_df['year'] == year]
    total_electoral_votes = electoral_votes['electoral_votes'].sum().astype(int)
    electoral_votes_to_win = total_electoral_votes // 2 + 1

    D_electoral, R_electoral, T_electoral = 0, 0, 0
    # Calculate the electoral votes for each party
    # We check if party_win is D, R, or neither (T)
    for index, row in electoral_votes.iterrows():
        if row['party_win'] == 'D':
            D_electoral += row['electoral_votes']
        elif row['party_win'] == 'R':
            R_electoral += row['electoral_votes']
        else:
            # check if the value is not empty
            if row['party_win']:
                T_electoral += row['electoral_votes']
    
    # set the values to integers
    D_electoral = int(D_electoral)
    R_electoral = int(R_electoral)
    T_electoral = 0 if math.isnan(T_electoral) else int(T_electoral)  # Handle NaN case
    overall_winner = "D" if D_electoral > R_electoral else "R"
    # the "loser" is the party that did second best in the electoral college
    # ex. in 1912, T_electoral = 88, D_electoral = 435, R_electoral = 8. the winner is D, the loser is T
    # sort [D_elecoral, R_electoral, T_electoral] and get the second highest value
    electoral_collection_list = sorted([D_electoral, R_electoral, T_electoral])
    if electoral_collection_list[1] == D_electoral:
        overall_runner_up = "D"
    elif electoral_collection_list[1] == R_electoral:
        overall_runner_up = "R"
    else:
        overall_runner_up = "T"
    
    return {
        "total_electoral_votes": total_electoral_votes,
        "electoral_votes_to_win": electoral_votes_to_win,
        "D_electoral": D_electoral,
        "R_electoral": R_electoral,
        "T_electoral": T_electoral,
        "overall_winner": overall_winner,
        "overall_runner_up": overall_runner_up
    }

state_po = {
    'ALABAMA': 'AL', 'ALASKA': 'AK', 'ARIZONA': 'AZ', 'ARKANSAS': 'AR', 'CALIFORNIA': 'CA', 'COLORADO': 'CO', 'CONNECTICUT': 'CT', 'DELAWARE': 'DE', 'FLORIDA': 'FL', 'GEORGIA': 'GA', 'HAWAII': 'HI', 'IDAHO': 'ID', 'ILLINOIS': 'IL', 'INDIANA': 'IN', 'IOWA': 'IA', 'KANSAS': 'KS', 'KENTUCKY': 'KY', 'LOUISIANA': 'LA', 'MAINE': 'ME', 'MARYLAND': 'MD', 'MASSACHUSETTS': 'MA', 'MICHIGAN': 'MI', 'MINNESOTA': 'MN', 'MISSISSIPPI': 'MS', 'MISSOURI': 'MO', 'MONTANA': 'MT', 'NEBRASKA': 'NE', 'NEVADA': 'NV', 'NEW HAMPSHIRE': 'NH', 'NEW JERSEY': 'NJ', 'NEW MEXICO': 'NM', 'NEW YORK': 'NY', 'NORTH CAROLINA': 'NC', 'NORTH DAKOTA': 'ND', 'OHIO': 'OH', 'OKLAHOMA': 'OK', 'OREGON': 'OR', 'PENNSYLVANIA': 'PA', 'RHODE ISLAND': 'RI', 'SOUTH CAROLINA': 'SC', 'SOUTH DAKOTA': 'SD', 'TENNESSEE': 'TN', 'TEXAS': 'TX', 'UTAH': 'UT', 'VERMONT': 'VT', 'VIRGINIA': 'VA', 'WASHINGTON': 'WA', 'WEST VIRGINIA': 'WV', 'WISCONSIN': 'WI', 'WYOMING': 'WY', 'D.C.': 'DC'
}


def create_row_dict(year, state, state_po_code, D_name, R_name, T_name, party_win, D_votes, R_votes, T_votes, overall_winner, winner_state, state_electoral_votes, winner_votes, loser_votes, overall_runner_up, total_electoral_votes, electoral_votes_to_win, D_electoral, R_electoral, T_electoral):
    totalvotes = D_votes + R_votes + T_votes
    votes_to_flip = max((winner_votes - loser_votes) // 2 + 1, 0)
    return {
        "year": year,
        "state": state,
        "state_po": state_po_code,
        "D_name": D_name,
        "R_name": R_name,
        "T_name": T_name,
        "party_win": party_win,
        "D_votes": D_votes,
        "R_votes": R_votes,
        "T_votes": T_votes,
        "overall_winner": overall_winner,
        "overall_runner_up": overall_runner_up,
        "winner_state": winner_state,
        "electoral_votes": state_electoral_votes.astype(int),
        "winner_votes": winner_votes,
        "loser_votes": loser_votes,
        "votes_to_flip": votes_to_flip,
        "total_electoral_votes": total_electoral_votes,
        "electoral_votes_to_win": electoral_votes_to_win,
        "D_electoral": D_electoral,
        "R_electoral": R_electoral,
        "T_electoral": T_electoral,
        "totalvotes": totalvotes
    }

def generate_row(year, state, vote_data, electoral_college_df):
    # Get the election data for the specified year
    election_data = vote_data.get(year, {})[year][state]
    
    # Get the electoral votes for the specified year
    electoral_data = get_electoral_votes(year, electoral_college_df)
    
    # get candidates for the specified year
    candidates = get_candidate_names(year, state)
    
    # Combine the election and electoral data
    state_po_code = state_po.get(state, "")
    D_votes = election_data.get("D_votes", 0)
    R_votes = election_data.get("R_votes", 0)
    T_votes = election_data.get("T_votes", 0)
    if D_votes > R_votes and D_votes > T_votes:
        party_win = 'D'
    elif R_votes > D_votes and R_votes > T_votes:
        party_win = 'R'
    else:
        party_win = 'T'
    D_electoral = electoral_data.get("D_electoral", 0)
    R_electoral = electoral_data.get("R_electoral", 0)
    T_electoral = electoral_data.get("T_electoral", 0)
    overall_winner = electoral_data.get("overall_winner", "")
    overall_runner_up = electoral_data.get("overall_runner_up", "")
    winner_state = overall_winner == party_win
    #winner_state = bool(winner_state)
    #winner_votes = max(D_votes, R_votes, T_votes)
    winner_votes = election_data.get(overall_winner + "_votes", 0)
    # the "loser" is the party that did second best in the electoral college
    # ex. in 1912, T_electoral = 88, D_electoral = 435, R_electoral = 8. the winner is D, the loser is T
    # sort [D_elecoral, R_electoral, T_electoral] and get the second highest value
    loser_votes = election_data.get(overall_runner_up + "_votes", 0)
    if winner_votes == loser_votes:
        print(f"Error: winner_votes == loser_votes for {year} in {state}")
    votes_to_flip = (winner_votes - loser_votes) // 2 + 1
    R_name = candidates.get("R_name", "")
    D_name = candidates.get("D_name", "")
    T_name = candidates.get("T_name", "")
    total_electoral_votes = electoral_data.get("total_electoral_votes", 0)
    electoral_votes_to_win = electoral_data.get("electoral_votes_to_win", 0)
    
    state_electoral_votes_series = electoral_college_df[(electoral_college_df['year'] == year) & (electoral_college_df['state'].str.upper() == state)]['electoral_votes']
    if not state_electoral_votes_series.empty:
        state_electoral_votes = state_electoral_votes_series.iloc[0]
    else:
        state_electoral_votes = 0  # or any default value you prefer
    
    return create_row_dict(year, state, state_po_code, D_name, R_name, T_name, party_win, D_votes, R_votes, T_votes, overall_winner, winner_state, state_electoral_votes, winner_votes, loser_votes, overall_runner_up, total_electoral_votes, electoral_votes_to_win, D_electoral, R_electoral, T_electoral)

def recalculate_votes(row, D_votes, R_votes, state_electoral_votes):
    # this function is only used for the NE and ME split votes, so we need to pass the D_votes and R_votes. there is no third party in any year when we split the votes
    year = row['year'].iloc[0]
    R_name = row['R_name'].iloc[0]
    D_name = row['D_name'].iloc[0]
    state = row['state'].iloc[0]
    state_po_code = state_po.get(state, "")
    
    totalvotes = D_votes + R_votes
    overall_winner = row['overall_winner'].iloc[0]
    overall_runner_up = row['overall_runner_up'].iloc[0]
    party_win = 'D' if D_votes > R_votes else 'R'
    winner_state = overall_winner == party_win
    winner_votes = max(D_votes, R_votes)
    # loser_votes is the votes of the party that did not win
    loser_votes = D_votes if overall_winner == "R" else R_votes
    votes_to_flip = (winner_votes - loser_votes) // 2 + 1
    total_electoral_votes = 538 # in the case of NE and ME split votes, the total electoral votes is always 538
    electoral_votes_to_win = 270 # in the case of NE and ME split votes, the electoral votes to win is always 270
    D_electoral = row['D_electoral'].iloc[0]
    R_electoral = row['R_electoral'].iloc[0]
    
    return create_row_dict(year, state, state_po_code, D_name, R_name, "", party_win, D_votes, R_votes, 0, overall_winner, winner_state, state_electoral_votes, winner_votes, loser_votes, overall_runner_up, total_electoral_votes, electoral_votes_to_win, D_electoral, R_electoral, 0)

def generate_election_results_df(years, electoral_college_df=electoral_college_df):
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

    election_results = []
    vote_data = {}
    filename = f'election_results_{years[0]}_{years[-1]}.csv'

    for year in years:
        print(f"Processing data for {year}...")
        vote_data[year] = get_election_data(year)
        for state in vote_data[year][year].keys():
            if state == 'NEBRASKA' and year in NE_split:
                # Handle Nebraska split votes
                # Split the state into two rows, one for the state and one for the second district
                # Subtract D_votes and R_votes from the state and add a new row with the defecting district data
                overall_row = generate_row(year, state, vote_data, electoral_college_df)
                second_district_row = overall_row.copy()
                second_district_row['state_po'] = 'NE-02'
                second_district_row['state'] = 'NE-02'
                overall_D_votes = overall_row['D_votes'].iloc[0] - NE_split[year]['D_votes']
                overall_R_votes = overall_row['R_votes'].iloc[0] - NE_split[year]['R_votes']
                second_district_row = recalculate_votes(second_district_row, NE_split[year]['D_votes'], NE_split[year]['R_votes'], 1)
                overall_row = recalculate_votes(overall_row, overall_D_votes, overall_R_votes, 4)
                
            elif state == 'MAINE' and year in ME_split:
                # Handle Maine split votes
                # Split the state into two rows, one for the state and one for the second district
                # Subtract D_votes and R_votes from the state and add a new row with the defecting district data
                overall_row = generate_row(year, state, vote_data, electoral_college_df)
                second_district_row = overall_row.copy()
                second_district_row['state_po'] = 'ME-02'
                second_district_row['state'] = 'ME-02'
                overall_D_votes = overall_row['D_votes'].iloc[0] - ME_split[year]['D_votes']
                overall_R_votes = overall_row['R_votes'].iloc[0] - ME_split[year]['R_votes']
                second_district_row = recalculate_votes(second_district_row, ME_split[year]['D_votes'], ME_split[year]['R_votes'], 1)
                overall_row = recalculate_votes(overall_row, overall_D_votes, overall_R_votes, 3)
            else:
                election_results.append(generate_row(year, state, vote_data, electoral_college_df))
        # save to csv
        election_results_df = pd.DataFrame(election_results)
        election_results_df.to_csv(filename, index=False)

    election_results_df = pd.DataFrame(election_results)
    return election_results_df
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
# want election years start_year to end_year (every 4 years)
start_year = 1968
end_year = 1976
years = list(range(start_year, end_year + 1, 4))
#election_results_df = generate_election_results_df(years)