from typing import List, AnyStr, Optional
import xml.etree.ElementTree as ET

from .span import Span


def construct_ltf(text: str, spans: List[Span], encoding: Optional[str] = None) -> AnyStr:
    """
    Construct Loio Tagging Format from text and spans.
    :param text: original plain text.
    :param spans: list of spans.
    :param encoding: encoding passed to the xml.etree.ElementTree.ET.tostring() method.
    :return: bytes or str xml, depending on encoding. str is returned if encoding=='unicode'.
    """

    # parameters checks
    text_len = len(text)
    sorted_spans = sorted(spans, key=lambda span: span.start)
    prev_span_end = 0
    for s in sorted_spans:
        if s.start < 0:
            raise ValueError(f"Span {s} starts from negative offset.")
        if s.finish > text_len:
            raise ValueError(f"Span {s} ends after the last text character.")
        if s.start > s.finish:
            raise ValueError(f"Span {s} starts after their end position.")
        if prev_span_end > s.start:
            raise ValueError(f"Span {s} starts before ends the previous one {prev_span_end}.")
        prev_span_end = s.finish

    root = ET.Element('body')
    current_element = root
    prev_span_end = 0
    for s in sorted_spans:
        if current_element is root:
            current_element.text = text[prev_span_end: s.start]
        else:
            current_element.tail = text[prev_span_end: s.start]
        e = ET.SubElement(root, 'e')
        e.text = text[s.start: s.finish]
        current_element = e
        prev_span_end = s.finish
    if current_element is root:
        current_element.text = text
    else:
        current_element.tail = text[prev_span_end:]

    return ET.tostring(root, encoding=encoding)