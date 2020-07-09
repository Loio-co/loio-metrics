import pytest

from loio_metrics import construct_ltf, Span


_to_be_or_not_to_be = "To be or not to be."


def test_construct_ltf_pos():
    expected = '<body>To <e>be</e> or not to <e>be</e>.</body>'
    actual = construct_ltf(_to_be_or_not_to_be, spans=[
        Span(3, 5),
        Span(16, 18),
    ], encoding="unicode")

    assert expected == actual


def test_construct_ltf_bounds():
    expected = '<body><e>To</e> be or not to be<e>.</e></body>'
    actual = construct_ltf(_to_be_or_not_to_be, spans=[
        Span(0, 2),
        Span(len(_to_be_or_not_to_be)-1, len(_to_be_or_not_to_be)),
    ], encoding="unicode")

    assert expected == actual


def test_construct_ltf_negative():
    # Span started after its end.
    with pytest.raises(ValueError):
        construct_ltf(_to_be_or_not_to_be, spans=[Span(2, 1)])

    # Spans overlapped
    with pytest.raises(ValueError):
        construct_ltf(_to_be_or_not_to_be, spans=[Span(2, 10), Span(8, 12)])

    # Span started at negative position.
    with pytest.raises(ValueError):
        construct_ltf(_to_be_or_not_to_be, spans=[Span(-2, 1)])

    # Span finished after the text end.
    with pytest.raises(ValueError):
        construct_ltf(_to_be_or_not_to_be, spans=[Span(1, len(_to_be_or_not_to_be)+1)])


def test_construct_ltf_empty():
    expected = '<body>To be or not to be.</body>'
    actual = construct_ltf(_to_be_or_not_to_be, spans=[], encoding="unicode")

    assert expected == actual


def test_construct_ltf_whole_is_entity():
    expected = '<body><e>To be or not to be.</e></body>'
    actual = construct_ltf(_to_be_or_not_to_be, spans=[Span(0, len(_to_be_or_not_to_be))], encoding="unicode")
    assert expected == actual


def test_construct_ltf_zero_length_entity():
    expected = '<body>T<e />o be or not to be.</body>'
    actual = construct_ltf(_to_be_or_not_to_be, spans=[Span(1, 1)], encoding="unicode")
    assert expected == actual

