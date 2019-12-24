bayes-bet
==============================

A bayesian model for predicting the outcomes of NHL games, complete with a Django based web app for visualization.

http://hockey.everettsprojects.com

Associated Blog Posts
-------------

* [Modeling the NHL - March 24, 2018](http://everettsprojects.com/2018/03/24/modeling-the-nhl.html)



Project Organization
------------

    ├── LICENSE
    ├── README.md
    ├── front_end/                  <- Django web app code.
    |   ├── .elasticbeanstalk/      <- Elastic Beanstalk config.
    |   ├── app/
    |   |   ├── .ebextensions/      <- Elastic Beanstalk config.
    |   |   ├── .elasticbeanstalk/  <- Elastic Beanstalk config.
    |   |   ├── bayesbet/           <- Main app code.
    |   |   ├── data/               <- REST API for data and model results.
    |   |   ├── plots/              <- D3 code for plots
    |   |   ├── static/             <- Django main static files folder.
    |   |   ├── templates/          <- Django html templates.
    |   |   ├── manage.py           <- Django management script.
    |   |   └── requirements.txt    <- Python virtualenv for Django.
    ├── model/                      <- PyMC3 model run with docker in AWS batch.
    |   ├── bayes_bet_aws.yml       <- Conda environment used by model.
    |   ├── bayes_bet_update.py     <- Python code for NHL data pull and model update.
    |   └── Dockerfile              <- Dockerfile for AWS batch job container image.
    └── sql/                    <- Queries used to construct PostgreSQL database underlying the project.


--------
