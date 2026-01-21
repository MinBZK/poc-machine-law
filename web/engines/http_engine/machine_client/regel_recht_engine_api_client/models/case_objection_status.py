from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CaseObjectionStatus")


@_attrs_define
class CaseObjectionStatus:
    """Parameters to set the objection status

    Attributes:
        possible (Union[Unset, bool]):
        not_possible_reason (Union[Unset, str]):
        objection_period (Union[Unset, int]):
        decision_period (Union[Unset, int]):
        extension_period (Union[Unset, int]):
        admissable (Union[Unset, bool]):
    """

    possible: Unset | bool = UNSET
    not_possible_reason: Unset | str = UNSET
    objection_period: Unset | int = UNSET
    decision_period: Unset | int = UNSET
    extension_period: Unset | int = UNSET
    admissable: Unset | bool = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        possible = self.possible

        not_possible_reason = self.not_possible_reason

        objection_period = self.objection_period

        decision_period = self.decision_period

        extension_period = self.extension_period

        admissable = self.admissable

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if possible is not UNSET:
            field_dict["possible"] = possible
        if not_possible_reason is not UNSET:
            field_dict["notPossibleReason"] = not_possible_reason
        if objection_period is not UNSET:
            field_dict["objectionPeriod"] = objection_period
        if decision_period is not UNSET:
            field_dict["decisionPeriod"] = decision_period
        if extension_period is not UNSET:
            field_dict["extensionPeriod"] = extension_period
        if admissable is not UNSET:
            field_dict["admissable"] = admissable

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        possible = d.pop("possible", UNSET)

        not_possible_reason = d.pop("notPossibleReason", UNSET)

        objection_period = d.pop("objectionPeriod", UNSET)

        decision_period = d.pop("decisionPeriod", UNSET)

        extension_period = d.pop("extensionPeriod", UNSET)

        admissable = d.pop("admissable", UNSET)

        case_objection_status = cls(
            possible=possible,
            not_possible_reason=not_possible_reason,
            objection_period=objection_period,
            decision_period=decision_period,
            extension_period=extension_period,
            admissable=admissable,
        )

        case_objection_status.additional_properties = d
        return case_objection_status

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
