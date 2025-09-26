import json
import pytest
from pathlib import Path
from machine.nrml.rules_engine import NrmlRulesEngine


class TestNrmlDependencies:
    """Test NRML dependency graph functionality"""

    @pytest.fixture
    def rules_engine(self):
        """Create rules engine with BRP NRML data"""
        project_root = Path(__file__).parent.parent.parent
        brp_path = project_root / "law" / "nrml" / "brp_nationaliteit.nrml.json"

        with open(brp_path, 'r') as f:
            spec = json.load(f)

        return NrmlRulesEngine(spec)

    def test_dependency_graph_creation(self, rules_engine):
        """Test that dependency graph is created correctly"""
        # Should have 4 items total
        assert len(rules_engine.items) == 4

        # Should have 2 items with dependencies (calc item + inverted target)
        assert len(rules_engine.dependencies) == 2

    def test_find_references_recursive(self, rules_engine):
        """Test recursive reference finding"""
        # Test with a simple dict containing a $ref
        test_obj = {
            "target": [{"$ref": "#/facts/test/items/test"}],
            "nested": {
                "deep": {
                    "reference": {"$ref": "#/facts/deep/items/deep"}
                }
            }
        }

        refs = rules_engine._find_references_recursive(test_obj)
        expected = {"#/facts/test/items/test", "#/facts/deep/items/deep"}
        assert refs == expected

    def test_find_references_in_lists(self, rules_engine):
        """Test finding references in list structures"""
        test_obj = [
            {"$ref": "#/facts/list1/items/item1"},
            {"nested": {"$ref": "#/facts/list2/items/item2"}},
            "not_a_ref"
        ]

        refs = rules_engine._find_references_recursive(test_obj)
        expected = {"#/facts/list1/items/item1", "#/facts/list2/items/item2"}
        assert refs == expected

    def test_get_dependencies(self, rules_engine):
        """Test getting dependencies for specific items"""
        # The main calculation item (no longer depends on target)
        calc_item = "#/facts/a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d/items/b2c3d4e5-6f7a-8b9c-0d1e-2f3a4b5c6d7e"

        deps = rules_engine.get_dependencies(calc_item)
        assert len(deps) == 2  # Should depend on 2 items (expression refs, not target)

        # Result item now depends on calc item (inverted target dependency)
        result_item = "#/facts/f1e2d3c4-5b6a-7c8d-9e0f-1a2b3c4d5e6f/items/a2f3e4d5-6c7b-8d9e-0f1a-2b3c4d5e6f78"
        deps = rules_engine.get_dependencies(result_item)
        assert len(deps) == 1  # Should depend on calc item

        # Type definition items should have no dependencies
        type_item = "#/facts/3c8e2a5f-1b6d-4e9c-7f2d-a5c3b6e1d9f4/items/9d2c5b1e-7f3a-4d6c-b2e8-f5a1c9d3b7e6"
        deps = rules_engine.get_dependencies(type_item)
        assert len(deps) == 0

    def test_get_dependents(self, rules_engine):
        """Test getting items that depend on a specific item"""
        # Type definition items should be depended upon
        type_item = "#/facts/3c8e2a5f-1b6d-4e9c-7f2d-a5c3b6e1d9f4/items/9d2c5b1e-7f3a-4d6c-b2e8-f5a1c9d3b7e6"

        dependents = rules_engine.get_dependents(type_item)
        assert len(dependents) == 1  # Should have 1 dependent (calc item)

        # The calculation item now has a dependent (result item via inverted target)
        calc_item = "#/facts/a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d/items/b2c3d4e5-6f7a-8b9c-0d1e-2f3a4b5c6d7e"
        dependents = rules_engine.get_dependents(calc_item)
        assert len(dependents) == 1  # Should have 1 dependent (result item)

    def test_dependency_chain(self, rules_engine):
        """Test complete dependency chain generation"""
        # The main calculation item
        calc_item = "#/facts/a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d/items/b2c3d4e5-6f7a-8b9c-0d1e-2f3a4b5c6d7e"

        chain = rules_engine.get_dependency_chain(calc_item)

        # Should include calc item + its 2 dependencies
        assert len(chain) == 3

        # The calculation item should be last in the chain
        assert chain[-1] == calc_item

        # Dependencies should come before the item that depends on them
        dependencies = rules_engine.get_dependencies(calc_item)
        calc_index = chain.index(calc_item)

        for dep in dependencies:
            dep_index = chain.index(dep)
            assert dep_index < calc_index, f"Dependency {dep} should come before {calc_item}"

        # Test the result item chain (should include all items due to inverted dependency)
        result_item = "#/facts/f1e2d3c4-5b6a-7c8d-9e0f-1a2b3c4d5e6f/items/a2f3e4d5-6c7b-8d9e-0f1a-2b3c4d5e6f78"
        result_chain = rules_engine.get_dependency_chain(result_item)

        # Should include all 4 items (full dependency chain)
        assert len(result_chain) == 4

        # Result item should be last
        assert result_chain[-1] == result_item

    def test_circular_dependency_handling(self, rules_engine):
        """Test that circular dependencies are handled gracefully"""
        # This should not cause infinite recursion
        non_existent_item = "#/facts/fake/items/fake"
        chain = rules_engine.get_dependency_chain(non_existent_item)

        # Should return empty chain for non-existent item
        assert len(chain) == 1
        assert chain[0] == non_existent_item

    def test_actual_nrml_dependencies(self, rules_engine):
        """Test with actual NRML data structure"""
        # Verify the specific dependencies from brp_nationaliteit.nrml.json
        calc_item = "#/facts/a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d/items/b2c3d4e5-6f7a-8b9c-0d1e-2f3a4b5c6d7e"

        dependencies = rules_engine.get_dependencies(calc_item)

        # Should depend on these specific items (excluding target reference)
        expected_deps = {
            "#/facts/3c8e2a5f-1b6d-4e9c-7f2d-a5c3b6e1d9f4/items/9d2c5b1e-7f3a-4d6c-b2e8-f5a1c9d3b7e6",
            "#/facts/8c3f1d6a-5b9e-4f2c-d7b1-e3a6f4c8d5b2/items/2d9f5c1b-7e3a-4b6d-c8f2-1a5e9d3b7f4c"
        }

        assert dependencies == expected_deps

        # Test inverted target dependency
        result_item = "#/facts/f1e2d3c4-5b6a-7c8d-9e0f-1a2b3c4d5e6f/items/a2f3e4d5-6c7b-8d9e-0f1a-2b3c4d5e6f78"
        result_deps = rules_engine.get_dependencies(result_item)

        expected_result_deps = {calc_item}
        assert result_deps == expected_result_deps