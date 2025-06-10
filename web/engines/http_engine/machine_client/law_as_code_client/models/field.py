from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.input_field import InputField
    from ..models.source_field import SourceField


T = TypeVar("T", bound="Field")


@_attrs_define
class Field:
    """Field containing input or source field

    Attributes:
        input_ (Union[Unset, InputField]): Input field extending BaseField
        source (Union[Unset, SourceField]): Source field extending BaseField
    """

    input_: Union[Unset, "InputField"] = UNSET
    source: Union[Unset, "SourceField"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        input_: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.input_, Unset):
            input_ = self.input_.to_dict()

        source: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.source, Unset):
            source = self.source.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if input_ is not UNSET:
            field_dict["input"] = input_
        if source is not UNSET:
            field_dict["source"] = source

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.input_field import InputField
        from ..models.source_field import SourceField

        d = dict(src_dict)
        _input_ = d.pop("input", UNSET)
        input_: Union[Unset, InputField]
        if isinstance(_input_, Unset):
            input_ = UNSET
        else:
            input_ = InputField.from_dict(_input_)

        _source = d.pop("source", UNSET)
        source: Union[Unset, SourceField]
        if isinstance(_source, Unset):
            source = UNSET
        else:
            source = SourceField.from_dict(_source)

        field = cls(
            input_=input_,
            source=source,
        )

        field.additional_properties = d
        return field

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
