from django.db import models


class Conferences(models.Model):
    conference_id = models.IntegerField(primary_key=True)
    conference_name = models.TextField()
    active = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'conferences'
        app_label = 'data'


class Divisions(models.Model):
    division_id = models.IntegerField(primary_key=True)
    division_name = models.TextField()
    division_abbreviation = models.TextField()
    conference = models.ForeignKey(Conferences, models.DO_NOTHING)
    active = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'divisions'
        app_label = 'data'


class GamePredictions(models.Model):
    game_pk = models.OneToOneField('Games', models.DO_NOTHING, db_column='game_pk', primary_key=True)
    prediction_date = models.ForeignKey('ModelRuns', models.DO_NOTHING, db_column='prediction_date')
    prediction_number = models.IntegerField()
    home_team_regulation_goals = models.IntegerField()
    away_team_regulation_goals = models.IntegerField()
    home_wins_after_regulation = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'game_predictions'
        unique_together = (('game_pk', 'prediction_date', 'prediction_number'),)
        app_label = 'data'


class Games(models.Model):
    game_pk = models.IntegerField(primary_key=True)
    game_date = models.DateField(blank=True, null=True)
    season = models.TextField(blank=True, null=True)
    game_type = models.TextField()
    game_state = models.TextField()
    home_team = models.ForeignKey('Teams', models.DO_NOTHING, related_name='home_teams')
    away_team = models.ForeignKey('Teams', models.DO_NOTHING, related_name='away_teams')

    class Meta:
        managed = False
        db_table = 'games'
        app_label = 'data'


class GeneralPosteriors(models.Model):
    prediction_date = models.OneToOneField('ModelRuns', models.DO_NOTHING, db_column='prediction_date', primary_key=True)
    home_ice_advantage_median = models.FloatField()
    home_ice_advantage_hpd_low = models.FloatField()
    home_ice_advantage_hpd_high = models.FloatField()
    intercept_median = models.FloatField()
    intercept_hpd_low = models.FloatField()
    intercept_hpd_high = models.FloatField()

    class Meta:
        managed = False
        db_table = 'general_posteriors'
        app_label = 'data'


class ModelRuns(models.Model):
    prediction_date = models.DateField(primary_key=True)
    bfmi = models.FloatField()
    gelman_rubin = models.FloatField()

    class Meta:
        managed = False
        db_table = 'model_runs'
        app_label = 'data'


class Periods(models.Model):
    game_pk = models.OneToOneField(Games, models.DO_NOTHING, db_column='game_pk', primary_key=True)
    period_number = models.IntegerField()
    period_type = models.TextField()
    home_goals = models.IntegerField()
    home_shots_on_goal = models.IntegerField()
    away_goals = models.IntegerField()
    away_shots_on_goal = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'periods'
        unique_together = (('game_pk', 'period_number'),)
        app_label = 'data'


class Shootouts(models.Model):
    game_pk = models.OneToOneField(Games, models.DO_NOTHING, db_column='game_pk', primary_key=True)
    home_scores = models.IntegerField()
    home_attempts = models.IntegerField()
    away_scores = models.IntegerField()
    away_attempts = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'shootouts'
        app_label = 'data'


class TeamPosteriors(models.Model):
    team = models.OneToOneField('Teams', models.DO_NOTHING, primary_key=True)
    prediction_date = models.ForeignKey(ModelRuns, models.DO_NOTHING, db_column='prediction_date')
    offence_median = models.FloatField()
    offence_hpd_low = models.FloatField()
    offence_hpd_high = models.FloatField()
    defence_median = models.FloatField()
    defence_hpd_low = models.FloatField()
    defence_hpd_high = models.FloatField()

    class Meta:
        managed = False
        db_table = 'team_posteriors'
        unique_together = (('team', 'prediction_date'),)
        app_label = 'data'


class Teams(models.Model):
    team_id = models.IntegerField(primary_key=True)
    team_name = models.TextField()
    team_abbreviation = models.TextField()
    division = models.ForeignKey(Divisions, models.DO_NOTHING, blank=True, null=True)
    active = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'teams'
        app_label = 'data'