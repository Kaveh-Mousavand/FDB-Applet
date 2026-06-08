"""
FastAPI server for fd-applet Python port.

Mirrors the original Kotlin/Ktor server endpoints.
Run with:
    pip install fastapi uvicorn
    uvicorn fd_applet_python.server:app --reload --port 8000

Then open:
    http://localhost:8000/docs   (interactive Swagger UI)
    http://localhost:8000/redoc  (ReDoc UI)
"""

from __future__ import annotations
import json
import sys
import os
from typing import Any, Dict, List, Optional

# ── FastAPI imports ───────────────────────────────────────────────────────────
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── local algebra imports ────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from fd_applet_python.algebra.binomial_algebra import (
    load_algebra_from_json,
    _quiver_from_dict,
    _monomial_from_labels,
    MonomialAlgebra,
    BinomialAlgebra,
)
from fd_applet_python.algebra.string_algebra import StringAlgebra, GentleAlgebra
from fd_applet_python.algebra.rf_algebra import RfAlgebra, build_rf_algebra
from fd_applet_python.quiver.arrow import Arrow
from fd_applet_python.quiver.quiver import Quiver
from fd_applet_python.quiver.monomial import Monomial

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="fd-applet API",
    description="Python port of the fd-applet Kotlin/Ktor server.\n"
                "Provides computations for finite-dimensional algebras over quivers.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory session state ───────────────────────────────────────────────────
# Simple global state (mirrors Kotlin's SessionStorage).
# For production, replace with a proper session/cache layer.
_session: Dict[str, Any] = {}


def _get_algebra():
    alg = _session.get("algebra")
    if alg is None:
        raise HTTPException(status_code=400, detail="No algebra loaded. POST to /algebra first.")
    return alg


def _get_rf() -> RfAlgebra:
    rf = _session.get("rf_algebra")
    if rf is not None:
        return rf
    alg = _get_algebra()
    if not isinstance(alg, StringAlgebra):
        raise HTTPException(status_code=400, detail="Current algebra is not a string algebra.")
    if not alg.is_rep_finite():
        raise HTTPException(status_code=400,
                            detail="Algebra is representation-infinite. RF operations unavailable.")
    rf = build_rf_algebra(alg)
    _session["rf_algebra"] = rf
    return rf


def _algebra_type_name(alg) -> str:
    if isinstance(alg, GentleAlgebra):
        return "GentleAlgebra"
    if isinstance(alg, StringAlgebra):
        return "StringAlgebra"
    if isinstance(alg, BinomialAlgebra):
        return "BinomialAlgebra"
    if isinstance(alg, MonomialAlgebra):
        return "MonomialAlgebra"
    return type(alg).__name__


# ── Pydantic request/response models ─────────────────────────────────────────

class ArrowData(BaseModel):
    label: str
    from_: str
    to: str

    class Config:
        populate_by_name = True
        fields = {"from_": "from"}


class QuiverData(BaseModel):
    vertices: List[str]
    arrows: List[Dict[str, str]]


class AlgebraInput(BaseModel):
    quiver: QuiverData
    monoRelations: List[List[str]] = []
    biRelations: List[Dict[str, List[str]]] = []


class AlgebraInfo(BaseModel):
    type: str
    vertices: List[str]
    num_arrows: int
    is_finite_dimensional: bool
    dimension: Optional[int]
    is_string: bool
    is_gentle: bool
    is_rep_finite: Optional[bool]
    num_indecs: Optional[int]


class ModuleInfo(BaseModel):
    name: str
    dim: int
    is_projective: bool
    is_injective: bool
    is_brick: bool
    top_vertices: List[str]
    socle_vertices: List[str]
    proj_dim: Optional[int]
    inj_dim: Optional[int]


class HomResult(BaseModel):
    hom: int
    ext1: Optional[int]
    stable_hom: Optional[int]


