import gzip
import json
import os
import pandas as pd
from tqdm import tqdm
import yaml

from bayesbet.nhl.model import IterativeUpdateModel


def main():
    with open("params.yaml", "r") as f:
        params = yaml.safe_load(f)

    with gzip.open('results/train/model_states.json.gz', 'rb') as f:
        model_states = json.loads(f.read().decode('utf-8'))

    # Initialize model
    params["model"]["priors"] = model_states[-1]
    model = IterativeUpdateModel(**params["model"])

    # Import the test games and find the unique game dates
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
        predictions += date_predictions

        # Get games from the most recent game date played
        posteriors = model.fit(games)
        model_states.append(posteriors)

    os.makedirs("results/test", exist_ok=True)

    predictions_json = json.dumps(predictions, indent=2).encode('utf-8')
    with gzip.open('results/test/predictions.json.gz', 'wb') as f:
        f.write(predictions_json)

    model_states_json = json.dumps(model_states, indent=2).encode('utf-8')
    with gzip.open('results/test/model_states.json.gz', 'wb') as f:
        f.write(model_states_json)


if __name__ == "__main__":
    main()