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
        'hw': [False,False,True]
    })
    return data

@pytest.fixture
def mock_priors():
    priors = {
        'i':[1.0, 0.25],
        'h':[0.3, 0.3],
        'o':[np.array([0.1, 0.2, 0.3]), np.array([0.05, 0.1, 0.15])],
        'd':[np.array([0.15, 0.25, 0.3]), np.array([0.075, 0.125, 0.15])],
    }
    return priors

def test_model_iteration(mock_data, mock_priors):
    n_teams = 3
    Δσ = 0.001
    posteriors = model_iteration(mock_data, mock_priors, n_teams, Δσ, 500, 100)
    assert isinstance(posteriors, dict), "Did not get a posteriors dict back from model_iteration()!"