import requests
import json
import pandas as pd
from tqdm import tqdm   
import os
import sys
from pathlib import Path

# Set up the project root directory and append to system path for module imports
current_working_directory = Path(os.getcwd())
project_root = current_working_directory.parents[1]
sys.path.append(str(project_root / 'src'))

# Define the directory for data storage
data_dir = project_root / 'data'

#%%
class NBALineupsScraper:
    """
    A class used to scrape NBA lineup data from the NBA Stats website.

    Attributes
    ----------
    url : str
        The API endpoint for fetching NBA lineup data.
    parameters : dict
        The parameters required for the API request.
    headers : dict
        The HTTP headers required to simulate a browser request.

    Methods
    -------
    scraper()
        Sends a GET request to the NBA Stats API and returns the raw JSON data.
    clean_data()
        Processes the raw JSON data into a dictionary format.
    """

    def __init__(self, group_quantity, season, team_id, per_mode):
        """
        Constructs all the necessary attributes for the NBALineupsScraper object.

        Parameters
        ----------
        group_quantity : str
            The number of players in the lineup (e.g., '5' for a 5-player lineup).
        season : str
            The NBA season (e.g., '2021-22').
        team_id : int
            The ID of the NBA team.
        per_mode : str
            The statistical mode for data (e.g., 'Per100Possessions').
        """
        self.url = 'https://stats.nba.com/stats/leaguedashlineups'
        self.parameters = {
            'GroupQuantity': group_quantity,
            'Season': season,
            'TeamID': team_id,
            'PerMode': per_mode,
            'SeasonType': 'Regular Season',
            'MeasureType': 'Base',
            'PaceAdjust': 'N',
            'PlusMinus': 'N',
            'Rank': 'N',
            'LeagueID': '00',
            'LastNGames': '0',
            'Month': '0',
            'OpponentTeamID': '0',
            'Period': '0',
            'PORound': '0',
            'Conference': None,
            'DateFrom': None,
            'DateTo': None,
            'Division': None,
            'GameSegment': None,
            'Location': None,
            'Outcome': None,
            'SeasonSegment': None,
            'ShotClockRange': None,
            'VsConference': None,
            'VsDivision': None
        }
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.nba.com/",
        }
    
    def scraper(self):
        """
        Sends a GET request to the NBA Stats API to retrieve raw lineup data.

        Returns
        -------
        dict
            The raw JSON data converted to a dictionary.
        """
        response = requests.get(
            url     = self.url,
            params  = self.parameters,
            headers = self.headers
        )
        raw_dict_data = json.loads(response.text)
        return raw_dict_data
    
    def clean_data(self):
        """
        Cleans and processes the raw lineup data into a structured dictionary.

        Returns
        -------
        dict
            A dictionary containing the cleaned lineup data.
        """
        raw_dict_data = self.scraper()   
        columns = raw_dict_data['resultSets'][0]['headers']
        data    = raw_dict_data['resultSets'][0]['rowSet']
        df      = pd.DataFrame(data=data, columns=columns)
        dict_data = df.to_dict()
        return dict_data

#%%

# Load team ID to team name mapping from CSV
team_df   = pd.read_csv(data_dir / 'team_and_teamid.csv')
team_dict = pd.Series(team_df.team.values, index=team_df.team_id).to_dict()

# Define the list of seasons and group quantity for lineups
season_list = ['2013-14', '2014-15', '2015-16', '2016-17', '2017-18',
               '2018-19', '2019-20', '2020-21', '2021-22']    
group_quantity = '5' # Number of players in the lineup
per_mode = 'Per100Possessions'
# per_mode = 'Totals'
# Initialize a dictionary to hold the scraped data
expect_data_dict = {
    season: {
            team: {} for team in team_dict.values()
    } for season in season_list
}

# NBA.com restricts data to 2000 rows per request, so be aware of this limit
for season in tqdm(season_list, desc='Seasons'):
    for team_id, team in tqdm(team_dict.items(), desc='Teams', leave=False):
        print(f'Scraping {season} season for {team} with {group_quantity} lineups...')
        processor = NBALineupsScraper(group_quantity, season, team_id, per_mode)
        dict_data = processor.clean_data()
        expect_data_dict[season][team] = dict_data

# Save the scraped lineup data to a JSON file
with open(data_dir / 'lineups_data' / '5lineups_100poss.json', 'w') as f:
    json.dump(expect_data_dict, f, indent=4)
# with open(data_dir / 'lineups_data' / '5lineups_totals.json') as f:
#     json.dump(expect_data_dict, f, indent=4)

