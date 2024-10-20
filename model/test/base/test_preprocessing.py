import pytest
import pandas as pd
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from bayesbet.base.preprocessing import FeatureSelector


@pytest.fixture
def input_dataset():
    return pd.DataFrame(
        {
            "float1": [0.1, 1.1, 2.1, 3.1],
            "float2": [0.2, 1.2, 2.2, 3.2],
            "cat1": ["A", "B", "A", "B"],
            "cat2": ["X", "Y", "X", "Y"],
            "extra": [1, 2, 3, 4],
        }
    )


@pytest.fixture
def float_cols():
    return ["float1", "float2"]


@pytest.fixture
def categorical_cols():
    return ["cat1", "cat2"]


class TestFeatureSelector:
    def test_init(self, float_cols, categorical_cols):
        FeatureSelector(float_cols, categorical_cols)

    def test_init_with_duplicates(self):
        with pytest.raises(ValueError):
            FeatureSelector(["col1", "col2"], ["col2", "col3"])

    def test_fit(self, input_dataset, float_cols, categorical_cols):
        transformer = FeatureSelector(float_cols, categorical_cols)
        assert transformer.fit(input_dataset) is transformer

    def test_transform(self, input_dataset, float_cols, categorical_cols):
        transformer = FeatureSelector(float_cols, categorical_cols)
        transformer.fit(input_dataset)
        X_transformed = transformer.transform(input_dataset)
        assert isinstance(X_transformed, pd.DataFrame)
        assert list(X_transformed.columns) == float_cols + categorical_cols
        assert X_transformed.shape[0] == input_dataset.shape[0]
        assert X_transformed.shape[1] == len(float_cols) + len(categorical_cols)

    def test_fit_transform(self, input_dataset, float_cols, categorical_cols):
        transformer = FeatureSelector(float_cols, categorical_cols)
        X_transformed = transformer.fit_transform(input_dataset)
        assert isinstance(X_transformed, pd.DataFrame)
        assert list(X_transformed.columns) == float_cols + categorical_cols
        assert X_transformed.shape[0] == input_dataset.shape[0]
        assert X_transformed.shape[1] == len(float_cols) + len(categorical_cols)

    def test_non_dataframe_input(self, float_cols, categorical_cols):
        transformer = FeatureSelector(float_cols, categorical_cols)
        X = np.array([[0, 0], [1, 1]])
        with pytest.raises(TypeError):
            transformer.fit(X)
        with pytest.raises(TypeError):
            transformer.transform(X)

    def test_missing_columns(self, input_dataset, float_cols, categorical_cols):
        transformer = FeatureSelector(float_cols + ["missing_col"], categorical_cols)
        with pytest.raises(KeyError):
            transformer.fit_transform(input_dataset)

    def test_float_conversion(self, input_dataset, float_cols, categorical_cols):
        transformer = FeatureSelector(float_cols, categorical_cols)
        X_transformed = transformer.fit_transform(input_dataset)
        assert X_transformed[float_cols].dtypes.apply(lambda x: x == np.float64).all()
