import os
import pickle
import yaml

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from dvclive import Live
from sklearn.neural_network import MLPClassifier
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_validate
from sklearn.preprocessing import OneHotEncoder, RobustScaler
from sklearn.metrics import log_loss, auc, roc_auc_score, roc_curve
from sklearn.metrics import RocCurveDisplay

def main(model_type):
    with Live("results/evaluate_model") as live:
        train_shots = pd.read_parquet("../data/final/train/shots.parquet")
        test_shots = pd.read_parquet("../data/final/test/shots.parquet")

        float_cols = ["shot_x", "shot_y", "last_event_x", "last_event_y", "time_since_last_event", "opposing_skaters", "current_skaters", "time_since_even_strength"]
        categorical_cols = ["shot_type", "last_event"]

        X_train = train_shots.drop(columns=["goal", "home_team_defending_side", "play_number", "player_id", "game_id"])
        X_train[float_cols] = X_train[float_cols].astype(float)
        y_train = train_shots["goal"]

        X_test = test_shots.drop(columns=["goal", "home_team_defending_side",  "play_number", "player_id", "game_id"])
        X_test[float_cols] = X_test[float_cols].astype(float)
        y_test = test_shots["goal"]

        preprocessor = ColumnTransformer(
            transformers = [
                ('scale', RobustScaler(), float_cols),
                ('onehot', OneHotEncoder(drop="if_binary", handle_unknown="infrequent_if_exist"), categorical_cols)
            ]
        )

        if model_type == "MLPClassifier":
            classifier = MLPClassifier(hidden_layer_sizes=(20, 20, 20, 20), max_iter=1000, alpha=1e-4)

        pipe = Pipeline(
            [
                ('preprocess', preprocessor),
                ('classifier', classifier),
            ]
        )

        scoring = ["neg_log_loss", "roc_auc"]
        scores = cross_validate(pipe, X_train, y_train, cv=5, scoring=scoring, return_train_score=True)

        train_log_loss = -np.mean(scores["train_neg_log_loss"])
        validation_log_loss = -np.mean(scores["test_neg_log_loss"])
        train_roc_auc = np.mean(scores["train_roc_auc"])
        validation_roc_auc = np.mean(scores["test_roc_auc"])

        live.log_metric("train_log_loss", train_log_loss)
        live.log_metric("validation_log_loss", validation_log_loss)
        live.log_metric("train_roc_auc", train_roc_auc)
        live.log_metric("validation_roc_auc", validation_roc_auc)

        pipe.fit(X_train, y_train)

        y_pred_proba = pipe.predict_proba(X_test)
        test_log_loss = log_loss(y_test, y_pred_proba)
        test_roc_auc = roc_auc_score(y_test, y_pred_proba[:,1])
    
        live.log_metric("test_log_loss", test_log_loss)
        live.log_metric("test_roc_auc", test_roc_auc)

        # ROC curve for trained model
        y_pred = pipe.predict_proba(X_train)[:,1]
        fpr, tpr, _ = roc_curve(y_train, y_pred)
        roc_auc = auc(fpr, tpr)
        display = RocCurveDisplay(fpr=fpr, tpr=tpr, roc_auc=roc_auc)
        display.plot()
        plt.title("Training ROC")
        live.log_image("training_roc_curve.png", display.figure_)

        # ROC curve for test model
        y_pred = pipe.predict_proba(X_test)[:,1]
        fpr, tpr, _ = roc_curve(y_test, y_pred)
        roc_auc = auc(fpr, tpr)
        display = RocCurveDisplay(fpr=fpr, tpr=tpr, roc_auc=roc_auc)
        display.plot()
        plt.title("Test ROC")
        live.log_image("test_roc_curve.png", display.figure_)

        # Save the model
        os.makedirs("results/evaluate_model", exist_ok=True)
        with open("results/evaluate_model/model.pkl", "wb") as f:
            pickle.dump(pipe, f)
    

if __name__ == "__main__":
    with open("params.yaml", "r") as f:
        params = yaml.safe_load(f)
    model_type = params["evaluate_model"]["model_type"]
    main(model_type)