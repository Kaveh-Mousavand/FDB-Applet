"""
Full port of StringIndec.kt — indecomposable string modules with all operations:
  hom, ext1, stableHom, injStableHom, syzygy, cosyzygy, AR sequences (sinkSequence /
  sourceSequence), isProjective, isInjective, radical, coradical, topVertices, socleVertices.

A StringIndec is defined by a legal Word over a StringAlgebra.
Two words w and !w give isomorphic modules.
"""

from __future__ import annotations
from collections import deque
from typing import List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .string_algebra import StringAlgebra
    from ..quiver.word import Word


# ── GraphHom ──────────────────────────────────────────────────────────────────

class GraphHom:
    """
    A morphism between two string modules, given by interval maps on their words.

    A basis element of Hom(X, Y) is determined by choosing:
      - a quotient range of X  (an IntRange i..j such that X.word[i:j] is a quotient)
      - a submodule range of Y (an IntRange such that Y.word[k:l] is a submodule)
    such that X.word.sub_word(quot_range) == ± Y.word.sub_word(sub_range).

    Attributes:
        from_mod: source StringIndec (X)
        to_mod:   target StringIndec (Y)
        ranges:   (quot_range, sub_range) as (range, range)
        is_straight: True if the two subwords are equal (not inverse)
    """

    def __init__(
        self,
        from_mod: "StringIndec",
        to_mod: "StringIndec",
        ranges: Tuple[range, range],
    ):
        self.from_mod = from_mod
        self.to_mod = to_mod
        self.ranges = ranges  # (quot_range, sub_range)
        quot_range, sub_range = ranges
        from_quot = from_mod.sub_word_range(quot_range)
        to_sub = to_mod.sub_word_range(sub_range)
        self.is_straight = (from_quot == to_sub)
        if not self.is_straight and from_quot != (~to_sub.word if hasattr(to_sub, 'word') else None):
            # Validate lazily: just store, check on construction if needed
            pass

    def __eq__(self, other) -> bool:
        if not isinstance(other, GraphHom):
            return False
        return (self.from_mod == other.from_mod and
                self.to_mod == other.to_mod and
                self.ranges == other.ranges)

    def __hash__(self):
        return hash((id(self.from_mod), id(self.to_mod), self.ranges))

    def __repr__(self):
        return f"GraphHom({self.from_mod} -> {self.to_mod}, ranges={self.ranges})"


def _compose_homs(hom1: GraphHom, hom2: GraphHom) -> Optional[GraphHom]:
    """
    Compose two GraphHoms. hom1 goes X->Y, hom2 goes Y->Z.
    Returns None if the composition is zero.
    """
    assert hom1.to_mod == hom2.from_mod, "Cannot compose"
    x_quot, y_sub = hom1.ranges
    y_quot, z_sub = hom2.ranges

    # y_inter = intersection of y_sub and y_quot (as sets of integers)
    y_sub_set = set(y_sub)
    y_inter = [i for i in y_quot if i in y_sub_set]
    if not y_inter:
        return None

    y_inter_first = y_inter[0]
    y_inter_last = y_inter[-1]

    if hom1.is_straight:
        x_result = range(
            x_quot.start + y_inter_first - y_sub.start,
            x_quot.start + y_inter_last - y_sub.start + 1,
        )
    else:
        x_result = range(
            x_quot.start + y_sub.stop - 1 - y_inter_last,
            x_quot.start + y_sub.stop - 1 - y_inter_first + 1,
        )

    if hom2.is_straight:
        z_result = range(
            z_sub.start + y_inter_first - y_quot.start,
            z_sub.start + y_inter_last - y_quot.start + 1,
        )
    else:
        z_result = range(
            z_sub.start + y_quot.stop - 1 - y_inter_last,
            z_sub.start + y_quot.stop - 1 - y_inter_first + 1,
        )

    return GraphHom(hom1.from_mod, hom2.to_mod, (x_result, z_result))


# ── StringIndec ───────────────────────────────────────────────────────────────

