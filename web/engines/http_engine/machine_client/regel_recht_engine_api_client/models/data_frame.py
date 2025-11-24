from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="DataFrame")


@_attrs_define
class DataFrame:
    """
    Example:
        {'service': 'CBS', 'table': 'levensverwachting', 'data': [{'jaar': 2025, 'verwachting_65': '20.5'}]}

    Attributes:
        service (str):
        table (str):
        data (list[Any]): Column definitions for the data frame
    """

    service: str
    table: str
    data: list[Any]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        service = self.service

        table = self.table

        data = self.data

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "service": service,
                "table": table,
                "data": data,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        service = d.pop("service")

        table = d.pop("table")

        data = cast(list[Any], d.pop("data"))

        data_frame = cls(
            service=service,
            table=table,
            data=data,
        )

        data_frame.additional_properties = d
        return data_frame

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
