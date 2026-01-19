"""Delegation module for handling act-on-behalf-of scenarios.

This module provides the infrastructure for users to act on behalf of others,
such as entrepreneurs acting for their businesses.
"""

from machine.delegation.manager import DelegationManager
from machine.delegation.models import Delegation, DelegationContext

__all__ = ["Delegation", "DelegationContext", "DelegationManager"]
