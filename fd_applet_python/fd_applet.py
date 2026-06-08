#!/usr/bin/env python3
"""
fd-applet CLI — Python port of the fd-applet Kotlin backend.

Usage:
    python fd_applet.py                        # interactive mode
    python fd_applet.py examples/A4.json       # load file directly
    python fd_applet.py --help

Mirrors the features shown in the original fd-applet web interface:
  - Load an algebra from a JSON file
  - Show quiver / algebra type
  - Finite-dimensionality and dimension
  - String / Gentle algebra detection
  - Representation-finiteness
  - List all string modules (indecomposables)
  - List projective and injective modules
  - List primitive bands (for rep-infinite algebras)
  - Define an algebra interactively
"""

import sys
import os
import json
from typing import Optional

# ── resolve package path ──────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from fd_applet_python.algebra.binomial_algebra import load_algebra_from_json
from fd_applet_python.algebra.monomial_algebra import MonomialAlgebra
from fd_applet_python.algebra.string_algebra import StringAlgebra, GentleAlgebra
from fd_applet_python.algebra.binomial_algebra import BinomialAlgebra
from fd_applet_python.quiver.arrow import Arrow
from fd_applet_python.quiver.quiver import Quiver
from fd_applet_python.quiver.monomial import Monomial

# ─────────────────────────────────────────────────────────────────────────────
BANNER = """
╔══════════════════════════════════════════════════════╗
║       fd-applet  ·  Python CLI  (port of Kotlin)     ║
║  Tool for Finite-Dimensional algebras over quivers   ║
╚══════════════════════════════════════════════════════╝
"""

MENU = """
Commands:
  load <path>     Load an algebra from a .json file
  demo            Load the built-in A4 example
  info            Show quiver + algebra type
  type            Detect algebra type (Gentle / String / Monomial)
  dim             Compute the dimension of the algebra
  reptype         Check representation-finiteness
  indecs          List all indecomposable string modules
  projs           List projective indecomposables
  injs            List injective indecomposables
  simples         List simple modules
  bands           List primitive bands (rep-∞ case)
  words [N]       List all legal words (length ≤ N if given)
  new             Define a new algebra interactively
  help            Show this menu
  quit            Exit
"""

# ─────────────────────────────────────────────────────────────────────────────
# Display helpers
# ─────────────────────────────────────────────────────────────────────────────

def _algebra_type_name(alg) -> str:
    if isinstance(alg, GentleAlgebra):
        return "Gentle algebra"
    if isinstance(alg, StringAlgebra):
        return "String algebra"
    if isinstance(alg, BinomialAlgebra):
        return "Binomial algebra"
    if isinstance(alg, MonomialAlgebra):
        return "Monomial algebra"
    return type(alg).__name__


def _print_module_list(modules, title: str):
    print(f"\n{title} ({len(modules)} total):")
    if not modules:
        print("  (none)")
        return
    for i, m in enumerate(modules, 1):
        print(f"  {i:3}. {m}")


# ─────────────────────────────────────────────────────────────────────────────
# Interactive algebra builder
# ─────────────────────────────────────────────────────────────────────────────