class StringIndec:
    """
    An indecomposable string module, defined by a legal Word over a StringAlgebra.

    Note: word and ~word give isomorphic but distinct Python objects.
    Use is_isomorphic() for mathematical equality.
    """

    def __init__(self, algebra: "StringAlgebra", word: "Word"):
        self.algebra = algebra
        self.word = word

    @classmethod
    def from_word(
        cls, algebra: "StringAlgebra", word: "Word", check: bool = True
    ) -> "StringIndec":
        if check and not algebra.is_legal(word):
            raise ValueError(f"Word {word} is not legal over this algebra.")
        return cls(algebra, word)

    # ── basic properties ──────────────────────────────────────────────────────

    def __invert__(self) -> "StringIndec":
        return StringIndec(self.algebra, ~self.word)

    def __str__(self) -> str:
        return str(self.word)

    def __repr__(self) -> str:
        return f"StringIndec({self.word!r})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, StringIndec):
            return False
        return self.algebra is other.algebra and self.word == other.word

    def __hash__(self):
        return hash(self.word)

    def __lt__(self, other: "StringIndec") -> bool:
        return self.word < other.word

    def dim(self) -> int:
        """Vector space dimension = word length + 1."""
        return self.word.length + 1

    def is_simple(self) -> bool:
        return self.dim() == 1

    def vertex_list(self) -> list:
        return self.word.vertex_list()

    def support(self) -> set:
        return self.word.support()

    def is_isomorphic(self, other: "StringIndec") -> bool:
        if self.algebra is not other.algebra:
            raise ValueError("Not over the same algebra.")
        if self.word.length != other.word.length:
            return False
        return self.word == other.word or self.word == (~other.word)

    # ── subword helpers ───────────────────────────────────────────────────────

    def sub_word(self, i: int, j: int) -> "StringIndec":
        return StringIndec(self.algebra, self.word.sub_word(i, j))

    def sub_word_range(self, r: range) -> "StringIndec":
        # Ranges are stored as range(i, j+1) (exclusive stop), sub_word uses inclusive [i, j]
        return self.sub_word(r.start, r.stop - 1)

    def _drop(self, n: int) -> "StringIndec":
        return StringIndec(self.algebra, self.word.drop(n))

    def _drop_last(self, n: int) -> "StringIndec":
        return StringIndec(self.algebra, self.word.drop_last(n))

    def _take(self, n: int) -> "StringIndec":
        return StringIndec(self.algebra, self.word.take(n))

    def _take_last(self, n: int) -> "StringIndec":
        return StringIndec(self.algebra, self.word.take_last(n))

    # ── top / socle indices ───────────────────────────────────────────────────

    def top_indices(self) -> List[int]:
        """
        Indices i such that sub_word(i, i) is a top vertex.
        Pattern: positions where a False->True transition occurs in
        [False] + [letter.is_arrow for letter in word] + [True].
        """
        check = [False] + [l.is_arrow for l in self.word.letters] + [True]
        return [i for i, (a, b) in enumerate(zip(check, check[1:])) if (not a and b)]

    def socle_indices(self) -> List[int]:
        """Indices i such that sub_word(i, i) is a socle vertex."""
        check = [True] + [l.is_arrow for l in self.word.letters] + [False]
        return [i for i, (a, b) in enumerate(zip(check, check[1:])) if (a and not b)]

    def top_vertices(self) -> list:
        return [self.word.get_vertex_at(i) for i in self.top_indices()]

    def socle_vertices(self) -> list:
        return [self.word.get_vertex_at(i) for i in self.socle_indices()]

    def top(self) -> List["StringIndec"]:
        return [self.algebra.simple_at(v) for v in self.top_vertices()]

    def socle(self) -> List["StringIndec"]:
        return [self.algebra.simple_at(v) for v in self.socle_vertices()]

    # ── submodule / quotient ranges ───────────────────────────────────────────

    def _sub_ranges(self) -> List[range]:
        """
        Ranges [i, j] (as range(i, j+1)) such that word.sub_word(i, j) is a submodule word:
        - i == 0 or word[i-1] is an arrow
        - j == len or word[j] is an inverse arrow
        """
        results = []
        n = self.word.length
        for i in range(n + 1):
            if i != 0 and not self.word.letters[i - 1].is_arrow:
                continue
            for j in range(i, n + 1):
                if j != n and self.word.letters[j].is_arrow:
                    continue
                results.append(range(i, j + 1))
        return results

    def _quot_ranges(self) -> List[range]:
        """
        Ranges [i, j] such that word.sub_word(i, j) is a quotient module word:
        - i == 0 or word[i-1] is an inverse arrow
        - j == len or word[j] is an arrow
        """
        results = []
        n = self.word.length
        for i in range(n + 1):
            if i != 0 and self.word.letters[i - 1].is_arrow:
                continue
            for j in range(i, n + 1):
                if j != n and not self.word.letters[j].is_arrow:
                    continue
                results.append(range(i, j + 1))
        return results

    # ── Hom computation ───────────────────────────────────────────────────────

    def _private_hom(self, other: "StringIndec") -> int:
        """
        dim Hom(self, other).
        Count pairs (quot_range of self, sub_range of other) where the
        subwords match (equal or inverse).
        """
        count = 0
        for qr in self._quot_ranges():
            w1 = self.sub_word_range(qr).word
            w1_len = w1.length
            for sr in other._sub_ranges():
                w2 = other.sub_word_range(sr).word
                if w1_len != w2.length:
                    continue
                if w1 == w2 or w1 == ~w2:
                    count += 1
        return count

    def hom(self, other: "StringIndec") -> int:
        return self._private_hom(other)

    def is_brick(self) -> bool:
        return self.hom(self) == 1

    # ── end-shape helpers (peak / deep) ──────────────────────────────────────

    def _ends_peak(self) -> bool:
        """True if no legal extension of the form word * !ar exists."""
        for ar in self.algebra.arrows:
            if ar.to_vertex == self.word.to_vertex:
                cand = self.word * (~ar)
                if self.algebra.is_legal(cand):
                    return False
        return True

    def _ends_deep(self) -> bool:
        """True if no legal extension of the form word * ar exists."""
        for ar in self.algebra.arrows:
            if ar.from_vertex == self.word.to_vertex:
                cand = self.word * ar
                if self.algebra.is_legal(cand):
                    return False
        return True

    def _starts_peak(self) -> bool:
        return (~self)._ends_peak()

    def _starts_deep(self) -> bool:
        return (~self)._ends_deep()

    # ── hook / cohook operations ──────────────────────────────────────────────

    def _make_end_deep(self) -> List["StringIndec"]:
        """Maximal extensions word * ar1 * ar2 * ... (arrows only)."""
        return [
            StringIndec(self.algebra, w)
            for w in self.algebra.words_starting_with(
                self.word, add_only_arrow=True, only_maximal=True
            )
        ]

    def _make_start_deep(self) -> List["StringIndec"]:
        return [(~m) for m in (~self)._make_end_deep()]

    def _make_end_peak(self) -> List["StringIndec"]:
        """Maximal extensions word * !ar1 * !ar2 * ... (inverse arrows only)."""
        return [
            StringIndec(self.algebra, w)
            for w in self.algebra.words_starting_with(
                self.word, add_only_inverse=True, only_maximal=True
            )
        ]

    def _make_start_peak(self) -> List["StringIndec"]:
        return [(~m) for m in (~self)._make_end_peak()]

    def _remove_left_hook(self) -> Optional["StringIndec"]:
        """If word starts in a deep (!a !b c d), return the module after first arrow."""
        assert self._starts_deep()
        idx = next((i for i, l in enumerate(self.word.letters) if l.is_arrow), -1)
        if idx == -1:
            return None
        return self.sub_word(idx + 1, self.word.length)

    def _remove_left_cohook(self) -> Optional["StringIndec"]:
        """If word starts on a peak (a b !c !d), return the module after first inverse."""
        assert self._starts_peak()
        idx = next((i for i, l in enumerate(self.word.letters) if not l.is_arrow), -1)
        if idx == -1:
            return None
        return self.sub_word(idx + 1, self.word.length)

    def _remove_right_hook(self) -> Optional["StringIndec"]:
        result = (~self)._remove_left_hook()
        return (~result) if result is not None else None

    def _remove_right_cohook(self) -> Optional["StringIndec"]:
        result = (~self)._remove_left_cohook()
        return (~result) if result is not None else None

    def _add_right_hook(self) -> List["StringIndec"]:
        """
        For each arrow ar ending at word.to (so we can append !ar),
        if word * !ar is legal, extend to deep and return result.
        """
        return [
            StringIndec(self.algebra, self.word * (~ar)).make_end_deep_first()
            for ar in self.algebra.arrows
            if ar.to_vertex == self.word.to_vertex
            and self.algebra.is_legal(self.word * (~ar))
        ]

    def make_end_deep_first(self) -> "StringIndec":
        ends = self._make_end_deep()
        assert len(ends) == 1
        return ends[0]

    def _add_left_hook(self) -> List["StringIndec"]:
        return [(~m) for m in (~self)._add_right_hook()]

    def _add_right_cohook(self) -> List["StringIndec"]:
        """Extend word * ar to a peak on the right."""
        return [
            StringIndec(self.algebra, self.word * ar).make_end_peak_first()
            for ar in self.algebra.arrows
            if ar.from_vertex == self.word.to_vertex
            and self.algebra.is_legal(self.word * ar)
        ]

    def make_end_peak_first(self) -> "StringIndec":
        ends = self._make_end_peak()
        assert len(ends) == 1
        return ends[0]

    def _add_left_cohook(self) -> List["StringIndec"]:
        return [(~m) for m in (~self)._add_right_cohook()]

    # ── projective / injective ────────────────────────────────────────────────

    def is_projective(self) -> bool:
        return (
            len(self.top()) == 1
            and self._starts_deep()
            and self._ends_deep()
        )

    def is_injective(self) -> bool:
        return (
            len(self.socle()) == 1
            and self._starts_peak()
            and self._ends_peak()
        )

    # ── radical / coradical ───────────────────────────────────────────────────

    def radical(self) -> List["StringIndec"]:
        """
        Submodule obtained by removing the top:
        - remove each "peak" vertex, splitting the word into pieces.
        """
        indices = self.top_indices()
        result = []
        if indices[0] != 0:
            result.append(self.sub_word(0, indices[0] - 1))
        if indices[-1] != self.word.length:
            result.append(self.sub_word(indices[-1] + 1, self.word.length))
        for i, j in zip(indices, indices[1:]):
            result.append(self.sub_word(i + 1, j - 1))
        return result

    def coradical(self) -> List["StringIndec"]:
        """
        Quotient obtained by removing the socle.
        """
        indices = self.socle_indices()
        result = []
        if indices[0] != 0:
            result.append(self.sub_word(0, indices[0] - 1))
        if indices[-1] != self.word.length:
            result.append(self.sub_word(indices[-1] + 1, self.word.length))
        for i, j in zip(indices, indices[1:]):
            result.append(self.sub_word(i + 1, j - 1))
        return result

    def proj_cover(self) -> List["StringIndec"]:
        return [self.algebra.proj_at(v) for v in self.top_vertices()]

    def inj_hull(self) -> List["StringIndec"]:
        return [self.algebra.inj_at(v) for v in self.socle_vertices()]

    # ── syzygy ────────────────────────────────────────────────────────────────

    def _mountain_to_valley(self, mx: "StringIndec") -> List["Word"]:
        """
        Given a submodule mx with simple top and dim > 1,
        compute the syzygy contribution (one or two words).
        """
        assert len(mx.top_vertices()) == 1
        assert mx.dim() > 1

        # For string algebra (not biserial):
        left_leg = next(
            self.algebra.words_ending_with(
                mx.word, add_only_inverse=True, only_maximal=True
            )
        )
        left_leg = (~left_leg).drop(mx.word.length)

        right_leg = next(
            self.algebra.words_starting_with(
                mx.word, add_only_arrow=True, only_maximal=True
            )
        )
        right_leg = (~right_leg).drop_last(mx.word.length)

        return [left_leg, right_leg]

    def _syzygy_words(self) -> List["Word"]:
        """
        Core syzygy computation.
        Split self into mountains (regions between socle vertices),
        compute valley words for each mountain, then stitch together.
        """
        indices = sorted(set([0] + self.socle_indices() + [self.word.length]))
        valley_list = [
            self._mountain_to_valley(self.sub_word(i, j))
            for i, j in zip(indices, indices[1:])
        ]

        syzygies: List["Word"] = []
        # Initialise from the leftmost valley
        if len(valley_list[0]) == 1:
            intermediate = valley_list[0][0]
        else:  # size == 2
            syzygies.append(valley_list[0][0])  # will be trimmed later
            intermediate = valley_list[0][1]

        for valley in valley_list[1:]:
            if len(valley) == 1:
                # Concatenate in-place using Word's __mul__
                intermediate = intermediate * valley[0]
            else:
                intermediate = intermediate * valley[0]
                syzygies.append(intermediate)
                intermediate = valley[1]
        syzygies.append(intermediate)

        # Trim left-most and right-most
        if syzygies[0].length != 0:
            syzygies[0] = syzygies[0].drop(1)
        else:
            syzygies.pop(0)
        if syzygies and syzygies[-1].length != 0:
            syzygies[-1] = syzygies[-1].drop_last(1)
        elif syzygies:
            syzygies.pop(-1)

        return syzygies

    def _syzygy(self) -> List["StringIndec"]:
        """Internal syzygy (not cached)."""
        if self.is_projective():
            return []
        if self.word.length == 0:
            return self.algebra.proj_at(self.word.from_vertex).radical()
        return [StringIndec(self.algebra, w) for w in self._syzygy_words()]

    def syzygy(self) -> List["StringIndec"]:
        """Cached syzygy."""
        key = ("syz", id(self.word), str(self.word))
        if not hasattr(self.algebra, "_syzygy_cache"):
            self.algebra._syzygy_cache = {}
        cache = self.algebra._syzygy_cache
        if key not in cache:
            cache[key] = self._syzygy()
        return cache[key]

    def syzygy_n(self, n: int) -> List["StringIndec"]:
        result = [self]
        for _ in range(n):
            result = [s for m in result for s in m.syzygy()]
        return result

    # ── cosyzygy ─────────────────────────────────────────────────────────────

    def _valley_to_mountain(self, mx: "StringIndec") -> List["Word"]:
        """
        Dual of _mountain_to_valley: given mx with simple socle and dim > 1,
        compute the cosyzygy contribution.
        """
        assert len(mx.socle_vertices()) == 1
        assert mx.dim() > 1

        left_arm = next(
            self.algebra.words_ending_with(
                mx.word, add_only_arrow=True, only_maximal=True
            )
        )
        left_arm = left_arm.drop_last(mx.word.length)
        left_arm = ~left_arm

        right_arm = next(
            self.algebra.words_starting_with(
                mx.word, add_only_inverse=True, only_maximal=True
            )
        )
        right_arm = right_arm.drop(mx.word.length)
        right_arm = ~right_arm

        return [left_arm, right_arm]

    def _cosyzygy_words(self) -> List["Word"]:
        indices = sorted(set([0] + self.top_indices() + [self.word.length]))
        mountain_list = [
            self._valley_to_mountain(self.sub_word(i, j))
            for i, j in zip(indices, indices[1:])
        ]

        cosyzygies: List["Word"] = []
        if len(mountain_list[0]) == 1:
            intermediate = mountain_list[0][0]
        else:
            cosyzygies.append(mountain_list[0][0])
            intermediate = mountain_list[0][1]

        for mountain in mountain_list[1:]:
            if len(mountain) == 1:
                intermediate = intermediate * mountain[0]
            else:
                intermediate = intermediate * mountain[0]
                cosyzygies.append(intermediate)
                intermediate = mountain[1]
        cosyzygies.append(intermediate)

        if cosyzygies[0].length != 0:
            cosyzygies[0] = cosyzygies[0].drop(1)
        else:
            cosyzygies.pop(0)
        if cosyzygies and cosyzygies[-1].length != 0:
            cosyzygies[-1] = cosyzygies[-1].drop_last(1)
        elif cosyzygies:
            cosyzygies.pop(-1)

        return cosyzygies

    def cosyzygy(self) -> List["StringIndec"]:
        if self.is_injective():
            return []
        if self.word.length == 0:
            return self.algebra.inj_at(self.word.from_vertex).coradical()
        return [StringIndec(self.algebra, w) for w in self._cosyzygy_words()]

    def cosyzygy_n(self, n: int) -> List["StringIndec"]:
        result = [self]
        for _ in range(n):
            result = [s for m in result for s in m.cosyzygy()]
        return result

    # ── stable Hom spaces ─────────────────────────────────────────────────────

    def stable_hom(self, other: "StringIndec") -> int:
        """
        dim underline{Hom}(self, other) — projectively stable.
        Uses the exact sequence from the proj cover of other:
          0 -> (self, syz(other)) -> (self, P) -> (self, other) -> stable_hom -> 0
        """
        syz = other.syzygy()
        proj_cover = other.proj_cover()
        hom_to_syz = sum(self.hom(s) for s in syz)
        hom_to_proj = sum(self.hom(p) for p in proj_cover)
        hom_to_other = self.hom(other)
        return hom_to_syz - hom_to_proj + hom_to_other

    def inj_stable_hom(self, other: "StringIndec") -> int:
        """
        dim overline{Hom}(self, other) — injectively stable.
        Uses exact sequence from the inj hull of self.
        """
        cosyz = self.cosyzygy()
        inj_hull = self.inj_hull()
        first = sum(c.hom(other) for c in cosyz)
        second = sum(i.hom(other) for i in inj_hull)
        third = self.hom(other)
        return first - second + third

    def ext1(self, other: "StringIndec") -> int:
        """
        dim Ext^1(self, other).
        Uses: 0 -> (self, other) -> (P, other) -> (syz, other) -> Ext^1 -> 0
        """
        syz = self.syzygy()
        top_verts = self.top_vertices()
        other_verts = other.vertex_list()
        hom_self = self.hom(other)
        hom_proj = sum(
            sum(1 for v2 in other_verts if v2 == v) for v in top_verts
        )
        hom_syz = sum(s.hom(other) for s in syz)
        return hom_self - hom_proj + hom_syz

    def proj_dim(self) -> Optional[int]:
        """Projective dimension, None if infinite."""
        queue: deque = deque([[self]])
        maximal_paths = []
        while queue:
            path = queue.popleft()
            next_mods = list({s for m in [path[-1]] for s in m.syzygy()})
            if not next_mods:
                maximal_paths.append(path)
            for nxt in next_mods:
                if any(nxt.is_isomorphic(p) for p in path):
                    return None
                queue.append(path + [nxt])
        if not maximal_paths:
            return 0
        return max(len(p) - 1 for p in maximal_paths)

    def inj_dim(self) -> Optional[int]:
        """Injective dimension, None if infinite."""
        queue: deque = deque([[self]])
        maximal_paths = []
        while queue:
            path = queue.popleft()
            next_mods = list({s for m in [path[-1]] for s in m.cosyzygy()})
            if not next_mods:
                maximal_paths.append(path)
            for nxt in next_mods:
                if any(nxt.is_isomorphic(p) for p in path):
                    return None
                queue.append(path + [nxt])
        if not maximal_paths:
            return 0
        return max(len(p) - 1 for p in maximal_paths)

    def all_syzygies(self) -> List["StringIndec"]:
        """All indecomposable summands appearing in Ω^i(self) for i >= 0."""
        visited = [self]
        queue: deque = deque([self])
        while queue:
            cur = queue.popleft()
            for nxt in cur.syzygy():
                if not any(nxt.is_isomorphic(v) for v in visited):
                    visited.append(nxt)
                    queue.append(nxt)
        return visited

    # ── AR sequences ─────────────────────────────────────────────────────────

    def source_sequence(self) -> Tuple[List["StringIndec"], Optional["StringIndec"]]:
        """
        The source (left) AR sequence ending at self: 0 -> tau^-X -> E -> X -> 0.
        Returns (list_of_middle_terms, tau_minus_X).
        Only for string algebras (not biserial).
        """
        left = self._starts_peak()
        right = self._ends_peak()

        if not left and not right:
            if self.is_simple():
                middle = self._add_left_hook()
                tau_inv_candidates = self._add_right_hook()
                if tau_inv_candidates:
                    tau_inv = tau_inv_candidates[0]._drop_last(1)
                else:
                    tau_inv = middle[0]._drop_last(1) if middle else None
            else:
                left_hooks = self._add_left_hook()
                right_hooks = self._add_right_hook()
                middle = left_hooks + right_hooks
                if len(middle) == 2:
                    tau_inv = left_hooks[0]._add_right_hook()[0]
                elif len(middle) == 1:
                    tau_inv = self._add_right_hook()[0]._drop(1)
                else:
                    raise RuntimeError("source_sequence: unexpected middle size")
        elif left and not right:
            right_hooks = self._add_right_hook()
            cohook = self._remove_left_cohook()
            middle = ([cohook] if cohook is not None else []) + right_hooks
            tau_inv = right_hooks[0]._remove_left_cohook()
        elif not left and right:
            left_hooks = self._add_left_hook()
            cohook = self._remove_right_cohook()
            middle = left_hooks + ([cohook] if cohook is not None else [])
            tau_inv = left_hooks[0]._remove_right_cohook()
        else:
            # starts and ends on a peak → injective-like
            lc = self._remove_left_cohook()
            rc = self._remove_right_cohook()
            middle = [m for m in [lc, rc] if m is not None]
            if len(self.socle_vertices()) == 1:
                tau_inv = None
            else:
                tau_inv = lc._remove_right_cohook() if lc else None

        return middle, tau_inv

    def sink_sequence(self) -> Tuple[List["StringIndec"], Optional["StringIndec"]]:
        """
        The sink (right) AR sequence starting at self: 0 -> X -> E -> tau X -> 0.
        Returns (list_of_middle_terms, tau_X).
        """
        left = self._starts_deep()
        right = self._ends_deep()

        if not left and not right:
            if self.is_simple():
                middle = self._add_left_cohook()
                right_cohooks = self._add_right_cohook()
                if right_cohooks:
                    tau = right_cohooks[0]._drop(1)
                else:
                    tau = middle[0]._drop(1) if middle else None
            else:
                lc = self._add_left_cohook()
                rc = self._add_right_cohook()
                middle = lc + rc
                if len(middle) == 2:
                    tau = lc[0]._add_right_cohook()[0]
                elif len(middle) == 1:
                    tau = self._add_right_cohook()[0]._drop_last(1)
                else:
                    raise RuntimeError("sink_sequence: unexpected middle size")
        elif left and not right:
            right_cohooks = self._add_right_cohook()
            hook = self._remove_left_hook()
            middle = right_cohooks + ([hook] if hook is not None else [])
            tau = right_cohooks[0]._remove_left_hook()
        elif not left and right:
            left_cohooks = self._add_left_cohook()
            hook = self._remove_right_hook()
            middle = left_cohooks + ([hook] if hook is not None else [])
            tau = left_cohooks[0]._remove_right_hook()
        else:
            # starts and ends deep → projective-like
            lh = self._remove_left_hook()
            rh = self._remove_right_hook()
            middle = [m for m in [lh, rh] if m is not None]
            if len(self.top_vertices()) == 1:
                tau = None
            else:
                tau = lh._remove_right_hook() if lh else None

        return middle, tau

    def tau_plus(self) -> Optional["StringIndec"]:
        """AR translation τX (None if projective)."""
        return self.sink_sequence()[1]

    def tau_minus(self) -> Optional["StringIndec"]:
        """Inverse AR translation τ⁻X (None if injective)."""
        return self.source_sequence()[1]

    def theta_plus(self) -> List["StringIndec"]:
        """Middle terms of the sink map (right almost-split)."""
        return self.sink_sequence()[0]

    def theta_minus(self) -> List["StringIndec"]:
        """Middle terms of the source map (left almost-split)."""
        return self.source_sequence()[0]

    # ── dominantdim / codominantdim ───────────────────────────────────────────

    def dominant_dim(self) -> Optional[int]:
        """Dominant dimension. None if infinite."""
        def is_good(m):
            return all(ih.is_projective() for ih in m.inj_hull())

        queue: deque = deque([[self]])
        visited = [self]
        while queue:
            path = queue.popleft()
            if not is_good(path[-1]):
                return len(path) - 1
            for nxt in path[-1].cosyzygy():
                if any(nxt.is_isomorphic(v) for v in visited):
                    continue
                queue.append(path + [nxt])
                visited.append(nxt)
        return None

    def co_dominant_dim(self) -> Optional[int]:
        """Co-dominant dimension. None if infinite."""
        def is_good(m):
            return all(pc.is_injective() for pc in m.proj_cover())

        queue: deque = deque([[self]])
        visited = [self]
        while queue:
            path = queue.popleft()
            if not is_good(path[-1]):
                return len(path) - 1
            for nxt in path[-1].syzygy():
                if any(nxt.is_isomorphic(v) for v in visited):
                    continue
                queue.append(path + [nxt])
                visited.append(nxt)
        return None
