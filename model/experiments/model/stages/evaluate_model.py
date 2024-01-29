from dvclive import Live
import gzip
import json
import yaml

from bayesbet.nhl.data_model import GamePrediction
from bayesbet.nhl.evaluate import accuracy, log_loss


def main():
    with Live("results/evaluate") as live:
        # Load and log
        with open("params.yaml", "r") as f:
            params = yaml.safe_load(f)

        live.log_params(params["model"])

        # Load predictions
        with gzip.open('results/train/predictions.json.gz', 'rb') as f:
            training_predictions_json = json.load(f)
            training_predictions = [
                GamePrediction.model_validate_json(gp) 
                for gp in training_predictions_json
            ]

        with gzip.open('results/test/predictions.json.gz', 'rb') as f:
            test_predictions_json = json.load(f)
            test_predictions = [
                GamePrediction.model_validate_json(gp) 
                for gp in test_predictions_json
            ]

        # Compute and log model performance
        print(test_predictions_json)
        training_accuracy = accuracy(training_predictions)
        training_log_loss = log_loss(training_predictions)

        test_accuracy = accuracy(test_predictions)
        test_log_loss = log_loss(test_predictions)

        live.log_metric("training_accuracy", training_accuracy)
        live.log_metric("training_log_loss", training_log_loss)
        live.log_metric("test_accuracy", test_accuracy)
        live.log_metric("test_log_loss", test_log_loss)

if __name__ == "__main__":
    main()