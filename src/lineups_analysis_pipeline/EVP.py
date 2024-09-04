import json
import pandas as pd
import numpy as np
from tqdm import tqdm

class EVP:
    """
    Calculate EVP using the method outlined in "Eigenvalue Productivity: Measurement of Individual Contributions in Teams."
    This class calculates the EVP for all players and the standard deviation for each lineup by receiving a large DataFrame containing all the lineups data.
    """
    def __init__(self, df, gp, team_effect):
        self.df = df
        self.gp = gp          # Number of joint appearances for lineups.
        self.sp = team_effect # Select data used to measure team outcomes.
    
    def normalized_fun(self, lst: list) -> np.array:
        x = np.array(lst)
        normalized_x = (x - np.min(x)) / (np.max(x) - np.min(x))
        return normalized_x
   
    # Create two n x n player matrices, DataFrame S and DataFrame G, both initialized with values of 0.
    def create_M(self, p_lst: list) -> pd.DataFrame:
        return pd.DataFrame(
            data    = np.zeros((len(p_lst), len(p_lst))),
            index   = p_lst,
            columns = p_lst
        )
    
    def get_evp(
        self,
        df: pd.DataFrame,
        p_lst: list,
        matrix_S: pd.DataFrame
    ):
        # create matrix S
        for player_1 in p_lst:
            for player_2 in p_lst:
                if player_1 != player_2:
                    # Create two boolean Series to indicate whether the row contains the player being searched for.
                    condition_1 = df.isin([player_1]).any(axis=1)
                    condition_2 = df.isin([player_2]).any(axis=1)
                    # Retrieve the rows that contain both of the players being searched for simultaneously.
                    pair_df = df[condition_1 & condition_2]
                    # Calculate the weighted average of the Plus/Minus values based on the number of appearances.
                    if pair_df.empty:
                        mean_score = np.nan
                    else:
                        mean_score = (
                            (pair_df['GP'] * pair_df[f'normal_{self.sp}'])
                            .sum()
                            / pair_df['GP']
                            .sum()
                        )
                    # Populate the pre-created matrix with the calculated values.
                    matrix_S.loc[player_1, player_2] = mean_score
                else:
                    # Calculate the mean of all lineups that include the player to represent their individual ability.
                    condition_3 = df.isin([player_1]).any(axis=1)
                    self_df = df[condition_3]
                    mean_score = (
                        (self_df['GP']*self_df[f'normal_{self.sp}']).sum()
                        / self_df['GP'].sum()
                    )
                    matrix_S.loc[player_1, player_1] = mean_score
                    
        for row in range(len(matrix_S)):
            for col in range(len(matrix_S)):
                if np.isnan(matrix_S.iloc[row, col]):
                    player_1_score = matrix_S.iloc[row, row]
                    player_2_score = matrix_S.iloc[col, col]
                    matrix_S.iloc[row, col] = np.sqrt(player_1_score * player_2_score)
        
        # create matrix G
        matrix_G_np = np.zeros((len(matrix_S), len(matrix_S)))
        matrix_S_np = np.array(matrix_S)
        for col in range(len(matrix_S)):
            if matrix_S_np[col, col] == 0:
                matrix_G_np[:, col] = 0
            else:
                matrix_G_np[:, col] = matrix_S_np[:, col] / matrix_S_np[col, col]      
        # If a player's individual ability Sii is 0, it indicates that the player only appears in combinations with a Plus/Minus of 0.
        # This can cause division by zero during the calculation, resulting in NaN values in the G matrix. Fill these NaN values with 0 (indicating no contribution).
        matrix_G_np = np.nan_to_num(matrix_G_np, nan=0)
       
        eigenvalues, eigenvectors = np.linalg.eig(matrix_G_np)                 
        max_eigenvalue_index = np.argmax(eigenvalues)
        evp = eigenvectors[:, max_eigenvalue_index]
        evp = np.abs(evp)
        
        evp_dict = dict(zip(p_lst, evp))
        def evp_std(row, evp_dict):
            player_scores = [evp_dict[player] for player in row.values]
            return pd.Series([pd.Series(player_scores).std()], index=['std']) 
                
        df['evp_std'] = (
            df.loc[:, 'player_1':'player_5']
            .apply(evp_std, axis=1, args=(evp_dict,))
        )
        return evp_dict, df
 
    def clean_data(self) -> pd.DataFrame:
        self.df = self.df[self.df['GP'] > self.gp]        
        self.df[f'normal_{self.sp}'] = (self
                                        .normalized_fun(self.df[self.sp])
                                        )
        df_col = [f'player_{i+1}' for i in range(5)]
        self.df[df_col] = (self
                           .df['GROUP_NAME']
                           .str
                           .split(' - ', expand=True)
                           )
        df_col.extend(['GROUP_ID', 'year', 'team', 'TEAM_ABBREVIATION',
                       'W_PCT', 'GP', f'normal_{self.sp}'])
        self.df = self.df[df_col]
        
        result_dfs = []
        result_dict = {}
        for (year, team), group_df in tqdm(self.df.groupby(['year', 'team'])):
            p_lst = list(
                (np
                 .unique(
                     group_df
                     .loc[:, 'player_1':'player_5']
                     .to_numpy())
                 )
            )
            matrix_S = self.create_M(p_lst)
            evp_dict, df = self.get_evp(group_df, p_lst, matrix_S)
            if year not in result_dict:
                result_dict[year] = {}
            result_dict[year][team] = evp_dict
            result_dfs.append(df)

        result_df = pd.concat(result_dfs)      
        return result_df, result_dict
        
#%% Load lineups data
import os
import sys
from pathlib import Path
current_working_directory = Path(os.getcwd())
project_root = current_working_directory.parents[1]
sys.path.append(str(project_root / 'src'))

data_dir = project_root / 'data'

with open(data_dir / '5lineups_100poss.json') as f:
    lineups_data = json.load(f)  

def read_lineups_df(lineups_dict):
    dfs = []
    for year, data in lineups_dict.items():
        for team, team_data in data.items():
            print(f'Processing data for the {year} season of the {team} team')
            df = pd.DataFrame(team_data)
            df['year'] = year
            df['team'] = team
            dfs.append(df)
    df = pd.concat(dfs)
    return df

lineups_df = read_lineups_df(lineups_data)

#%%
gp = 9
processor = EVP(lineups_df, gp, 'PLUS_MINUS')
std_evp_df, evp_dict = processor.clean_data()
