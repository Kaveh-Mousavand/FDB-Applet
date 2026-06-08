"""
Python conversion of Word.kt

Represents a sequence of letters with compatible sources and targets.
Note: allows words of the form "a * !a" (checked separately in MonomialAlgebra.is_legal).
"""

from __future__ import annotations
from typing import TypeVar, Generic, List, Iterator, TYPE_CHECKING

if TYPE_CHECKING:
    from .arrow import Arrow
    from .letter import Letter

T = TypeVar("T")
U = TypeVar("U")


class Word(Generic[T, U]):
    """
    Represents a sequence of letters with compatible sources and targets.

    Attributes:
        letters: list of Letter objects (possibly empty for a trivial word).
        from_vertex: source vertex.
        to_vertex: target vertex.
        length: number of letters in the word.
    """

    def __init__(self, letters: List["Letter[T, U]"], from_vertex: T, to_vertex: T):
        self.letters = letters
        self.from_vertex = from_vertex
        self.to_vertex = to_vertex
        self.length = len(letters)

    @classmethod
    def from_letters(
        cls,
        letters: List["Letter[T, U]"],
        from_vertex: T,
        to_vertex: T,
        check: bool = True,
    ) -> "Word[T, U]":
        """
        Creates a Word, optionally validating the letter sequence.

        Args:
            letters: list of letters.
            from_vertex: expected source vertex.
            to_vertex: expected target vertex.
            check: if True, validates the word structure.
        Returns:
            a new Word instance.
        Raises:
            ValueError: if check=True and the word is invalid.
        """
        if check:
            if not letters:
                if from_vertex != to_vertex:
                    raise ValueError("Source and target of a trivial word should coincide.")
            else:
                if letters[0].from_vertex != from_vertex or letters[-1].to_vertex != to_vertex:
                    raise ValueError("Source or target of a word doesn't match.")
                for a, b in zip(letters, letters[1:]):
                    if a.to_vertex != b.from_vertex:
                        raise ValueError(
                            f"Target of {a} and source of {b} don't coincide."
                        )
        return cls(letters, from_vertex, to_vertex)

    def __getitem__(self, n: int) -> "Letter[T, U]":
        return self.letters[n]

    def __str__(self) -> str:
        if not self.letters:
            return str(self.to_vertex)
        return "*".join(str(l) for l in self.letters)

    def __repr__(self) -> str:
        return f"Word({self.letters!r}, from={self.from_vertex!r}, to={self.to_vertex!r})"

    def info_string(self) -> str:
        """Returns a verbose string showing all traversed vertices."""
        if not self.letters:
            return f"{self.from_vertex} (trivial word)"
        path = " ".join(str(l) for l in self.letters)
        traversal = str(self.from_vertex)
        for letter in self.letters:
            traversal += f" --{letter}--> {letter.to_vertex}"
        return f"{path}: {traversal}"

    def __mul__(self, other) -> "Word[T, U]":
        """Concatenates this word with an Arrow, Letter, or Word."""
        from .arrow import Arrow
        from .letter import Letter
        if isinstance(other, Arrow):
            return self * other.to_word()
        if isinstance(other, Letter):
            return self * other.to_word()
        if isinstance(other, Word):
            if self.to_vertex != other.from_vertex:
                raise ValueError("Cannot concatenate: target of first != source of second.")
            return Word(self.letters + other.letters, self.from_vertex, other.to_vertex)
        return NotImplemented

    def __invert__(self) -> "Word[T, U]":
        """Returns the inverse of this word (reverses letters and inverts each)."""
        return Word(
            [~l for l in reversed(self.letters)],
            self.to_vertex,
            self.from_vertex,
        )

    def get_vertex_at(self, index: int) -> T:
        """Returns the vertex visited at position [index]."""
        if index == 0:
            return self.from_vertex
        return self.letters[index - 1].to_vertex

    def vertex_list(self) -> List[T]:
        """Returns all vertices visited in order."""
        return [l.from_vertex for l in self.letters] + [self.to_vertex]

    def support(self) -> set:
        """Returns the set of vertices visited."""
        return set(self.vertex_list())

    def drop(self, n: int) -> "Word[T, U]":
        """Drops the first n letters."""
        return self.sub_word(n, self.length)

    def drop_last(self, n: int) -> "Word[T, U]":
        """Drops the last n letters."""
        return self.sub_word(0, self.length - n)

    def sub_word(self, i: int, j: int) -> "Word[T, U]":
        """
        Returns the substring from index i to j (exclusive of j-th letter, half-open [i,j)).

        If i == j, returns the trivial word at that position's vertex.
        """
        if not (0 <= i <= j <= self.length):
            raise ValueError(f"Invalid indices: i={i}, j={j}, length={self.length}")
        if self.length == 0:
            return self
        if i < j:
            sub = self.letters[i:j]
            return Word.from_letters(sub, sub[0].from_vertex, sub[-1].to_vertex, check=False)
        if i == j == self.length:
            return _trivial_word(self.to_vertex)
        return _trivial_word(self.letters[i].from_vertex)

    def take(self, i: int) -> "Word[T, U]":
        """Takes the first i letters."""
        return self.sub_word(0, i)

    def take_last(self, i: int) -> "Word[T, U]":
        """Takes the last i letters."""
        return self.sub_word(self.length - i, self.length)

    def __lt__(self, other: "Word") -> bool:
        # Trivial words compared by vertex label
        if self.length == 0 and other.length == 0:
            s, o = str(self.from_vertex), str(other.from_vertex)
            try:
                return int(s) < int(o)
            except ValueError:
                return s < o
        if self.length != other.length:
            return self.length < other.length
        for a, b in zip(self.letters, other.letters):
            if a != b:
                return a < b
        return False

    def __eq__(self, other) -> bool:
        if not isinstance(other, Word):
            return False
        return (self.letters == other.letters and
                self.from_vertex == other.from_vertex and
                self.to_vertex == other.to_vertex)

    def __hash__(self):
        return hash((tuple(self.letters), self.from_vertex, self.to_vertex))

    def __le__(self, other):
        return self == other or self < other


def _trivial_word(vertex) -> Word:
    """Creates a trivial (empty) word at the given vertex."""
    return Word.from_letters([], vertex, vertex, check=False)


def to_trivial_word(vertex) -> Word:
    """Extension: creates a trivial word from a vertex (mirrors Kotlin extension fun)."""
    return _trivial_word(vertex)


def letters_to_word(letters: list, check: bool = True) -> Word:
    """Extension: constructs a Word from a list of Letters."""
    return Word.from_letters(letters, letters[0].from_vertex, letters[-1].to_vertex, check=check)
