import os
import pickle
import yaml

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from dvclive import Live
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter
from sklearn.neural_network import MLPClassifier
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_validate
from sklearn.preprocessing import OneHotEncoder, RobustScaler
from sklearn.metrics import log_loss, auc, roc_auc_score, roc_curve
from sklearn.metrics import RocCurveDisplay
from sklearn.calibration import calibration_curve
from sklearn.inspection import permutation_importance


# expected goals plotting
def plot_rink(ax, plot_half=False, board_radius=28, alpha=1):
    def add_arc(center, theta1, theta2):
        ax.add_artist(mpl.patches.Arc(center, board_radius * 2, board_radius * 2,
                                      theta1=theta1, theta2=theta2, edgecolor="Black",
                                      lw=4.5, zorder=0, alpha=alpha))

    # Corner Boards
    corners = [
        ((100 - board_radius, (85 / 2) - board_radius), 0, 89),
        ((-100 + board_radius, (85 / 2) - board_radius), 90, 180),
        ((-100 + board_radius, -(85 / 2) + board_radius), 180, 270),
        ((100 - board_radius, -(85 / 2) + board_radius), 270, 360)
    ]
    for center, theta1, theta2 in corners:
        add_arc(center, theta1, theta2)

    # Plot Boards
    boards = [
        ([-100 + board_radius, 100 - board_radius], [-42.5, -42.5]),
        ([-100 + board_radius, 100 - board_radius], [42.5, 42.5]),
        ([-100, -100], [-42.5 + board_radius, 42.5 - board_radius]),
        ([100, 100], [-42.5 + board_radius, 42.5 - board_radius])
    ]
    for x, y in boards:
        ax.plot(x, y, linewidth=4.5, color="Black", zorder=0, alpha=alpha)

    # Goal Lines
    for x in [-89, 89]:
        ax.plot([x, x], [-42.5 + 4.7, 42.5 - 4.7], linewidth=3, color="Red", zorder=0, alpha=alpha)

    # Center Line and FaceOff Dot
    ax.plot([0, 0], [-42.5, 42.5], linewidth=3, color="Red", zorder=0, alpha=alpha)
    ax.plot(0, 0, markersize=6, color="Blue", marker="o", zorder=0, alpha=alpha)

    # Center Circle
    ax.add_artist(mpl.patches.Circle((0, 0), radius=33/2, facecolor="none",
                                     edgecolor="Blue", linewidth=3, zorder=0, alpha=alpha))

    # Zone Faceoff Dots and Circles
    for x, y in [(69, 22), (69, -22), (-69, 22), (-69, -22)]:
        ax.plot(x, y, markersize=6, color="Red", marker="o", zorder=0, alpha=alpha)
        ax.add_artist(mpl.patches.Circle((x, y), radius=15, facecolor="none",
                                         edgecolor="Red", linewidth=3, zorder=0, alpha=alpha))

    # Neutral Zone Faceoff Dots
    for x, y in [(22, 22), (22, -22), (-22, 22), (-22, -22)]:
        ax.plot(x, y, markersize=6, color="Red", marker="o", zorder=0, alpha=alpha)

    # Blue Lines
    for x in [-25, 25]:
        ax.plot([x, x], [-42.5, 42.5], linewidth=2, color="Blue", zorder=0, alpha=alpha)

    # Goalie Crease and Goal
    for x in [-89, 89]:
        ax.add_artist(mpl.patches.Arc((x, 0), 6, 6, theta1=90 if x > 0 else 270,
                                      theta2=270 if x > 0 else 90, facecolor="Blue",
                                      edgecolor="Red", lw=2, zorder=0, alpha=alpha))
        ax.add_artist(mpl.patches.Rectangle((x if x > 0 else x - 2, -2), 2, 4,
                                            lw=2, color="Red", fill=False, zorder=0, alpha=alpha))

    # Set axis limits and remove spines
    ax.set_xlim((-0.5, 100.5) if plot_half else (-101, 101))
    ax.set_ylim(-43, 43)
    for spine in ax.spines.values():
        spine.set_visible(False)


def plot_xgoals(xgoals, title="Expected Goals"):
    data_min = 0
    data_max = xgoals.max()
    mid_val = xgoals.mean()

    fig, ax = plt.subplots(1, 1, figsize=(11, 12), facecolor='w', edgecolor='k')
    xgoal_heatmap = ax.imshow(xgoals, alpha=0.5, cmap='jet', extent=[0, 100, -42.5, 42.5])
    plot_rink(ax, plot_half=True, board_radius=25, alpha=0.9)
    plt.axis('off')
    fig.colorbar(xgoal_heatmap, orientation="horizontal", pad=0.05)
    plt.title(title)

    return fig


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

        # Calibration plot
        prob_true, prob_pred = calibration_curve(y_test, y_pred_proba[:,1], n_bins=10)
        plt.figure(figsize=(10, 6))
        plt.plot(prob_pred, prob_true, marker='o')
        plt.plot([0, 1], [0, 1], linestyle='--')
        plt.xlabel('Predicted probability')
        plt.ylabel('True probability')
        plt.title('Calibration plot')
        live.log_image("calibration_plot.png", plt.gcf())
        plt.close()

        # Feature importance
        perm_importance = permutation_importance(pipe, X_test, y_test, n_repeats=10, random_state=42)
        feature_importance = pd.DataFrame({
            'feature': X_test.columns,
            'importance': perm_importance.importances_mean
        }).sort_values('importance', ascending=False)
        plt.figure(figsize=(10, 6))
        plt.barh(feature_importance['feature'][:10][::-1], feature_importance['importance'][:10][::-1])
        plt.yticks(rotation=0)
        plt.title('Top 10 Feature Importances')
        plt.xlabel('Importance')
        plt.ylabel('Feature')
        plt.tight_layout()
        live.log_image("feature_importance.png", plt.gcf())
        plt.close()

        # Compute and plot expected goals
        y_train_proba = pipe.predict_proba(X_train)
        [x,y] = np.round(np.meshgrid(np.linspace(0,100,100),np.linspace(-42.5,42.5,85)))
        xgoals = griddata((train_shots['shot_x'], train_shots['shot_y']), y_train_proba[:, 1], (x,y), method='cubic', fill_value=0)
        xgoals[xgoals < 0] = 0

        fig = plot_xgoals(xgoals)
        live.log_image("expected_goals.png", fig)

        xgoals_smooth = gaussian_filter(xgoals, sigma=2)
        fig = plot_xgoals(xgoals_smooth, title="Expected Goals (Smoothed)")
        live.log_image("expected_goals_smooth.png", fig)

        # Save the model
        os.makedirs("results/evaluate_model", exist_ok=True)
        with open("results/evaluate_model/model.pkl", "wb") as f:
            pickle.dump(pipe, f)
    

if __name__ == "__main__":
    with open("params.yaml", "r") as f:
        params = yaml.safe_load(f)
    model_type = params["evaluate_model"]["model_type"]
    main(model_type)