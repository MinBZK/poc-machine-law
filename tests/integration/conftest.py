import gc

import pytest

from machine import utils
from machine.service import RuleService
from machine.utils import RuleResolver


@pytest.fixture(autouse=True)
def clear_caches_after_test():
    """Clear all caches after each test to ensure test isolation"""
    yield
    # Clear file cache to prevent cross-test pollution
    utils._file_cache.clear()
    # Clear rule resolver cache if there's an active RuleService
    # Access the RuleService class-level resolver if it exists
    if hasattr(RuleService, "_resolver_cache"):
        RuleService._resolver_cache.clear()
    # Also clear any existing resolver instances
    # Clear the rule cache for all instances - walk through gc to find them
    for obj in gc.get_objects():
        if isinstance(obj, RuleResolver):
            obj._rule_cache.clear()
