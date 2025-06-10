from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.apply_event import ApplyEvent
    from ..models.update import Update


T = TypeVar("T", bound="Apply")


@_attrs_define
class Apply:
    """
    Attributes:
        name (str): Name of the application rule
        aggregate (str): Aggregate identifier
        events (list['ApplyEvent']): Associated events
        update (list['Update']): Update rules
    """

    name: str
    aggregate: str
    events: list["ApplyEvent"]
    update: list["Update"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        aggregate = self.aggregate

        events = []
        for events_item_data in self.events:
            events_item = events_item_data.to_dict()
            events.append(events_item)

        update = []
        for update_item_data in self.update:
            update_item = update_item_data.to_dict()
            update.append(update_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "aggregate": aggregate,
                "events": events,
                "update": update,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.apply_event import ApplyEvent
        from ..models.update import Update

        d = dict(src_dict)
        name = d.pop("name")

        aggregate = d.pop("aggregate")

        events = []
        _events = d.pop("events")
        for events_item_data in _events:
            events_item = ApplyEvent.from_dict(events_item_data)

            events.append(events_item)

        update = []
        _update = d.pop("update")
        for update_item_data in _update:
            update_item = Update.from_dict(update_item_data)

            update.append(update_item)

        apply = cls(
            name=name,
            aggregate=aggregate,
            events=events,
            update=update,
        )

        apply.additional_properties = d
        return apply

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
