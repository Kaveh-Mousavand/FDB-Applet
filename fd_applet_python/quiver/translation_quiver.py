"""
Python conversion of TranslationQuiver.kt

Represents translation quivers (e.g. Auslander-Reiten quivers).
Arrows have no labels (label=None).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TypeVar, Generic, Dict, List, Collection, TYPE_CHECKING

if TYPE_CHECKING:
    from .quiver import Quiver
    from .arrow import Arrow

T = TypeVar("T")


@dataclass
class TranslationQuiver(Generic[T]):
    """
    A translation quiver: a quiver together with a partial translation map tau.

    Attributes:
        quiver: the underlying Quiver (arrows have no labels).
        tau: dict mapping non-projective vertices to their tau-images.
    """

    quiver: "Quiver[T, None]"
    tau: Dict[T, T]

    def __post_init__(self):
        verts = set(self.quiver.vertices)
        if not set(self.tau.keys()) <= verts or not set(self.tau.values()) <= verts:
            raise ValueError("tau should be defined on the vertex set of a quiver.")
        # tau must be injective
        if len(set(self.tau.values())) != len(self.tau):
            raise ValueError("tau should be one-to-one.")
        # Check translation quiver axiom: arrows into v == arrows out of tau(v)
        for vtx, tau_vtx in self.tau.items():
            to_vtx = [a.from_vertex for a in self.quiver.arrows if a.to_vertex == vtx]
            from_tau = [a.to_vertex for a in self.quiver.arrows if a.from_vertex == tau_vtx]
            # Compare as multisets
            def multiset(lst):
                d = {}
                for x in lst:
                    d[x] = d.get(x, 0) + 1
                return d
            if multiset(to_vtx) != multiset(from_tau):
                raise ValueError(
                    f"Arrows to {vtx} and arrows from {tau_vtx} do not correspond."
                )

    @property
    def vertices(self) -> Collection[T]:
        return self.quiver.vertices

    @property
    def tau_minus(self) -> Dict[T, T]:
        """Inverse of tau (maps injective images back to their source)."""
        return {v: k for k, v in self.tau.items()}

    @property
    def projectives(self) -> List[T]:
        """Vertices not in the domain of tau."""
        return [v for v in self.vertices if v not in self.tau]

    @property
    def injectives(self) -> List[T]:
        """Vertices not in the image of tau."""
        return [v for v in self.vertices if v not in self.tau_minus]

    def print_info(self):
        """Prints vertices, arrows, and translation pairs."""
        print("Vertices:")
        print(list(self.vertices))
        print("Arrows:")
        for ar in self.quiver.arrows:
            print(ar.info_string())
        print("Translations:")
        for vtx, tau_vtx in self.tau.items():
            print(f"{vtx} --tau--> {tau_vtx}")

    def to_quiver(self) -> "Quiver[T, None]":
        """
        Returns the underlying quiver with tau-arrows added as extra arrows
        (marked with is_tau=True).
        """
        from .arrow import Arrow
        from .quiver import Quiver
        tau_arrows = [
            Arrow(None, k, v, is_tau=True) for k, v in self.tau.items()
        ]
        return Quiver(
            self.quiver.vertices,
            list(self.quiver.arrows) + tau_arrows,
        )
