from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TypeSpec")


@_attrs_define
class TypeSpec:
    """
    Attributes:
        type_ (str): Specific type definition
        unit (Union[None, Unset, str]): Unit of measurement
        precision (Union[None, Unset, int]): Precision for numeric types
        min_ (Union[None, Unset, float]): Minimum value
        max_ (Union[None, Unset, float]): Maximum value
    """

    type_: str
    unit: None | Unset | str = UNSET
    precision: None | Unset | int = UNSET
    min_: None | Unset | float = UNSET
    max_: None | Unset | float = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_

        unit: None | Unset | str
        if isinstance(self.unit, Unset):
            unit = UNSET
        else:
            unit = self.unit

        precision: None | Unset | int
        if isinstance(self.precision, Unset):
            precision = UNSET
        else:
            precision = self.precision

        min_: None | Unset | float
        if isinstance(self.min_, Unset):
            min_ = UNSET
        else:
            min_ = self.min_

        max_: None | Unset | float
        if isinstance(self.max_, Unset):
            max_ = UNSET
        else:
            max_ = self.max_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
            }
        )
        if unit is not UNSET:
            field_dict["unit"] = unit
        if precision is not UNSET:
            field_dict["precision"] = precision
        if min_ is not UNSET:
            field_dict["min"] = min_
        if max_ is not UNSET:
            field_dict["max"] = max_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = d.pop("type")

        def _parse_unit(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        unit = _parse_unit(d.pop("unit", UNSET))

        def _parse_precision(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        precision = _parse_precision(d.pop("precision", UNSET))

        def _parse_min_(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        min_ = _parse_min_(d.pop("min", UNSET))

        def _parse_max_(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        max_ = _parse_max_(d.pop("max", UNSET))

        type_spec = cls(
            type_=type_,
            unit=unit,
            precision=precision,
            min_=min_,
            max_=max_,
        )

        type_spec.additional_properties = d
        return type_spec

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
