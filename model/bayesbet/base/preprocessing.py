import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class FeatureSelector(BaseEstimator, TransformerMixin):
    def __init__(self, float_cols, categorical_cols):
        # Check for duplicated column names
        duplicated_cols = set(float_cols) & set(categorical_cols)
        if duplicated_cols:
            raise ValueError(
                f"Duplicated columns found in float_cols and categorical_cols: {duplicated_cols}"
            )

        self.feature_cols = float_cols + categorical_cols
        self.float_cols = float_cols
        self.categorical_cols = categorical_cols

    def fit(self, X, y=None):
        if not isinstance(X, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame")
        return self

    def transform(self, X):
        if not isinstance(X, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame")

        if not all(col in X.columns for col in self.feature_cols):
            missing_cols = [col for col in self.feature_cols if col not in X.columns]
            raise KeyError(f"Missing columns in the input DataFrame: {missing_cols}")

        X_subset = X[self.feature_cols].copy()
        X_subset[self.float_cols] = X_subset[self.float_cols].astype(float)
        
        return X_subset
