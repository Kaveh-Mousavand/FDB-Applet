"""
Python conversions of:
  - PowerSet.kt  (power_set_list utility)
  - ListWithLeq.kt (ListWithLeq data class)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TypeVar, Generic, List, Set, Tuple, Collection, TYPE_CHECKING

if TYPE_CHECKING:
    from ..quiver.quiver import Quiver

T = TypeVar("T")
U = TypeVar("U")


# ── PowerSet ──────────────────────────────────────────────────────────────────

def power_set_list(items: Collection[T], include: Collection[T] = ()) -> List[List[T]]:
    """
    Returns all subsets (as lists) of [items] that contain every element in [include].
    [include] is assumed to be a subset of [items] (not checked).

    Python conversion of Collection<T>.powerSetList() in PowerSet.kt.
    """
    include = list(include)
    acc: List[List[T]] = [include[:]]
    for elem in items:
        if elem not in include:
            acc = acc + [subset + [elem] for subset in acc]
    return acc


# ── ListWithLeq ───────────────────────────────────────────────────────────────

class ListWithLeq(Generic[T]):
    """
    A list of elements together with a binary relation ≤ (leqs).

    leqs is a set of (x, y) pairs meaning x ≤ y.

    Python conversion of ListWithLeq<T> in ListWithLeq.kt.
    """

    def __init__(
        self,
        elements: List[T],
        leqs: Set[Tuple[T, T]],
        always_poset: bool = True,
    ):
        self.elements = elements
        self.leqs = leqs
        self.always_poset = always_poset

    # ── delegate list behaviour ──────────────────────────────────────────────

    def __iter__(self):
        return iter(self.elements)

    def __len__(self):
        return len(self.elements)

    def __getitem__(self, index):
        return self.elements[index]

    def __contains__(self, item):
        return item in self.elements

    # ── relation helpers ─────────────────────────────────────────────────────

    def leq(self, x: T, y: T) -> bool:
        """Returns True if x ≤ y."""
        return (x, y) in self.leqs

    def geq(self, x: T, y: T) -> bool:
        """Returns True if x ≥ y (i.e. y ≤ x)."""
        return (y, x) in self.leqs

    def down(self, x: T) -> List[T]:
        """Returns all elements e with e ≤ x."""
        if x not in self.elements:
            raise ValueError(f"{x!r} is not in elements.")
        return [e for e in self.elements if self.leq(e, x)]

    def up(self, x: T) -> List[T]:
        """Returns all elements e with e ≥ x."""
        if x not in self.elements:
            raise ValueError(f"{x!r} is not in elements.")
        return [e for e in self.elements if self.geq(e, x)]

    # ── poset check ──────────────────────────────────────────────────────────

    def is_poset(self) -> bool:
        """
        Returns True iff the relation is a partial order:
        reflexive, antisymmetric, and transitive.
        """
        for x in self.elements:
            if not self.leq(x, x):
                return False
            for y in self.down(x):   # y ≤ x
                if self.leq(x, y) and x != y:   # antisymmetry violation
                    return False
                for z in self.down(y):  # z ≤ y
                    if not self.leq(z, x):       # transitivity violation
                        return False
        return True

    # ── Hasse quiver ─────────────────────────────────────────────────────────

    def hasse_quiver(self) -> "Quiver":
        """
        Returns the Hasse quiver of this partial order.
        Vertices are elements; there is an arrow x → y iff x > y and no z with x > z > y.
        """
        from ..quiver.arrow import Arrow
        from ..quiver.quiver import Quiver

        if not self.always_poset and not self.is_poset():
            raise ValueError("This is not a poset!")

        arrows = []
        for x in self.elements:
            for y in self.down(x):   # y ≤ x
                if x == y:
                    continue         # skip reflexive pairs
                # interval between y and x must be exactly {y, x}
                mid = [e for e in self.elements if self.leq(y, e) and self.leq(e, x)]
                if len(mid) == 2:    # only y and x in the interval → covering relation
                    arrows.append(Arrow(x, y))
        return Quiver(self.elements, arrows)


# ── Extension: List[Collection[T]] → ListWithLeq ────────────────────────────

def collections_to_list_with_leq(collections: List[Collection[T]]) -> "ListWithLeq[Collection[T]]":
    """
    Builds a ListWithLeq from a list of collections, ordered by inclusion.
    c1 ≤ c2 iff c2 contains all elements of c1.

    Python conversion of List<U>.toListWithLeq() in ListWithLeq.kt.
    """
    leqs: Set[Tuple] = set()
    for c1 in collections:
        for c2 in collections:
            if all(item in c2 for item in c1):
                leqs.add((c1, c2))          # type: ignore[arg-type]
    return ListWithLeq(collections, leqs)   # type: ignore[arg-type]
