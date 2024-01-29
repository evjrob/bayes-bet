import gzip
import json
import os
import pandas as pd
from tqdm import tqdm
import yaml

from bayesbet.nhl.data_utils import team_abbrevs
from bayesbet.nhl.model import IterativeUpdateModel, ModelState, ModelVariables


def main():
    os.makedirs("results/train", exist_ok=True)
    with open("params.yaml", "r") as f:
        params = yaml.safe_load(f)

    # Initialize model
    n_teams = len(team_abbrevs)
    initial_priors = ModelState(
        teams = list(team_abbrevs.keys()),
        variables = ModelVariables(
            i=(1.0, 0.1),
            h=(0.25, 0.1),
            o=([0.0] * n_teams, [0.15] * n_teams),
            d=([0.0] * n_teams, [0.15] * n_teams),
        )
    )
    model = IterativeUpdateModel(initial_priors, **params["model"])

    # Import the training games and find the unique game dates
    games = pd.read_parquet("../data/final/train/games.parquet")
    game_dates = games["game_date"].sort_values().unique()

    predictions = []
    model_states = [model.priors]
    
    for game_date in tqdm(game_dates):
        # Game day predictions
        date_idx = (games["game_date"] == game_date) & (
            games["game_state"] != "Postponed"
        )
        games = games[date_idx].reset_index(drop=True)
        date_predictions = model.predict(games)
        date_predictions = [p.model_dump_json() for p in date_predictions]
        predictions += date_predictions

        # Get games from the most recent game date played
        posteriors = model.fit(games, cores=3)
        model_states.append(posteriors)

    predictions_json = json.dumps(predictions, indent=2).encode('utf-8')
    with gzip.open('results/train/predictions.json.gz', 'wb') as f:
        f.write(predictions_json)

    model_states_json = [m.model_dump_json() for m in model_states]
    model_states_json = json.dumps(model_states_json, indent=2).encode('utf-8')
    with gzip.open('results/train/model_states.json.gz', 'wb') as f:
        f.write(model_states_json)

    # Generate matching LeagueStates from the model states
    league_states = [m.to_league_state() for m in model_states]
    league_states_json = [l.model_dump_json() for l in league_states]
    league_states_json = json.dumps(league_states_json, indent=2).encode('utf-8')
    with gzip.open('results/train/league_states.json.gz', 'wb') as f:
        f.write(league_states_json)


if __name__ == "__main__":
    main()