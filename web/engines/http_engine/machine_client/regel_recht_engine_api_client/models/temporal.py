from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="Temporal")


@_attrs_define
class Temporal:
    """
    Attributes:
        type_ (str): Temporal type
        period_type (Union[None, Unset, str]): Period type specification
        reference (Union[None, Unset, str]): Reference (can be string or VariableReference)
        immutable_after (Union[None, Unset, str]): Immutability rule
    """

    type_: str
    period_type: Union[None, Unset, str] = UNSET
    reference: Union[None, Unset, str] = UNSET
    immutable_after: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_

        period_type: Union[None, Unset, str]
        if isinstance(self.period_type, Unset):
            period_type = UNSET
        else:
            period_type = self.period_type

        reference: Union[None, Unset, str]
        if isinstance(self.reference, Unset):
            reference = UNSET
        else:
            reference = self.reference

        immutable_after: Union[None, Unset, str]
        if isinstance(self.immutable_after, Unset):
            immutable_after = UNSET
        else:
            immutable_after = self.immutable_after

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
            }
        )
        if period_type is not UNSET:
            field_dict["period_type"] = period_type
        if reference is not UNSET:
            field_dict["reference"] = reference
        if immutable_after is not UNSET:
            field_dict["immutable_after"] = immutable_after

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = d.pop("type")

        def _parse_period_type(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        period_type = _parse_period_type(d.pop("period_type", UNSET))

        def _parse_reference(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        reference = _parse_reference(d.pop("reference", UNSET))

        def _parse_immutable_after(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        immutable_after = _parse_immutable_after(d.pop("immutable_after", UNSET))

        temporal = cls(
            type_=type_,
            period_type=period_type,
            reference=reference,
            immutable_after=immutable_after,
        )

        temporal.additional_properties = d
        return temporal

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
