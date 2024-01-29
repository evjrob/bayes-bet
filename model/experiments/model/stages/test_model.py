import gzip
import json
import os
import pandas as pd
from tqdm import tqdm
import yaml

from bayesbet.nhl.model import IterativeUpdateModel, ModelState


def main():
    os.makedirs("results/test", exist_ok=True)
    with open("params.yaml", "r") as f:
        params = yaml.safe_load(f)

    # Initialize model
    with gzip.open('results/train/model_states.json.gz', 'rb') as f:
        model_states_json = json.load(f)
        last_model_state_json = model_states_json[-1]
    initial_priors = ModelState.model_validate_json(last_model_state_json)
    model = IterativeUpdateModel(initial_priors, **params["model"])

    # Import the testing games and find the unique game dates
    games = pd.read_parquet("../data/final/test/games.parquet")
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
    with gzip.open('results/test/predictions.json.gz', 'wb') as f:
        f.write(predictions_json)

    model_states_json = [m.model_dump_json() for m in model_states]
    model_states_json = json.dumps(model_states_json, indent=2).encode('utf-8')
    with gzip.open('results/test/model_states.json.gz', 'wb') as f:
        f.write(model_states_json)

    # Generate matching LeagueStates from the model states
    league_states = [m.to_league_state() for m in model_states]
    league_states_json = [l.model_dump_json() for l in league_states]
    league_states_json = json.dumps(league_states_json, indent=2).encode('utf-8')
    with gzip.open('results/test/league_states.json.gz', 'wb') as f:
        f.write(league_states_json)

if __name__ == "__main__":
    main()