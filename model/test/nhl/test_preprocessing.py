import pytest
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import NotFittedError
from bayesbet.nhl.preprocessing import ShotFeatures


@pytest.fixture
def input_dataset():
    return pd.DataFrame({
        'shot_x': [0, 1, 1, 0],
        'shot_y': [0, 1, 0, 1],
        'last_event_x': [-1, 2, 0, 1],
        'last_event_y': [1, -1, 2, 0],
        'goal_x': [89, 89, 89, 89],
        'goal_y': [0, 0, 0, 0],
        'last_event': ['Pass', 'Shot', 'Block', 'Pass'],
        'time_since_last_event': [5.2, 3.1, 8.7, 2.5]
    })


class TestShotFeatures:
    def test_init(self):
        ShotFeatures()

    def test_fit(self, input_dataset):
        transformer = ShotFeatures()
        assert transformer.fit(input_dataset) is transformer
        assert hasattr(transformer, "n_features_in_")

    def test_transform(self, input_dataset):
        transformer = ShotFeatures()
        transformer.fit(input_dataset)
        X_transformed = transformer.transform(input_dataset)
        assert X_transformed.shape[0] == input_dataset.shape[0]

    def test_fit_transform(self, input_dataset):
        transformer = ShotFeatures()
        X_transformed = transformer.fit_transform(input_dataset)
        assert X_transformed.shape[0] == input_dataset.shape[0]

    def test_error_handling(self):
        transformer = ShotFeatures()
        X = pd.DataFrame({'shot_x': [0, 1], 'shot_y': [0, 1]})
        with pytest.raises(ValueError):
            transformer.transform(X)
        

    def test_input_validation(self, input_dataset):
        transformer = ShotFeatures()
        with pytest.raises(ValueError):
            transformer.fit(input_dataset.drop('shot_x', axis=1))

    def test_column_order_invariance(self, input_dataset):
        transformer = ShotFeatures()
        transformer.fit(input_dataset)
        
        # Shuffle columns
        shuffled_input = input_dataset.sample(frac=1, axis=1)
        
        X_transformed_original = transformer.transform(input_dataset)
        X_transformed_shuffled = transformer.transform(shuffled_input)
        
        # Check only the added columns
        added_columns = ['shot_distance', 'shot_angle', 'last_event_distance', 
                         'last_event_angle', 'is_rebound', 'rebound_angle']
        
        pd.testing.assert_frame_equal(
            X_transformed_original[added_columns],
            X_transformed_shuffled[added_columns],
        )
