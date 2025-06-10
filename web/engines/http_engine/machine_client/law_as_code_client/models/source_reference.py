from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.select_field import SelectField


T = TypeVar("T", bound="SourceReference")


@_attrs_define
class SourceReference:
    """
    Attributes:
        source_type (Union[Unset, str]): Type of the data source
        table (Union[Unset, str]): Table name in the source
        field (Union[None, Unset, str]): Specific field to reference
        fields (Union[None, Unset, list[str]]): Multiple fields to reference
        select_on (Union[Unset, list['SelectField']]): Selection criteria
    """

    source_type: Union[Unset, str] = UNSET
    table: Union[Unset, str] = UNSET
    field: Union[None, Unset, str] = UNSET
    fields: Union[None, Unset, list[str]] = UNSET
    select_on: Union[Unset, list["SelectField"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        source_type = self.source_type

        table = self.table

        field: Union[None, Unset, str]
        if isinstance(self.field, Unset):
            field = UNSET
        else:
            field = self.field

        fields: Union[None, Unset, list[str]]
        if isinstance(self.fields, Unset):
            fields = UNSET
        elif isinstance(self.fields, list):
            fields = self.fields

        else:
            fields = self.fields

        select_on: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.select_on, Unset):
            select_on = []
            for select_on_item_data in self.select_on:
                select_on_item = select_on_item_data.to_dict()
                select_on.append(select_on_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if source_type is not UNSET:
            field_dict["source_type"] = source_type
        if table is not UNSET:
            field_dict["table"] = table
        if field is not UNSET:
            field_dict["field"] = field
        if fields is not UNSET:
            field_dict["fields"] = fields
        if select_on is not UNSET:
            field_dict["select_on"] = select_on

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.select_field import SelectField

        d = dict(src_dict)
        source_type = d.pop("source_type", UNSET)

        table = d.pop("table", UNSET)

        def _parse_field(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        field = _parse_field(d.pop("field", UNSET))

        def _parse_fields(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                fields_type_0 = cast(list[str], data)

                return fields_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        fields = _parse_fields(d.pop("fields", UNSET))

        select_on = []
        _select_on = d.pop("select_on", UNSET)
        for select_on_item_data in _select_on or []:
            select_on_item = SelectField.from_dict(select_on_item_data)

            select_on.append(select_on_item)

        source_reference = cls(
            source_type=source_type,
            table=table,
            field=field,
            fields=fields,
            select_on=select_on,
        )

        source_reference.additional_properties = d
        return source_reference

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
