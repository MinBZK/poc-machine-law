from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.apply_event_filter import ApplyEventFilter


T = TypeVar("T", bound="ApplyEvent")


@_attrs_define
class ApplyEvent:
    """
    Attributes:
        type_ (str): Event type
        filter_ (ApplyEventFilter): Event filter criteria
    """

    type_: str
    filter_: "ApplyEventFilter"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_

        filter_ = self.filter_.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "filter": filter_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.apply_event_filter import ApplyEventFilter

        d = dict(src_dict)
        type_ = d.pop("type")

        filter_ = ApplyEventFilter.from_dict(d.pop("filter"))

        apply_event = cls(
            type_=type_,
            filter_=filter_,
        )

        apply_event.additional_properties = d
        return apply_event

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
