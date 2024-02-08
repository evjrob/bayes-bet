from dvclive import Live
import gzip
import json
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import yaml

from bayesbet.nhl.data_model import GamePrediction
from bayesbet.nhl.evaluate import accuracy, log_loss


def cumulative_performance_by_date(prediction_dict):
    performance_by_date = {
        date: {
            "accuracy": accuracy(predictions),
            "log_loss": log_loss(predictions),
            "n_games": len(predictions),
        }
        for date, predictions in prediction_dict.items()
    }

    cumulative_performance = []
    previous_total_games_played = 0
    previous_accuracy = 0
    previous_log_loss = 0

    for date, performance in performance_by_date.items():
        current_date_games_played = performance["n_games"]
        new_total_games_played = previous_total_games_played + current_date_games_played
        previous_weight = previous_total_games_played / new_total_games_played
        new_weight = current_date_games_played / new_total_games_played

        new_accuracy = previous_weight * previous_accuracy + new_weight * performance["accuracy"]
        new_log_loss = previous_weight * previous_log_loss + new_weight * performance["log_loss"]

        cumulative_performance.append({
            "date": date,
            "accuracy": new_accuracy,
            "log_loss": new_log_loss,
            "n_games": new_total_games_played,
        })

        previous_total_games_played = new_total_games_played
        previous_accuracy = new_accuracy
        previous_log_loss = new_log_loss

    return cumulative_performance


def performance_vs_time_plot(
    training_performance_by_date, test_performance_by_date
):
    train_data = pd.DataFrame(training_performance_by_date)
    train_data["dataset_type"] = "train"
    test_data = pd.DataFrame(test_performance_by_date)
    test_data["dataset_type"] = "test"

    plot_data = pd.concat([train_data, test_data], ignore_index=True)
    plot_data["date"] = pd.to_datetime(plot_data["date"])
    plot_data = plot_data.melt(
        id_vars=["date", "n_games", "dataset_type"],
        value_vars=["accuracy", "log_loss"],
        var_name="metric",
        value_name="score",
    ).reset_index(drop=True)

    g = sns.FacetGrid(
        data=plot_data,
        row="metric",
        col="dataset_type",
        sharex=False,
        height=5.0,
        aspect=1.2
    )
    g.map(sns.lineplot, "date", "score")
    g.set_xticklabels(rotation=90)
    plt.tight_layout()

    return g.figure


def main():
    with Live("results/evaluate") as live:
        # Load and log
        with open("params.yaml", "r") as f:
            params = yaml.safe_load(f)

        live.log_params(params["model"])

        # Load predictions
        with gzip.open('results/train/predictions.json.gz', 'rb') as f:
            training_predictions_json = json.load(f)
            training_predictions = {
                d: [GamePrediction.model_validate(gp) for gp in p]
                for d, p in training_predictions_json.items()
            }

        with gzip.open('results/test/predictions.json.gz', 'rb') as f:
            test_predictions_json = json.load(f)
            test_predictions = {
                d: [GamePrediction.model_validate(gp) for gp in p] 
                for d, p in test_predictions_json.items()
            }

        # Compute cumulative model performance by date
        training_performance_by_date = cumulative_performance_by_date(
            training_predictions
        )
        
        test_performance_by_date = cumulative_performance_by_date(
            test_predictions
        )

        performance_plot = performance_vs_time_plot(
            training_performance_by_date,
            test_performance_by_date,
        )
        performance_plot.savefig("results/evaluate/bayesbet_performance.png")

        live.log_metric("training_accuracy", training_performance_by_date[-1]["accuracy"])
        live.log_metric("training_log_loss", training_performance_by_date[-1]["log_loss"])
        live.log_metric("test_accuracy", test_performance_by_date[-1]["accuracy"])
        live.log_metric("test_log_loss", test_performance_by_date[-1]["log_loss"])
        live.log_artifact(
            path="results/evaluate/bayesbet_performance.png",
            name="performance",
        )

if __name__ == "__main__":
    main()