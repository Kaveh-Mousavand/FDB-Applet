"""
Python conversion of Quiver.kt

Represents a finite quiver (directed graph) with typed vertex and arrow labels.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TypeVar, Generic, List, Collection, Optional, Iterator, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from .arrow import Arrow
    from .word import Word

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")


@dataclass
class Quiver(Generic[T, U]):
    """
    A data class representing a finite quiver.

    Attributes:
        vertices: collection of vertex labels.
        arrows: collection of Arrow objects.
    """

    vertices: Collection[T]
    arrows: Collection["Arrow[T, U]"]

    def __post_init__(self):
        for arrow in self.arrows:
            if arrow.from_vertex not in self.vertices:
                raise ValueError(f"Source of {arrow}: {arrow.from_vertex} is not a vertex.")
            if arrow.to_vertex not in self.vertices:
                raise ValueError(f"Target of {arrow}: {arrow.to_vertex} is not a vertex.")

    def print_info(self):
        """Prints the quiver's vertices and arrows."""
        print("Vertices:")
        print(list(self.vertices))
        print("Arrows:")
        for ar in self.arrows:
            print(ar.info_string())

    def arrow_of_label(self, arrow_label: U) -> "Arrow[T, U]":
        """Returns the arrow with the given label, or raises if not found."""
        result = next((a for a in self.arrows if a.label == arrow_label), None)
        if result is None:
            raise ValueError(f"Arrow of label {arrow_label} doesn't exist.")
        return result

    def _path_dfs(self, current_path: "Word[T, U]") -> Iterator["Word[T, U]"]:
        """Recursive DFS yielding all paths starting from current_path."""
        yield current_path
        for arrow in (a for a in self.arrows if current_path.to_vertex == a.from_vertex):
            yield from self._path_dfs(current_path * arrow)

    def _maximal_path_dfs(self, current_path: "Word[T, U]") -> Iterator["Word[T, U]"]:
        """Recursive DFS yielding all maximal (non-extendable) paths from current_path."""
        next_arrows = [a for a in self.arrows if current_path.to_vertex == a.from_vertex]
        if not next_arrows:
            yield current_path
        else:
            for arrow in next_arrows:
                yield from self._maximal_path_dfs(current_path * arrow)

    def _paths_sequence_from(self, vtx: T) -> Iterator["Word[T, U]"]:
        """All paths starting at vtx (possibly infinite for cyclic quivers)."""
        from .word import to_trivial_word
        yield from self._path_dfs(to_trivial_word(vtx))

    def _maximal_paths_sequence_from(self, vtx: T) -> Iterator["Word[T, U]"]:
        """All maximal paths starting at vtx."""
        from .word import to_trivial_word
        yield from self._maximal_path_dfs(to_trivial_word(vtx))

    def _cycle_dfs(
        self, current_path: "Word[T, U]", visited: List[T]
    ) -> Iterator["Word[T, U]"]:
        """DFS for simple cycles. Stops expanding when reaching a visited vertex."""
        if current_path.to_vertex not in visited:
            vertex_list = current_path.vertex_list()
            index = vertex_list.index(current_path.to_vertex)
            if index != len(vertex_list) - 1:  # revisiting a vertex
                if index == 0:  # it's a cycle back to start
                    yield current_path
            else:  # still a simple path — expand
                for arrow in (a for a in self.arrows if current_path.to_vertex == a.from_vertex):
                    yield from self._cycle_dfs(current_path * arrow, visited)

    def simple_cycles(self) -> Iterator["Word[T, U]"]:
        """
        Yields all simple cycles (each cycle reported once via canonical starting vertex).
        A simple cycle visits no vertex more than once, except start == end.
        """
        from .word import to_trivial_word
        checked: List[T] = []
        for vtx in self.vertices:
            if vtx not in checked:
                yield from self._cycle_dfs(to_trivial_word(vtx), checked)
                checked.append(vtx)

    def primitive_cycle_finite(self) -> bool:
        """
        Returns True if there are finitely many primitive cycles.
        This holds iff no two simple cycles share a common vertex.
        """
        seen = set()
        for vtx in (v for cycle in self.simple_cycles() for v in cycle.support()):
            if vtx in seen:
                return False
            seen.add(vtx)
        return True

    def is_acyclic(self, vtx: Optional[T] = None) -> bool:
        """
        Returns True if the quiver is acyclic (no directed cycles).
        If vtx is given, checks only that vtx has finitely many paths.
        """
        check_list = list(self.vertices) if vtx is None else [vtx]
        for v in check_list:
            # A path with a repeated vertex implies a cycle
            bad = next(
                (p for p in self._paths_sequence_from(v)
                 if len(p.support()) != len(p.vertex_list())),
                None,
            )
            if bad is not None:
                return False
        return True

    def paths_from(
        self, vtx: T, only_maximal: bool = False, check: bool = True
    ) -> List["Word[T, U]"]:
        """
        Returns all paths starting at vtx.

        Args:
            vtx: starting vertex.
            only_maximal: if True, return only non-extendable paths.
            check: if True, raises if there are infinitely many paths.
        Raises:
            ValueError: if check=True and the quiver has cycles from vtx.
        """
        if check and not self.is_acyclic(vtx):
            raise ValueError("There are infinitely many paths.")
        seq = (
            self._maximal_paths_sequence_from(vtx)
            if only_maximal
            else self._paths_sequence_from(vtx)
        )
        return list(seq)

    def map_vertices(self, f: Callable[[T], V]) -> "Quiver[V, U]":
        """
        Returns a new quiver with vertices mapped by f.

        Args:
            f: function mapping old vertex labels to new ones.
        """
        from .arrow import Arrow
        return Quiver(
            [f(v) for v in self.vertices],
            [Arrow(a.label, f(a.from_vertex), f(a.to_vertex)) for a in self.arrows],
        )
