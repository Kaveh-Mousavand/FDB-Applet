"""
Fringed algebra construction for gentle algebras.

References:
  Brüstle, Douville, Mousavand, Thomas, Yıldırım,
  "On the combinatorics of gentle algebras", Section 3.

For a gentle algebra A = kQ/I we build the fringed quiver Q̂ by adding
fringe vertices so every original vertex of Q has exactly two incoming
and two outgoing arrows in Q̂. The fringed ideal Î extends I with
quadratic zero relations so that Â = kQ̂/Î is again gentle.
"""

from __future__ import annotations
from typing import List, Tuple, Dict, Any


def fringed_algebra_data(alg) -> Dict[str, Any]:
    """Compute the fringed quiver Q̂ and ideal Î for a gentle algebra A=kQ/I.

    Returns a dict with:
      - is_gentle: True / False
      - original_vertices, original_arrows
      - fringe_vertices: list of new vertex labels added by fringing
      - fringe_arrow_labels: list of new arrow labels added by fringing
      - all_vertices, all_arrows: the vertices and arrows of Q̂
      - relations_I: list of (β, γ) labels — the quadratic zero relations of I
      - relations_I_hat_minus_I: list of (β, γ) labels — relations added to Î
      - error (optional): explanation if not gentle
    """
    if not getattr(alg, "is_gentle_algebra", lambda: False)():
        return {
            "is_gentle": False,
            "error": "The input algebra is not gentle. "
                     "This function works only for gentle algebras.",
        }

    Q_vertices = [str(v) for v in alg.vertices]
    Q_arrows = []  # list of (label, src, tgt) tuples
    for a in alg.arrows:
        Q_arrows.append((str(a.label), str(a.from_vertex), str(a.to_vertex)))

    # Read original quadratic relations (every gentle relation is length 2).
    I_relations: List[Tuple[str, str]] = []
    for rel in alg.relations:
        try:
            arrs = list(rel.arrows)
            if len(arrs) == 2:
                I_relations.append((str(arrs[0].label), str(arrs[1].label)))
        except Exception:
            pass
    I_set = set(I_relations)

    # ── Fringing ────────────────────────────────────────────────────────────
    Qhat_vertices = list(Q_vertices)
    Qhat_arrows = list(Q_arrows)
    new_relations: List[Tuple[str, str]] = []
    fringe_vertices: List[str] = []
    fringe_arrows: List[str] = []

    next_v_idx = 1

    def fresh_vertex():
        nonlocal next_v_idx
        while True:
            name = f"f{next_v_idx}"
            next_v_idx += 1
            if name not in Qhat_vertices:
                return name

    next_a_idx = 1

    def fresh_arrow_label():
        nonlocal next_a_idx
        while True:
            name = f"φ{next_a_idx}"  # φ1, φ2, ...
            next_a_idx += 1
            if not any(a[0] == name for a in Qhat_arrows):
                return name

    def has_legal(beta_label: str, gamma_label: str) -> bool:
        return (beta_label, gamma_label) not in I_set

    def is_zero(beta_label: str, gamma_label: str) -> bool:
        return (beta_label, gamma_label) in I_set

    for v in Q_vertices:
        in_v = [(lab, src) for (lab, src, tgt) in Qhat_arrows if tgt == v]
        out_v = [(lab, tgt) for (lab, src, tgt) in Qhat_arrows if src == v]

        # Add incoming fringe arrows to fill in_v up to 2.
        while len(in_v) < 2:
            f = fresh_vertex()
            new_lab = fresh_arrow_label()
            Qhat_vertices.append(f)
            Qhat_arrows.append((new_lab, f, v))
            fringe_vertices.append(f)
            fringe_arrows.append(new_lab)

            # For each existing out-arrow γ of v, decide whether new_lab*γ is
            # zero or legal in Î, respecting gentleness.
            for gamma_label, _gtgt in list(out_v):
                existing_legal = any(
                    has_legal(beta_label, gamma_label) for beta_label, _ in in_v
                )
                existing_zero = any(
                    is_zero(beta_label, gamma_label) for beta_label, _ in in_v
                )
                if existing_legal and not existing_zero:
                    # need new_lab * γ to be the zero relation
                    new_relations.append((new_lab, gamma_label))
                    I_set.add((new_lab, gamma_label))
                # else: leave legal (no relation added)
            in_v.append((new_lab, f))

        # Add outgoing fringe arrows to fill out_v up to 2.
        while len(out_v) < 2:
            f = fresh_vertex()
            new_lab = fresh_arrow_label()
            Qhat_vertices.append(f)
            Qhat_arrows.append((new_lab, v, f))
            fringe_vertices.append(f)
            fringe_arrows.append(new_lab)

            for beta_label, _bsrc in list(in_v):
                existing_legal = any(
                    has_legal(beta_label, gamma_label) for gamma_label, _ in out_v
                )
                existing_zero = any(
                    is_zero(beta_label, gamma_label) for gamma_label, _ in out_v
                )
                if existing_legal and not existing_zero:
                    new_relations.append((beta_label, new_lab))
                    I_set.add((beta_label, new_lab))
            out_v.append((new_lab, f))

    return {
        "is_gentle": True,
        "original_vertices": Q_vertices,
        "original_arrows": [
            {"label": lab, "from": src, "to": tgt}
            for (lab, src, tgt) in Q_arrows
        ],
        "fringe_vertices": fringe_vertices,
        "fringe_arrow_labels": fringe_arrows,
        "all_vertices": Qhat_vertices,
        "all_arrows": [
            {"label": lab, "from": src, "to": tgt,
             "is_fringe": lab in set(fringe_arrows)}
            for (lab, src, tgt) in Qhat_arrows
        ],
        "relations_I": [{"first": b, "second": g} for (b, g) in I_relations],
        "relations_I_hat_minus_I": [
            {"first": b, "second": g} for (b, g) in new_relations
        ],
    }
