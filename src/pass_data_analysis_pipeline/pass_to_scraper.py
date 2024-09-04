# The data for all player-to-player passing interactions is compiled by scraping individual player data.
# The specific endpoint for this data is https://stats.nba.com/stats/playerdashptpass?
# The `playerdashptpass` is an endpoint where the NBA website stores different types of data.
# Parameters are appended to the URL after the `?` to specify the desired data.
import requests
import json
import pandas as pd
from tqdm import tqdm 

# The 'pass_to' and 'pass_from' data are complementary; only 'pass_to' data is used here.
class NBAPassScraper:
    """
    A class to scrape NBA player passing data from the NBA Stats API.

    Parameters
    ----------
    season : str
        The NBA season in the format 'YYYY-YY'.
    player_id : int
        The unique identifier for the NBA player.

    Attributes
    ----------
    season : str
        The NBA season for which data is being scraped.
    url : str
        The endpoint URL for scraping NBA player passing data.
    parameters : dict
        The parameters required for the API request.
    """
    def __init__(self, season, player_id):
        self.season = season 
        self.url = 'https://stats.nba.com/stats/playerdashptpass'
        self.parameters = {
                'Season': season,
                'PlayerID': player_id,
                'PerMode': 'Totals',
                'SeasonType': 'Regular Season',
                'TeamID': '0',
                'Month': '0',
                'OpponentTeamID': '0',
                'LastNGames': '0',
                'LeagueID': '00',
                'DateFrom': None,
                'DateTo': None,
                'Location': None,
                'Outcome': None,
                'SeasonSegment': None,
                'VsConference': None,
                'VsDivision': None
        }
        self.headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
                'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': 'https://www.nba.com/',
        }
    
    def scraper(self):
        response = requests.get(
            url     = self.url,
            params  = self.parameters,
            headers = self.headers)
        dict_data = json.loads(response.text)
        return dict_data
    
    def split_name(self, name):
        """
        Reformat the player's name from 'Last, First' to 'First Last'.
        """
        try:
            last, first = name.split(', ')
            return f'{first} {last}'
        except:
            # Handle exceptions for specific names like 'ZHOW QI (周琦)' and 'Nene'
            return name
    
    def clean_data(self):
        dict_data = self.scraper()
        columns   = dict_data['resultSets'][0]['headers']
        data      = dict_data['resultSets'][0]['rowSet']
        df        = pd.DataFrame(data = data, columns = columns)
        
        df['PLAYER_NAME_LAST_FIRST'] = df['PLAYER_NAME_LAST_FIRST'].apply(lambda x : self.split_name(x))
        df['PASS_TO'] = df['PASS_TO'].apply(lambda x : self.split_name(x))
        df['season'] = self.season
        return df
   
#%%
import os
import sys
from pathlib import Path
# Set up the project root directory and append to system path for module imports
current_working_directory = Path(os.getcwd())
project_root = current_working_directory.parents[1]
sys.path.append(str(project_root / 'src'))

# Define the directory for data storage
data_dir = project_root / 'data'
season_list = [f'{year}-{str(year+1)[-2:]}' for year in range(2013, 2022)]
# Expected output DataFrame structure
expect_columns = ['season', 'PLAYER_ID', 'PLAYER_NAME_LAST_FIRST', 'TEAM_ID', 'TEAM_NAME', 'TEAM_ABBREVIATION', 'PASS_TYPE', 'G', 'PASS_TEAMMATE_PLAYER_ID', 'PASS_TO', 'FREQUENCY', 'PASS', 'AST', 'FGM', 'FGA', 'FG_PCT', 'FG2M', 'FG2A', 'FG2_PCT', 'FG3M', 'FG3A', 'FG3_PCT']
expect_df = pd.DataFrame(columns=expect_columns)

#%% Generate DataFrame for all players' passing data from 2014 to 2022
# 2024/07/25 Update: Search only for players who actually played each season. 
# This approach scrapes 11 seasons in about 100 minutes.
with open(data_dir / 'season_players_id_14_22.json', 'r') as json_file:
    season_players_dict = json.load(json_file)

for season in tqdm(season_list, desc='Seasons'):
    for player_id, player in tqdm(season_players_dict[season].items(),
                                  desc='Players', leave=False):
        print(f'Scraping passing data for {player} in the {season} season')
        processor = NBAPassScraper(season, player_id)
        df = processor.clean_data()
        expect_df = pd.concat([expect_df, df])

# expect_df.to_csv(data_dir / 'pass_data_14_22.csv', index=False)
