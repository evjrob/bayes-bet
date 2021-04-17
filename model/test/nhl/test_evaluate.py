import pandas as pd
import pytest

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
    blank = {
        'PredictionDate': '1990-05-20',
        'GamePredictions': [{
            'game_pk': game_pks[i],
            'score':{
                'home': '-',
                'away': '-'
            }
        } for i in range(3)]
    }
    expected = {
        'PredictionDate': '1990-05-20',
        'GamePredictions': [{
            'game_pk': game_pks[i],
            'score':{
                'home': home_scores[i],
                'away': away_scores[i]
            }
        } for i in range(3)]
    }
    return blank, expected

class TestUpdateScores:
    def test_update_scores(self, mock_scores, mock_games):
        blank_scores, expected_scores = mock_scores
        updated_scores = update_scores(blank_scores, mock_games)
        assert updated_scores == expected_scores, "Updated scores do not match expected!"

    def test_update_scores_postponed(self, mock_scores, mock_games_postponed):
        blank_scores, expected_scores = mock_scores
        expected_scores['GamePredictions'][2]['score'] = {'home':'-', 'away':'-'}
        updated_scores = update_scores(blank_scores, mock_games_postponed)
        assert updated_scores == expected_scores, "Updated postponed scores do not match expected!"

    def test_update_scores_missing(self, mock_scores, mock_games_missing):
        blank_scores, expected_scores = mock_scores
        expected_scores['GamePredictions'][2]['score'] = {'home':'-', 'away':'-'}
        updated_scores = update_scores(blank_scores, mock_games_missing)
        assert updated_scores == expected_scores, "Updated missing scores do not match expected!"
