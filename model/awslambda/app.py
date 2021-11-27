from bayesbet.nhl import tasks as nhl_tasks
from bayesbet.logger import get_logger


logger = get_logger(__name__)

task_modules = {
    "nhl": nhl_tasks,
}


def lambda_handler(event, context):
    league = event["league"]
    task_module = task_modules[league]
    task = event["task"]  # Matches the function name in task module
    function_parameters = event["task_parameters"]
    logger.info(f"Execution task={task} on league={league} with parameters:")
    if isinstance(function_parameters, dict):
        for k, v in function_parameters.items():
            logger.info(f"{k}: {v}")
    if hasattr(task_module, task):
        return getattr(task_module, task)(**function_parameters)
    else:
        logger.info(f'Task="{task}" does not exist for league="{league}"!')
