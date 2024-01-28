import pytest

from bayesbet.nhl.data_model import GamePrediction, LeagueState, TeamState


@pytest.fixture
def league_state():
    return LeagueState(
        i=(1.0,0.1),
        h=(0.25,0.075),
        teams={
            "A": TeamState(o=(-0.5, 0.15), d=(0.5, 0.15)),
            "B": TeamState(o=(0.0, 0.1), d=(0.0, 0.1)),
            "C": TeamState(o=(0.5, 0.15), d=(-0.5, 0.15))
        },
    )

@pytest.fixture
def serialized_league_state():
    return {
        "i": ("1.00000", "0.10000"),
        "h": ("0.25000", "0.07500"),
        "teams": {
            "A": {"o": ("-0.50000", "0.15000"), "d": ("0.50000", "0.15000")},
            "B": {"o": ("0.00000", "0.10000"), "d": ("0.00000", "0.10000")},
            "C": {"o": ("0.50000", "0.15000"), "d": ("-0.50000", "0.15000")},
        }
    }

@pytest.fixture
def game_prediction():
    return GamePrediction(
        game_pk=1,
        home_team="A",
        away_team="B",
        outcome={
            "home": 3,
            "away": 2,
        },
        score_probabilities={
            "home": [0.1] * 10,
            "away": [0.1] * 10,
        },
        win_percentages={
            "home": {
                "regulation": 0.4,
                "overtime": 0.05,
                "shootout": 0.05,
            },
            "away": {
                "regulation": 0.4,
                "overtime": 0.05,
                "shootout": 0.05,
            },
        },
    )

@pytest.fixture
def serialized_game_prediction():
    return {
        "game_pk": 1,
        "home_team": "A",
        "away_team": "B",
        "outcome": {
            "home": 3,
            "away": 2,
        },
        "score_probabilities": {
            "home": ["0.10000"] * 10,
            "away": ["0.10000"] * 10,
        },
        "win_percentages": {
            "home": {
                "regulation": "0.40000",
                "overtime": "0.05000",
                "shootout": "0.05000", 
            },
            "away": {
                "regulation": "0.40000", 
                "overtime": "0.05000", 
                "shootout": "0.05000",
            },
        },
    }


class TestLeagueState:
    def test_serialization_json(self, league_state):
        serialized = league_state.model_dump_json()
        deserialized_league_state = LeagueState.model_validate_json(serialized)
        assert league_state == deserialized_league_state

    def test_serialization_dict(self, league_state, serialized_league_state):
        league_state_dict = league_state.model_dump()
        assert league_state_dict == serialized_league_state

    def test_from_dictionary(self, league_state, serialized_league_state):
        parsed_league_state = LeagueState.model_validate(serialized_league_state)
        assert parsed_league_state == league_state


class TestGamePrediction:
    def test_serialization_json(self, game_prediction):
        serialized = game_prediction.model_dump_json()
        deserialized_game_prediction = GamePrediction.model_validate_json(serialized)
        assert game_prediction == deserialized_game_prediction

    def test_serialization_dict(self, game_prediction, serialized_game_prediction):
        game_prediction_dict = game_prediction.model_dump()
        assert game_prediction_dict == serialized_game_prediction

    def test_from_dictionary(self, game_prediction, serialized_game_prediction):
        parsed_game_prediction = GamePrediction.model_validate(serialized_game_prediction)
        assert parsed_game_prediction == game_prediction

    def test_serialization_dict_no_score(self, game_prediction, serialized_game_prediction):
        game_prediction.outcome.home = "-"
        game_prediction.outcome.away = "-"
        game_prediction_dict = game_prediction.model_dump()
        serialized_game_prediction["outcome"]["home"] = "-"
        serialized_game_prediction["outcome"]["away"] = "-"
        assert game_prediction_dict == serialized_game_prediction

    def test_from_dictionary_no_score(self, game_prediction, serialized_game_prediction):
        serialized_game_prediction["outcome"]["home"] = "-"
        serialized_game_prediction["outcome"]["away"] = "-"
        parsed_game_prediction = GamePrediction.model_validate(serialized_game_prediction)
        game_prediction.outcome.home = "-"
        game_prediction.outcome.away = "-"
        assert parsed_game_prediction == game_prediction