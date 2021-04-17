import numpy as np
import pandas as pd
import pytest

# from bayesbet.nhl.model import get_model_posteriors
# from bayesbet.nhl.model import fatten_priors
from bayesbet.nhl.model import model_iteration

@pytest.fixture
def mock_trace():
    trace = {
        'h': np.array([]),
        'i': np.array([]),
        'o': np.array([]),
        'd': np.array([])
    }
    return trace

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

def test_model_iteration(mock_data, mock_priors):
    n_teams = 3
    Δσ = 0.001
    # Test with a small number of samples, just to verify model works
    posteriors = model_iteration(mock_data, mock_priors, n_teams, Δσ, 100, 25)
    assert isinstance(posteriors, dict), "Did not get a posteriors dict back from model_iteration()!"
    assert 'i' in posteriors.keys(), "Did not find 'i' in returned posteriors dict!"
    assert 'h' in posteriors.keys(), "Did not find 'h' in returned posteriors dict!"
    assert 'o' in posteriors.keys(), "Did not find 'o' in returned posteriors dict!"
    assert 'd' in posteriors.keys(), "Did not find 'd' in returned posteriors dict!"