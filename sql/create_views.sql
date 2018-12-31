CREATE OR REPLACE VIEW scores AS
    SELECT regulation.game_pk, 
            home_team_regulation_score, 
            home_team_final_score,
            away_team_regulation_score,
            away_team_final_score
    FROM
        (SELECT game_pk, 
                SUM(home_goals) AS home_team_regulation_score,
                SUM(away_goals) AS away_team_regulation_score
        FROM periods
        WHERE period_type = 'REGULAR'
        GROUP BY game_pk) AS regulation
    LEFT JOIN
        ((SELECT overtime.game_pk,
                home_goals + home_so_win::INT AS home_team_final_score,
                away_goals + (NOT home_so_win)::INT AS away_team_final_score
         FROM
            (SELECT game_pk, 
                    SUM(home_goals) AS home_goals,
                    SUM(away_goals) AS away_goals
            FROM periods
            GROUP BY game_pk) AS overtime 
        LEFT JOIN
            (SELECT game_pk,
                    (home_scores > away_scores) AS home_so_win
             FROM shootouts) as shootouts
        ON overtime.game_pk = shootouts.game_pk
        WHERE shootouts.game_pk IS NOT NULL)
        UNION
        (SELECT overtime.game_pk,
                home_goals AS home_team_final_score,
                away_goals AS away_team_final_score
         FROM
            (SELECT game_pk, 
                    SUM(home_goals) AS home_goals,
                    SUM(away_goals) AS away_goals
            FROM periods
            GROUP BY game_pk) AS overtime 
        LEFT JOIN
            (SELECT game_pk,
                    (home_scores > away_scores) AS home_so_win
             FROM shootouts) as shootouts
        ON overtime.game_pk = shootouts.game_pk
        WHERE shootouts.game_pk IS NULL)) AS final
    ON regulation.game_pk = final.game_pk;

CREATE OR REPLACE VIEW model_input_data AS
    SELECT  games.game_pk,
            game_date,
            season,
            game_type,
            home_team_id,
            home_team_regulation_score,
            home_team_final_score,
            away_team_id,
            away_team_regulation_score,
            away_team_final_score
    FROM games LEFT JOIN  scores
    ON games.game_pk = scores.game_pk 
    WHERE ((game_type = 'R' OR game_type = 'P') AND 
           (game_state = 'Final'));

CREATE OR REPLACE VIEW model_prediction_data AS
    SELECT  game_pk,
            game_date,
            season,
            game_type,
            home_team_id,
            away_team_id
    FROM games
    WHERE (game_type = 'R' OR game_type = 'P');