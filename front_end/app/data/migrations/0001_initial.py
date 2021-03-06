# Generated by Django 2.2.4 on 2019-08-05 21:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Conferences',
            fields=[
                ('conference_id', models.IntegerField(primary_key=True, serialize=False)),
                ('conference_name', models.TextField()),
                ('active', models.BooleanField()),
            ],
            options={
                'db_table': 'conferences',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Divisions',
            fields=[
                ('division_id', models.IntegerField(primary_key=True, serialize=False)),
                ('division_name', models.TextField()),
                ('division_abbreviation', models.TextField()),
                ('active', models.BooleanField()),
            ],
            options={
                'db_table': 'divisions',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Games',
            fields=[
                ('game_pk', models.IntegerField(primary_key=True, serialize=False)),
                ('game_date', models.DateField(blank=True, null=True)),
                ('season', models.TextField(blank=True, null=True)),
                ('game_type', models.TextField()),
                ('game_state', models.TextField()),
            ],
            options={
                'db_table': 'games',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='ModelRuns',
            fields=[
                ('prediction_date', models.DateField(primary_key=True, serialize=False)),
                ('bfmi', models.FloatField()),
                ('gelman_rubin', models.FloatField()),
            ],
            options={
                'db_table': 'model_runs',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Teams',
            fields=[
                ('team_id', models.IntegerField(primary_key=True, serialize=False)),
                ('team_name', models.TextField()),
                ('team_abbreviation', models.TextField()),
                ('active', models.BooleanField()),
            ],
            options={
                'db_table': 'teams',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='GamePredictions',
            fields=[
                ('game_pk', models.ForeignKey(db_column='game_pk', on_delete=django.db.models.deletion.DO_NOTHING, primary_key=True, serialize=False, to='data.Games')),
                ('prediction_number', models.IntegerField()),
                ('home_team_regulation_goals', models.IntegerField()),
                ('away_team_regulation_goals', models.IntegerField()),
                ('home_wins_after_regulation', models.BooleanField()),
            ],
            options={
                'db_table': 'game_predictions',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='GeneralPosteriors',
            fields=[
                ('prediction_date', models.ForeignKey(db_column='prediction_date', on_delete=django.db.models.deletion.DO_NOTHING, primary_key=True, serialize=False, to='data.ModelRuns')),
                ('home_ice_advantage_median', models.FloatField()),
                ('home_ice_advantage_hpd_low', models.FloatField()),
                ('home_ice_advantage_hpd_high', models.FloatField()),
                ('intercept_median', models.FloatField()),
                ('intercept_hpd_low', models.FloatField()),
                ('intercept_hpd_high', models.FloatField()),
            ],
            options={
                'db_table': 'general_posteriors',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Periods',
            fields=[
                ('game_pk', models.ForeignKey(db_column='game_pk', on_delete=django.db.models.deletion.DO_NOTHING, primary_key=True, serialize=False, to='data.Games')),
                ('period_number', models.IntegerField()),
                ('period_type', models.TextField()),
                ('home_goals', models.IntegerField()),
                ('home_shots_on_goal', models.IntegerField()),
                ('away_goals', models.IntegerField()),
                ('away_shots_on_goal', models.IntegerField()),
            ],
            options={
                'db_table': 'periods',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Shootouts',
            fields=[
                ('game_pk', models.ForeignKey(db_column='game_pk', on_delete=django.db.models.deletion.DO_NOTHING, primary_key=True, serialize=False, to='data.Games')),
                ('home_scores', models.IntegerField()),
                ('home_attempts', models.IntegerField()),
                ('away_scores', models.IntegerField()),
                ('away_attempts', models.IntegerField()),
            ],
            options={
                'db_table': 'shootouts',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='TeamPosteriors',
            fields=[
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, primary_key=True, serialize=False, to='data.Teams')),
                ('offence_median', models.FloatField()),
                ('offence_hpd_low', models.FloatField()),
                ('offence_hpd_high', models.FloatField()),
                ('defence_median', models.FloatField()),
                ('defence_hpd_low', models.FloatField()),
                ('defence_hpd_high', models.FloatField()),
            ],
            options={
                'db_table': 'team_posteriors',
                'managed': False,
            },
        ),
    ]
