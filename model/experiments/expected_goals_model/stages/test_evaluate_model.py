import pytest
import pandas as pd
import numpy as np
from evaluate_model import (
    CoordinateAdjustmentTransformer,
    FeatureSelector,
    ShotFeatureTransformer,
)

@pytest.fixture
def sample_data():
    return pd.DataFrame({
        'float_col1': [1.0, 2.0, 3.0],
        'float_col2': [4.0, 5.0, 6.0],
        'cat_col1': ['a', 'b', 'c'],
        'cat_col2': ['d', 'e', 'f'],
        'extra_col': [7, 8, 9]
    })

@pytest.fixture
def empty_data():
    return pd.DataFrame(columns=['float_col1', 'cat_col1'])

@pytest.fixture
def missing_columns_data():
    return pd.DataFrame({
        'float_col1': [1.0, 2.0, 3.0],
        'cat_col1': ['a', 'b', 'c']
    })

@pytest.fixture
def mixed_type_data():
    return pd.DataFrame({
        'float_col1': [1.0, '2.0', 3.0],
        'cat_col1': ['a', 'b', 'c']
    })

@pytest.fixture
def non_standard_index_data():
    return pd.DataFrame({
        'float_col1': [1.0, 2.0, 3.0],
        'cat_col1': ['a', 'b', 'c']
    }, index=['x', 'y', 'z'])

@pytest.fixture
def nan_values_data():
    return pd.DataFrame({
        'float_col1': [1.0, None, 3.0],
        'cat_col1': ['a', None, 'c']
    })

@pytest.fixture
def sample_shot_data():
    return pd.DataFrame({
        'shot_x': [0, 10, -10],
        'shot_y': [0, 5, -5],
        'goal_x': [89, 89, 89],
        'goal_y': [0, 0, 0],
        'last_event_x': [5, 15, -15],
        'last_event_y': [2, 7, -7],
        'last_event': ['pass', 'shot-on-goal', 'shot-on-goal'],
        'time_since_last_event': [5, 1, 3]
    })

@pytest.fixture
def empty_shot_data():
    return pd.DataFrame(columns=['shot_x', 'shot_y', 'goal_x', 'goal_y', 'last_event_x', 'last_event_y', 'last_event', 'time_since_last_event'])

def test_basic_functionality(sample_data):
    selector = FeatureSelector(float_cols=['float_col1', 'float_col2'], categorical_cols=['cat_col1', 'cat_col2'])
    transformed = selector.fit_transform(sample_data)
    assert list(transformed.columns) == ['float_col1', 'float_col2', 'cat_col1', 'cat_col2']
    assert transformed['float_col1'].dtype == float

def test_empty_dataframe(empty_data):
    selector = FeatureSelector(float_cols=['float_col1'], categorical_cols=['cat_col1'])
    transformed = selector.fit_transform(empty_data)
    assert transformed.empty

def test_missing_columns(missing_columns_data):
    selector = FeatureSelector(float_cols=['float_col1', 'float_col2'], categorical_cols=['cat_col1', 'cat_col2'])
    with pytest.raises(KeyError):
        selector.fit_transform(missing_columns_data)

def test_no_float_or_categorical_columns(sample_data):
    selector = FeatureSelector(float_cols=[], categorical_cols=[])
    transformed = selector.fit_transform(sample_data)
    assert transformed.empty

def test_mixed_type_data(mixed_type_data):
    selector = FeatureSelector(float_cols=['float_col1'], categorical_cols=['cat_col1'])
    transformed = selector.fit_transform(mixed_type_data)
    assert transformed['float_col1'].dtype == float

def test_non_dataframe_input():
    selector = FeatureSelector(float_cols=['float_col1'], categorical_cols=['cat_col1'])
    with pytest.raises(TypeError):
        selector.fit_transform([1, 2, 3])

def test_non_standard_index(non_standard_index_data):
    selector = FeatureSelector(float_cols=['float_col1'], categorical_cols=['cat_col1'])
    transformed = selector.fit_transform(non_standard_index_data)
    assert list(transformed.index) == ['x', 'y', 'z']

