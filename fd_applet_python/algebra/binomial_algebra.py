"""
Python conversion of BinomialAlgebra.kt + JSON serialization helpers.

Loads algebras from the same .json format used by the original fd-applet.
"""
from __future__ import annotations
import json
from typing import List, Tuple, Optional, Dict, Any

from .monomial_algebra import MonomialAlgebra
from .quiver_algebra import QuiverAlgebra
from ..quiver.arrow import Arrow
from ..quiver.quiver import Quiver
from ..quiver.monomial import Monomial


# ── Binomial Algebra ──────────────────────────────────────────────────────────

class BinomialAlgebra(QuiverAlgebra):
    """
    Binomial algebra = monomial algebra + commutativity relations p = q.

    Args:
        over_algebra: the underlying monomial algebra (for monomial relations).
        bi_relations: list of (Monomial, Monomial) pairs meaning path1 = path2.
    """

    def __init__(
        self,
        over_algebra: MonomialAlgebra,
        bi_relations: List[Tuple[Monomial, Monomial]],
    ):
        super().__init__(over_algebra.quiver)
        self.over_algebra = over_algebra
        self.bi_relations = bi_relations
        for p, q in bi_relations:
            if p.from_vertex != q.from_vertex:
                raise ValueError(f"Sources of {p} and {q} don't coincide.")
            if p.to_vertex != q.to_vertex:
                raise ValueError(f"Targets of {p} and {q} don't coincide.")
            if not over_algebra.is_legal(p.to_word()):
                raise ValueError(f"{p} vanishes in the monomial algebra.")
            if not over_algebra.is_legal(q.to_word()):
                raise ValueError(f"{q} vanishes in the monomial algebra.")
            if p.length < 2:
                raise ValueError(f"{p} is an arrow, not a path.")
            if q.length < 2:
                raise ValueError(f"{q} is an arrow, not a path.")
            if p == q:
                raise ValueError("Trivial commutativity relation.")

    @property
    def is_word_finite(self) -> bool:
        return self.over_algebra.is_word_finite

    def print_info(self):
        print("A binomial algebra with quiver:")
        self.quiver.print_info()
        print("---- monomial relations ----")
        print(self.over_algebra.relations)
        print("---- commutativity relations ----")
        for p, q in self.bi_relations:
            print(f"  {p} = {q}")

    def is_legal(self, word, check_only_last=False):
        return self.over_algebra.is_legal(word, check_only_last)

    def is_finite_dimensional(self):
        return self.over_algebra.is_finite_dimensional()

    def dim(self):
        return self.over_algebra.dim()

    def is_string_algebra(self):
        return False  # BinomialAlgebra with bi-relations is not a string algebra

    def is_gentle_algebra(self):
        return False  # BinomialAlgebra with bi-relations is never gentle

    def is_rep_finite(self):
        raise NotImplementedError

    def proj_at(self, vtx):
        raise NotImplementedError

    def inj_at(self, vtx):
        raise NotImplementedError

    def simple_at(self, vtx):
        return self.over_algebra.simple_at(vtx)

    def string_indecs(self, length_bound=None, non_isomorphic=True):
        raise NotImplementedError

    def make(self) -> QuiverAlgebra:
        """Return the most specific algebra type."""
        if not self.bi_relations:
            return self.over_algebra.make()
        return self  # SbAlgebra not yet ported


# ── JSON loader ───────────────────────────────────────────────────────────────

def _quiver_from_dict(d: Dict[str, Any]) -> Quiver:
    """Parse a quiver from its JSON dict representation."""
    vertices = d["vertices"]
    arrows = [
        Arrow(a["from"], a["to"], label=a["label"])
        for a in d["arrows"]
    ]
    return Quiver(vertices, arrows)


def _monomial_from_labels(quiver: Quiver, labels: List[str]) -> Monomial:
    """Build a Monomial from a list of arrow label strings."""
    arrows = [quiver.arrow_of_label(lbl) for lbl in labels]
    return Monomial(arrows)


def load_algebra_from_json(path: str) -> QuiverAlgebra:
    """
    Load a fd-applet algebra from a JSON file.

    The format is:
    {
      "quiver": { "vertices": [...], "arrows": [{"label":..,"from":..,"to":..}, ...] },
      "monoRelations": [ ["a","b"], ... ],
      "biRelations":   [ {"first": [...], "second": [...]}, ... ]
    }

    Returns the most specific algebra type (GentleAlgebra > StringAlgebra > MonomialAlgebra
    > BinomialAlgebra).
    """
    with open(path) as f:
        data = json.load(f)

    quiver = _quiver_from_dict(data["quiver"])
    mono_rels = [_monomial_from_labels(quiver, r) for r in data.get("monoRelations", [])]
    mono_alg = MonomialAlgebra(quiver, mono_rels)

    raw_bi = data.get("biRelations", [])
    if raw_bi:
        bi_rels = [
            (
                _monomial_from_labels(quiver, br["first"]),
                _monomial_from_labels(quiver, br["second"]),
            )
            for br in raw_bi
        ]
        bi_alg = BinomialAlgebra(mono_alg, bi_rels)
        return bi_alg.make()

    return mono_alg.make()


def load_algebra_from_dict(data: Dict[str, Any]) -> QuiverAlgebra:
    """Load an algebra directly from a parsed JSON dict."""
    import tempfile, json, os
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        tmp_path = f.name
    try:
        return load_algebra_from_json(tmp_path)
    finally:
        os.unlink(tmp_path)
