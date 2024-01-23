import numpy as np
import pandas as pd
import pytest

from bayesbet.nhl.data_utils import GamePrediction, LeagueState, TeamState
from bayesbet.nhl.model import (
    ModelVariables,
    ModelState,
    IterativeUpdateModel
)

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
def mock_model_state():
    return ModelState(
        teams=["A", "B"],
        variables=ModelVariables(
            h=(0.75, 0.25),
            i=(1.0, 0.5),
            o=([0.0, 0.25], [0.25, 0.25]),
            d=([0.0, 0.5], [0.5, 0.5]),
        ),
    )

@pytest.fixture
def mock_game_data():
    data = pd.DataFrame({
        "game_pk": [1, 2, 3],
        "game_type": ['R', 'R', 'R'],
        "game_state": ["Final", "Final", "Final"],
        "home_team": ["A", "C", "C"],
        "home_reg_score": [1, 2, 3],
        "home_fin_score": [1, 2, 3],
        "away_team": ["B", "B", "A"],
        "away_reg_score": [3, 2, 1],
        "away_fin_score": [3, 3, 1],
    })
    return data

@pytest.fixture
def mock_model_state_2():
    return ModelState(
        teams=["A", "B", "C"],
        variables=ModelVariables(
            i=(1.0, 0.5),
            h=(0.3, 0.5),
            o=([0.1, 0.2, 0.3], [0.2, 0.2, 0.2]),
            d=([0.15, 0.25, 0.3], [0.2, 0.2, 0.2]),
        )
    )

class TestModelState:
    def test_serialization(self, mock_model_state):
        serialized = mock_model_state.model_dump_json()
        deserialized_model_state = ModelState.model_validate_json(serialized)
        assert mock_model_state == deserialized_model_state

    def test_to_league_state(self, mock_model_state):
        league_state = mock_model_state.to_league_state()
        expected_league_state = LeagueState(
            i=(1.0, 0.5),
            h=(0.75, 0.25),
            teams={
                "A": TeamState(o=(0.0, 0.25), d=(0.0, 0.5)),
                "B": TeamState(o=(0.25, 0.25), d=(0.5, 0.5)),
            },
        )
        assert league_state == expected_league_state

    def test_from_league_state(self, mock_model_state):
        league_state = LeagueState(
            i=(1.0, 0.5),
            h=(0.75, 0.25),
            teams={
                "A": TeamState(o=(0.0, 0.25), d=(0.0, 0.5)),
                "B": TeamState(o=(0.25, 0.25), d=(0.5, 0.5)),
            },
        )
        model_state = ModelState(
            teams=["A"],
            variables=ModelVariables(
                i=(0,0),
                h=(0,0),
                o=([0], [0]),
                d=([0], [0]),
            ),
        )
        model_state.from_league_state(league_state)
        print(model_state)
        assert model_state == mock_model_state



class TestIterativeUpdateModel:
    def test_get_model_posteriors(self, mock_trace, mock_model_state):
        expected_posteriors = mock_model_state
        model = IterativeUpdateModel(
            expected_posteriors,
            delta_sigma=0.001,
            f_thresh=0.075,
            fattening_factor=1.05,
        )
        posteriors = model.get_model_posteriors(mock_trace)
        assert posteriors == expected_posteriors

    def test_fatten_priors(self, mock_model_state):
        model = IterativeUpdateModel(
            mock_model_state,
            delta_sigma=0.001,
            f_thresh=0.75,
            fattening_factor=2.0,
        )
        expected_priors = ModelState(
            teams=["A", "B"],
            variables=ModelVariables(
                h=(0.75, 0.5),
                i=(1.0, 0.75),
                o=([0.0, 0.25], [0.5, 0.5]),
                d=([0.0, 0.5], [0.75, 0.75]),
            ),
        )
        model.fatten_priors()
        assert model.priors == expected_priors

    @pytest.mark.slow
    def test_fit(self, mock_game_data, mock_model_state_2):
        # Test with a small number of samples, just to verify model works
        model = IterativeUpdateModel(
            mock_model_state_2,
            delta_sigma=0.001,
            f_thresh=0.075,
            fattening_factor=1.05,
        )
        model.fit(mock_game_data)
        assert isinstance(model.priors, ModelState)

    @pytest.mark.slow
    def test_predict(self, mock_game_data, mock_model_state_2):
        # Test with a small number of samples, just to verify model works
        model = IterativeUpdateModel(
            mock_model_state_2,
            delta_sigma=0.001,
            f_thresh=0.075,
            fattening_factor=1.05,
        )
        predictions = model.predict(mock_game_data)
        for prediction in predictions:
            assert isinstance(prediction, GamePrediction)
