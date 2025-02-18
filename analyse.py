from collections import defaultdict
from pprint import pprint

from machine.utils import RuleResolver

resolver = RuleResolver()

law = resolver.find_rule("participatiewet/bijstand", "2023-02-01", "GEMEENTE_AMSTERDAM")

sources = defaultdict(set)


def extract_dollar_vars(data):
    """
    Recursively extract all strings starting with $ from a nested structure.

    :param data: Input data (dict, list, or primitive)
    :return: Set of unique $ variables
    """
    dollar_vars = set()

    def _extract(item):
        if isinstance(item, dict):
            # Recursively search through dictionary values
            for value in item.values():
                _extract(value)
        elif isinstance(item, list):
            # Recursively search through list items
            for value in item:
                _extract(value)
        elif isinstance(item, str) and item.startswith("$"):
            dollar_vars.add(item[1:])

    _extract(data)
    return dollar_vars


def resolve_input(law, field=None):
    if "input" in law.properties:
        for input in law.properties.get("input"):
            sr = input.get("service_reference")
            s = sr.get("service")
            l = sr.get("law")
            resolve_input(resolver.find_rule(l, "2024-02-01", s), sr.get("field"))

    vars = set()
    if field:
        for action in law.actions:
            if action.get("output") == field:
                vars = extract_dollar_vars(action)
                break
    print("vars:", vars)
    if "sources" in law.properties:
        for source in law.properties.get("sources"):
            if source.get("name") in vars:
                sources[law.service].add(source.get("name"))


resolve_input(law)
pprint(sources)
