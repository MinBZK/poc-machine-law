"""
Law Synthesis Module

This module provides tools to synthesize simplified laws from simulation results.
It learns interpretable rules from simulation data and generates Machine Law YAML.
"""

from synthesize.learner import SynthesisLearner
from synthesize.validator import SynthesisValidator
from synthesize.yaml_generator import YAMLGenerator

__all__ = ["SynthesisLearner", "SynthesisValidator", "YAMLGenerator"]
