# The specific endpoint for this data is https://stats.nba.com/stats/leaguedashplayerstats?
# The `leaguedashplayerstats` is an endpoint where the NBA website stores different types of data.
# Parameters are appended to the URL after the `?` to specify the desired data.
import requests
import json
import time
import pandas as pd
from tqdm import tqdm

class NBAScraper:
    def __init__(self, endpoint: str, parameters: dict):
        self.url = f'https://stats.nba.com/stats/{endpoint}'
        self.parameters = parameters
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
        raw_dict_data = json.loads(response.text)
        return raw_dict_data
    
    def get_data(self):
        raw_dict_data = self.scraper()
        columns = raw_dict_data['resultSets'][0]['headers'] # data columns
        data    = raw_dict_data['resultSets'][0]['rowSet']  # data location
        df      = pd.DataFrame(data=data, columns=columns)
        return df

#%% 
# This study subsequently utilizes traditional data considering five-player lineups,
# without incorporating directly aggregated traditional statistical data.
# total_dfs   = []
# per100_dfs  = []
# seasons     = [f'{year}-{str(year+1)[-2:]}' for year in range(2007, 2022)]
# season_type = 'Regular Season'    # 'Playoffs'
# per_mode    = 'Per100Possessions' # 'PerGame', 'Totals'

# for season in tqdm(seasons):
#     parameters = {
#         'LastNGames': '0', 
#         'LeagueID': '00',
#         'MeasureType': 'Base',
#         'Month': '0',
#         'TeamID': '0',
#         'OpponentTeamID': '0',
#         'PORound': '0',
#         'Period': '0',
#         'PaceAdjust': 'N',
#         'PlusMinus': 'N',
#         'Rank': 'N',
#         'Season': f'{season}',
#         'SeasonType': f'{season_type}',
#         'PerMode': f'{per_mode}'
#     }
#     processor = NBAScraper('leaguedashplayerstats', parameters)
#     df = processor.get_data()
#     df = df[['PLAYER_ID', 'PLAYER_NAME', 'TEAM_ID', 'TEAM_ABBREVIATION',
#            'AGE', 'GP', 'W', 'L', 'W_PCT', 'MIN', 'FGM', 'FGA', 'FG_PCT',
#            'FG3M', 'FG3A', 'FG3_PCT', 'FTM', 'FTA', 'FT_PCT',
#            'OREB', 'DREB', 'REB', 'AST', 'TOV', 'STL', 'BLK',
#            'PF', 'PTS', 'PLUS_MINUS']]
#     df = df.rename(columns={'PLAYER_ID': 'player_id',
#                             'PLAYER_NAME': 'player',
#                             'TEAM_ID': 'team_id',
#                             'TEAM_ABBREVIATION': 'team_abb'})
#     df['year'] = season
#     total_dfs.append(df)
#     per100_dfs.append(df)
#     time.sleep(2)

# player_totals_data_08_22 = pd.concat(total_dfs, ignore_index=True)
# player_totals_data_08_22.to_csv('player_totals_data_08_22.csv', index=False)

# player_100pos_data_08_22 = pd.concat(per100_dfs, ignore_index=True)
# player_100pos_data_08_22.to_csv('player_100pos_data_08_22.csv', index=False)

#%%
# Obtain the player IDs of all players with recorded appearances for the current season,
# and efficiently scrape the interactive passing data for each season.
from collections import defaultdict
import os
import sys
from pathlib import Path
# Set up the project root directory and append to system path for module imports
current_working_directory = Path(os.getcwd())
project_root = current_working_directory.parents[1]
sys.path.append(str(project_root / 'src'))

# Define the directory for data storage
data_dir = project_root / 'data'
season_players_dict = defaultdict(dict)
seasons = [f'{year}-{str(year+1)[-2:]}' for year in range(2013, 2022)]
season_type = 'Regular Season'
per_mode = 'Totals'

for season in tqdm(seasons):
    parameters = {
        'LastNGames': '0', 
        'LeagueID': '00',
        'MeasureType': 'Base',
        'Month': '0',
        'TeamID': '0',
        'OpponentTeamID': '0',
        'PORound': '0',
        'Period': '0',
        'PaceAdjust': 'N',
        'PlusMinus': 'N',
        'Rank': 'N',
        'Season': f'{season}',
        'SeasonType': f'{season_type}',
        'PerMode': f'{per_mode}'
    }
    processor = NBAScraper('leaguedashplayerstats', parameters)
    df = processor.get_data()
    df = df[['PLAYER_ID', 'PLAYER_NAME']]
    df = df.rename(columns={'PLAYER_ID': 'player_id',
                            'PLAYER_NAME': 'player'})
    df['year'] = season

    for index, row in df.iterrows():
        year        = row['year']
        player_id   = row['player_id']
        player_name = row['player']
        season_players_dict[year][player_id] = player_name

    time.sleep(1)

season_players_dict = dict(season_players_dict)

with open(data_dir / 'season_players_id_14_22.json', 'w') as json_file:
    json.dump(season_players_dict, json_file, indent=4)

# with open('data_dir / season_players_id_14_22.json', 'r') as json_file:
#     season_players_dict = json.load(json_file)
