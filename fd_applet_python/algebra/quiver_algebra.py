"""
Python conversion of QuiverAlgebra.kt

Abstract base class for algebras defined by a quiver.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from collections import deque
from typing import TypeVar, Generic, List, Optional, Iterator, TYPE_CHECKING

if TYPE_CHECKING:
    from ..quiver.quiver import Quiver
    from ..quiver.word import Word
    from ..quiver.letter import Letter
    from ..quiver.arrow import Arrow

T = TypeVar("T")
U = TypeVar("U")


class QuiverAlgebra(ABC, Generic[T, U]):
    """Abstract base for quiver algebras kQ/I."""

    def __init__(self, quiver: "Quiver[T, U]"):
        self.quiver = quiver
        self.vertices: List[T] = list(quiver.vertices)
        self.arrows = list(quiver.arrows)

    @abstractmethod
    def print_info(self): ...

    @property
    @abstractmethod
    def is_word_finite(self) -> bool: ...

    @abstractmethod
    def is_legal(self, word: "Word[T, U]", check_only_last: bool = False) -> bool: ...

    @abstractmethod
    def string_indecs(self, length_bound: Optional[int] = None, non_isomorphic: bool = True) -> list: ...

    @abstractmethod
    def is_finite_dimensional(self) -> bool: ...

    @abstractmethod
    def dim(self) -> Optional[int]: ...

    @abstractmethod
    def is_string_algebra(self) -> bool: ...

    @abstractmethod
    def is_gentle_algebra(self) -> bool: ...

    @abstractmethod
    def is_rep_finite(self) -> bool: ...

    @abstractmethod
    def proj_at(self, vtx: T): ...

    @abstractmethod
    def inj_at(self, vtx: T): ...

    @abstractmethod
    def simple_at(self, vtx: T): ...

    # ── BFS word enumeration ─────────────────────────────────────────────────

    def words_starting_with(
        self,
        word: "Word[T, U]",
        length_bound: Optional[int] = None,
        add_only_arrow: bool = False,
        add_only_inverse: bool = False,
        only_maximal: bool = False,
    ) -> Iterator["Word[T, U]"]:
        """BFS over all legal words that start with (extend) the given word."""
        if not self.is_legal(word):
            raise ValueError("Invalid word.")
        queue: deque["Word[T, U]"] = deque([word])
        while queue:
            current = queue.popleft()
            if not only_maximal:
                if length_bound is None or current.length <= length_bound:
                    yield current
                else:
                    break
            is_maximal = True
            if not add_only_inverse:
                for ar in (a for a in self.arrows if current.to_vertex == a.from_vertex):
                    candidate = current * ar
                    if self.is_legal(candidate, check_only_last=True):
                        queue.append(candidate)
                        is_maximal = False
            if not add_only_arrow:
                for ar in (a for a in self.arrows if current.to_vertex == a.to_vertex):
                    candidate = current * (~ar)
                    if self.is_legal(candidate, check_only_last=True):
                        queue.append(candidate)
                        is_maximal = False
            if only_maximal and is_maximal:
                yield current

    def words_ending_with(
        self,
        word: "Word[T, U]",
        length_bound: Optional[int] = None,
        add_only_arrow: bool = False,
        add_only_inverse: bool = False,
        only_maximal: bool = False,
    ) -> Iterator["Word[T, U]"]:
        """BFS over all legal words ending with the given word (runs on inverse)."""
        for w in self.words_starting_with(
            ~word, length_bound,
            add_only_arrow=add_only_inverse,
            add_only_inverse=add_only_arrow,
            only_maximal=only_maximal,
        ):
            yield ~w
