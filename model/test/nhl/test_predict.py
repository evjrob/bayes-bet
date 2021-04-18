import pandas as pd
import pytest

from bayesbet.nhl.predict import bayesian_poisson_pdf
from bayesbet.nhl.predict import bayesian_bernoulli_win_pdf
from bayesbet.nhl.predict import bayesian_goal_within_time

# @pytest.fixture
# def poisson_cases():
#     cases = [
#         (0.0, 0.1, 5, 
#         [0.3678839711698872, 0.366049307392375, 0.18392385257827024, 0.06222208712974248, 
#         0.015944512312484223, 0.00397626941724083]),
#         (0.0, 0.1, 6, 
#         [0.3678839711698872, 0.366049307392375, 0.18392385257827024, 0.06222208712974248, 
#         0.015944512312484223, 0.00397626941724083, 0.0006751111828385836])
#     ]
#     return cases

# def test_bayesian_poisson_pdf(poisson_cases):
#     for case in poisson_cases:
#         μ, σ, max_y, expected = case
#         poisson_pdf = bayesian_poisson_pdf(μ, σ, max_y)
#         assert poisson_pdf == expected, \
#             f"Did not get the expected bayesian Poisson pdf (μ={μ}, σ={σ}, max_y={max_y}"