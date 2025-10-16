import subprocess
import time

import requests
from eventsourcing.utils import clear_topic_cache

from machine.logging_config import configure_logging


def before_all(context) -> None:
    log_level = context.config.userdata.get("log_level", "DEBUG")
    context.loggers = configure_logging(log_level)

    # Start the web server once for all tests that need it
    # Check if server is already running
    server_running = False
    try:
        response = requests.get("http://localhost:8000", timeout=2)
        if response.status_code == 200:
            server_running = True
            print("Web server is already running")
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        pass

    if not server_running:
        print("Starting web server for tests...")
        # Capture server logs for debugging in CI
        import os

        # Ensure locale environment variables are set for the subprocess
        env = os.environ.copy()
        if "LANG" not in env:
            env["LANG"] = "nl_NL.UTF-8"
        if "LC_ALL" not in env:
            env["LC_ALL"] = "nl_NL.UTF-8"

        if os.getenv("CI"):
            # In CI, capture logs for debugging
            context.web_server_process = subprocess.Popen(
                ["uv", "run", "web/main.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env
            )
        else:
            # Locally, suppress output as before
            context.web_server_process = subprocess.Popen(
                ["uv", "run", "web/main.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env
            )

        # Wait for server to be ready
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get("http://localhost:8000", timeout=1)
                if response.status_code == 200:
                    print(f"Web server started successfully after {i + 1} attempts")
                    break
                elif response.status_code != 200:
                    print(f"Server responded with status {response.status_code} on attempt {i + 1}")
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                time.sleep(1)
        else:
            # Clean up if we couldn't start
            if os.getenv("CI") and hasattr(context.web_server_process, "stdout"):
                # Print server logs for debugging in CI
                print("Server logs:")
                if context.web_server_process.poll() is None:
                    context.web_server_process.terminate()
                    try:
                        stdout, _ = context.web_server_process.communicate(timeout=5)
                        print(stdout)
                    except subprocess.TimeoutExpired:
                        context.web_server_process.kill()
            context.web_server_process.terminate()
            raise AssertionError("Failed to start web server after 30 seconds")


def after_all(context) -> None:
    # Clean up the web server if we started it
    if hasattr(context, "web_server_process"):
        print("Stopping web server...")
        context.web_server_process.terminate()
        try:
            context.web_server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            context.web_server_process.kill()


def before_scenario(context, scenario) -> None:
    context.config.setup_logging()
    context.test_data = {}
    context.parameters = {}
    context.result = None

    # Clear source dataframes to prevent data pollution between scenarios
    if hasattr(context, 'services') and context.services:
        for service_name, service in context.services.services.items():
            service.source_dataframes.clear()


def after_scenario(context, scenario) -> None:
    clear_topic_cache()

    # Close Playwright browser and context if they exist
    if hasattr(context, "page"):
        context.page.close()
    if hasattr(context, "browser_context"):
        context.browser_context.close()
    if hasattr(context, "browser"):
        context.browser.close()
    if hasattr(context, "playwright"):
        context.playwright.stop()
