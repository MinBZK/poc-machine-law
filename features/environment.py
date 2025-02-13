from eventsourcing.utils import clear_topic_cache

from machine.logging_config import configure_logging


def before_all(context) -> None:
    log_level = context.config.userdata.get("log_level", "DEBUG")
    context.loggers = configure_logging(log_level)


def before_scenario(context, scenario) -> None:
    context.config.setup_logging()
    context.test_data = {}
    context.parameters = {}
    context.result = None


def after_scenario(context, scenario) -> None:
    clear_topic_cache()