def _interactive_new_algebra():
    """Walk the user through defining a quiver algebra."""
    print("\n── Define a new algebra ──")
    print("Enter vertices as a comma-separated list, e.g.:  1, 2, 3")
    raw = input("Vertices: ").strip()
    vertices = [v.strip() for v in raw.split(",") if v.strip()]
    if not vertices:
        print("No vertices entered.")
        return None

    arrows = []
    print("\nEnter arrows one per line as  label from to, e.g.:  a 1 2")
    print("Leave blank to finish.")
    while True:
        line = input("  Arrow: ").strip()
        if not line:
            break
        parts = line.split()
        if len(parts) != 3:
            print("  Format: label source target")
            continue
        label, src, tgt = parts
        if src not in vertices or tgt not in vertices:
            print(f"  Unknown vertex. Known: {vertices}")
            continue
        arrows.append(Arrow(src, tgt, label=label))

    quiver = Quiver(vertices, arrows)
    print("\nQuiver:")
    quiver.print_info()

    print("\nEnter monomial relations as arrow sequences, e.g.:  a b c")
    print("Leave blank to finish.")
    mono_rels = []
    while True:
        line = input("  Monomial relation: ").strip()
        if not line:
            break
        parts = line.split()
        try:
            arrow_objs = [quiver.arrow_of_label(p) for p in parts]
            mono_rels.append(Monomial(arrow_objs))
        except Exception as e:
            print(f"  Error: {e}")

    print("\nEnter commutativity relations as  path1 = path2, e.g.:  a b = c d")
    print("Leave blank to finish.")
    bi_rels = []
    while True:
        line = input("  Commutativity relation: ").strip()
        if not line:
            break
        if "=" not in line:
            print("  Format: a b c = d e f")
            continue
        left_raw, right_raw = line.split("=", 1)
        left_lbls = left_raw.strip().split()
        right_lbls = right_raw.strip().split()
        try:
            left_arrows  = [quiver.arrow_of_label(l) for l in left_lbls]
            right_arrows = [quiver.arrow_of_label(r) for r in right_lbls]
            bi_rels.append((Monomial(left_arrows), Monomial(right_arrows)))
        except Exception as e:
            print(f"  Error: {e}")

    try:
        mono_alg = MonomialAlgebra(quiver, mono_rels)
        if bi_rels:
            alg = BinomialAlgebra(mono_alg, bi_rels).make()
        else:
            alg = mono_alg.make()
        print(f"\nAlgebra created: {_algebra_type_name(alg)}")
        return alg
    except Exception as e:
        print(f"Error creating algebra: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# A4 demo algebra
# ─────────────────────────────────────────────────────────────────────────────

def _load_demo():
    demo = {
        "quiver": {
            "vertices": ["1", "2", "3", "4"],
            "arrows": [
                {"label": "a", "from": "1", "to": "2"},
                {"label": "b", "from": "2", "to": "3"},
                {"label": "c", "from": "3", "to": "4"},
            ],
        },
        "monoRelations": [],
        "biRelations": [],
    }
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(demo, f)
        path = f.name
    alg = load_algebra_from_json(path)
    os.unlink(path)
    return alg


# ─────────────────────────────────────────────────────────────────────────────
# Command dispatcher
# ─────────────────────────────────────────────────────────────────────────────

def _run_command(cmd_line: str, alg):
    parts = cmd_line.strip().split()
    if not parts:
        return alg
    cmd = parts[0].lower()

    if cmd in ("help", "?"):
        print(MENU)

    elif cmd == "load":
        if len(parts) < 2:
            print("Usage: load <path>")
        else:
            path = parts[1]
            try:
                alg = load_algebra_from_json(path)
                print(f"Loaded: {_algebra_type_name(alg)}")
            except Exception as e:
                print(f"Error loading {path}: {e}")

    elif cmd == "demo":
        alg = _load_demo()
        print(f"Loaded demo (A4 quiver): {_algebra_type_name(alg)}")

    elif cmd == "new":
        new_alg = _interactive_new_algebra()
        if new_alg is not None:
            alg = new_alg

    elif cmd == "info":
        if alg is None:
            print("No algebra loaded. Use 'load' or 'demo'.")
        else:
            print(f"\nType: {_algebra_type_name(alg)}")
            alg.print_info()

    elif cmd == "type":
        if alg is None:
            print("No algebra loaded.")
        else:
            name = _algebra_type_name(alg)
            print(f"\nAlgebra type: {name}")
            if isinstance(alg, MonomialAlgebra):
                print(f"  Is gentle  : {alg.is_gentle_algebra()}")
                print(f"  Is string  : {alg.is_string_algebra()}")

    elif cmd == "dim":
        if alg is None:
            print("No algebra loaded.")
        else:
            try:
                d = alg.dim()
                if d is None:
                    print("Dimension: ∞ (infinite-dimensional)")
                else:
                    print(f"Dimension: {d}")
            except Exception as e:
                print(f"Error: {e}")

    elif cmd == "reptype":
        if alg is None:
            print("No algebra loaded.")
        else:
            try:
                if not alg.is_finite_dimensional():
                    print("Algebra is infinite-dimensional.")
                elif alg.is_rep_finite():
                    if isinstance(alg, StringAlgebra):
                        n = len(alg.string_indecs(non_isomorphic=True))
                        print(f"Representation-FINITE  ({n} indecomposables)")
                    else:
                        print("Representation-FINITE")
                else:
                    print("Representation-INFINITE")
                    if isinstance(alg, MonomialAlgebra):
                        print(f"  Band-finite (domestic): {alg.is_band_finite}")
            except NotImplementedError as e:
                print(f"Not supported: {e}")

    elif cmd == "indecs":
        if alg is None:
            print("No algebra loaded.")
        elif not isinstance(alg, StringAlgebra):
            print("indecs is only supported for string algebras.")
        else:
            try:
                mods = alg.string_indecs(non_isomorphic=True)
                _print_module_list(mods, "Indecomposable string modules")
            except Exception as e:
                print(f"Error: {e}")

    elif cmd == "projs":
        if alg is None:
            print("No algebra loaded.")
        elif not isinstance(alg, StringAlgebra):
            print("projs is only supported for string algebras.")
        else:
            mods = [alg.proj_at(v) for v in alg.vertices]
            _print_module_list(mods, "Projective indecomposables")

    elif cmd == "injs":
        if alg is None:
            print("No algebra loaded.")
        elif not isinstance(alg, StringAlgebra):
            print("injs is only supported for string algebras.")
        else:
            mods = [alg.inj_at(v) for v in alg.vertices]
            _print_module_list(mods, "Injective indecomposables")

    elif cmd == "simples":
        if alg is None:
            print("No algebra loaded.")
        else:
            mods = [alg.simple_at(v) for v in alg.vertices]
            _print_module_list(mods, "Simple modules")

    elif cmd == "bands":
        if alg is None:
            print("No algebra loaded.")
        elif not isinstance(alg, MonomialAlgebra):
            print("bands is only supported for monomial algebras.")
        else:
            try:
                bands = alg.primitive_bands()
                _print_module_list(bands, "Primitive bands")
            except Exception as e:
                print(f"Error: {e}")

    elif cmd == "words":
        if alg is None:
            print("No algebra loaded.")
        elif not isinstance(alg, MonomialAlgebra):
            print("words is only supported for monomial algebras.")
        else:
            bound = None
            if len(parts) >= 2:
                try:
                    bound = int(parts[1])
                except ValueError:
                    print("Usage: words [max_length]")
                    return alg
            try:
                ws = alg._words(bound)
                _print_module_list(ws, f"Legal words (length ≤ {bound if bound else '∞'})")
            except Exception as e:
                print(f"Error: {e}")

    elif cmd in ("quit", "exit", "q"):
        print("Goodbye!")
        sys.exit(0)

    else:
        print(f"Unknown command '{cmd}'. Type 'help' for options.")

    return alg


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print(BANNER)
    alg = None

    # If a path is given as argument, load it immediately
    if len(sys.argv) >= 2 and not sys.argv[1].startswith("-"):
        path = sys.argv[1]
        try:
            alg = load_algebra_from_json(path)
            print(f"Loaded: {path}  →  {_algebra_type_name(alg)}")
        except Exception as e:
            print(f"Could not load {path}: {e}")

    if alg is None:
        print("Type 'demo' to load the A4 example, 'load <file>' to load a JSON algebra,")
        print("or 'new' to define one interactively. Type 'help' for all commands.\n")

    while True:
        try:
            line = input("fd-applet> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        if not line:
            continue
        alg = _run_command(line, alg)


if __name__ == "__main__":
    main()
