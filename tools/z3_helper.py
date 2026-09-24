#!/usr/bin/env python3
"""
Z3 Constraint Solving Helper (tools/z3_helper.py)
Provides standard templates for:
1. Reversing string check / keygen functions.
2. Bitwise constraint satisfaction (hashes, linear feedback, custom scramblers).
3. Integer & modular arithmetic solving.
"""

from typing import List, Optional, Callable
import z3

class Z3StringSolver:
    """Helper to solve byte-level and character-level string constraints."""

    @staticmethod
    def solve_printable_string(
        length: int,
        constraint_fn: Callable[[List[z3.BitVecRef], z3.Solver], None],
        prefix: str = "",
        suffix: str = "",
        custom_alphabet: Optional[str] = None
    ) -> Optional[str]:
        """
        Creates an array of 8-bit BitVecs, applies printable constraints and custom constraints,
        and solves for the valid string.
        """
        solver = z3.Solver()
        chars = [z3.BitVec(f"c_{i}", 8) for i in range(length)]

        # Apply printable ASCII constraint (0x20 to 0x7E)
        if custom_alphabet:
            valid_bytes = [ord(c) for c in custom_alphabet]
            for c in chars:
                solver.add(z3.Or([c == b for b in valid_bytes]))
        else:
            for c in chars:
                solver.add(z3.And(c >= 0x20, c <= 0x7E))

        # Enforce prefix
        for i, ch in enumerate(prefix):
            if i < length:
                solver.add(chars[i] == ord(ch))

        # Enforce suffix
        for i, ch in enumerate(suffix):
            idx = length - len(suffix) + i
            if 0 <= idx < length:
                solver.add(chars[idx] == ord(ch))

        # Apply user logic
        constraint_fn(chars, solver)

        if solver.check() == z3.sat:
            m = solver.model()
            res = bytes([m.eval(c).as_long() for c in chars]).decode("latin1")
            return res
        return None


class Z3ArithmeticSolver:
    """Solves system of linear / non-linear integer equations."""

    @staticmethod
    def solve_system(num_vars: int, constraint_fn: Callable[[List[z3.Int], z3.Solver], None]) -> Optional[List[int]]:
        """Solves a system of integer variables."""
        solver = z3.Solver()
        vars_ = [z3.Int(f"x_{i}") for i in range(num_vars)]
        constraint_fn(vars_, solver)

        if solver.check() == z3.sat:
            m = solver.model()
            return [m.eval(v).as_long() for v in vars_]
        return None


if __name__ == "__main__":
    print("Z3 Helper Tool initialized.")
    # Quick self-test: solve a simple 5-char string where c[0]^c[1] == 10 and starts with 'A'
    def test_logic(chars, s):
        s.add(chars[0] ^ chars[1] == 10)
    sol = Z3StringSolver.solve_printable_string(length=2, constraint_fn=test_logic, prefix="A")
    print(f"Self-test: Solved string = {repr(sol)}")
