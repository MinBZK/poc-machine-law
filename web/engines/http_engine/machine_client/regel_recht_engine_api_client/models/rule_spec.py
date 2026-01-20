import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.action import Action
    from ..models.properties import Properties
    from ..models.reference import Reference
    from ..models.requirement import Requirement


T = TypeVar("T", bound="RuleSpec")


@_attrs_define
class RuleSpec:
    """
    Attributes:
        uuid (UUID): Unique identifier for the rule specification
        name (str): Name of the rule specification
        law (str): Associated law reference
        valid_from (datetime.datetime): Date from which the rule is valid
        service (str): Associated service identifier
        description (str): Description of the rule specification
        properties (Properties):
        law_type (Union[None, Unset, str]): Type of law
        legal_character (Union[None, Unset, str]): Legal character of the rule
        decision_type (Union[None, Unset, str]): Type of decision
        discoverable (Union[None, Unset, str]): Discoverability setting
        references (Union[Unset, list['Reference']]): Legal references
        requirements (Union[Unset, list['Requirement']]): Requirements for the rule
        actions (Union[Unset, list['Action']]): Actions associated with the rule
    """

    uuid: UUID
    name: str
    law: str
    valid_from: datetime.datetime
    service: str
    description: str
    properties: "Properties"
    law_type: None | Unset | str = UNSET
    legal_character: None | Unset | str = UNSET
    decision_type: None | Unset | str = UNSET
    discoverable: None | Unset | str = UNSET
    references: Unset | list["Reference"] = UNSET
    requirements: Unset | list["Requirement"] = UNSET
    actions: Unset | list["Action"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        uuid = str(self.uuid)

        name = self.name

        law = self.law

        valid_from = self.valid_from.isoformat()

        service = self.service

        description = self.description

        properties = self.properties.to_dict()

        law_type: None | Unset | str
        if isinstance(self.law_type, Unset):
            law_type = UNSET
        else:
            law_type = self.law_type

        legal_character: None | Unset | str
        if isinstance(self.legal_character, Unset):
            legal_character = UNSET
        else:
            legal_character = self.legal_character

        decision_type: None | Unset | str
        if isinstance(self.decision_type, Unset):
            decision_type = UNSET
        else:
            decision_type = self.decision_type

        discoverable: None | Unset | str
        if isinstance(self.discoverable, Unset):
            discoverable = UNSET
        else:
            discoverable = self.discoverable

        references: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.references, Unset):
            references = []
            for references_item_data in self.references:
                references_item = references_item_data.to_dict()
                references.append(references_item)

        requirements: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.requirements, Unset):
            requirements = []
            for requirements_item_data in self.requirements:
                requirements_item = requirements_item_data.to_dict()
                requirements.append(requirements_item)

        actions: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.actions, Unset):
            actions = []
            for actions_item_data in self.actions:
                actions_item = actions_item_data.to_dict()
                actions.append(actions_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "uuid": uuid,
                "name": name,
                "law": law,
                "valid_from": valid_from,
                "service": service,
                "description": description,
                "properties": properties,
            }
        )
        if law_type is not UNSET:
            field_dict["law_type"] = law_type
        if legal_character is not UNSET:
            field_dict["legal_character"] = legal_character
        if decision_type is not UNSET:
            field_dict["decision_type"] = decision_type
        if discoverable is not UNSET:
            field_dict["discoverable"] = discoverable
        if references is not UNSET:
            field_dict["references"] = references
        if requirements is not UNSET:
            field_dict["requirements"] = requirements
        if actions is not UNSET:
            field_dict["actions"] = actions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.action import Action
        from ..models.properties import Properties
        from ..models.reference import Reference
        from ..models.requirement import Requirement

        d = dict(src_dict)
        uuid = UUID(d.pop("uuid"))

        name = d.pop("name")

        law = d.pop("law")

        valid_from = isoparse(d.pop("valid_from"))

        service = d.pop("service")

        description = d.pop("description")

        properties = Properties.from_dict(d.pop("properties"))

        def _parse_law_type(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        law_type = _parse_law_type(d.pop("law_type", UNSET))

        def _parse_legal_character(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        legal_character = _parse_legal_character(d.pop("legal_character", UNSET))

        def _parse_decision_type(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        decision_type = _parse_decision_type(d.pop("decision_type", UNSET))

        def _parse_discoverable(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        discoverable = _parse_discoverable(d.pop("discoverable", UNSET))

        references = []
        _references = d.pop("references", UNSET)
        for references_item_data in _references or []:
            references_item = Reference.from_dict(references_item_data)

            references.append(references_item)

        requirements = []
        _requirements = d.pop("requirements", UNSET)
        for requirements_item_data in _requirements or []:
            requirements_item = Requirement.from_dict(requirements_item_data)

            requirements.append(requirements_item)

        actions = []
        _actions = d.pop("actions", UNSET)
        for actions_item_data in _actions or []:
            actions_item = Action.from_dict(actions_item_data)

            actions.append(actions_item)

        rule_spec = cls(
            uuid=uuid,
            name=name,
            law=law,
            valid_from=valid_from,
            service=service,
            description=description,
            properties=properties,
            law_type=law_type,
            legal_character=legal_character,
            decision_type=decision_type,
            discoverable=discoverable,
            references=references,
            requirements=requirements,
            actions=actions,
        )

        rule_spec.additional_properties = d
        return rule_spec

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
