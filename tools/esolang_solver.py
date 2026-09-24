"""
esolang_solver.py - Deterministic Esoteric Programming Language Interpreters.
Supports: Brainfuck, Ook!, Befunge-93, JSFuck analysis.
Zero-hallucination execution engine.
"""

import re
import sys
from typing import Optional, Tuple, List


def run_brainfuck(code: str, input_data: str = "", max_ops: int = 5_000_000, cell_size: int = 256) -> str:
    """
    Executes Brainfuck code deterministically.
    cell_size: 256 for standard 8-bit wrap, 0 for unbounded integers.
    """
    # Filter code to valid Brainfuck operations
    cleaned = [c for c in code if c in '><+-.,[]']
    
    # Precompute bracket jumps
    bracket_map = {}
    stack = []
    for i, c in enumerate(cleaned):
        if c == '[':
            stack.append(i)
        elif c == ']':
            if not stack:
                raise ValueError(f"Unmatched closing bracket at position {i}")
            start = stack.pop()
            bracket_map[start] = i
            bracket_map[i] = start
    if stack:
        raise ValueError(f"Unmatched opening bracket at position {stack[-1]}")

    tape = [0] * 30000
    ptr = 0
    pc = 0
    in_idx = 0
    output = []
    ops = 0

    while pc < len(cleaned):
        ops += 1
        if ops > max_ops:
            return ''.join(output) + f"\n[!] Execution stopped: max operations ({max_ops}) exceeded."

        cmd = cleaned[pc]
        if cmd == '>':
            ptr += 1
            if ptr >= len(tape):
                tape.extend([0] * 10000)
        elif cmd == '<':
            ptr = max(0, ptr - 1)
        elif cmd == '+':
            tape[ptr] += 1
            if cell_size > 0:
                tape[ptr] %= cell_size
        elif cmd == '-':
            tape[ptr] -= 1
            if cell_size > 0:
                tape[ptr] %= cell_size
        elif cmd == '.':
            output.append(chr(tape[ptr] % 256))
        elif cmd == ',':
            if in_idx < len(input_data):
                tape[ptr] = ord(input_data[in_idx])
                in_idx += 1
            else:
                tape[ptr] = 0
        elif cmd == '[':
            if tape[ptr] == 0:
                pc = bracket_map[pc]
        elif cmd == ']':
            if tape[ptr] != 0:
                pc = bracket_map[pc]

        pc += 1

    return ''.join(output)


def ook_to_brainfuck(ook_code: str) -> str:
    """Converts Ook! code to Brainfuck."""
    tokens = re.findall(r'Ook[\.!\?]', ook_code)
    if len(tokens) % 2 != 0:
        raise ValueError("Invalid Ook! code: Odd number of Ook tokens.")

    bf = []
    ook_map = {
        ('Ook.', 'Ook?'): '>',
        ('Ook?', 'Ook.'): '<',
        ('Ook.', 'Ook.'): '+',
        ('Ook!', 'Ook!'): '-',
        ('Ook!', 'Ook.'): '.',
        ('Ook.', 'Ook!'): ',',
        ('Ook!', 'Ook?'): '[',
        ('Ook?', 'Ook!'): ']'
    }

    for i in range(0, len(tokens), 2):
        pair = (tokens[i], tokens[i+1])
        if pair in ook_map:
            bf.append(ook_map[pair])
        else:
            raise ValueError(f"Unknown Ook pair: {pair}")

    return ''.join(bf)


