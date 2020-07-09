from typing import List, AnyStr, Optional, Union, Tuple
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


def parse_ltf(src: Union[str, bytes]) -> Tuple[str, List[Span]]:
    """
    Function extracts text and spans from the XML in Loio Tagging Format

    @param src: XML source.
    @return: Tuple of plain text and list of extracted spans.
    """
    def safe_empty(s: Optional[str]) -> str:
        return s if s else ''

    root = ET.fromstring(src)
    if root.tag != 'body':
        raise ValueError(f"Document's root element is <{root.tag}> but <body> is expected.")
    res = []
    text_buf = [safe_empty(root.text)]
    cur_pos = len(text_buf[0])
    for e in root:
        if e.tag != 'e':
            raise ValueError(f"'Document contains non-root element <{e.tag}> but <e> is expected only.")
        e_txt = safe_empty(e.text)
        res.append(Span(cur_pos, cur_pos + len(e_txt)))
        txt = e_txt + safe_empty(e.tail)
        cur_pos += len(txt)
        text_buf += txt
    text = ''.join(text_buf)
    return text, res
