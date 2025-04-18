from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.path_node_details import PathNodeDetails


T = TypeVar("T", bound="PathNode")


@_attrs_define
class PathNode:
    """path node

    Attributes:
        type_ (str):
        name (str):
        result (Union[Unset, Any]):
        resolve_type (Union[Unset, str]):
        required (Union[Unset, bool]):
        details (Union[Unset, PathNodeDetails]):
        children (Union[Unset, list['PathNode']]):
    """

    type_: str
    name: str
    result: Union[Unset, Any] = UNSET
    resolve_type: Union[Unset, str] = UNSET
    required: Union[Unset, bool] = UNSET
    details: Union[Unset, "PathNodeDetails"] = UNSET
    children: Union[Unset, list["PathNode"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_

        name = self.name

        result = self.result

        resolve_type = self.resolve_type

        required = self.required

        details: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.details, Unset):
            details = self.details.to_dict()

        children: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.children, Unset):
            children = []
            for children_item_data in self.children:
                children_item = children_item_data.to_dict()
                children.append(children_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "name": name,
            }
        )
        if result is not UNSET:
            field_dict["result"] = result
        if resolve_type is not UNSET:
            field_dict["resolveType"] = resolve_type
        if required is not UNSET:
            field_dict["required"] = required
        if details is not UNSET:
            field_dict["details"] = details
        if children is not UNSET:
            field_dict["children"] = children

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.path_node_details import PathNodeDetails

        d = dict(src_dict)
        type_ = d.pop("type")

        name = d.pop("name")

        result = d.pop("result", UNSET)

        resolve_type = d.pop("resolveType", UNSET)

        required = d.pop("required", UNSET)

        _details = d.pop("details", UNSET)
        details: Union[Unset, PathNodeDetails]
        if isinstance(_details, Unset):
            details = UNSET
        else:
            details = PathNodeDetails.from_dict(_details)

        children = []
        _children = d.pop("children", UNSET)
        for children_item_data in _children or []:
            children_item = PathNode.from_dict(children_item_data)

            children.append(children_item)

        path_node = cls(
            type_=type_,
            name=name,
            result=result,
            resolve_type=resolve_type,
            required=required,
            details=details,
            children=children,
        )

        path_node.additional_properties = d
        return path_node

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
