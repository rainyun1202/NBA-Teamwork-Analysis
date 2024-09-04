import pandas as pd
import statsmodels.api as sm
import os
import sys
from pathlib import Path
# Set up the project root directory and append to system path for module imports
current_working_directory = Path(os.getcwd())
project_root = current_working_directory.parents[1]
sys.path.append(str(project_root / 'src'))
from models import formatted_reg_model
from utils import generate_latex_table

# Define the directory for data storage
data_dir = project_root / 'data'

#%%

df = pd.read_csv(data_dir / '(new) all_100poss_lineups_data.csv')
df['const'] = 1
df.columns
y = df['PLUS_MINUS']
X = df[['const', 'player_rapm_sum']]
model = sm.OLS(y, X)
results = model.fit()
print(results.summary())

#%%

result_df = formatted_reg_model(results)
generate_latex_table(result_df, "reg_team_apm.tex")

#%%
# In my master's thesis,
# I overlooked the issue of mismatched player names between the passing data and the Lineups data,
# resulting in some discrepancies.
# The values in the code have been updated to the correct version.
df['PM_minus_RAPM'] = df['PLUS_MINUS'] - df['player_rapm_sum']*2.1760
view = df[['year', 'team', 'player_1', 'player_2', 'player_3',
           'player_4', 'player_5', 'PM_minus_RAPM', 'Appearances']]

view.to_csv(data_dir / 'team_effect.csv', index=False)

#%%

y = df['PM_minus_RAPM']
X = df[['const',
        'OREB', 'DREB', 'AST', 'TOV', 'STL',
        'std_pass_out']]

model = sm.OLS(y, X)
results = model.fit()
print(results.summary())

#%%

result_df = formatted_reg_model(results)
generate_latex_table(result_df, "team_effect.tex")
