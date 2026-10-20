"""``nada_ai.search.cursor``: the paging cursor's wire form and its strict validation."""

from __future__ import annotations

import base64
import json

import pytest

from nada_ai.search.cursor import (
    MAX_CURSOR_LENGTH,
    Cursor,
    CursorError,
    Direction,
    SortValueKind,
    decode,
    encode,
)

RELEVANCE = (SortValueKind.score, SortValueKind.id)
TITLE = (SortValueKind.text, SortValueKind.text, SortValueKind.id)


def _token(payload: object) -> str:
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()


def test_a_cursor_round_trips_exactly() -> None:
    cursor = Cursor(Direction.after, (8.123456789, 440192), 990, 29762, False)
    token = encode(cursor)
    assert set(token) <= set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")  # URL-safe as is
    assert decode(token, RELEVANCE) == cursor


def test_text_values_and_missing_ones_round_trip() -> None:
    cursor = Cursor(Direction.before, ('enquête, 2010 "rural"', None, 7), 15, 20000, True)
    assert decode(encode(cursor), TITLE) == cursor


@pytest.mark.parametrize(
    "token",
    [
        "",
        "not base64!",
        _token({"v": 1}),  # not the array
        _token([2, "a", [1.0, 1], 0, 0, False]),  # unknown version
        _token([1, "x", [1.0, 1], 0, 0, False]),  # unknown direction
        _token([1, "a", [1.0], 0, 0, False]),  # sort values of another sort
        _token([1, "a", ["text", 1], 0, 0, False]),  # a text value where a score goes
        _token([1, "a", [1.0, 0], 0, 0, False]),  # an id must be positive
        _token([1, "a", [1.0, True], 0, 0, False]),  # a boolean is not an id
        _token([1, "a", [1.0, 1], -1, 0, False]),  # negative position
        _token([1, "a", [1.0, 1], 0, 0, "no"]),  # the lower-bound flag is a boolean
        base64.urlsafe_b64encode(b'[1,"a",[NaN,1],0,0,false]').decode(),  # Python's json would accept NaN
        base64.urlsafe_b64encode(b'[1,"a",[Infinity,1],0,0,false]').decode(),
    ],
)
def test_anything_else_is_rejected(token: str) -> None:
    with pytest.raises(CursorError):
        decode(token, RELEVANCE)


def test_an_overlong_cursor_is_rejected_before_it_is_decoded() -> None:
    with pytest.raises(CursorError, match="too long"):
        decode("A" * (MAX_CURSOR_LENGTH + 1), RELEVANCE)


def test_an_overlong_text_value_is_rejected() -> None:
    with pytest.raises(CursorError):
        decode(_token([1, "a", ["x" * 600, None, 1], 0, 0, False]), TITLE)
