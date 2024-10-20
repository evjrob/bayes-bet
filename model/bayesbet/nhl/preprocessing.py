import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.exceptions import NotFittedError


class ShotFeatures(BaseEstimator, TransformerMixin):
    def __init__(self):
        self.required_columns = [
            "shot_x",
            "shot_y",
            "last_event_x",
            "last_event_y",
            "goal_x",
            "goal_y",
            "last_event",
            "time_since_last_event",
        ]
        self.n_features_in_ = None

    def fit(self, shot_data, y=None):
        self._validate_input(shot_data)
        self.n_features_in_ = len(self.required_columns)
        return self

    def transform(self, shot_data):
        self._validate_input(shot_data)
        if not hasattr(self, "n_features_in_"):
            raise NotFittedError(
                "This ShotFeatures instance is not fitted yet. Call 'fit' before using this estimator."
            )

        shot_data = shot_data.copy()

        # Add shot distance
        shot_data["shot_distance"] = np.sqrt(
            (shot_data["shot_x"] - shot_data["goal_x"]) ** 2
            + (shot_data["shot_y"] - shot_data["goal_y"]) ** 2
        )
        shot_data["shot_angle"] = np.arctan2(
            shot_data["shot_y"] - shot_data["goal_y"],
            np.maximum(abs(shot_data["shot_x"] - shot_data["goal_x"]), 0.1),
        )
        shot_data["last_event_distance"] = np.sqrt(
            (shot_data["last_event_x"] - shot_data["shot_x"]) ** 2
            + (shot_data["last_event_y"] - shot_data["shot_y"]) ** 2
        )
        shot_data["last_event_angle"] = np.arctan2(
            shot_data["last_event_y"] - shot_data["goal_y"],
            np.maximum(abs(shot_data["last_event_x"] - shot_data["goal_x"]), 0.1),
        )
        shot_data["is_rebound"] = (shot_data["last_event"] == "Shot") & (
            shot_data["time_since_last_event"] < 2
        )
        shot_data["rebound_angle"] = (
            shot_data["shot_angle"] - shot_data["last_event_angle"]
        ) * shot_data["is_rebound"]

        return shot_data

    def _validate_input(self, shot_data):
        if not isinstance(shot_data, pd.DataFrame):
            raise ValueError("Input data must be a pandas DataFrame.")

        missing_columns = set(self.required_columns) - set(shot_data.columns)
        if missing_columns:
            raise ValueError(
                f"Input data is missing required columns: {missing_columns}"
            )
