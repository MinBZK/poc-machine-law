from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="CaseReview")


@_attrs_define
class CaseReview:
    """
    Attributes:
        verifier_id (str): ID of the verifier making the decision
        approved (bool): Decision outcome - true for approval, false for rejection
        reason (str): Explanation for the decision
    """

    verifier_id: str
    approved: bool
    reason: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        verifier_id = self.verifier_id

        approved = self.approved

        reason = self.reason

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "verifierId": verifier_id,
                "approved": approved,
                "reason": reason,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        verifier_id = d.pop("verifierId")

        approved = d.pop("approved")

        reason = d.pop("reason")

        case_review = cls(
            verifier_id=verifier_id,
            approved=approved,
            reason=reason,
        )

        case_review.additional_properties = d
        return case_review

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
