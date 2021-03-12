import json
import numpy as np
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import sys

sys.path.append('../model/nhl/')
from db import most_recent_dynamodb_item
from metadata import team_abbrevs, team_colors

# Get the predictions for today
today_dt = dt.date.today()
today = today_dt.strftime('%Y-%m-%d')
title_date = today_dt.strftime('%b %d, %Y')
item = most_recent_dynamodb_item('nhl', today)

# Extract the game predictions and win probabilities
games = []
for g in item['GamePredictions']:
    home_team = g['home_team']
    away_team = g['away_team']
    win_percentages = [float(p) for p in g['WinPercentages']]
    home_win_prob = sum(win_percentages[:3]) * 100
    away_win_prob = sum(win_percentages[3:]) * 100
    games.append([home_team, away_team, home_win_prob, away_win_prob])

rows = np.ceil(len(games)/2).astype(int)
#colors = ['#619CFF', '#F8766D']
fig, axs = plt.subplots(rows, 2, figsize=(12, rows*2))

for k in range(rows*2):
    i = k // rows
    j = k % rows
    if k < len(games):
        g = games[k]
        teams = g[:2]
        labels = [team_abbrevs[t] for t in teams]
        probs = g[2:]
        colors = [team_colors[t][0] for t in teams]
        accents = [team_colors[t][1] for t in teams]
        axs[j,i].barh(labels, probs, color=colors, edgecolor=accents, linewidth=3)
        axs[j,i].set_title(f'{teams[1]} @ {teams[0]}', loc='left')
        for vidx, v in enumerate(probs):
            axs[j,i].text(v + 3, vidx - 0.075, f'{v:.2f}%')
    else:
        axs[j,i].get_yaxis().set_ticks([])
    axs[j,i].set_xlim([0,100])
    axs[j,i].set_frame_on(False)
    axs[j,i].get_xaxis().set_ticks([])

fig.subplots_adjust(hspace=1, wspace=0.5, top=0.85, right=0.85, left=0.15)
plt.suptitle(f'BayesBet Estimated Hockey Game Win Probabilities - {title_date}', fontsize=19)
fig.text(.1, .025, 'Everett Robinson (@evjrob)', ha='left')
fig.text(.9, .025, 'bayesbet.everettsprojects.com', ha='right')
plt.savefig('game_preds_plot.png', bbox_inches='tight')