from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.data_frame import DataFrame


T = TypeVar("T", bound="SetSourceDataFrameBody")


@_attrs_define
class SetSourceDataFrameBody:
    """
    Attributes:
        data (DataFrame):  Example: {'service': 'CBS', 'table': 'levensverwachting', 'data': [{'jaar': 2025,
            'verwachting_65': '20.5'}]}.
    """

    data: "DataFrame"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = self.data.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "data": data,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.data_frame import DataFrame

        d = dict(src_dict)
        data = DataFrame.from_dict(d.pop("data"))

        set_source_data_frame_body = cls(
            data=data,
        )

        set_source_data_frame_body.additional_properties = d
        return set_source_data_frame_body

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
