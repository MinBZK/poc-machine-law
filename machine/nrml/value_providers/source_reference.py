from dataclasses import dataclass
from typing import Any


@dataclass
class SelectOnField:
    """Field specification for selecting rows in source reference"""

    name: str
    description: str
    type: str
    value: str


@dataclass
class SourceReference:
    """Reference to a source table and field for value resolution"""

    table: str
    field: str
    select_on: list[SelectOnField]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SourceReference":
        """Create SourceReference from dictionary"""
        select_on_list = []
        for select_item in data.get("select_on", []):
            select_on_list.append(
                SelectOnField(
                    name=select_item["name"],
                    description=select_item["description"],
                    type=select_item["type"],
                    value=select_item["value"],
                )
            )

        return cls(
            table=data["table"],
            field=data["field"],
            select_on=select_on_list,
        )
