#!/usr/bin/env python3
"""
Digital Logic & Hardware CTF Solver (tools/dld_solver.py)
Provides deterministic solvers for:
1. LFSR simulation, cycle detection, and Berlekamp-Massey polynomial recovery.
2. Synchronous & asynchronous JK/D/T flip-flop circuit simulation.
3. Hardware encodings: Excess-3 (XS-3), Gray code, BCD, split-bank 7-bit ASCII.
"""

from typing import List, Tuple, Optional, Dict, Any

class DLDEncoder:
    """Hardware encoding and decoding routines."""
    
    @staticmethod
    def excess3_decode(val: int) -> Optional[int]:
        """Convert a 4-bit binary value to Excess-3 decimal digit (val - 3)."""
        if 3 <= val <= 12:
            return val - 3
        return None  # Invalid BCD digit in Excess-3

    @staticmethod
    def excess3_encode(digit: int) -> int:
        """Convert a decimal digit (0-9) to 4-bit Excess-3 value."""
        if not (0 <= digit <= 9):
            raise ValueError(f"Excess-3 only encodes single decimal digits (0-9), got {digit}")
        return digit + 3

    @staticmethod
    def binary_to_gray(n: int) -> int:
        """Convert binary integer to Gray code."""
        return n ^ (n >> 1)

    @staticmethod
    def gray_to_binary(g: int) -> int:
        """Convert Gray code integer to binary."""
        b = 0
        while g:
            b ^= g
            g >>= 1
        return b

    @staticmethod
    def assemble_7bit_ascii(high_3bits: int, low_4bits: int) -> str:
        """Combine 3-bit high bank with 4-bit low bank to yield ASCII character."""
        code = ((high_3bits & 0x7) << 4) | (low_4bits & 0xF)
        return chr(code) if 32 <= code <= 126 else f"\\x{code:02x}"


class LFSR:
    """Linear Feedback Shift Register simulation and recovery."""
    
    def __init__(self, size: int, taps: List[int], state: Optional[List[int]] = None):
        """
        size: Number of stages in the shift register.
        taps: 0-indexed positions of feedback taps XORed together.
        state: Initial state list of bits [q0, q1, ..., q(n-1)]. Defaults to all 1s.
        """
        self.size = size
        self.taps = taps
        self.state = state[:] if state else [1] * size

    def step(self) -> int:
        """Perform one clock step (shift right, feedback to stage 0). Returns output bit."""
        out_bit = self.state[-1]
        feedback = 0
        for t in self.taps:
            feedback ^= self.state[t]
        self.state = [feedback] + self.state[:-1]
        return out_bit

    def get_state_int(self, msb_first: bool = False) -> int:
        """Get current register state as an integer."""
        val = 0
        bits = self.state if msb_first else self.state[::-1]
        for b in bits:
            val = (val << 1) | b
        return val

    def find_cycle(self, max_steps: int = 1024) -> List[Tuple[int, List[int], int]]:
        """Run until cycle repeats or max_steps reached. Returns (step, state_bits, int_val)."""
        seen: Dict[Tuple[int, ...], int] = {}
        history = []
        for step in range(max_steps):
            st_tuple = tuple(self.state)
            val = self.get_state_int(msb_first=False)
            if st_tuple in seen:
                break
            seen[st_tuple] = step
            history.append((step, list(self.state), val))
            self.step()
        return history

    @staticmethod
    def berlekamp_massey(keystream: List[int]) -> List[int]:
        """
        Recover the minimal feedback polynomial from a known bit keystream.
        Returns the connection polynomial coefficients.
        """
        n = len(keystream)
        c = [1] + [0] * n
        b = [1] + [0] * n
        l = 0
        m = 1
        for i in range(n):
            d = keystream[i]
            for j in range(1, l + 1):
                d ^= c[j] & keystream[i - j]
            if d == 1:
                t = c[:]
                for j in range(n - i):
                    if j + m < len(c):
                        c[j + m] ^= b[j]
                if 2 * l <= i:
                    l = i + 1 - l
                    b = t
                    m = 1
                else:
                    m += 1
            else:
                m += 1
        return c[:l + 1]


class FlipFlopSimulator:
    """Simulates custom synchronous or asynchronous flip-flop networks."""
    
    @staticmethod
    def jk_next(current_q: int, j: int, k: int) -> int:
        """Compute next state of a JK flip-flop."""
        if j == 0 and k == 0:
            return current_q
        elif j == 0 and k == 1:
            return 0
        elif j == 1 and k == 0:
            return 1
        else:  # j == 1 and k == 1
            return 1 - current_q

    @staticmethod
    def d_next(d: int) -> int:
        """Compute next state of a D flip-flop."""
        return d & 1

    @staticmethod
    def simulate_synchronous(
        initial_state: List[int],
        transition_fn,
        steps: int = 16
    ) -> List[Tuple[int, List[int]]]:
        """
        Simulate a synchronous circuit for a given number of steps.
        transition_fn: Callable[[List[int]], List[int]] mapping current Qs to next Qs.
        """
        history = [(0, list(initial_state))]
        state = list(initial_state)
        for step in range(1, steps + 1):
            state = transition_fn(state)
            history.append((step, list(state)))
        return history


if __name__ == "__main__":
    print("DLD Solver Tool initialized successfully.")
    # Quick self-test: 4-bit LFSR with taps at 2, 3
    lfsr = LFSR(size=4, taps=[2, 3], state=[1, 1, 1, 1])
    cycle = lfsr.find_cycle(20)
    print(f"Self-test: LFSR cycle length = {len(cycle)} states.")
