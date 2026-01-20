from dataclasses import dataclass
from typing import Any


@dataclass
class AggregationContext:
    """Context for aggregation expression evaluation"""

    active_item: dict[str, Any]

    def resolve_value(self, *keys: str) -> Any:
        """Resolve a value from the active item using a chain of keys

        Args:
            *keys: Variable number of key names to traverse

        Returns:
            The resolved value after traversing all keys

        Example:
            >>> context = AggregationContext(active_item={"person": {"name": "John"}})
            >>> context.resolve_value("person", "name")
            "John"
        """
        value = self.active_item

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None

        return value
