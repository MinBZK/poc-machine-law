from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.condition import Condition


T = TypeVar("T", bound="Action")


@_attrs_define
class Action:
    """
    Attributes:
        output (str): Action output
        value (Union['Action', Any, Unset]): Represents a value in an operation (can be a primitive value or nested
            action)
        operation (Union[None, Unset, str]): Operation to perform
        subject (Union[None, Unset, str]): Subject of the action
        unit (Union[None, Unset, str]): Unit for the action
        combine (Union[None, Unset, str]): Combination method
        values (Union[Any, Unset, list[Union['Action', Any]]]): Represents multiple values or a single value
        conditions (Union[Unset, list['Condition']]): Conditional logic
    """

    output: str
    value: Union["Action", Any, Unset] = UNSET
    operation: None | Unset | str = UNSET
    subject: None | Unset | str = UNSET
    unit: None | Unset | str = UNSET
    combine: None | Unset | str = UNSET
    values: Any | Unset | list[Union["Action", Any]] = UNSET
    conditions: Unset | list["Condition"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        output = self.output

        value: Any | Unset | dict[str, Any]
        if isinstance(self.value, Unset):
            value = UNSET
        elif isinstance(self.value, Action):
            value = self.value.to_dict()
        else:
            value = self.value

        operation: None | Unset | str
        if isinstance(self.operation, Unset):
            operation = UNSET
        else:
            operation = self.operation

        subject: None | Unset | str
        if isinstance(self.subject, Unset):
            subject = UNSET
        else:
            subject = self.subject

        unit: None | Unset | str
        if isinstance(self.unit, Unset):
            unit = UNSET
        else:
            unit = self.unit

        combine: None | Unset | str
        if isinstance(self.combine, Unset):
            combine = UNSET
        else:
            combine = self.combine

        values: Any | Unset | list[Any | dict[str, Any]]
        if isinstance(self.values, Unset):
            values = UNSET
        elif isinstance(self.values, list):
            values = []
            for componentsschemas_action_values_type_0_item_data in self.values:
                componentsschemas_action_values_type_0_item: Any | dict[str, Any]
                if isinstance(componentsschemas_action_values_type_0_item_data, Action):
                    componentsschemas_action_values_type_0_item = (
                        componentsschemas_action_values_type_0_item_data.to_dict()
                    )
                else:
                    componentsschemas_action_values_type_0_item = componentsschemas_action_values_type_0_item_data
                values.append(componentsschemas_action_values_type_0_item)

        else:
            values = self.values

        conditions: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.conditions, Unset):
            conditions = []
            for conditions_item_data in self.conditions:
                conditions_item = conditions_item_data.to_dict()
                conditions.append(conditions_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "output": output,
            }
        )
        if value is not UNSET:
            field_dict["value"] = value
        if operation is not UNSET:
            field_dict["operation"] = operation
        if subject is not UNSET:
            field_dict["subject"] = subject
        if unit is not UNSET:
            field_dict["unit"] = unit
        if combine is not UNSET:
            field_dict["combine"] = combine
        if values is not UNSET:
            field_dict["values"] = values
        if conditions is not UNSET:
            field_dict["conditions"] = conditions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.condition import Condition

        d = dict(src_dict)
        output = d.pop("output")

        def _parse_value(data: object) -> Union["Action", Any, Unset]:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_action_value_type_0 = Action.from_dict(data)

                return componentsschemas_action_value_type_0
            except:  # noqa: E722
                pass
            return cast(Union["Action", Any, Unset], data)

        value = _parse_value(d.pop("value", UNSET))

        def _parse_operation(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        operation = _parse_operation(d.pop("operation", UNSET))

        def _parse_subject(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        subject = _parse_subject(d.pop("subject", UNSET))

        def _parse_unit(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        unit = _parse_unit(d.pop("unit", UNSET))

        def _parse_combine(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        combine = _parse_combine(d.pop("combine", UNSET))

        def _parse_values(data: object) -> Any | Unset | list[Union["Action", Any]]:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                componentsschemas_action_values_type_0 = []
                _componentsschemas_action_values_type_0 = data
                for componentsschemas_action_values_type_0_item_data in _componentsschemas_action_values_type_0:

                    def _parse_componentsschemas_action_values_type_0_item(data: object) -> Union["Action", Any]:
                        try:
                            if not isinstance(data, dict):
                                raise TypeError()
                            componentsschemas_action_value_type_0 = Action.from_dict(data)

                            return componentsschemas_action_value_type_0
                        except:  # noqa: E722
                            pass
                        return cast(Union["Action", Any], data)

                    componentsschemas_action_values_type_0_item = _parse_componentsschemas_action_values_type_0_item(
                        componentsschemas_action_values_type_0_item_data
                    )

                    componentsschemas_action_values_type_0.append(componentsschemas_action_values_type_0_item)

                return componentsschemas_action_values_type_0
            except:  # noqa: E722
                pass
            return cast(Any | Unset | list[Union["Action", Any]], data)

        values = _parse_values(d.pop("values", UNSET))

        conditions = []
        _conditions = d.pop("conditions", UNSET)
        for conditions_item_data in _conditions or []:
            conditions_item = Condition.from_dict(conditions_item_data)

            conditions.append(conditions_item)

        action = cls(
            output=output,
            value=value,
            operation=operation,
            subject=subject,
            unit=unit,
            combine=combine,
            values=values,
            conditions=conditions,
        )

        action.additional_properties = d
        return action

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
