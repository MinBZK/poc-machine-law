"""Integration tests for backward compatibility with Services architecture."""

import pytest
import pandas as pd

from machine.service import Services, RuleResult
from machine.law_evaluator import LawEvaluator
from machine.data_context import DataContext


class TestBackwardCompatibility:
    """Test suite for backward compatibility between old and new architectures."""

    def test_services_still_works(self, services: Services):
        """Test that Services class can still be instantiated."""
        assert services is not None
        assert hasattr(services, "services")
        assert hasattr(services, "resolver")

    def test_services_discovers_laws(self, services: Services):
        """Test that Services discovers laws from YAMLs."""
        # Services should have discovered service names
        assert len(services.services) > 0

        # Should have common services like SVB, TOESLAGEN, etc.
        service_names = set(services.services.keys())
        expected_services = {"SVB", "TOESLAGEN", "BELASTINGDIENST"}
        assert expected_services.issubset(service_names)

    def test_services_evaluate_law(self, services: Services, reference_date: str):
        """Test evaluating a law using Services (old architecture)."""
        # Use session-scoped services fixture to avoid TopicError

        # Add test data
        df_personen = pd.DataFrame([{
            "bsn": "123456789",
            "geboortedatum": "1990-01-01"
        }])
        services.set_source_dataframe("SVB", "personen", df_personen)

        # Evaluate law
        result = services.evaluate(
            service="SVB",
            law="algemene_kinderbijslagwet",
            parameters={"BSN": "123456789"},
            reference_date=reference_date
        )

        # Verify result
        assert isinstance(result, RuleResult)
        assert isinstance(result.requirements_met, bool)
        assert isinstance(result.output, dict)

    def test_both_architectures_same_result(self, services: Services, law_evaluator: LawEvaluator, reference_date: str):
        """Test that both architectures produce equivalent results."""
        # Use session-scoped fixtures to avoid TopicError
        df_personen = pd.DataFrame([{
            "bsn": "123456789",
            "geboortedatum": "1990-01-01"
        }])

        # Set up old architecture (Services)
        services.set_source_dataframe("SVB", "personen", df_personen)

        # Set up new architecture (LawEvaluator)
        law_evaluator.data_context.sources.clear()
        law_evaluator.data_context.add_source("SVB", "personen", df_personen.copy())

        # Evaluate same law with both
        result_old = services.evaluate(
            service="SVB",
            law="algemene_kinderbijslagwet",
            parameters={"BSN": "123456789"},
            reference_date=reference_date
        )

        result_new = law_evaluator.evaluate_law(
            law="algemene_kinderbijslagwet",
            parameters={"BSN": "123456789"},
            reference_date=reference_date
        )

        # Results should be equivalent
        assert result_old.requirements_met == result_new.requirements_met
        assert result_old.output.keys() == result_new.output.keys()

    def test_execution_context_has_service_provider_property(self, law_evaluator: LawEvaluator):
        """Test that ExecutionContext has service_provider property for backward compat."""
        from machine.context import ExecutionContext

        # Use session-scoped law_evaluator to avoid TopicError
        context = ExecutionContext(
            definitions={},
            law_evaluator=law_evaluator,
            data_context=law_evaluator.data_context,
            parameters={},
            property_specs={},
            output_specs={},
            sources={},
            calculation_date="2025-01-01",
            overwrite_input={},
            overwrite_definitions={},
            approved=False
        )

        # service_provider should point to law_evaluator
        assert hasattr(context, "service_provider")
        assert context.service_provider is law_evaluator

    def test_rule_context_alias_exists(self):
        """Test that RuleContext is aliased to ExecutionContext."""
        from machine.context import RuleContext, ExecutionContext

        # RuleContext should be the same as ExecutionContext
        assert RuleContext is ExecutionContext

    def test_rules_engine_accepts_both_parameters(self, services: Services, law_evaluator: LawEvaluator):
        """Test that RulesEngine accepts both service_provider and law_evaluator."""
        from machine.engine import RulesEngine
        from machine.utils import RuleResolver

        resolver = RuleResolver()
        spec = resolver.get_rule_spec("algemene_kinderbijslagwet", "2025-01-01", service="SVB")

        # Should work with service_provider (old)
        engine_old = RulesEngine(spec=spec, service_provider=services)
        assert engine_old.service_provider is services

        # Should work with law_evaluator (new)
        engine_new = RulesEngine(spec=spec, law_evaluator=law_evaluator)
        assert engine_new.law_evaluator is law_evaluator
        # service_provider should point to law_evaluator for backward compat
        assert engine_new.service_provider is law_evaluator

    def test_v016_yaml_still_works(self, services: Services):
        """Test that v0.1.6 YAMLs with service field still work."""
        # All current YAMLs are v0.1.6 with service field
        # If we can discover services, v0.1.6 YAMLs are working
        assert len(services.services) > 0

    def test_rule_resolver_handles_optional_service(self):
        """Test that RuleResolver handles optional service field."""
        from machine.utils import RuleResolver

        resolver = RuleResolver()

        # Should be able to find rules with service (v0.1.6)
        rule_with_service = resolver.find_rule(
            law="algemene_kinderbijslagwet",
            reference_date="2025-01-01",
            service="SVB"
        )
        assert rule_with_service is not None
        assert rule_with_service.service == "SVB"

        # Should also work with service=None (for v0.1.7 in future)
        rule_without_service = resolver.find_rule(
            law="algemene_kinderbijslagwet",
            reference_date="2025-01-01",
            service=None
        )
        # This should still find the v0.1.6 rule
        assert rule_without_service is not None
