from datetime import date
from pydantic import BaseModel, field_serializer, model_validator


precision = ".5f"

class TeamState(BaseModel):
    o: tuple[float, float]  # (mu, sigma)
    d: tuple[float, float]  # (mu, sigma)

    @field_serializer("o")
    def serialize_o(self, o: tuple[float, float], _info):
        return tuple(f"{v:{precision}}" for v in o)

    @field_serializer("d")
    def serialize_d(self, d: tuple[float, float], _info):
        return tuple(f"{v:{precision}}" for v in d)


class LeagueState(BaseModel):
    i: tuple[float, float]  # (mu, sigma)
    h: tuple[float, float]  # (mu, sigma)
    teams: dict[str, TeamState]

    @field_serializer("i")
    def serialize_i(self, i: tuple[float, float], _info):
        return tuple(f"{v:{precision}}" for v in i)

    @field_serializer("h")
    def serialize_h(self, h: tuple[float, float], _info):
        return tuple(f"{v:{precision}}" for v in h)


class GameOutcome(BaseModel):
    home_score: int | str
    away_score: int | str

    def home_win(self) -> bool:
        if self.home_score == "-" or self.away_score == "-":
            raise ValueError("Game has not concluded yet! Can't determine a winner!")
        return self.home_score > self.away_score

class ScoreProbabilities(BaseModel):
    home: list[float]
    away: list[float]

    @model_validator(mode='after')
    def total_goal_probability(self) -> 'ScoreProbabilities':
        if abs(sum(self.home) - 1.0) > 1e-4:
            raise ValueError('Home goal probabilities do not sum to one!')
        if abs(sum(self.away) - 1.0) > 1e-4:
            raise ValueError('Away goal probabilities do not sum to one!')
        return self

    @field_serializer("home", "away")
    def serialize_score_probabilities(self, score_probabilities: list[float], _info):
        return [f"{s:{precision}}" for s in score_probabilities]


class TeamWinPercentage(BaseModel):
    regulation: float
    overtime: float
    shootout: float

    def total_win_probability(self):
        return self.regulation + self.overtime + self.shootout

    @field_serializer("regulation", "overtime", "shootout")
    def serialize_score_probabilities(self, value: float, _info):
        return f"{value:{precision}}"


class WinPercentages(BaseModel):
    home: TeamWinPercentage
    away: TeamWinPercentage

    @model_validator(mode='after')
    def check_probability_sums_to_one(self) -> 'WinPercentages':
        probability_sum = (
            self.home.total_win_probability() 
            + self.away.total_win_probability()
        )
        if abs(probability_sum - 1.0) > 1e-4:
            raise ValueError('Probabilities do not sum to one!')
        return self


class GamePrediction(BaseModel):
    game_pk: int
    home_team: str
    away_team: str
    outcome: GameOutcome
    score_probabilities: ScoreProbabilities
    win_percentages: WinPercentages


class PredictionPerformance(BaseModel):
    prediction_date: date
    total_games: int
    cumulative_accuracy: float
    cumulative_log_loss: float
    rolling_accuracy: float
    rolling_log_loss: float

    @field_serializer("cumulative_accuracy", "cumulative_log_loss", "rolling_accuracy", "rolling_log_loss")
    def serialize_score_probabilities(self, value: float, _info):
        return f"{value:{precision}}"

    @field_serializer("prediction_date")
    def serialize_prediction_date(self, value: float, _info):
        return value.strftime("%Y-%m-%d")


class PredictionRecord(BaseModel):
    league: str
    prediction_date: date
    deployment_version: str
    league_state: LeagueState
    predictions: list[GamePrediction]
    prediction_performance: list[PredictionPerformance]

    @field_serializer("prediction_date")
    def serialize_prediction_date(self, value: float, _info):
        return value.strftime("%Y-%m-%d")


class ModelVariables(BaseModel):
    i: tuple[float, float]
    h: tuple[float, float]
    o: tuple[list[float], list[float]]
    d: tuple[list[float], list[float]]

    @field_serializer("i")
    def serialize_i(self, i: tuple[float, float], _info):
        return tuple(f"{v:{precision}}" for v in i)

    @field_serializer("h")
    def serialize_h(self, h: tuple[float, float], _info):
        return tuple(f"{v:{precision}}" for v in h)

    @field_serializer("o")
    def serialize_o(self, o: tuple[float, float], _info):
        return tuple([f"{v:{precision}}" for v in o_i] for o_i in o)

    @field_serializer("d")
    def serialize_d(self, d: tuple[float, float], _info):
        return tuple([f"{v:{precision}}" for v in d_i] for d_i in d)


class ModelState(BaseModel):
    teams: list[str]
    variables: ModelVariables

    def to_league_state(self) -> LeagueState:
        teams = {}
        for i, t in enumerate(self.teams):
            teams[t] = TeamState(
                o=(
                    self.variables.o[0][i],
                    self.variables.o[1][i],
                ),
                d=(
                    self.variables.d[0][i],
                    self.variables.d[1][i],
                ),
            )
        return LeagueState(
            i=self.variables.i,
            h=self.variables.h,
            teams=teams,
        )
    
    def from_league_state(self, league_state: LeagueState):
        self.teams = list(league_state.teams.keys())
        i = league_state.i
        h = league_state.h
        o_μ = []
        o_σ = []
        d_μ = []
        d_σ = []
        for t in self.teams:
            o_μ.append(league_state.teams[t].o[0])
            o_σ.append(league_state.teams[t].o[1])
            d_μ.append(league_state.teams[t].d[0])
            d_σ.append(league_state.teams[t].d[1])
        self.variables = ModelVariables(
            i=i,
            h=h,
            o=(o_μ, o_σ),
            d=(d_μ, d_σ),
        )


class ModelStateRecord(BaseModel):
    league: str
    prediction_date: date
    state: ModelState

    @field_serializer("prediction_date")
    def serialize_prediction_date(self, value: float, _info):
        return value.strftime("%Y-%m-%d")