import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup

# Load the dataset
election_results_df = pd.read_csv('summary_results_split_verify.csv')

# We want to generalize the data to be able to handle elections where more than two parties win electoral votes

# print the current columns
#print(election_results_df.columns)

def get_election_data(year):
    import requests
    from bs4 import BeautifulSoup

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
    
    # Handle special cases where the state name needs to be renamed
    state_renames = {
        "THE DISTRICT OF COLUMBIA": "D.C.",
        "WASHINGTON (STATE)": "WASHINGTON",
    }
    

    for link in state_links:
        state_url = f"https://en.wikipedia.org{link}"
        state_name = link.split("_in_")[-1].replace("_", " ").upper()

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
                        nominees = [td.get_text(strip=True) for td in data]
                    elif header_text == "Party":
                        parties = [td.get_text(strip=True) for td in data]
                    elif header_text == "Popular\xa0vote":
                        vote_counts = [
                            int(td.get_text(strip=True).replace(",", ""))
                            for td in data
                            if td.get_text(strip=True).replace(",", "").isdigit()
                        ]

            # If infobox data is incomplete, fall back to vote breakdown table
            if not nominees or len(vote_counts) < 2:  # Check if infobox lacks third-party data
                print(f"Infobox incomplete for {state_name}. Falling back to table.")
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
                    state_results["D_votes"] += vote_counts[i]
                elif party == "Republican":
                    state_results["R_votes"] += vote_counts[i]
                else:
                    state_results["T_votes"] += vote_counts[i]
            # rename the state if necessary
            state_name = state_renames.get(state_name, state_name)
            vote_data[year][state_name] = state_results
            print(f"Processed {state_name} in {year}: {state_results}")

        except Exception as e:
            print(f"Error processing {state_name}: {e}")

    return vote_data



# Example usage
year = 1968
vote_data = get_election_data(year)

# Print the results for verification
import pprint
pprint.pprint(vote_data)

# Save to a JSON file for future use
import json
with open(f"{year}_election_data.json", "w") as f:
    json.dump(vote_data, f, indent=4)