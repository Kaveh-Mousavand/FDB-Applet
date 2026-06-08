"""
Python conversions of StringAlgebra.kt and GentleAlgebra.kt
"""
from __future__ import annotations
from typing import TypeVar, List, Optional, TYPE_CHECKING

from .monomial_algebra import MonomialAlgebra
from .string_indec_full import StringIndec

if TYPE_CHECKING:
    from ..quiver.quiver import Quiver
    from ..quiver.monomial import Monomial

T = TypeVar("T")
U = TypeVar("U")


class StringAlgebra(MonomialAlgebra[T, U]):
    """
    A string algebra: monomial algebra where at each vertex
    at most 2 arrows start and at most 2 arrows end,
    and for each arrow at most one legal length-2 path starts/ends.

    Raises:
        ValueError if the algebra does not satisfy string algebra axioms.
    """

    def __init__(self, quiver: "Quiver[T, U]", relations: List["Monomial[T, U]"]):
        super().__init__(quiver, relations)
        for vtx in self.vertices:
            out_ = [a for a in self.arrows if a.from_vertex == vtx]
            in_  = [a for a in self.arrows if a.to_vertex == vtx]
            if len(out_) > 2:
                raise ValueError(f"Too many arrows starting at {vtx}")
            if len(in_) > 2:
                raise ValueError(f"Too many arrows ending at {vtx}")
        for ar in self.arrows:
            # at most one legal length-2 path beginning with ar
            continuations = [
                ar.to_word() * b
                for b in self.arrows if b.from_vertex == ar.to_vertex
            ]
            legal_continuations = [p for p in continuations if self.is_legal(p)]
            if len(legal_continuations) > 1:
                raise ValueError(
                    f"Few relations. Both length-2 paths beginning with {ar} are legal."
                )
            # at most one legal length-2 path ending with ar
            predecessors = [
                b.to_word() * ar
                for b in self.arrows if b.to_vertex == ar.from_vertex
            ]
            legal_preds = [p for p in predecessors if self.is_legal(p)]
            if len(legal_preds) > 1:
                raise ValueError(
                    f"Few relations. Both length-2 paths ending with {ar} are legal."
                )

    @classmethod
    def from_monomial(cls, algebra: MonomialAlgebra) -> "StringAlgebra":
        return cls(algebra.quiver, algebra.relations)

    def is_rep_finite(self) -> bool:
        return self.is_word_finite

    def proj_at(self, vtx: T) -> StringIndec:
        strings = self.paths_from(vtx, only_maximal=True)
        if len(strings) == 1:
            return StringIndec.from_word(self, strings[0], check=False)
        if len(strings) == 2:
            return StringIndec.from_word(self, (~strings[0]) * strings[1], check=False)
        raise RuntimeError("Something is wrong in proj_at")

    def inj_at(self, vtx: T) -> StringIndec:
        strings = self.paths_to(vtx, only_maximal=True)
        if len(strings) == 1:
            return StringIndec.from_word(self, strings[0], check=False)
        if len(strings) == 2:
            return StringIndec.from_word(self, strings[0] * (~strings[1]), check=False)
        raise RuntimeError("Something is wrong in inj_at")

    def string_modules(self) -> List[StringIndec]:
        return self.string_indecs(non_isomorphic=True)

    def global_dim(self) -> Optional[int]:
        """
        Approximate global dimension computation.
        Returns None if infinite or not yet computable.
        """
        # Full computation requires projective resolutions — placeholder.
        raise NotImplementedError(
            "global_dim() requires projective resolution support (not yet ported)."
        )


class GentleAlgebra(StringAlgebra[T, U]):
    """
    A gentle algebra: string algebra where every relation has length exactly 2,
    and for each arrow at most one length-2 path starting/ending with it VANISHES.

    Raises:
        ValueError if not a gentle algebra.
    """

    def __init__(self, quiver: "Quiver[T, U]", relations: List["Monomial[T, U]"]):
        super().__init__(quiver, relations)
        for rel in self.relations:
            if rel.length != 2:
                raise ValueError(
                    f"The length of each relation should be 2, got {rel.length} for {rel}."
                )
        for ar in self.arrows:
            # at most one VANISHING length-2 path starting with ar
            continuations = [
                ar.to_word() * b
                for b in self.arrows if b.from_vertex == ar.to_vertex
            ]
            illegal = [p for p in continuations if not self.is_legal(p)]
            if len(illegal) > 1:
                raise ValueError(
                    f"Too many relations: both length-2 paths beginning with {ar} vanish."
                )
            predecessors = [
                b.to_word() * ar
                for b in self.arrows if b.to_vertex == ar.from_vertex
            ]
            illegal_pre = [p for p in predecessors if not self.is_legal(p)]
            if len(illegal_pre) > 1:
                raise ValueError(
                    f"Too many relations: both length-2 paths ending with {ar} vanish."
                )

    @classmethod
    def from_monomial(cls, algebra: MonomialAlgebra) -> "GentleAlgebra":
        return cls(algebra.quiver, algebra.relations)