def test_nan_values(nan_values_data):
    selector = FeatureSelector(float_cols=['float_col1'], categorical_cols=['cat_col1'])
    transformed = selector.fit_transform(nan_values_data)
    assert transformed.isna().sum().sum() > 0

def test_duplicated_columns():
    with pytest.raises(ValueError, match="Duplicated columns found in float_cols and categorical_cols"):
        FeatureSelector(float_cols=['float_col1'], categorical_cols=['float_col1'])

def test_shot_feature_transformer_basic_functionality(sample_shot_data):
    transformer = ShotFeatureTransformer()
    transformed = transformer.fit_transform(sample_shot_data)
    
    expected_columns = [
        'shot_x', 'shot_y', 'goal_x', 'goal_y', 'last_event_x', 'last_event_y',
        'last_event', 'time_since_last_event', 'shot_distance', 'shot_angle',
        'last_event_distance', 'last_event_angle', 'is_rebound', 'rebound_angle'
    ]
    
    assert list(transformed.columns) == expected_columns
    assert len(transformed) == len(sample_shot_data)

def test_shot_feature_transformer_empty_dataframe(empty_shot_data):
    transformer = ShotFeatureTransformer()
    transformed = transformer.fit_transform(empty_shot_data)

    expected_columns = [
        'shot_x', 'shot_y', 'goal_x', 'goal_y', 'last_event_x', 'last_event_y',
        'last_event', 'time_since_last_event', 'shot_distance', 'shot_angle',
        'last_event_distance', 'last_event_angle', 'is_rebound', 'rebound_angle'
    ]
    
    assert transformed.empty
    assert list(transformed.columns) == expected_columns

def test_shot_feature_transformer_rebound_detection(sample_shot_data):
    transformer = ShotFeatureTransformer()
    transformed = transformer.fit_transform(sample_shot_data)
    
    expected_is_rebound = [False, True, False]
    np.testing.assert_array_equal(transformed['is_rebound'], expected_is_rebound)

@pytest.fixture
def sample_data_cdf():
    return pd.DataFrame({
        'shot_x': np.random.rand(2000) * 100,
        'shot_y': np.random.rand(2000) * 85 - 42.5,
        'last_event_x': np.random.rand(2000) * 100,
        'last_event_y': np.random.rand(2000) * 85 - 42.5,
        'venue_location': ['Venue A'] * 1200 + ['Venue B'] * 800,
        'shot_is_home_team': np.random.choice([True, False], 2000)
    })

def test_initialization():
    transformer = CoordinateAdjustmentTransformer()
    assert isinstance(transformer, CoordinateAdjustmentTransformer)

def test_fit(sample_data_cdf):
    transformer = CoordinateAdjustmentTransformer()
    transformer.fit(sample_data_cdf)
    assert hasattr(transformer, 'venues')
    assert 'Venue A' in transformer.venues
    assert 'Venue B' not in transformer.venues
    assert hasattr(transformer, 'x_cdf')
    assert hasattr(transformer, 'y_cdf')

def test_transform(sample_data_cdf):
    transformer = CoordinateAdjustmentTransformer()
    transformer.fit(sample_data_cdf)
    result = transformer.transform(sample_data_cdf)
    
    assert len(result) == len(sample_data_cdf)
    assert 'shot_x_original' in result.columns
    assert 'shot_y_original' in result.columns
    assert result['shot_x'].dtype == float
    assert result['shot_y'].dtype == float
    
    # Check that Venue B (which has < 1000 shots) is not adjusted
    venue_b_mask = sample_data_cdf['venue_location'] == 'Venue B'
    assert np.allclose(result.loc[venue_b_mask, 'shot_x'], 
                       sample_data_cdf.loc[venue_b_mask, 'shot_x'])


def test_cdf_adjust():
    values = np.array([1, 2, 3, 4, 5])
    venue_cdf = np.array([1, 2, 3, 4, 5])
    venue_away_cdf = np.array([1, 2, 3, 4, 5])
    league_away_cdf = np.array([1, 2, 3, 4, 5])
    league_values = np.array([1, 2, 3, 4, 5])
    
    result = CoordinateAdjustmentTransformer._cdf_adjust(
        values, venue_cdf, venue_away_cdf, league_away_cdf, league_values
    )
    np.testing.assert_array_equal(result, values)
