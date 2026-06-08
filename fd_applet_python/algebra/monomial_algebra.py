"""
Python conversion of MonomialAlgebra.kt

Monomial algebra kQ/<R> where R is a set of path (monomial) relations.
"""

from __future__ import annotations
from collections import deque
from functools import cached_property
from typing import TypeVar, Generic, List, Optional, Iterator, TYPE_CHECKING

from .quiver_algebra import QuiverAlgebra

if TYPE_CHECKING:
    from ..quiver.quiver import Quiver
    from ..quiver.monomial import Monomial
    from ..quiver.word import Word
    from ..quiver.letter import Letter
    from ..quiver.arrow import Arrow

T = TypeVar("T")
U = TypeVar("U")


class MonomialAlgebra(QuiverAlgebra[T, U]):
    """
    Monomial algebra kQ/<R> — a quiver algebra whose relations are all paths.

    Args:
        quiver: the underlying quiver.
        initial_relations: list of Monomial objects (overlap/duplication allowed).
    """

    def __init__(self, quiver: "Quiver[T, U]", initial_relations: List["Monomial[T, U]"]):
        super().__init__(quiver)
        # Remove overlapping (non-minimal) relations
        temp: List["Monomial[T, U]"] = []
        for rel in initial_relations:
            if rel in temp:
                continue
            for a in rel.arrows:
                if a not in self.arrows:
                    raise ValueError(f"Each arrow in relations should be in the quiver.")
            if rel.length < 2:
                raise ValueError("The length of each relation must be >= 2.")
            minimal = True
            for rel2 in initial_relations:
                if rel == rel2:
                    continue
                windows = [
                    rel.arrows[i: i + rel2.length]
                    for i in range(len(rel.arrows) - rel2.length + 1)
                ]
                from ..quiver.monomial import Monomial as Mon
                if any(Mon(w) == rel2 for w in windows if w):
                    minimal = False
                    break
            if minimal:
                temp.append(rel)
        self.relations: List["Monomial[T, U]"] = temp

        # doubled arrows: forward + inverse letters
        self._doubled_arrows: List["Letter[T, U]"] = (
            [a.to_letter() for a in self.arrows] +
            [~a for a in self.arrows]
        )
        # forbidden subwords: relations, their inverses, a*!a, !a*a
        self._forbidden_words: List["Word[T, U]"] = (
            [r.to_word() for r in self.relations] +
            [~r.to_word() for r in self.relations] +
            [a.to_word() * (~a) for a in self.arrows] +
            [(~a).to_word() * a for a in self.arrows]
        )

    # ── cached heavy computations ────────────────────────────────────────────

    @cached_property
    def _path_automaton(self):
        return self._make_path_automaton()

    @cached_property
    def _word_automaton(self):
        return self._make_word_automaton()

    @cached_property
    def _is_fd(self) -> bool:
        return self._fd_check()

    @cached_property
    def is_band_finite(self) -> bool:
        return self._word_automaton.primitive_cycle_finite()

    @cached_property
    def is_word_finite(self) -> bool:
        return self._word_finite_check()

    # ── QuiverAlgebra interface ───────────────────────────────────────────────

    def print_info(self):
        print("A monomial algebra with quiver:")
        self.quiver.print_info()
        print("---- and relations ----")
        print(self.relations)

    def is_finite_dimensional(self) -> bool:
        return self._is_fd

    def dim(self) -> Optional[int]:
        if not self._is_fd:
            return None
        return sum(len(self.paths_from(v)) for v in self.vertices)

    def is_string_algebra(self) -> bool:
        try:
            from .string_algebra import StringAlgebra
            StringAlgebra(self.quiver, self.relations)
            return True
        except (ValueError, Exception):
            return False

    def is_gentle_algebra(self) -> bool:
        try:
            from .string_algebra import GentleAlgebra
            GentleAlgebra(self.quiver, self.relations)
            return True
        except (ValueError, Exception):
            return False

    def is_rep_finite(self) -> bool:
        raise NotImplementedError("Only supported for special biserial algebras.")

    def simple_at(self, vtx: T):
        from .string_indec_full import StringIndec
        from ..quiver.word import to_trivial_word
        return StringIndec.from_word(self, to_trivial_word(vtx), check=False)

    def proj_at(self, vtx: T):
        raise NotImplementedError("Only supported for string algebras.")

    def inj_at(self, vtx: T):
        raise NotImplementedError("Only supported for string algebras.")

    def string_indecs(self, length_bound: Optional[int] = None, non_isomorphic: bool = True):
        from .string_indec_full import StringIndec
        word_list = []
        for word in self._words(length_bound):
            if not non_isomorphic or (~word) not in word_list:
                word_list.append(word)
        return [StringIndec.from_word(self, w, check=False) for w in word_list]

    # ── legality check ────────────────────────────────────────────────────────

    def is_legal(self, word: "Word[T, U]", check_only_last: bool = False) -> bool:
        """Returns True if word contains no forbidden subword."""
        for letter in word.letters:
            if letter not in self._doubled_arrows:
                raise ValueError(f"Each letter should be in the quiver.")
        if check_only_last:
            return all(
                fw.letters != word.letters[-fw.length:] for fw in self._forbidden_words
            )
        for fw in self._forbidden_words:
            windows = [
                word.letters[i: i + fw.length]
                for i in range(len(word.letters) - fw.length + 1)
            ]
            if any(w == fw.letters for w in windows):
                return False
        return True

    # ── path enumeration ──────────────────────────────────────────────────────

    def _paths_sequence_from(
        self, vtx: T, length_bound: Optional[int] = None, only_maximal: bool = False
    ) -> Iterator["Word[T, U]"]:
        from ..quiver.word import to_trivial_word
        yield from self.words_starting_with(
            to_trivial_word(vtx), length_bound,
            add_only_arrow=True, only_maximal=only_maximal,
        )

    def _paths_sequence_to(
        self, vtx: T, length_bound: Optional[int] = None, only_maximal: bool = False
    ) -> Iterator["Word[T, U]"]:
        from ..quiver.word import to_trivial_word
        yield from self.words_ending_with(
            to_trivial_word(vtx), length_bound,
            add_only_arrow=True, only_maximal=only_maximal,
        )

    def paths_from(
        self, vtx: T, length_bound: Optional[int] = None, only_maximal: bool = False
    ) -> List["Word[T, U]"]:
        if length_bound is None and not self._fd_check(vtx):
            raise ValueError("There are infinitely many paths!")
        return list(self._paths_sequence_from(vtx, length_bound, only_maximal))

    def paths_to(
        self, vtx: T, length_bound: Optional[int] = None, only_maximal: bool = False
    ) -> List["Word[T, U]"]:
        if length_bound is None and not self.is_finite_dimensional():
            raise ValueError("There are infinitely many paths!")
        return list(self._paths_sequence_to(vtx, length_bound, only_maximal))

    # ── word enumeration ──────────────────────────────────────────────────────

    def _words_from(self, vtx: T, length_bound: Optional[int] = None) -> List["Word[T, U]"]:
        from ..quiver.word import to_trivial_word
        if length_bound is None and not self._word_finite_check(vtx):
            raise ValueError("There are infinitely many words!")
        return list(self.words_starting_with(to_trivial_word(vtx), length_bound))

    def _words(self, length_bound: Optional[int] = None) -> List["Word[T, U]"]:
        result = []
        for v in self.vertices:
            result.extend(self._words_from(v, length_bound))
        return result

    # ── bands ─────────────────────────────────────────────────────────────────

    def primitive_bands(self) -> List["Word[T, U]"]:
        """Returns one representative per equivalence class of primitive bands."""
        def _to_word(cycle):
            return cycle.letters[0].label.to_word() if False else _letters_word(cycle)

        def _letters_word(cycle):
            # Each label of the word automaton's cycle is a Letter in the original algebra
            from ..quiver.word import letters_to_word
            letters = [state_letter.label for state_letter in cycle.letters]
            return letters_to_word(letters, check=False)

        candidates = [_letters_word(c) for c in self._word_automaton.simple_cycles()]

        def is_rotation(l1, l2):
            if len(l1) != len(l2):
                return False
            double = l2 + l2
            size = len(l1)
            return any(double[i:i+size] == l1 for i in range(len(double) - size + 1))

        result = []
        for word in candidates:
            if any(is_rotation(word.letters, (~w).letters) for w in result):
                continue
            result.append(word)
        return result

    # ── automaton transition ──────────────────────────────────────────────────

    def _transition(self, state, letter: "Letter[T, U]"):
        """
        state = (vtx, word_suffix).
        Returns next state or None if the transition is forbidden.
        """
        from ..quiver.word import Word
        _, current_word = state
        try:
            long_word = current_word * letter
        except (ValueError, Exception):
            return None
        if not self.is_legal(long_word, check_only_last=True):
            return None
        # Optimization: if direction flips, next suffix = just the new letter
        if long_word.letters and long_word.letters[0].is_arrow != letter.is_arrow:
            return (letter.to_vertex, letter.to_word())
        for i in range(long_word.length):
            temp = long_word.drop(i)
            if any(
                fw.letters[:temp.length] == temp.letters for fw in self._forbidden_words
            ):
                return (letter.to_vertex, temp)
        raise RuntimeError("Automaton transition failed — something is wrong.")

    def _make_automaton(self, use_doubled: bool):
        """Generic BFS automaton builder (path automaton or word automaton)."""
        from ..quiver.quiver import Quiver as Q
        from ..quiver.arrow import Arrow
        from ..quiver.word import to_trivial_word

        letters = self._doubled_arrows if use_doubled else [a.to_letter() for a in self.arrows]
        initial_states = [(v, to_trivial_word(v)) for v in self.vertices]
        states = list(initial_states)
        state_set = set(range(len(states)))
        transition_arrows = []
        queue = deque(range(len(states)))

        while queue:
            idx = queue.popleft()
            state = states[idx]
            vtx = state[0]
            for letter in (l for l in letters if l.from_vertex == vtx):
                next_state = self._transition(state, letter)
                if next_state is None:
                    continue
                # Find or register next_state
                try:
                    next_idx = next(
                        i for i, s in enumerate(states)
                        if s[0] == next_state[0] and s[1] == next_state[1]
                    )
                except StopIteration:
                    next_idx = len(states)
                    states.append(next_state)
                    queue.append(next_idx)
                transition_arrows.append(Arrow((states[idx][0], states[idx][1]), (states[next_idx][0], states[next_idx][1]), label=letter))

        # Quiver vertices = integer indices; arrows carry Letter labels
        # This avoids trying to use unhashable Word objects as vertex identifiers.
        fixed_arrows = []
        for i, s in enumerate(states):
            for j, s2 in enumerate(states):
                pass  # just enumerate
        # Rebuild: states[idx] and states[next_idx] were used as from/to — switch to ints
        int_arrows = []
        for ar in transition_arrows:
            # ar.from_vertex and ar.to_vertex are state tuples — find their indices
            fi = next(k for k,s in enumerate(states) if s[0]==ar.from_vertex[0] and s[1]==ar.from_vertex[1])
            ti = next(k for k,s in enumerate(states) if s[0]==ar.to_vertex[0] and s[1]==ar.to_vertex[1])
            int_arrows.append(Arrow(fi, ti, label=ar.label))
        return Q(list(range(len(states))), int_arrows), states

    def _make_path_automaton(self):
        """Path automaton (only arrow letters)."""
        automaton, _ = self._make_automaton(use_doubled=False)
        return automaton

    def _make_word_automaton(self):
        """Word automaton (both arrows and inverse arrows)."""
        automaton, _ = self._make_automaton(use_doubled=True)
        return automaton

    def _fd_check(self, vtx=None) -> bool:
        automaton, states = self._make_automaton(use_doubled=False)
        if vtx is None:
            return automaton.is_acyclic()
        start_idx = next(
            (i for i, s in enumerate(states) if s[0] == vtx and s[1].length == 0),
            None,
        )
        if start_idx is None:
            return True
        return automaton.is_acyclic(start_idx)

    def _word_finite_check(self, vtx=None) -> bool:
        automaton, states = self._make_automaton(use_doubled=True)
        if vtx is None:
            return automaton.is_acyclic()
        start_idx = next(
            (i for i, s in enumerate(states) if s[0] == vtx and s[1].length == 0),
            None,
        )
        if start_idx is None:
            return True
        return automaton.is_acyclic(start_idx)

    def make(self) -> "MonomialAlgebra":
        """Returns the most specific algebra type that fits."""
        if self.is_gentle_algebra():
            from .string_algebra import GentleAlgebra
            return GentleAlgebra(self.quiver, self.relations)
        if self.is_string_algebra():
            from .string_algebra import StringAlgebra
            return StringAlgebra(self.quiver, self.relations)
        return self
