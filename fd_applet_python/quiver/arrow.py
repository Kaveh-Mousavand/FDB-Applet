"""
Python conversion of Arrow.kt

Represents arrows in a quiver.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TypeVar, Generic, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .letter import Letter
    from .word import Word

T = TypeVar("T")
U = TypeVar("U")


@dataclass
class Arrow(Generic[T, U]):
    """
    A data class representing arrows in a quiver.

    Attributes:
        from_vertex: the source vertex of the arrow.
        to_vertex: the target vertex of the arrow.
        label: the label of the arrow. If None, the arrow is anonymous
               (especially useful for translation quivers).
        is_tau: if True, this arrow represents a translation arrow.
    """

    from_vertex: T
    to_vertex: T
    label: Optional[U] = None
    is_tau: bool = False

    def to_letter(self) -> "Letter":
        """Converts this arrow into a letter."""
        from .letter import Letter
        return Letter(self, is_arrow=True)

    def to_word(self) -> "Word":
        """Converts this arrow into a single-letter word."""
        return self.to_letter().to_word()

    def __invert__(self) -> "Letter":
        """Returns the negation (inverse) of this arrow as a letter."""
        return self.to_letter().__invert__()

    def __mul__(self, other) -> "Word":
        """
        Concatenates this arrow with another arrow, letter, or word.

        Args:
            other: an Arrow, Letter, or Word to concatenate with.
        Returns:
            a Word representing the concatenation.
        """
        return self.to_word() * other

    def __str__(self) -> str:
        return str(self.label)

    def __repr__(self) -> str:
        return f"Arrow(label={self.label!r}, from={self.from_vertex!r}, to={self.to_vertex!r})"

    def info_string(self) -> str:
        """Returns a descriptive string with source, target, and label information."""
        if self.label is None and not self.is_tau:
            return f"{self.from_vertex} ----> {self.to_vertex}"
        elif self.label is None:
            return f"(translation) {self.from_vertex} ----> {self.to_vertex}"
        else:
            return f"{self.label}: {self.from_vertex} ----> {self.to_vertex}"

    def __hash__(self):
        return hash((self.label, self.from_vertex, self.to_vertex, self.is_tau))

    def __eq__(self, other):
        if not isinstance(other, Arrow):
            return False
        return (self.label == other.label and
                self.from_vertex == other.from_vertex and
                self.to_vertex == other.to_vertex and
                self.is_tau == other.is_tau)
