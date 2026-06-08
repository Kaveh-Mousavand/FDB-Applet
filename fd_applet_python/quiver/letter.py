"""
Python conversion of Letter.kt

Represents letters: arrows and their inverses.
For example, given Arrow(from_vertex="1", to_vertex="2", label="a") i.e. "a: 1 -> 2",
  Letter(arrow, is_arrow=True)  represents "a"
  Letter(arrow, is_arrow=False) represents the inverse of "a", denoted "!a".
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import TypeVar, Generic, TYPE_CHECKING

if TYPE_CHECKING:
    from .arrow import Arrow
    from .word import Word

T = TypeVar("T")
U = TypeVar("U")


@dataclass
class Letter(Generic[T, U]):
    """
    A data class representing letters: arrows and their inverses.

    Attributes:
        arrow: the underlying arrow (same object for both arrow and its inverse).
        is_arrow: True if this letter is the arrow; False if it's the inverse.
    """

    arrow: "Arrow[T, U]"
    is_arrow: bool = True

    @property
    def label(self) -> U:
        """The label of this letter (same as the arrow's label)."""
        if self.arrow.label is None:
            raise ValueError("A label is required for letters.")
        return self.arrow.label

    @property
    def from_vertex(self) -> T:
        """Source vertex (arrow's target if this is an inverse)."""
        return self.arrow.from_vertex if self.is_arrow else self.arrow.to_vertex

    @property
    def to_vertex(self) -> T:
        """Target vertex (arrow's source if this is an inverse)."""
        return self.arrow.to_vertex if self.is_arrow else self.arrow.from_vertex

    def __lt__(self, other: "Letter") -> bool:
        if other.is_arrow != self.is_arrow:
            return self.is_arrow  # arrow < inverse
        return str(self.label) < str(other.label)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Letter):
            return False
        return self.arrow == other.arrow and self.is_arrow == other.is_arrow

    def __hash__(self):
        return hash((self.arrow, self.is_arrow))

    def __str__(self) -> str:
        if self.is_arrow:
            return str(self.label)
        return "!" + str(self.label)

    def __repr__(self) -> str:
        return f"Letter({self.arrow!r}, is_arrow={self.is_arrow})"

    def __invert__(self) -> "Letter[T, U]":
        """Returns the inverse of this letter."""
        return Letter(self.arrow, not self.is_arrow)

    def __mul__(self, other) -> "Word":
        """Concatenates this letter with another arrow, letter, or word."""
        return self.to_word() * other

    def to_word(self) -> "Word":
        """Converts this letter to a single-letter word."""
        from .word import Word
        return Word.from_letters([self], self.from_vertex, self.to_vertex, check=False)

    def info_string(self) -> str:
        """Returns a descriptive string with source, target, and label information."""
        return f"{self}: {self.from_vertex} ----> {self.to_vertex}"
