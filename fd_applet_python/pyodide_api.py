"""Pyodide-friendly dispatcher mirroring server.py endpoints.

This module provides a single `dispatch(path, body)` entry point that the
browser JS calls. Inside Pyodide we never need fastapi/uvicorn — we just
call the algebra functions directly.
"""

from __future__ import annotations
import json
import os
import tempfile
from typing import Any, Dict, List, Optional

from fd_applet_python.algebra.binomial_algebra import (
    load_algebra_from_json,
    MonomialAlgebra,
    BinomialAlgebra,
)
from fd_applet_python.algebra.string_algebra import StringAlgebra, GentleAlgebra
from fd_applet_python.algebra.rf_algebra import RfAlgebra, build_rf_algebra
from fd_applet_python.algebra.fringed import fringed_algebra_data

_state: Dict[str, Any] = {"algebra": None, "rf_algebra": None}


def _algebra_type_name(alg) -> str:
    if isinstance(alg, GentleAlgebra):    return "GentleAlgebra"
    if isinstance(alg, StringAlgebra):    return "StringAlgebra"
    if isinstance(alg, BinomialAlgebra):  return "BinomialAlgebra"
    if isinstance(alg, MonomialAlgebra):  return "MonomialAlgebra"
    return type(alg).__name__


def _get_alg():
    alg = _state.get("algebra")
    if alg is None:
        raise RuntimeError("No algebra loaded. Call POST /algebra first.")
    return alg


def _get_rf() -> RfAlgebra:
    rf = _state.get("rf_algebra")
    if rf is not None:
        return rf
    alg = _get_alg()
    if not isinstance(alg, StringAlgebra):
        raise RuntimeError("Current algebra is not a string algebra.")
    if not alg.is_rep_finite():
        raise RuntimeError("Algebra is representation-infinite. RF operations unavailable.")
    rf = build_rf_algebra(alg)
    _state["rf_algebra"] = rf
    return rf


def _module_info(m, alg):
    pd = m.proj_dim() if isinstance(alg, StringAlgebra) else None
    id_ = m.inj_dim() if isinstance(alg, StringAlgebra) else None
    return {
        "name": str(m),
        "dim": m.dim(),
        "is_projective": m.is_projective() if isinstance(alg, StringAlgebra) else False,
        "is_injective": m.is_injective() if isinstance(alg, StringAlgebra) else False,
        "is_brick": m.is_brick() if isinstance(alg, StringAlgebra) else False,
        "top_vertices": m.top_vertices() if isinstance(alg, StringAlgebra) else [],
        "socle_vertices": m.socle_vertices() if isinstance(alg, StringAlgebra) else [],
        "proj_dim": pd,
        "inj_dim": id_,
    }


