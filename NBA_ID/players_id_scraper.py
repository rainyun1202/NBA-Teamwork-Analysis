# The specific endpoint for this data is https://stats.nba.com/stats/playerindex?
import requests
import json
import pandas as pd

class NBAIDScraper:
    def __init__(self, endpoint: str):
        self.url = f'https://stats.nba.com/stats/{endpoint}'
        # The 'Season' field can be set to any desired season, and setting 'Historical' to 1 will retrieve information for all historical players.
        self.parameters = {
            'Season': '2023-24', 
            'Historical': '1',
            'LeagueID': '00',
            'TeamID': '0'
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
        raw_dict_data = json.loads(response.text)
        return raw_dict_data
    
    def get_data(self):
        raw_dict_data = self.scraper()
        columns = raw_dict_data['resultSets'][0]['headers']
        data    = raw_dict_data['resultSets'][0]['rowSet']
        df      = pd.DataFrame(data = data, columns = columns)
        return df

processor = NBAIDScraper('playerindex')
df = processor.get_data()
# df.columns

df = df[['PERSON_ID', 'PLAYER_LAST_NAME', 'PLAYER_FIRST_NAME']]
df['player'] = (df
                .apply(lambda row: f"{row['PLAYER_FIRST_NAME']} {row['PLAYER_LAST_NAME']}",
                       axis=1)
                )
players_id = df[['PERSON_ID', 'player']].rename(columns={'PERSON_ID': 'player_id'})
# Manually remove the extra space (Excel or Notepad++) before the FIRST_NAME of player Nene.
# The data scraping includes the player list updated on NBA.com as of 2024/07/21.
# players_id.to_csv('players_id.csv', index=False)
