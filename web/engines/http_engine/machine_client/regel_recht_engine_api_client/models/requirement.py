from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.action import Action


T = TypeVar("T", bound="Requirement")


@_attrs_define
class Requirement:
    """Logical requirements with AND/OR operations

    Attributes:
        all_ (Union[None, Unset, list[Union['Action', 'Requirement']]]): All requirements must be met (AND logic)
        or_ (Union[None, Unset, list[Union['Action', 'Requirement']]]): Any requirement must be met (OR logic)
    """

    all_: Union[None, Unset, list[Union["Action", "Requirement"]]] = UNSET
    or_: Union[None, Unset, list[Union["Action", "Requirement"]]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        all_: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.all_, Unset):
            all_ = UNSET
        elif isinstance(self.all_, list):
            all_ = []
            for all_type_0_item_data in self.all_:
                all_type_0_item: dict[str, Any]
                if isinstance(all_type_0_item_data, Requirement):
                    all_type_0_item = all_type_0_item_data.to_dict()
                else:
                    all_type_0_item = all_type_0_item_data.to_dict()

                all_.append(all_type_0_item)

        else:
            all_ = self.all_

        or_: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.or_, Unset):
            or_ = UNSET
        elif isinstance(self.or_, list):
            or_ = []
            for or_type_0_item_data in self.or_:
                or_type_0_item: dict[str, Any]
                if isinstance(or_type_0_item_data, Requirement):
                    or_type_0_item = or_type_0_item_data.to_dict()
                else:
                    or_type_0_item = or_type_0_item_data.to_dict()

                or_.append(or_type_0_item)

        else:
            or_ = self.or_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if all_ is not UNSET:
            field_dict["all"] = all_
        if or_ is not UNSET:
            field_dict["or"] = or_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.action import Action

        d = dict(src_dict)

        def _parse_all_(data: object) -> Union[None, Unset, list[Union["Action", "Requirement"]]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                all_type_0 = []
                _all_type_0 = data
                for all_type_0_item_data in _all_type_0:

                    def _parse_all_type_0_item(data: object) -> Union["Action", "Requirement"]:
                        try:
                            if not isinstance(data, dict):
                                raise TypeError()
                            componentsschemas_action_requirement_type_0 = Requirement.from_dict(data)

                            return componentsschemas_action_requirement_type_0
                        except:  # noqa: E722
                            pass
                        if not isinstance(data, dict):
                            raise TypeError()
                        componentsschemas_action_requirement_type_1 = Action.from_dict(data)

                        return componentsschemas_action_requirement_type_1

                    all_type_0_item = _parse_all_type_0_item(all_type_0_item_data)

                    all_type_0.append(all_type_0_item)

                return all_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[Union["Action", "Requirement"]]], data)

        all_ = _parse_all_(d.pop("all", UNSET))

        def _parse_or_(data: object) -> Union[None, Unset, list[Union["Action", "Requirement"]]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                or_type_0 = []
                _or_type_0 = data
                for or_type_0_item_data in _or_type_0:

                    def _parse_or_type_0_item(data: object) -> Union["Action", "Requirement"]:
                        try:
                            if not isinstance(data, dict):
                                raise TypeError()
                            componentsschemas_action_requirement_type_0 = Requirement.from_dict(data)

                            return componentsschemas_action_requirement_type_0
                        except:  # noqa: E722
                            pass
                        if not isinstance(data, dict):
                            raise TypeError()
                        componentsschemas_action_requirement_type_1 = Action.from_dict(data)

                        return componentsschemas_action_requirement_type_1

                    or_type_0_item = _parse_or_type_0_item(or_type_0_item_data)

                    or_type_0.append(or_type_0_item)

                return or_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[Union["Action", "Requirement"]]], data)

        or_ = _parse_or_(d.pop("or", UNSET))

        requirement = cls(
            all_=all_,
            or_=or_,
        )

        requirement.additional_properties = d
        return requirement

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
