import os
import pickle
import yaml

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from dvclive import Live
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_validate
from sklearn.preprocessing import OneHotEncoder, RobustScaler
from sklearn.metrics import log_loss, auc, roc_auc_score, roc_curve
from sklearn.metrics import RocCurveDisplay
from sklearn.calibration import calibration_curve
from sklearn.inspection import permutation_importance
from xgboost import XGBClassifier

from bayesbet.base.models import BayesianMLPClassifier, MappedClassifier
from bayesbet.base.preprocessing import FeatureSelector
from bayesbet.nhl.preprocessing import ShotFeatures
from bayesbet.nhl.visualize import plot_expected_goals


def main(model_type):
    with Live("results/evaluate_model") as live:
        train_shots = pd.read_parquet("../data/final/train/shots.parquet")
        test_shots = pd.read_parquet("../data/final/test/shots.parquet")

        X_train = train_shots.drop(columns=["goal"])
        y_train = train_shots["goal"]

        X_test = test_shots.drop(columns=["goal"])
        y_test = test_shots["goal"]

        float_cols = [
            "shot_x",
            "shot_y",
            "shot_distance",
            "shot_angle",
            "last_event_x",
            "last_event_y",
            "last_event_distance",
            "last_event_angle",
            "time_since_last_event",
            "opposing_skaters",
            "current_skaters",
            "opposing_score",
            "current_score",
            "time_since_even_strength",
            "rebound_angle",
        ]
        categorical_cols = ["shot_type", "last_event", "is_rebound", "empty_net"]

        preprocessor = ColumnTransformer(
            transformers=[
                ("scale", RobustScaler(), float_cols),
                (
                    "onehot",
                    OneHotEncoder(
                        drop="if_binary", handle_unknown="infrequent_if_exist"
                    ),
                    categorical_cols,
                ),
            ]
        )

        if model_type == "MLPClassifier":
            classifier = MLPClassifier(
                hidden_layer_sizes=(20, 20, 20, 20), max_iter=1000, alpha=1e-4
            )
        elif model_type == "LogisticRegression":
            classifier = LogisticRegression(max_iter=1000)
        elif model_type == "GradientBoostingClassifier":
            classifier = GradientBoostingClassifier(
                n_estimators=100, learning_rate=0.1, max_depth=3
            )
        elif model_type == "XGBClassifier":
            classifier = XGBClassifier(n_estimators=100, learning_rate=0.1, max_depth=3)
        elif model_type == "BayesianMLPClassifier":
            classifier = BayesianMLPClassifier(
                hidden_layer_sizes=(15, 15, 15),
                num_warmup=5000,
                num_samples=70000,
                step_size=1e-2,
                show_progress=True,
            )
        elif model_type == "MappedClassifier":
            classifier = BayesianMLPClassifier(
                hidden_layer_sizes=(15, 15, 15),
                num_warmup=5000,
                num_samples=70000,
                step_size=1e-2,
                show_progress=True,
            )
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

        pipe = Pipeline(
            [
                ("features", ShotFeatures()),
                ("selector", FeatureSelector(float_cols, categorical_cols)),
                ("preprocess", preprocessor),
                ("classifier", classifier),
            ]
        )

        if model_type == "MappedClassifier":
            pipe = MappedClassifier(
                partition_columns=["empty_net", "opposing_skaters", "current_skaters"],
                base_estimator=pipe,
            )

        print("Cross validating model")
        scoring = ["neg_log_loss", "roc_auc"]
        scores = cross_validate(
            pipe, X_train, y_train, cv=5, scoring=scoring, return_train_score=True
        )

        train_log_loss = -np.mean(scores["train_neg_log_loss"])
        validation_log_loss = -np.mean(scores["test_neg_log_loss"])
        train_roc_auc = np.mean(scores["train_roc_auc"])
        validation_roc_auc = np.mean(scores["test_roc_auc"])

        live.log_metric("train_log_loss", train_log_loss)
        live.log_metric("validation_log_loss", validation_log_loss)
        live.log_metric("train_roc_auc", train_roc_auc)
        live.log_metric("validation_roc_auc", validation_roc_auc)

        print("Fitting model on all training data")
        pipe.fit(X_train, y_train)

        print("Evaluating model on test data")
        y_pred_proba = pipe.predict_proba(X_test)
        test_log_loss = log_loss(y_test, y_pred_proba)
        test_roc_auc = roc_auc_score(y_test, y_pred_proba[:, 1])

        live.log_metric("test_log_loss", test_log_loss)
        live.log_metric("test_roc_auc", test_roc_auc)

        # ROC curve for trained model
        y_pred = pipe.predict_proba(X_train)[:, 1]
        fpr, tpr, _ = roc_curve(y_train, y_pred)
        roc_auc = auc(fpr, tpr)
        display = RocCurveDisplay(fpr=fpr, tpr=tpr, roc_auc=roc_auc)
        display.plot()
        plt.title("Training ROC")
        live.log_image("training_roc_curve.png", display.figure_)

        # ROC curve for test model
        y_pred = pipe.predict_proba(X_test)[:, 1]
        fpr, tpr, _ = roc_curve(y_test, y_pred)
        roc_auc = auc(fpr, tpr)
        display = RocCurveDisplay(fpr=fpr, tpr=tpr, roc_auc=roc_auc)
        display.plot()
        plt.title("Test ROC")
        live.log_image("test_roc_curve.png", display.figure_)

        # Calibration plot
        prob_true, prob_pred = calibration_curve(y_test, y_pred_proba[:, 1], n_bins=10)
        plt.figure(figsize=(10, 6))
        plt.plot(prob_pred, prob_true, marker="o")
        plt.plot([0, 1], [0, 1], linestyle="--")
        plt.xlabel("Predicted probability")
        plt.ylabel("True probability")
        plt.title("Calibration plot")
        live.log_image("calibration_plot.png", plt.gcf())
        plt.close()

        # Feature importance
        perm_importance = permutation_importance(
            pipe, X_test, y_test, n_repeats=10, random_state=42
        )
        feature_importance = pd.DataFrame(
            {"feature": X_test.columns, "importance": perm_importance.importances_mean}
        ).sort_values("importance", ascending=False)
        plt.figure(figsize=(10, 6))
        plt.barh(
            feature_importance["feature"][:10][::-1],
            feature_importance["importance"][:10][::-1],
        )
        plt.yticks(rotation=0)
        plt.title("Top 10 Feature Importances")
        plt.xlabel("Importance")
        plt.ylabel("Feature")
        plt.tight_layout()
        live.log_image("feature_importance.png", plt.gcf())
        plt.close()

        # Compute and plot expected goals
        expected_goals = train_shots.copy()
        expected_goals["expected_goal"] = pipe.predict_proba(expected_goals)[:, 1]
        fig = plot_expected_goals(expected_goals)
        live.log_image("expected_goals.png", fig)

        # Save the model
        os.makedirs("results/evaluate_model", exist_ok=True)
        with open("results/evaluate_model/model.pkl", "wb") as f:
            pickle.dump(pipe, f)


if __name__ == "__main__":
    with open("params.yaml", "r") as f:
        params = yaml.safe_load(f)
    model_type = params["evaluate_model"]["model_type"]
    main(model_type)
