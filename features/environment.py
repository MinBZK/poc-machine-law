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

    # Close Playwright browser and context if they exist
    if hasattr(context, 'page'):
        context.page.close()
    if hasattr(context, 'browser_context'):
        context.browser_context.close()
    if hasattr(context, 'browser'):
        context.browser.close()
    if hasattr(context, 'playwright'):
        context.playwright.stop()

    # Reset application state by restarting the server
    # This ensures we don't have persisted claims between test runs
    import subprocess
    import time

    # Kill the existing server process
    subprocess.run(["pkill", "-f", "web/main.py"], capture_output=True)
    time.sleep(1)

    # Restart the server in the background
    subprocess.Popen(["uv", "run", "web/main.py"],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)
    time.sleep(3)  # Give the server time to start
