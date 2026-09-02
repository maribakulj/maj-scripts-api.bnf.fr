from __future__ import annotations

from collections import defaultdict
from xml.etree import ElementTree as ET


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def parse_xml(data: bytes | str) -> ET.Element:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return ET.fromstring(data)


def xml_to_dict(element: ET.Element):
    children = list(element)
    text = (element.text or "").strip()
    attrs = {f"@{local_name(k)}": v for k, v in element.attrib.items()}
    if not children:
        if attrs:
            if text:
                attrs["#text"] = text
            return attrs
        return text
    grouped: dict[str, list] = defaultdict(list)
    for child in children:
        grouped[local_name(child.tag)].append(xml_to_dict(child))
    result = dict(attrs)
    for key, values in grouped.items():
        result[key] = values[0] if len(values) == 1 else values
    if text:
        result["#text"] = text
    return result


def document_to_dict(data: bytes | str) -> dict:
    root = parse_xml(data)
    return {local_name(root.tag): xml_to_dict(root)}


def find_first_text(root: ET.Element, name: str) -> str | None:
    for elem in root.iter():
        if local_name(elem.tag) == name and elem.text:
            return elem.text.strip()
    return None