class GlobalDimResult(BaseModel):
    global_dim: Optional[int]
    finitistic_dim: Optional[int]
    right_self_inj_dim: Optional[int]
    left_self_inj_dim: Optional[int]
    dominant_dim: Optional[int]
    is_ig: bool
    is_self_injective: bool


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_algebra(data: AlgebraInput):
    raw = {
        "quiver": {
            "vertices": data.quiver.vertices,
            "arrows": data.quiver.arrows,
        },
        "monoRelations": data.monoRelations,
        "biRelations": [{"first": br["first"], "second": br["second"]}
                        for br in data.biRelations],
    }
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(raw, f)
        tmp = f.name
    try:
        alg = load_algebra_from_json(tmp)
    finally:
        os.unlink(tmp)
    return alg


def _module_info(m, alg) -> ModuleInfo:
    pd = m.proj_dim() if isinstance(alg, StringAlgebra) else None
    id_ = m.inj_dim() if isinstance(alg, StringAlgebra) else None
    return ModuleInfo(
        name=str(m),
        dim=m.dim(),
        is_projective=m.is_projective() if isinstance(alg, StringAlgebra) else False,
        is_injective=m.is_injective() if isinstance(alg, StringAlgebra) else False,
        is_brick=m.is_brick() if isinstance(alg, StringAlgebra) else False,
        top_vertices=m.top_vertices() if isinstance(alg, StringAlgebra) else [],
        socle_vertices=m.socle_vertices() if isinstance(alg, StringAlgebra) else [],
        proj_dim=pd,
        inj_dim=id_,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/", summary="Health check")
def root():
    return {"status": "ok", "app": "fd-applet Python API"}


# ── Algebra loading ────────────────────────────────────────────────────────────

@app.post("/algebra", summary="Load an algebra from JSON body")
def post_algebra(data: AlgebraInput):
    """
    Load a quiver algebra. Clears any cached RF algebra.

    The JSON format mirrors the fd-applet .json file format:
    - `quiver.vertices`: list of vertex label strings
    - `quiver.arrows`: list of `{"label": "a", "from": "1", "to": "2"}` objects
    - `monoRelations`: list of arrow-label lists (each is a zero path)
    - `biRelations`: list of `{"first": [...], "second": [...]}` (commutativity relations)
    """
    try:
        alg = _parse_algebra(data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
    _session["algebra"] = alg
    _session.pop("rf_algebra", None)
    return {"loaded": _algebra_type_name(alg), "vertices": alg.vertices}


@app.get("/algebra/info", response_model=AlgebraInfo, summary="Algebra type and dimensions")
def get_algebra_info():
    """Return type, dimension, and classification of the loaded algebra."""
    alg = _get_algebra()
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
    return AlgebraInfo(
        type=_algebra_type_name(alg),
        vertices=list(alg.vertices),
        num_arrows=len(list(alg.arrows)),
        is_finite_dimensional=alg.is_finite_dimensional(),
        dimension=alg.dim(),
        is_string=is_string,
        is_gentle=isinstance(alg, GentleAlgebra),
        is_rep_finite=is_rep_finite,
        num_indecs=num_indecs,
    )


# ── Module enumeration ─────────────────────────────────────────────────────────

@app.get("/modules/indecs", summary="All indecomposable string modules")
def get_indecs(length_bound: Optional[int] = None):
    """
    List all indecomposable string modules (non-isomorphic).
    Pass `length_bound` to limit word length (useful for rep-infinite algebras).
    """
    alg = _get_algebra()
    if not isinstance(alg, StringAlgebra):
        raise HTTPException(400, "Only supported for string algebras.")
    indecs = alg.string_indecs(length_bound=length_bound, non_isomorphic=True)
    return [_module_info(m, alg) for m in indecs]


@app.get("/modules/projectives", summary="Indecomposable projective modules")
def get_projectives():
    alg = _get_algebra()
    if not isinstance(alg, StringAlgebra):
        raise HTTPException(400, "Only supported for string algebras.")
    return [_module_info(alg.proj_at(v), alg) for v in alg.vertices]


@app.get("/modules/injectives", summary="Indecomposable injective modules")
def get_injectives():
    alg = _get_algebra()
    if not isinstance(alg, StringAlgebra):
        raise HTTPException(400, "Only supported for string algebras.")
    return [_module_info(alg.inj_at(v), alg) for v in alg.vertices]


@app.get("/modules/simples", summary="Simple modules")
def get_simples():
    alg = _get_algebra()
    return [_module_info(alg.simple_at(v), alg) for v in alg.vertices]


@app.get("/modules/bands", summary="Primitive bands (rep-infinite case)")
def get_bands():
    alg = _get_algebra()
    if not isinstance(alg, MonomialAlgebra):
        raise HTTPException(400, "Only supported for monomial algebras.")
    try:
        bands = alg.primitive_bands()
    except Exception as e:
        raise HTTPException(500, str(e))
    return [{"name": str(b), "length": b.length} for b in bands]


# ── Global dimensions ──────────────────────────────────────────────────────────

@app.get("/algebra/dimensions", response_model=GlobalDimResult,
         summary="Global, finitistic, self-injective, dominant dimensions")
def get_dimensions():
    """
    Compute global dimension, finitistic dimension, right/left self-injective
    dimension, dominant dimension, Iwanaga-Gorenstein status.
    Requires a rep-finite string algebra.
    """
    rf = _get_rf()
    return GlobalDimResult(
        global_dim=rf.global_dim(),
        finitistic_dim=rf.finitistic_dim(),
        right_self_inj_dim=rf.right_self_inj_dim(),
        left_self_inj_dim=rf.left_self_inj_dim(),
        dominant_dim=rf.dominant_dim(),
        is_ig=rf.is_ig(),
        is_self_injective=rf.is_self_injective(),
    )


# ── Hom / Ext calculator ──────────────────────────────────────────────────────

@app.get("/calculator/hom", summary="Compute Hom(X, Y) between two modules")
def calc_hom(x: str, y: str, compute_ext1: bool = False, compute_stable: bool = False):
    """
    Compute dim Hom(X, Y) where X and Y are module names (e.g. \"a*b\", \"!c\", \"1\").
    Optionally also compute Ext^1(X, Y) and projectively stable Hom.
    """
    alg = _get_algebra()
    if not isinstance(alg, StringAlgebra):
        raise HTTPException(400, "Only supported for string algebras.")
    indecs = alg.string_indecs(non_isomorphic=False)
    by_name = {str(m): m for m in indecs}
    # Also add inverse names
    for m in indecs:
        by_name[str(~m)] = ~m

    mx = by_name.get(x)
    my = by_name.get(y)
    if mx is None:
        raise HTTPException(404, f"Module '{x}' not found.")
    if my is None:
        raise HTTPException(404, f"Module '{y}' not found.")

    hom = mx.hom(my)
    ext1 = mx.ext1(my) if compute_ext1 else None
    stable = mx.stable_hom(my) if compute_stable else None
    return HomResult(hom=hom, ext1=ext1, stable_hom=stable)


@app.get("/calculator/projdim", summary="Projective dimension of a module")
def calc_projdim(module: str):
    alg = _get_algebra()
    if not isinstance(alg, StringAlgebra):
        raise HTTPException(400, "Only supported for string algebras.")
    indecs = alg.string_indecs(non_isomorphic=False)
    by_name = {str(m): m for m in indecs}
    for m in indecs:
        by_name[str(~m)] = ~m
    mx = by_name.get(module)
    if mx is None:
        raise HTTPException(404, f"Module '{module}' not found.")
    pd = mx.proj_dim()
    return {"module": module, "proj_dim": pd}


@app.get("/calculator/injdim", summary="Injective dimension of a module")
def calc_injdim(module: str):
    alg = _get_algebra()
    if not isinstance(alg, StringAlgebra):
        raise HTTPException(400, "Only supported for string algebras.")
    indecs = alg.string_indecs(non_isomorphic=False)
    by_name = {str(m): m for m in indecs}
    for m in indecs:
        by_name[str(~m)] = ~m
    mx = by_name.get(module)
    if mx is None:
        raise HTTPException(404, f"Module '{module}' not found.")
    id_ = mx.inj_dim()
    return {"module": module, "inj_dim": id_}


@app.get("/calculator/syzygy", summary="Syzygy (Ω) of a module")
def calc_syzygy(module: str, n: int = 1):
    """Compute the n-th syzygy Ω^n(M)."""
    alg = _get_algebra()
    if not isinstance(alg, StringAlgebra):
        raise HTTPException(400, "Only supported for string algebras.")
    indecs = alg.string_indecs(non_isomorphic=False)
    by_name = {str(m): m for m in indecs}
    for m in indecs:
        by_name[str(~m)] = ~m
    mx = by_name.get(module)
    if mx is None:
        raise HTTPException(404, f"Module '{module}' not found.")
    result = mx.syzygy_n(n)
    return {"module": module, "n": n, "syzygy": [str(s) for s in result]}


@app.get("/calculator/cosyzygy", summary="Cosyzygy (Σ) of a module")
def calc_cosyzygy(module: str, n: int = 1):
    alg = _get_algebra()
    if not isinstance(alg, StringAlgebra):
        raise HTTPException(400, "Only supported for string algebras.")
    indecs = alg.string_indecs(non_isomorphic=False)
    by_name = {str(m): m for m in indecs}
    for m in indecs:
        by_name[str(~m)] = ~m
    mx = by_name.get(module)
    if mx is None:
        raise HTTPException(404, f"Module '{module}' not found.")
    result = mx.cosyzygy_n(n)
    return {"module": module, "n": n, "cosyzygy": [str(s) for s in result]}


@app.get("/calculator/ar-sequence", summary="Auslander-Reiten sequence for a module")
def calc_ar_sequence(module: str):
    """
    Compute the AR sequence 0 → τX → E → X → 0 (sink sequence)
    and     0 → X → E' → τ⁻X → 0 (source sequence).
    """
    alg = _get_algebra()
    if not isinstance(alg, StringAlgebra):
        raise HTTPException(400, "Only supported for string algebras.")
    indecs = alg.string_indecs(non_isomorphic=False)
    by_name = {str(m): m for m in indecs}
    for m in indecs:
        by_name[str(~m)] = ~m
    mx = by_name.get(module)
    if mx is None:
        raise HTTPException(404, f"Module '{module}' not found.")
    middle_sink, tau = mx.sink_sequence()
    middle_source, tau_inv = mx.source_sequence()
    return {
        "module": module,
        "is_projective": mx.is_projective(),
        "is_injective": mx.is_injective(),
        "sink_sequence": {
            "tau": str(tau) if tau else None,
            "middle": [str(m) for m in middle_sink],
            "module": module,
        },
        "source_sequence": {
            "module": module,
            "middle": [str(m) for m in middle_source],
            "tau_minus": str(tau_inv) if tau_inv else None,
        },
    }


# ── Rep-finite / AR quiver ────────────────────────────────────────────────────

@app.get("/rf/ar-quiver", summary="Auslander-Reiten quiver (rep-finite algebras)")
def get_ar_quiver():
    """
    Returns the AR quiver as a list of vertices (modules) and arrows,
    plus the tau map. Only for rep-finite string algebras.
    """
    rf = _get_rf()
    ar = rf.ar_quiver
    vertices = [str(m) for m in ar.vertices]
    arrows = [
        {"from": str(a.from_vertex), "to": str(a.to_vertex)}
        for a in ar.quiver.arrows
    ]
    tau = {str(k): str(v) for k, v in ar.tau.items()}
    return {
        "vertices": vertices,
        "arrows": arrows,
        "tau": tau,
        "projectives": [str(m) for m in ar.projectives],
        "injectives": [str(m) for m in ar.injectives],
    }


@app.get("/rf/bricks", summary="All bricks (endomorphism ring = field)")
def get_bricks():
    rf = _get_rf()
    return [str(b) for b in rf.bricks]


@app.get("/rf/semibricks", summary="All semibricks (pairwise Hom-orthogonal bricks)")
def get_semibricks():
    rf = _get_rf()
    return [[str(b) for b in sb] for sb in rf.semibricks]


@app.get("/rf/torsion-classes", summary="All torsion classes")
def get_torsion_classes():
    rf = _get_rf()
    return [[str(m) for m in tc] for tc in rf.torsion_classes]


@app.get("/rf/torsion-free-classes", summary="All torsion-free classes")
def get_torsion_free_classes():
    rf = _get_rf()
    return [[str(m) for m in tfc] for tfc in rf.torsion_free_classes]


@app.get("/rf/wide-subcategories", summary="All wide subcategories")
def get_wide_subcats():
    rf = _get_rf()
    return [[str(m) for m in w] for w in rf.wide_subcategories]


@app.get("/rf/indec-tau-rigids", summary="All indecomposable tau-rigid modules")
def get_indec_tau_rigids():
    rf = _get_rf()
    return [str(m) for m in rf.indec_tau_rigids()]


@app.get("/rf/support-tau-tilting", summary="All support tau-tilting modules")
def get_support_tau_tilting():
    rf = _get_rf()
    return [[str(m) for m in stt] for stt in rf.support_tau_tilting_modules()]


# ═══════════════════════════════════════════════════════════════════════════════
# Example usage (run directly for quick test)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)


# ═══════════════════════════════════════════════════════════════════════════════
# New endpoints for enhanced UI
# ═══════════════════════════════════════════════════════════════════════════════

def _matrix_payload(modules: List[str], table: List[List[int]], sparse: bool):
    """Efficiency fix F: optionally return only nonzero entries as a sparse list."""
    if not sparse:
        return {"modules": modules, "table": table}
    nz = []
    for i, row in enumerate(table):
        for j, v in enumerate(row):
            if v is not None and v != 0:
                nz.append([i, j, v])
    return {"modules": modules, "nonzero": nz, "n": len(modules), "sparse": True}


@app.get("/rf/hom-table", summary="Full Hom matrix between all indecomposables")
def get_hom_table(sparse: bool = False):
    rf = _get_rf()
    return _matrix_payload([str(m) for m in rf.indecs], rf.hom_table(), sparse)


@app.get("/rf/ext1-table", summary="Full Ext¹ matrix between all indecomposables")
def get_ext1_table(sparse: bool = False):
    rf = _get_rf()
    return _matrix_payload([str(m) for m in rf.indecs], rf.ext1_table(), sparse)


@app.get("/rf/tau-tilting-quiver", summary="Mutation quiver of support tau-tilting modules")
def get_tau_tilting_quiver():
    rf = _get_rf()
    return rf.tau_tilting_quiver()


@app.get("/rf/tau-tilting-hasse", summary="Hasse diagram of support tau-tilting modules")
def get_tau_tilting_hasse():
    rf = _get_rf()
    return rf.tau_tilting_hasse()


@app.get("/rf/morphism-quiver", summary="Quiver of nonzero non-iso morphisms between indecomposables")
def get_morphism_quiver():
    rf = _get_rf()
    return rf.morphism_quiver()


@app.get("/rf/morphism-cycles", summary="Cycles of nonzero non-iso morphisms")
def get_morphism_cycles():
    rf = _get_rf()
    return {"cycles": rf.morphism_cycles()}


@app.get("/rf/ar-quiver-full", summary="AR quiver with layout positions")
def get_ar_quiver_full():
    """
    Returns AR quiver with suggested x/y positions for rendering.
    Projectives on the left, injectives on the right, tau-translates aligned.
    """
    rf = _get_rf()
    ar = rf.ar_quiver
    indecs = rf.indecs
    names = [str(m) for m in indecs]

    # Assign positions: column by projective dimension, row by index within column
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
            positions[name] = {
                "x": 120 + ci * 160,
                "y": 60 + ri * 100 - (len(mods)-1)*50,
            }

    return {
        "vertices": [{"name": n, **positions.get(n, {"x": 100, "y": 100})} for n in names],
        "arrows": [
            {"from": str(a.from_vertex), "to": str(a.to_vertex)}
            for a in ar.quiver.arrows
        ],
        "tau": {str(k): str(v) for k, v in ar.tau.items()},
        "projectives": [str(m) for m in ar.projectives],
        "injectives":  [str(m) for m in ar.injectives],
    }


@app.get("/rf/brick-cycles", summary="Directed cycles of nonzero non-iso morphisms between bricks")
def get_brick_cycles():
    rf = _get_rf()
    return {"cycles": rf.brick_cycles(), "num_bricks": len(rf.bricks), "bricks": [str(b) for b in rf.bricks]}


@app.get("/rf/directedness", summary="Representation-directed and brick-directed status")
def get_directedness():
    """
    Returns whether the algebra is representation-directed (no cycles of indecomposables)
    and brick-directed (no cycles of bricks).
    """
    rf = _get_rf()
    is_rd = rf.is_representation_directed()
    is_bd = rf.is_brick_directed()
    return {
        "is_representation_directed": is_rd,
        "is_brick_directed": is_bd,
        "num_indec_cycles": len(rf.morphism_cycles()),
        "num_brick_cycles": len(rf.brick_cycles()),
        "num_bricks": len(rf.bricks),
        "num_indecs": len(rf.indecs),
    }


@app.get("/rf/trim-lattice", summary="Trim lattice of torsion classes")
def get_trim_lattice():
    """
    Returns whether the algebra has a trim lattice of torsion classes
    (equivalent to being brick-directed), together with the full Hasse
    diagram of the torsion class lattice.
    """
    rf = _get_rf()
    return rf.trim_lattice_info()


@app.get("/rf/short-cycles", summary="Short cycles between indecomposables (X→Y→X)")
def get_short_cycles():
    """
    A short cycle is a pair of non-isomorphic indecomposables X, Y such that
    Hom(X, Y) > 0 AND Hom(Y, X) > 0 (i.e. nonzero non-iso maps X→Y→X exist).
    Returns all such pairs with their Hom dimensions.
    """
    rf = _get_rf()
    return rf.short_cycle_info()


@app.get("/rf/brick-splitting", summary="Brick-splitting torsion classes")
def get_brick_splitting():
    """
    A torsion class T is brick-splitting if for every brick B:
      B in T  (torsion class)  OR  B in T^perp  (torsion-free class).
    T^perp = { X : Hom(M, X) = 0 for all M in T }.
    Returns all torsion classes with their brick-splitting status.
    """
    rf = _get_rf()
    data = rf.brick_splitting_torsion_classes()
    return {
        "all_brick_splitting": rf.all_are_brick_splitting(),
        "num_torsion_classes": len(rf.torsion_classes),
        "num_bricks": len(rf.bricks),
        "bricks": [str(b) for b in rf.bricks],
        "torsion_classes": data,
    }


@app.get("/rf/brick-quiver", summary="Brick quiver of the algebra")
def get_brick_quiver():
    """
    Brick quiver: vertices = bricks, arrow X->Y iff Hom(X,Y)>0.
    Includes cycle detection, longest paths, and hom dimensions.
    """
    rf = _get_rf()
    return rf.brick_quiver_data()


@app.get("/rf/torsion-lattice-stats", summary="Lattice statistics: chains, length, BS chains")
def get_torsion_lattice_stats():
    """
    For the lattice of torsion classes:
    - Length (longest chain from bottom to top)
    - Total number of maximal chains (bottom to top)
    - Number of maximal chains through only brick-splitting nodes
    - List of brick-splitting torsion classes
    """
    rf = _get_rf()
    tors   = rf.torsion_classes
    n      = len(tors)
    hasse  = rf._hasse_arrows()
    bs_set = set(rf.trim_lattice_info()["brick_splitting_indices"])

    # Build adjacency: adj[i] = [j] where i is covered by j (i->j in Hasse)
    adj = {i: [] for i in range(n)}
    for (i, j) in hasse:
        adj[i].append(j)

    # Find bottom (no incoming) and top (no outgoing in Hasse upward direction)
    has_incoming = set(j for (_, j) in hasse)
    has_outgoing = set(i for (i, _) in hasse)
    bottoms = [i for i in range(n) if i not in has_incoming]
    tops    = [i for i in range(n) if i not in has_outgoing]
    bottom  = bottoms[0] if bottoms else 0
    top     = tops[0]    if tops    else n - 1

    # Count all maximal chains from bottom to top
    # and BS-only chains (all intermediate nodes are BS)
    total_chains = 0
    bs_chains    = 0
    max_length   = 0

    def dfs(node, path):
        nonlocal total_chains, bs_chains, max_length
        if node == top:
            total_chains += 1
            length = len(path) - 1
            if length > max_length:
                max_length = length
            # Check if all intermediate nodes (excluding bottom and top) are BS
            intermediates = path[1:-1]
            if all(v in bs_set for v in intermediates):
                bs_chains += 1
            return
        for nxt in adj[node]:
            dfs(nxt, path + [nxt])

    dfs(bottom, [bottom])

    # BS torsion class details
    bs_list = [
        {"index": i, "torsion_class": [str(m) for m in tors[i]]}
        for i in sorted(bs_set)
    ]

    return {
        "num_torsion_classes":   n,
        "lattice_length":        max_length,
        "total_maximal_chains":  total_chains,
        "bs_maximal_chains":     bs_chains,
        "num_brick_splitting":   len(bs_set),
        "brick_splitting_classes": bs_list,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FDB-Applet-bricK-M extensions
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/rf/info-bundle", summary="Aggregate metrics for the Information tile")
def get_info_bundle():
    """All numeric data for the FDB-Applet 'Information' tile."""
    rf = _get_rf()
    return rf.info_bundle()


@app.get("/rf/indec-extended", summary="Indecomposables with τ-translate, brick, iτ-rigid, i-rigid flags")
def get_indec_extended():
    rf = _get_rf()
    return rf.indec_extended_table()


@app.get("/rf/hom-tau-table", summary="Full dim Hom(X, τY) matrix")
def get_hom_tau_table():
    """Full table of dim Hom(X_i, τ X_j); None entries mark X_j projective."""
    rf = _get_rf()
    return {
        "modules": [str(m) for m in rf.indecs],
        "table": rf.hom_tau_table(),
    }


@app.get("/rf/i-tau-rigid-cycles", summary="Cycles among indecomposable τ-rigid modules")
def get_i_tau_rigid_cycles():
    rf = _get_rf()
    return {
        "cycles": rf.i_tau_rigid_cycles(),
        "modules": [str(m) for m in rf._indec_tau_rigids_cached],
    }


@app.get("/rf/i-rigid-cycles", summary="Cycles among indecomposable rigid modules")
def get_i_rigid_cycles():
    rf = _get_rf()
    return {
        "cycles": rf.i_rigid_cycles(),
        "modules": [str(m) for m in rf.indec_rigids],
    }


@app.get("/rf/tau-indec-table", summary="Indecomposables with τ-translate dimensions")
def get_tau_indec_table():
    rf = _get_rf()
    return rf.tau_indec_table()


@app.get("/rf/basic-semibricks", summary="All basic semibricks with sizes/dimensions")
def get_basic_semibricks():
    rf = _get_rf()
    items = rf.basic_semibricks_with_dims
    return {"count": len(items), "items": items}


@app.get("/rf/basic-tau-rigids", summary="All basic τ-rigid modules with sizes/dimensions")
def get_basic_tau_rigids():
    rf = _get_rf()
    items = rf.basic_tau_rigids
    return {"count": len(items), "items": items}


@app.get("/rf/basic-support-tau-tiltings", summary="All basic support τ-tilting modules")
def get_basic_support_tau_tiltings():
    rf = _get_rf()
    items = rf.basic_support_tau_tiltings
    return {"count": len(items), "items": items}


@app.get("/rf/basic-tau-tiltings", summary="All basic τ-tilting modules (no projective complement)")
def get_basic_tau_tiltings():
    rf = _get_rf()
    items = rf.basic_tau_tiltings
    return {"count": len(items), "items": items}


@app.get("/rf/basic-rigids", summary="All basic rigid modules")
def get_basic_rigids():
    rf = _get_rf()
    items = rf.basic_rigids
    return {"count": len(items), "items": items}


@app.get("/rf/basic-partial-tiltings", summary="All basic partial tilting modules")
def get_basic_partial_tiltings():
    rf = _get_rf()
    items = rf.basic_partial_tiltings
    return {"count": len(items), "items": items}


@app.get("/rf/basic-tiltings", summary="All basic tilting modules (rank summands)")
def get_basic_tiltings():
    rf = _get_rf()
    items = rf.basic_tiltings
    return {"count": len(items), "items": items}


@app.get("/rf/splitting-torsion", summary="Splitting torsion classes (every indec in T or T^perp)")
def get_splitting_torsion():
    rf = _get_rf()
    data = rf.splitting_torsion_data
    return {
        "all_splitting": all(d["is_splitting"] for d in data),
        "num_torsion_classes": len(rf.torsion_classes),
        "num_indecs": len(rf.indecs),
        "indecs": [str(m) for m in rf.indecs],
        "torsion_classes": data,
    }


@app.get("/rf/wide-lattice", summary="Lattice of wide subcategories with inclusion order")
def get_wide_lattice():
    rf = _get_rf()
    return rf.wide_lattice


@app.get("/rf/tau-rigid-summary", summary="τ-Phenomena tile: τ-rigid summary table")
def get_tau_rigid_summary():
    """For the τ-Phenomena tile.
    First column: basic τ-rigid module; second: dim;
    third: support τ-tilting flag; fourth: τ-tilting flag."""
    rf = _get_rf()
    tau_rigids = rf.basic_tau_rigids
    stt_keys = set(frozenset(e["names"]) for e in rf.basic_support_tau_tiltings)
    tt_keys = set(frozenset(e["names"]) for e in rf.basic_tau_tiltings)
    rows = []
    for e in tau_rigids:
        key = frozenset(e["names"])
        rows.append({
            **e,
            "is_support_tau_tilting": key in stt_keys,
            "is_tau_tilting":         key in tt_keys,
        })
    return {
        "rows": rows,
        "num_indec_tau_rigid":      len(rf._indec_tau_rigids_cached),
        "num_basic_tau_rigid":      len(tau_rigids),
        "num_support_tau_tilting":  len(rf.basic_support_tau_tiltings),
        "num_tau_tilting":          len(rf.basic_tau_tiltings),
    }


@app.get("/fringed", summary="Fringed algebra (BDMTY §3) — only for gentle algebras")
def get_fringed():
    """Compute the fringed quiver Q̂ and ideal Î for the loaded gentle algebra.
    Returns is_gentle:False with an error message if A is not gentle.
    """
    from fd_applet_python.algebra.fringed import fringed_algebra_data
    alg = _get_algebra()
    return fringed_algebra_data(alg)
