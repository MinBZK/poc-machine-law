from machine.nrml.aggregation_context import AggregationContext


class TestAggregationContext:
    """Test cases for AggregationContext"""

    def test_resolve_value_single_key(self):
        """Test resolving a value with a single key"""
        context = AggregationContext(active_item={"age": 25, "name": "John"})

        result = context.resolve_value("age")

        assert result == 25

    def test_resolve_value_nested_keys(self):
        """Test resolving a value with multiple nested keys"""
        context = AggregationContext(
            active_item={"person": {"details": {"age": 30, "city": "Amsterdam"}, "name": "Alice"}}
        )

        result = context.resolve_value("person", "details", "age")

        assert result == 30

    def test_resolve_value_deeply_nested(self):
        """Test resolving deeply nested values"""
        context = AggregationContext(active_item={"a": {"b": {"c": {"d": {"e": "deep_value"}}}}})

        result = context.resolve_value("a", "b", "c", "d", "e")

        assert result == "deep_value"

    def test_resolve_value_missing_key(self):
        """Test that missing keys return None"""
        context = AggregationContext(active_item={"age": 25})

        result = context.resolve_value("name")

        assert result is None

    def test_resolve_value_missing_nested_key(self):
        """Test that missing nested keys return None"""
        context = AggregationContext(active_item={"person": {"name": "John"}})

        result = context.resolve_value("person", "age")

        assert result is None

    def test_resolve_value_key_chain_broken(self):
        """Test that broken key chains return None"""
        context = AggregationContext(active_item={"person": {"name": "John"}})

        # "person" exists but "details" doesn't, so can't traverse further
        result = context.resolve_value("person", "details", "age")

        assert result is None

    def test_resolve_value_non_dict_intermediate(self):
        """Test that non-dict intermediate values return None"""
        context = AggregationContext(active_item={"person": "John"})

        # "person" is a string, not a dict, so can't traverse further
        result = context.resolve_value("person", "name")

        assert result is None

    def test_resolve_value_returns_dict(self):
        """Test that resolve_value can return dict values"""
        nested_dict = {"city": "Rotterdam", "country": "Netherlands"}
        context = AggregationContext(active_item={"address": nested_dict})

        result = context.resolve_value("address")

        assert result == nested_dict

    def test_resolve_value_returns_list(self):
        """Test that resolve_value can return list values"""
        hobbies = ["reading", "cycling", "coding"]
        context = AggregationContext(active_item={"hobbies": hobbies})

        result = context.resolve_value("hobbies")

        assert result == hobbies

    def test_resolve_value_empty_keys(self):
        """Test resolving with no keys returns the active_item itself"""
        active_item = {"age": 25, "name": "John"}
        context = AggregationContext(active_item=active_item)

        result = context.resolve_value()

        assert result == active_item

    def test_resolve_value_with_none_value(self):
        """Test resolving a key that has None as its value"""
        context = AggregationContext(active_item={"age": None})

        result = context.resolve_value("age")

        assert result is None

    def test_resolve_value_with_zero(self):
        """Test resolving a key with zero value (falsy but valid)"""
        context = AggregationContext(active_item={"count": 0})

        result = context.resolve_value("count")

        assert result == 0

    def test_resolve_value_with_empty_string(self):
        """Test resolving a key with empty string (falsy but valid)"""
        context = AggregationContext(active_item={"name": ""})

        result = context.resolve_value("name")

        assert result == ""

    def test_resolve_value_with_false(self):
        """Test resolving a key with False value (falsy but valid)"""
        context = AggregationContext(active_item={"active": False})

        result = context.resolve_value("active")

        assert result is False
