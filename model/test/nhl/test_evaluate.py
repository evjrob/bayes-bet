import pandas as pd
import pytest

from bayesbet.nhl.data_model import PredictionRecord, GamePrediction, LeagueState, PredictionPerformance, TeamState
from bayesbet.nhl.evaluate import update_scores

game_pks = [1,2,3]
game_states = ['Final', 'Final', 'Final']
home_scores = ['4','5','6']
away_scores = ['7','8','9']

@pytest.fixture
def mock_games():
    games = pd.DataFrame({
        'game_pk':game_pks,
        'game_state':['Final', 'Final', 'Final'],
        'home_fin_score':home_scores, 
        'away_fin_score':away_scores})
    return games

@pytest.fixture
def mock_games_missing():
    games = pd.DataFrame({
        'game_pk':game_pks[:2],
        'game_state':['Final', 'Final'],
        'home_fin_score':home_scores[:2], 
        'away_fin_score':away_scores[:2]})
    return games

@pytest.fixture
def mock_games_postponed():
    games = pd.DataFrame({
        'game_pk':game_pks,
        'game_state':['Final', 'Final', 'Postponed'],
        'home_fin_score':home_scores, 
        'away_fin_score':away_scores})
    return games


@pytest.fixture
def mock_scores():
    league_state = LeagueState(
        i=[0.1, 0.1],
        h=[0.1, 0.1],
        teams={
            'A': TeamState(o=[0.1, 0.1], d=[0.1, 0.1]),
            'B': TeamState(o=[0.1, 0.1], d=[0.1, 0.1])
        }
    )

    prediction_performance =[PredictionPerformance(
        prediction_date='1990-05-20',
        total_games=10,
        cumulative_accuracy=0.5,
        cumulative_log_loss=0.5,
        rolling_accuracy=0.5,
        rolling_log_loss=0.5,
    )]

    
    blank = PredictionRecord(
        league='nhl',
        prediction_date='1990-05-20',
        deployment_version="test",
        league_state=league_state,
        predictions=[
            GamePrediction(
                game_pk=game_pks[i],
                home_team='A',
                away_team='B',
                outcome={
                    'home_score': '-',
                    'away_score': '-'
                },
                score_probabilities={
                    'home': [0.1]*10,
                    'away': [0.1]*10
                },
                win_percentages={
                    'home': {
                        'regulation': 0.4,
                        'overtime': 0.05,
                        'shootout': 0.05
                    },
                    'away': {
                        'regulation': 0.4,
                        'overtime': 0.05,
                        'shootout': 0.05
                    }
                }
            ) for i in range(3)
        ],
        prediction_performance=prediction_performance,
    )

    expected = PredictionRecord(
        league='nhl',
        prediction_date='1990-05-20',
        deployment_version="test",
        league_state=league_state,
        predictions=[
            GamePrediction(
                game_pk=game_pks[i],
                home_team='A',
                away_team='B',
                outcome={
                    'home_score': home_scores[i],
                    'away_score': away_scores[i]
                },
                score_probabilities={
                    'home': [0.1]*10,
                    'away': [0.1]*10
                },
                win_percentages={
                    'home': {
                        'regulation': 0.4,
                        'overtime': 0.05,
                        'shootout': 0.05
                    },
                    'away': {
                        'regulation': 0.4,
                        'overtime': 0.05,
                        'shootout': 0.05
                    }
                }
            ) for i in range(3)
        ],
        prediction_performance=prediction_performance,
    )
    
    return blank, expected

class TestUpdateScores:
    def test_update_scores(self, mock_scores, mock_games):
        blank_scores, expected_scores = mock_scores
        updated_scores = update_scores(blank_scores, mock_games)
        assert updated_scores == expected_scores, "Updated scores do not match expected!"

    def test_update_scores_postponed(self, mock_scores, mock_games_postponed):
        blank_scores, expected_scores = mock_scores
        expected_scores.predictions[2].outcome.home_score = '-'
        expected_scores.predictions[2].outcome.away_score = '-'
        updated_scores = update_scores(blank_scores, mock_games_postponed)
        assert updated_scores == expected_scores, "Updated postponed scores do not match expected!"

    def test_update_scores_missing(self, mock_scores, mock_games_missing):
        blank_scores, expected_scores = mock_scores
        expected_scores.predictions[2].outcome.home_score = '-'
        expected_scores.predictions[2].outcome.away_score = '-'
        updated_scores = update_scores(blank_scores, mock_games_missing)
        assert updated_scores == expected_scores, "Updated missing scores do not match expected!"