def run_befunge93(code: str, input_data: str = "", max_ops: int = 1_000_000) -> str:
    """Executes Befunge-93 code deterministically."""
    lines = code.splitlines()
    grid = [list(line.ljust(80)) for line in lines]
    while len(grid) < 25:
        grid.append(list(' ' * 80))

    stack: List[int] = []
    x, y = 0, 0
    dx, dy = 1, 0  # Moving right initially
    string_mode = False
    in_idx = 0
    output = []
    ops = 0

    while ops < max_ops:
        ops += 1
        char = grid[y][x]

        if string_mode:
            if char == '"':
                string_mode = False
            else:
                stack.append(ord(char))
        else:
            if char == '@':
                break
            elif char.isdigit():
                stack.append(int(char))
            elif char == '+':
                a = stack.pop() if stack else 0
                b = stack.pop() if stack else 0
                stack.append(b + a)
            elif char == '-':
                a = stack.pop() if stack else 0
                b = stack.pop() if stack else 0
                stack.append(b - a)
            elif char == '*':
                a = stack.pop() if stack else 0
                b = stack.pop() if stack else 0
                stack.append(b * a)
            elif char == '/':
                a = stack.pop() if stack else 0
                b = stack.pop() if stack else 0
                stack.append(b // a if a != 0 else 0)
            elif char == '%':
                a = stack.pop() if stack else 0
                b = stack.pop() if stack else 0
                stack.append(b % a if a != 0 else 0)
            elif char == '!':
                a = stack.pop() if stack else 0
                stack.append(1 if a == 0 else 0)
            elif char == '`':
                a = stack.pop() if stack else 0
                b = stack.pop() if stack else 0
                stack.append(1 if b > a else 0)
            elif char == '>':
                dx, dy = 1, 0
            elif char == '<':
                dx, dy = -1, 0
            elif char == '^':
                dx, dy = 0, -1
            elif char == 'v':
                dx, dy = 0, 1
            elif char == '?':
                # Deterministic fallback: pick right
                dx, dy = 1, 0
            elif char == '_':
                a = stack.pop() if stack else 0
                dx, dy = (1, 0) if a == 0 else (-1, 0)
            elif char == '|':
                a = stack.pop() if stack else 0
                dx, dy = (0, 1) if a == 0 else (0, -1)
            elif char == '"':
                string_mode = True
            elif char == ':':
                a = stack[-1] if stack else 0
                stack.append(a)
            elif char == '\\':
                a = stack.pop() if stack else 0
                b = stack.pop() if stack else 0
                stack.append(a)
                stack.append(b)
            elif char == '$':
                if stack:
                    stack.pop()
            elif char == '.':
                a = stack.pop() if stack else 0
                output.append(str(a) + " ")
            elif char == ',':
                a = stack.pop() if stack else 0
                output.append(chr(a % 256))
            elif char == '#':
                x = (x + dx) % 80
                y = (y + dy) % 25
            elif char == 'g':
                y_coord = stack.pop() if stack else 0
                x_coord = stack.pop() if stack else 0
                if 0 <= y_coord < len(grid) and 0 <= x_coord < 80:
                    stack.append(ord(grid[y_coord][x_coord]))
                else:
                    stack.append(0)
            elif char == 'p':
                y_coord = stack.pop() if stack else 0
                x_coord = stack.pop() if stack else 0
                val = stack.pop() if stack else 0
                if 0 <= y_coord < len(grid) and 0 <= x_coord < 80:
                    grid[y_coord][x_coord] = chr(val % 256)
            elif char == '&':
                # Read integer from input
                m = re.match(r'^\s*(-?\d+)', input_data[in_idx:])
                if m:
                    stack.append(int(m.group(1)))
                    in_idx += len(m.group(0))
                else:
                    stack.append(0)
            elif char == '~':
                # Read character from input
                if in_idx < len(input_data):
                    stack.append(ord(input_data[in_idx]))
                    in_idx += 1
                else:
                    stack.append(-1)

        # Move IP
        x = (x + dx) % 80
        y = (y + dy) % 25

    return ''.join(output)


def detect_and_solve(content: str, input_data: str = "") -> Tuple[str, str]:
    """Detects the esolang and executes it."""
    # Check for Ook!
    if 'Ook.' in content or 'Ook!' in content or 'Ook?' in content:
        try:
            bf = ook_to_brainfuck(content)
            res = run_brainfuck(bf, input_data)
            return "Ook! -> Brainfuck", res
        except Exception as e:
            return "Ook! (Failed)", str(e)

    # Check for Brainfuck (ratio of bf chars)
    bf_chars = sum(1 for c in content if c in '><+-.,[]')
    if bf_chars >= 20 and bf_chars / max(1, len(re.sub(r'\s+', '', content))) > 0.6:
        try:
            res = run_brainfuck(content, input_data)
            return "Brainfuck", res
        except Exception as e:
            return "Brainfuck (Failed)", str(e)

    # Check for Befunge
    befunge_chars = sum(1 for c in content if c in '><^v_|"@:#$,.')
    if befunge_chars >= 10 and '@' in content:
        try:
            res = run_befunge93(content, input_data)
            return "Befunge-93", res
        except Exception as e:
            return "Befunge-93 (Failed)", str(e)

    return "Unknown", ""


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/esolang_solver.py <file_or_code> [input_string]")
        sys.exit(1)

    target = sys.argv[1]
    input_str = sys.argv[2] if len(sys.argv) > 2 else ""

    try:
        with open(target, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
    except Exception:
        code = target

    lang, output = detect_and_solve(code, input_str)
    print(f"[*] Detected Language: {lang}")
    print(f"[+] Output:\n{output}")


if __name__ == "__main__":
    main()
