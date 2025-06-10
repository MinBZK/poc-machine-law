from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CaseAppealStatus")


@_attrs_define
class CaseAppealStatus:
    """Parameters to set the objection status

    Attributes:
        possible (Union[Unset, bool]):
        not_possible_reason (Union[Unset, str]):
        appeal_period (Union[Unset, int]):
        direct_appeal (Union[Unset, bool]):
        direct_appeal_reason (Union[Unset, str]):
        competent_court (Union[Unset, str]):
        court_type (Union[Unset, str]):
    """

    possible: Union[Unset, bool] = UNSET
    not_possible_reason: Union[Unset, str] = UNSET
    appeal_period: Union[Unset, int] = UNSET
    direct_appeal: Union[Unset, bool] = UNSET
    direct_appeal_reason: Union[Unset, str] = UNSET
    competent_court: Union[Unset, str] = UNSET
    court_type: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        possible = self.possible

        not_possible_reason = self.not_possible_reason

        appeal_period = self.appeal_period

        direct_appeal = self.direct_appeal

        direct_appeal_reason = self.direct_appeal_reason

        competent_court = self.competent_court

        court_type = self.court_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if possible is not UNSET:
            field_dict["possible"] = possible
        if not_possible_reason is not UNSET:
            field_dict["notPossibleReason"] = not_possible_reason
        if appeal_period is not UNSET:
            field_dict["appealPeriod"] = appeal_period
        if direct_appeal is not UNSET:
            field_dict["directAppeal"] = direct_appeal
        if direct_appeal_reason is not UNSET:
            field_dict["directAppealReason"] = direct_appeal_reason
        if competent_court is not UNSET:
            field_dict["competentCourt"] = competent_court
        if court_type is not UNSET:
            field_dict["courtType"] = court_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        possible = d.pop("possible", UNSET)

        not_possible_reason = d.pop("notPossibleReason", UNSET)

        appeal_period = d.pop("appealPeriod", UNSET)

        direct_appeal = d.pop("directAppeal", UNSET)

        direct_appeal_reason = d.pop("directAppealReason", UNSET)

        competent_court = d.pop("competentCourt", UNSET)

        court_type = d.pop("courtType", UNSET)

        case_appeal_status = cls(
            possible=possible,
            not_possible_reason=not_possible_reason,
            appeal_period=appeal_period,
            direct_appeal=direct_appeal,
            direct_appeal_reason=direct_appeal_reason,
            competent_court=competent_court,
            court_type=court_type,
        )

        case_appeal_status.additional_properties = d
        return case_appeal_status

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
