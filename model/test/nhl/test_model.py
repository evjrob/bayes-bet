import numpy as np
import pandas as pd
import pytest

from common_test_functions import compare_mv_num_dict
from bayesbet.nhl.model import get_model_posteriors
from bayesbet.nhl.model import fatten_priors
from bayesbet.nhl.model import model_iteration

@pytest.fixture
def mock_trace():
    trace = {
        'h': np.array([0.375, 0.625, 0.75, 0.875, 1.125]),
        'i': np.array([0.25, 0.75, 1.0, 1.25, 1.75]),
        'o': np.array([[-0.375, -0.125],
            [-0.125,  0.125],
            [0.0, 0.25],
            [0.125, 0.375],
            [0.375, 0.625]]),
        'd': np.array([
            [-0.75, -0.25],
            [-0.25,  0.25],
            [ 0.  ,  0.5 ],
            [ 0.25,  0.75],
            [ 0.75,  1.25]])
    }
    return trace

@pytest.fixture
def mock_posteriors():
    posteriors = {
        'h': [0.75, 0.25],
        'i': [1.0, 0.5],
        'o': [np.array([0.0, 0.25]), np.array([0.25, 0.25])],
        'd': [np.array([0.0, 0.5]), np.array([0.5, 0.5])],
    }
    return posteriors

def test_get_model_posteriors(mock_trace, mock_posteriors):
    expected_posteriors = mock_posteriors
    n_teams = 2
    posteriors = get_model_posteriors(mock_trace, n_teams)
    compare_mv_num_dict(posteriors, expected_posteriors)

def test_fatten_priors(mock_posteriors):
    priors = mock_posteriors
    factor = 2.0
    f_thresh = 0.75
    expected_priors = {
        'h': [0.75, 0.5],
        'i': [1.0, 0.75],
        'o': [np.array([0.0, 0.25]), np.array([0.5, 0.5])],
        'd': [np.array([0.0, 0.5]), np.array([0.75, 0.75])],
    }
    priors = fatten_priors(priors, factor, f_thresh)
    compare_mv_num_dict(priors, expected_priors)

@pytest.fixture
def mock_data():
    data = pd.DataFrame({
        'idₕ': [0,2,2],
        'sₕ': [1,2,3],
        'idₐ': [1,1,0],
        'sₐ': [3,2,1],
        'hw': [0,0,1]
    })
    return data

@pytest.fixture
def mock_priors():
    priors = {
        'i':[1.0, 0.5],
        'h':[0.3, 0.5],
        'o':[np.array([0.1, 0.2, 0.3]), np.array([0.2, 0.2, 0.2])],
        'd':[np.array([0.15, 0.25, 0.3]), np.array([0.2, 0.2, 0.2])],
    }
    return priors

# This test takes close to a minute to run. Only execute it if the --runslow 
# argument has been passed.
@pytest.mark.slow
def test_model_iteration(mock_data, mock_priors):
    n_teams = 3
    Δσ = 0.001
    # Test with a small number of samples, just to verify model works
    posteriors = model_iteration(mock_data, mock_priors, n_teams, Δσ, 100, 25, 1)
    assert isinstance(posteriors, dict), "Did not get a posteriors dict back from model_iteration()!"
    assert 'i' in posteriors.keys(), "Did not find 'i' in returned posteriors dict!"
    assert 'h' in posteriors.keys(), "Did not find 'h' in returned posteriors dict!"
    assert 'o' in posteriors.keys(), "Did not find 'o' in returned posteriors dict!"
    assert 'd' in posteriors.keys(), "Did not find 'd' in returned posteriors dict!"