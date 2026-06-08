"""
Python conversion of Monomial.kt

Represents a monomial: a path of length > 0 (a non-empty sequence of composable arrows).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import TypeVar, Generic, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .arrow import Arrow
    from .word import Word

T = TypeVar("T")
U = TypeVar("U")


@dataclass
class Monomial(Generic[T, U]):
    """
    A data class representing a monomial: a path of positive length.

    Attributes:
        arrows: non-empty list of composable Arrow objects (all must have labels).
    """

    arrows: List["Arrow[T, U]"]

    def __post_init__(self):
        if not self.arrows:
            raise ValueError("The length of the monomial must be positive.")
        if any(a.label is None for a in self.arrows):
            raise ValueError("Arrow labels are required.")
        for a1, a2 in zip(self.arrows, self.arrows[1:]):
            if a1.to_vertex != a2.from_vertex:
                raise ValueError(
                    f"Target of {a1} and source of {a2} do not coincide."
                )

    @property
    def length(self) -> int:
        return len(self.arrows)

    @property
    def from_vertex(self) -> T:
        return self.arrows[0].from_vertex

    @property
    def to_vertex(self) -> T:
        return self.arrows[-1].to_vertex

    def to_word(self) -> "Word":
        """Converts this monomial to a Word."""
        from .word import Word
        letters = [a.to_letter() for a in self.arrows]
        return Word.from_letters(letters, self.from_vertex, self.to_vertex, check=False)

    def to_list(self) -> List[U]:
        """Returns the list of arrow labels."""
        return [a.label for a in self.arrows]

    def __lt__(self, other: "Monomial") -> bool:
        return self.to_word() < other.to_word()

    def __eq__(self, other) -> bool:
        if not isinstance(other, Monomial):
            return False
        return self.arrows == other.arrows

    def __hash__(self):
        return hash(tuple(self.arrows))

    def __str__(self) -> str:
        return "*".join(str(a) for a in self.arrows)

    def __repr__(self) -> str:
        return f"Monomial({self.arrows!r})"
