from pydantic import BaseModel, field_serializer


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


class GamePrediction(BaseModel):
    game_pk: int
    home_team: str
    away_team: str
    score: dict[str, int | str]
    score_probabilities: dict[str, list[float]]
    win_percentages: dict[str, dict[str, float]]

    @field_serializer("score_probabilities")
    def serialize_score_probabilities(self, score_probabilities: dict[str, list[float]], _info):
        serialized = {
            k: [f"{v_i:{precision}}" for v_i in v]
            for k, v in score_probabilities.items()
        }
        return serialized

    @field_serializer("win_percentages")
    def serialize_win_percentages(self, win_percentages: list[float], _info):
        serialized = {
            k1: {k2: f"{v2:{precision}}" for k2, v2 in v1.items()}
            for k1, v1 in win_percentages.items()
        }
        return serialized