def post_algebra(body: dict) -> dict:
    raw = {
        "quiver": {"vertices": body["quiver"]["vertices"],
                   "arrows":   body["quiver"]["arrows"]},
        "monoRelations": body.get("monoRelations", []),
        "biRelations":   [{"first": br["first"], "second": br["second"]}
                          for br in body.get("biRelations", [])],
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(raw, f); tmp = f.name
    try:
        alg = load_algebra_from_json(tmp)
    finally:
        os.unlink(tmp)
    _state["algebra"] = alg
    _state["rf_algebra"] = None
    return {"loaded": _algebra_type_name(alg), "vertices": list(alg.vertices)}


def get_algebra_info() -> dict:
    alg = _get_alg()
    is_string = isinstance(alg, StringAlgebra)
    num_indecs = None
    is_rep_finite = None
    if is_string:
        try:
            is_rep_finite = alg.is_rep_finite()
            if is_rep_finite:
                num_indecs = len(alg.string_indecs(non_isomorphic=True))
        except Exception:
            pass
    return {
        "type": _algebra_type_name(alg),
        "vertices": list(alg.vertices),
        "num_arrows": len(list(alg.arrows)),
        "is_finite_dimensional": alg.is_finite_dimensional(),
        "dimension": alg.dim(),
        "is_string": is_string,
        "is_gentle": isinstance(alg, GentleAlgebra),
        "is_rep_finite": is_rep_finite,
        "num_indecs": num_indecs,
    }


def _matrix_payload(modules, table, sparse: bool):
    if not sparse:
        return {"modules": modules, "table": table}
    nz = []
    for i, row in enumerate(table):
        for j, v in enumerate(row):
            if v is not None and v != 0:
                nz.append([i, j, v])
    return {"modules": modules, "nonzero": nz, "n": len(modules), "sparse": True}


# ── Route table ─────────────────────────────────────────────────────────────

def dispatch(path: str, body=None, query: Optional[dict] = None):
    """Main entry — mirrors the FastAPI server routes."""
    query = query or {}
    sparse = str(query.get("sparse", "")).lower() == "true"

    # ── Algebra loading and info ───────────────────────────────────────────
    if path == "/algebra" and body is not None:
        return post_algebra(body)
    if path == "/algebra/info":
        return get_algebra_info()
    if path == "/algebra/dimensions":
        rf = _get_rf()
        return {
            "global_dim":         rf.global_dim(),
            "finitistic_dim":     rf.finitistic_dim(),
            "right_self_inj_dim": rf.right_self_inj_dim(),
            "left_self_inj_dim":  rf.left_self_inj_dim(),
            "dominant_dim":       rf.dominant_dim(),
            "is_ig":              rf.is_ig(),
            "is_self_injective":  rf.is_self_injective(),
        }

    # ── Module enumeration ─────────────────────────────────────────────────
    if path == "/modules/indecs":
        alg = _get_alg()
        if not isinstance(alg, StringAlgebra):
            raise RuntimeError("Only supported for string algebras.")
        return [_module_info(m, alg) for m in alg.string_indecs(non_isomorphic=True)]
    if path == "/modules/projectives":
        alg = _get_alg()
        return [_module_info(alg.proj_at(v), alg) for v in alg.vertices]
    if path == "/modules/injectives":
        alg = _get_alg()
        return [_module_info(alg.inj_at(v), alg) for v in alg.vertices]
    if path == "/modules/simples":
        alg = _get_alg()
        return [_module_info(alg.simple_at(v), alg) for v in alg.vertices]
    if path == "/modules/bands":
        alg = _get_alg()
        if not isinstance(alg, MonomialAlgebra):
            return []
        try:
            return [{"name": str(b), "length": b.length} for b in alg.primitive_bands()]
        except Exception:
            return []

    # ── RfAlgebra endpoints ────────────────────────────────────────────────
    if path == "/rf/info-bundle":
        return _get_rf().info_bundle()
    if path == "/rf/indec-extended":
        return _get_rf().indec_extended_table()
    if path == "/rf/hom-table":
        rf = _get_rf()
        return _matrix_payload([str(m) for m in rf.indecs], rf.hom_table(), sparse)
    if path == "/rf/ext1-table":
        rf = _get_rf()
        return _matrix_payload([str(m) for m in rf.indecs], rf.ext1_table(), sparse)
    if path == "/rf/hom-tau-table":
        rf = _get_rf()
        return _matrix_payload([str(m) for m in rf.indecs], rf.hom_tau_table(), sparse)
    if path == "/rf/tau-indec-table":
        return _get_rf().tau_indec_table()
    if path == "/rf/basic-semibricks":
        rf = _get_rf(); items = rf.basic_semibricks_with_dims
        return {"count": len(items), "items": items}
    if path == "/rf/basic-tau-rigids":
        rf = _get_rf(); items = rf.basic_tau_rigids
        return {"count": len(items), "items": items}
    if path == "/rf/basic-support-tau-tiltings":
        rf = _get_rf(); items = rf.basic_support_tau_tiltings
        return {"count": len(items), "items": items}
    if path == "/rf/basic-tau-tiltings":
        rf = _get_rf(); items = rf.basic_tau_tiltings
        return {"count": len(items), "items": items}
    if path == "/rf/basic-rigids":
        rf = _get_rf(); items = rf.basic_rigids
        return {"count": len(items), "items": items}
    if path == "/rf/basic-partial-tiltings":
        rf = _get_rf(); items = rf.basic_partial_tiltings
        return {"count": len(items), "items": items}
    if path == "/rf/basic-tiltings":
        rf = _get_rf(); items = rf.basic_tiltings
        return {"count": len(items), "items": items}
    if path == "/rf/wide-lattice":
        return _get_rf().wide_lattice
    if path == "/rf/splitting-torsion":
        rf = _get_rf(); data = rf.splitting_torsion_data
        return {
            "all_splitting": all(d["is_splitting"] for d in data),
            "num_torsion_classes": len(rf.torsion_classes),
            "num_indecs": len(rf.indecs),
            "indecs": [str(m) for m in rf.indecs],
            "torsion_classes": data,
        }
    if path == "/rf/brick-splitting":
        rf = _get_rf(); data = rf.brick_splitting_torsion_classes()
        return {
            "all_brick_splitting": rf.all_are_brick_splitting(),
            "num_torsion_classes": len(rf.torsion_classes),
            "num_bricks": len(rf.bricks),
            "bricks": [str(b) for b in rf.bricks],
            "torsion_classes": data,
        }
    if path == "/rf/short-cycles":
        return _get_rf().short_cycle_info()
    if path == "/rf/brick-cycles":
        rf = _get_rf()
        return {"cycles": rf.brick_cycles(),
                "num_bricks": len(rf.bricks),
                "bricks": [str(b) for b in rf.bricks]}
    if path == "/rf/morphism-cycles":
        return {"cycles": _get_rf().morphism_cycles()}
    if path == "/rf/i-tau-rigid-cycles":
        rf = _get_rf()
        return {"cycles": rf.i_tau_rigid_cycles(),
                "modules": [str(m) for m in rf._indec_tau_rigids_cached]}
    if path == "/rf/i-rigid-cycles":
        rf = _get_rf()
        return {"cycles": rf.i_rigid_cycles(),
                "modules": [str(m) for m in rf.indec_rigids]}
    if path == "/rf/tau-rigid-summary":
        rf = _get_rf()
        tau_rigids = rf.basic_tau_rigids
        stt_keys = set(frozenset(e["names"]) for e in rf.basic_support_tau_tiltings)
        tt_keys  = set(frozenset(e["names"]) for e in rf.basic_tau_tiltings)
        rows = []
        for e in tau_rigids:
            key = frozenset(e["names"])
            rows.append({**e,
                "is_support_tau_tilting": key in stt_keys,
                "is_tau_tilting": key in tt_keys})
        return {
            "rows": rows,
            "num_indec_tau_rigid":     len(rf._indec_tau_rigids_cached),
            "num_basic_tau_rigid":     len(tau_rigids),
            "num_support_tau_tilting": len(rf.basic_support_tau_tiltings),
            "num_tau_tilting":         len(rf.basic_tau_tiltings),
        }
    if path == "/rf/morphism-quiver":
        return _get_rf().morphism_quiver()
    if path == "/rf/brick-quiver":
        return _get_rf().brick_quiver_data()
    if path == "/rf/ar-quiver-full":
        rf = _get_rf()
        ar = rf.ar_quiver
        indecs = rf.indecs
        names = [str(m) for m in indecs]
        from collections import defaultdict
        cols = defaultdict(list)
        for m in indecs:
            pd = m.proj_dim()
            col = pd if pd is not None else 99
            cols[col].append(str(m))
        positions = {}
        col_keys = sorted(cols.keys())
        for ci, ck in enumerate(col_keys):
            mods = cols[ck]
            for ri, name in enumerate(mods):
                positions[name] = {"x": 120 + ci * 160,
                                   "y": 60 + ri * 100 - (len(mods)-1)*50}
        return {
            "vertices":    [{"name": n, **positions.get(n, {"x": 100, "y": 100})}
                            for n in names],
            "arrows":      [{"from": str(a.from_vertex), "to": str(a.to_vertex)}
                            for a in ar.quiver.arrows],
            "tau":         {str(k): str(v) for k, v in ar.tau.items()},
            "projectives": [str(m) for m in ar.projectives],
            "injectives":  [str(m) for m in ar.injectives],
        }
    if path == "/rf/tau-tilting-hasse":
        return _get_rf().tau_tilting_hasse()
    if path == "/rf/trim-lattice":
        return _get_rf().trim_lattice_info()
    if path == "/rf/directedness":
        rf = _get_rf()
        return {
            "is_representation_directed": rf.is_representation_directed(),
            "is_brick_directed":          rf.is_brick_directed(),
            "num_indec_cycles":           len(rf.morphism_cycles()),
            "num_brick_cycles":           len(rf.brick_cycles()),
            "num_bricks":                 len(rf.bricks),
            "num_indecs":                 len(rf.indecs),
        }

    # ── Fringed algebra (BDMTY §3) ─────────────────────────────────────────
    if path == "/fringed":
        return fringed_algebra_data(_get_alg())

    raise ValueError(f"Unknown path: {path}")
