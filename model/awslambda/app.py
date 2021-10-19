import json
import logging
from bayesbet.nhl.tasks import main
from bayesbet.logger import get_logger


logger = get_logger(__name__)

def lambda_handler(event, context):
    league = event["league"]
    task = event["task"]
    funtion_parameters = event["task_parameters"]
    if league == "nhl":
        if task == "main":
            main.main()
        else:
            logger.info(f"Task=\"{task}\" does not exist for league=\"nhl\"!")
