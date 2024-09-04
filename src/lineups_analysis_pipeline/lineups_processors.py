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

#%% Load data
with open(data_dir / 'lineups_data' / '5lineups_totals.json') as f:
    lineups_totals = json.load(f)
with open(data_dir / 'lineups_data' / '5lineups_100poss.json') as f:
    lineups_100poss = json.load(f)

players_id = pd.read_csv(data_dir / 'players_id.csv')
players_id_dict = {}
for player_id, player in zip(players_id['player_id'], players_id['player']):
    players_id_dict[player_id] = player

group_apm = pd.read_csv(data_dir / 'RAPM_data' / 'group_apm_14_22_800possup.csv')
adj_apm_rapm = pd.read_csv(data_dir / 'RAPM_data' / 'adj_apm_rapm_14_22.csv')
# unadj_apm_rapm = pd.read_csv(data_dir / 'unadj_apm_rapm_14_22.csv')

#%%
def read_lineups_df(lineups_dict):
    """
    Convert lineup data from a dictionary to a pandas DataFrame.

    Parameters
    ----------
    lineups_dict : dict
        The dictionary containing lineup data for multiple seasons and teams.

    Returns
    -------
    df : pandas.DataFrame
        The consolidated DataFrame containing all lineup data.
    """
    dfs = []
    for year, data in lineups_dict.items():
        for team, team_data in data.items():
            print(f'Processing data for {team} in the {year} season.')
            df = pd.DataFrame(team_data)
            df['year'] = int(year[:2] + year[-2:])
            df['team'] = team
            dfs.append(df)
    df = pd.concat(dfs)
    return df

def find_player_id(player_name, players_id_dict):
    """
    Find the player ID corresponding to a given player name.

    Parameters
    ----------
    player_name : str
        The name of the player.
    players_id_dict : dict
        A dictionary mapping player IDs to player names.

    Returns
    -------
    int or None
        The ID of the player, or None if not found.
    """
    for player_id, name in players_id_dict.items():
        if name == player_name:
            return player_id

def process_players_column(players_string):
    """
    Process a string of player names into a formatted string of player IDs.

    Parameters
    ----------
    players_string : str
        A string containing the names of players in a lineup.

    Returns
    -------
    ids_string : str
        A formatted string of player IDs, separated by hyphens.
    """
    # Remove parentheses and quotes from the string
    players_list = [player.strip()[1:-1] for player in players_string.strip('()').split(",")]

    player_ids = []
    for player in players_list:
        player_id = find_player_id(player, players_id_dict)
        player_ids.append(str(player_id))
    
    # Create a string of IDs, formatted as '-id-id-id-id-id-'
    ids_string = '-' + '-'.join(player_ids) + '-'
    return ids_string

def sorted_players_id(players_string):
    """
    Sort the player IDs in a given string.

    Parameters
    ----------
    players_string : str
        A string of player IDs, separated by hyphens.

    Returns
    -------
    sorted_string : str
        A sorted and rejoined string of player IDs.
    """
    # Split the string by "-", sort the IDs, and rejoin them
    players_list = players_string.split('-')[1:-1]
    players_list = [int(idx) for idx in players_list]
    players_list_sorted = sorted(players_list)
    players_list_sorted = [str(idx) for idx in players_list_sorted]
    sorted_string = '-' + '-'.join(players_list_sorted) + '-'
    return sorted_string

def convert_ids_to_players(player_ids):
    """
    Convert a string of player IDs to a list of player names.

    Parameters
    ----------
    player_ids : str
        A string of player IDs, separated by hyphens.

    Returns
    -------
    list
        A list of player names corresponding to the IDs.
    """
    # Strip the hyphens and split the IDs
    ids = player_ids.strip('-').split('-')
    # Convert IDs to player names
    players = [players_id_dict.get(int(idx), None) for idx in ids]
    return players

#%%

group_apm['Group'] = group_apm['Group'].apply(process_players_column)
group_apm['Group'] = group_apm['Group'].apply(sorted_players_id)

lineups_df_totals = read_lineups_df(lineups_totals)
lineups_df_100poss = read_lineups_df(lineups_100poss)

lineups_df_totals['Group'] = (lineups_df_totals['GROUP_ID']
                              .apply(sorted_players_id)
                              )
# lineups_df.columns
lineups_df_totals = lineups_df_totals[['Group', 'team', 'year', 'MIN']]

# Filter lineups that played more than 100 minutes in a single season
lineups_df_totals = lineups_df_totals[lineups_df_totals['MIN'] >= 100]

merged_df = pd.merge(group_apm, lineups_df_totals, on=['Group', 'year'])

lineups_df_100poss['Group'] = (lineups_df_100poss['GROUP_ID']
                               .apply(sorted_players_id)
                               )
# lineups_df_100poss.columns
lineups_df_100poss = lineups_df_100poss[['Group', 'team', 'year', 'GP',
    'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT',
    'FTM', 'FTA', 'FT_PCT', 'OREB', 'DREB', 'REB',
    'AST', 'TOV', 'STL', 'BLK', 'PF',
    'PTS', 'PLUS_MINUS']]

merged_100poss_df = pd.merge(merged_df,
                             lineups_df_100poss,
                             on=['Group', 'team', 'year'])

merged_100poss_df[['player_1',
                   'player_2',
                   'player_3',
                   'player_4',
                   'player_5']] = (merged_100poss_df['Group']
                                   .apply(convert_ids_to_players)
                                   .apply(pd.Series)
                                   )

# Merge RAPM data into the corresponding player columns
for i in range(1, 6):
    merged_100poss_df = (merged_100poss_df
                         .merge(adj_apm_rapm[['Player', 'RAPM', 'year']],
                                left_on=[f'player_{i}', 'year'],
                                right_on=['Player', 'year'],
                                how='left')
                         .drop(columns=['Player'])
                         .rename(columns={'RAPM': f'player_{i}_rapm'})
                         )

merged_100poss_df['player_rapm_sum'] = (merged_100poss_df['player_1_rapm']
                                        + merged_100poss_df['player_2_rapm']
                                        + merged_100poss_df['player_3_rapm']
                                        + merged_100poss_df['player_4_rapm']
                                        + merged_100poss_df['player_5_rapm']
                                        )

# merged_100poss_df.to_csv(data_dir / 'all_100poss_lineups_data.csv',
#                          index=False)

#%% 2024/08/10 Add passing data into regression dataset

pass_data = pd.read_csv(data_dir / 'pass_data_14_22.csv')

pass_data['TEAM_NAME'].replace({
    'Charlotte Bobcats'   : 'Charlotte Hornets',
    'Los Angeles Clippers': 'LA Clippers'
    }, inplace=True)

pass_data['per_PASS'] = (
    pass_data['PASS'].div(pass_data['G'], axis = 0)
)

def calculate_passes(row, pass_data):
    passes = {}
    for i in range(1, 6):
        # 計算每個球員的 pass_out
        pass_out = (pass_data['season'] == row['season']) & \
            (pass_data['TEAM_NAME'] == row['team']) & \
            (pass_data['PLAYER_NAME_LAST_FIRST'] == row[f'player_{i}']) & \
            (pass_data['PASS_TO'].isin([row[f'player_{j}'] for j in range(1, 6) if j != i]))
        passes[f'player_{i}_pass_out'] = pass_data[pass_out]['per_PASS'].sum()
    return passes

merged_100poss_df['season'] = merged_100poss_df['year'].apply(lambda x: f'{x-1}-{str(x)[-2:]}')

for index, row in tqdm(merged_100poss_df.iterrows()):
    result = calculate_passes(row, pass_data)
    for key, value in result.items():
        merged_100poss_df.at[index, key] = value
        
std_pass_out = merged_100poss_df[['player_1_pass_out', 'player_2_pass_out', 'player_3_pass_out', 'player_4_pass_out', 'player_5_pass_out']].std(axis=1)
merged_100poss_df['std_pass_out'] = std_pass_out

merged_100poss_df.to_csv(data_dir / '(new) all_100poss_lineups_data.csv',
                         index=False)
