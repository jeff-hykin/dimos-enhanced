"""Scan test files for short var names + tautological tests.

Flagged patterns:
- Short var names (≤3 chars, not in allowlist) in test code.
- `test_default_config`-style: all asserts are `x.attr == LITERAL` or `x.attr is True/False`.
- `test_cli_args_generation`-style: only asserts `"-flag" in args` / `"value" in args`.
- `test_ports_declared`-style: only asserts membership in get_streams/get_type_hints output.
"""

import ast
import sys
from pathlib import Path

ALLOWED_SHORT = {
    "i", "j", "k", "x", "y", "z", "n", "t", "_", "r", "g", "b", "a",
    "ix", "iy", "iz", "dx", "dy", "dz", "vx", "vy", "vz", "wx", "wy", "wz",
    "id", "fn", "io", "os", "re", "tf", "ax", "fp", "ws",
}


def _is_literal_eq(test: ast.AST) -> bool:
    if isinstance(test, ast.Compare) and len(test.ops) == 1:
        op = test.ops[0]
        rhs = test.comparators[0]
        if isinstance(op, (ast.Eq, ast.Is, ast.NotEq, ast.IsNot)) and isinstance(rhs, ast.Constant):
            return True
    return False


def _is_in_args_check(test: ast.AST) -> bool:
    if isinstance(test, ast.Compare) and len(test.ops) == 1:
        op = test.ops[0]
        if isinstance(op, ast.In) and isinstance(test.left, ast.Constant):
            return True
    return False


def _is_membership_check(test: ast.AST) -> bool:
    """foo in bar where lhs is a string literal."""
    return _is_in_args_check(test)


class Critic(ast.NodeVisitor):
    def __init__(self) -> None:
        self.findings: list[tuple[int, str]] = []
        self._in_test = 0

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        is_test = node.name.startswith("test_") or self._in_test > 0
        prev = self._in_test
        if is_test:
            self._in_test += 1

        # Tautology detector
        if node.name.startswith("test_"):
            asserts = [s for s in ast.walk(node) if isinstance(s, ast.Assert)]
            if len(asserts) >= 2:
                eq_count = sum(1 for s in asserts if _is_literal_eq(s.test))
                in_count = sum(1 for s in asserts if _is_in_args_check(s.test))
                if eq_count == len(asserts):
                    self.findings.append((
                        node.lineno,
                        f"TAUTOLOGY {node.name}: {len(asserts)} asserts, all `x == LITERAL` (likely re-typing defaults/hints)",
                    ))
                elif in_count == len(asserts):
                    self.findings.append((
                        node.lineno,
                        f"TAUTOLOGY {node.name}: {len(asserts)} asserts, all `STR in collection` (likely cli/port re-type)",
                    ))
                elif eq_count + in_count == len(asserts) and len(asserts) >= 4:
                    self.findings.append((
                        node.lineno,
                        f"TAUTOLOGY {node.name}: {len(asserts)} asserts mixing eq/in literals (likely re-type)",
                    ))

        # Short param names in test functions
        if is_test:
            for arg in node.args.args:
                name = arg.arg
                if (
                    name not in {"self", "cls"}
                    and len(name) <= 3
                    and name not in ALLOWED_SHORT
                ):
                    self.findings.append((arg.lineno, f"short param '{name}' in {node.name}"))

        self.generic_visit(node)
        self._in_test = prev

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Assign(self, node: ast.Assign) -> None:
        if self._in_test > 0:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id
                    if (
                        len(name) <= 3
                        and name not in ALLOWED_SHORT
                        and not name.startswith("_")
                    ):
                        self.findings.append((target.lineno, f"short local '{name}'"))
        self.generic_visit(node)


def critique(path: Path) -> list[tuple[Path, int, str]]:
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError as exc:
        return [(path, exc.lineno or 0, f"parse error: {exc.msg}")]
    critic = Critic()
    critic.visit(tree)
    return [(path, line, msg) for line, msg in critic.findings]


def main() -> None:
    roots = [Path(arg) for arg in sys.argv[1:]] or [Path("dimos")]
    files: list[Path] = []
    for root in roots:
        if root.is_file():
            files.append(root)
        else:
            files.extend(p for p in root.rglob("test_*.py"))

    by_file: dict[Path, list[tuple[int, str]]] = {}
    tautology_files: dict[Path, int] = {}
    for path in sorted(set(files)):
        if not (path.name.startswith("test_") and path.suffix == ".py"):
            continue
        rows = critique(path)
        if rows:
            by_file[path] = [(l, m) for _, l, m in rows]
        tautology_files[path] = sum(1 for _, _, m in rows if m.startswith("TAUTOLOGY"))

    # Print tautology summary first
    print("=== FILES WITH TAUTOLOGY HITS (consider deleting) ===")
    for path, n in sorted(tautology_files.items(), key=lambda kv: -kv[1]):
        if n > 0:
            print(f"  {n} tautology test(s) in {path}")

    print("\n=== ALL FINDINGS ===")
    for path in sorted(by_file):
        items = sorted(by_file[path])
        print(f"\n{path} ({len(items)})")
        for line, msg in items:
            print(f"  {line}: {msg}")

    total = sum(len(v) for v in by_file.values())
    print(f"\n=== TOTAL: {total} findings across {len(by_file)} files ===")


if __name__ == "__main__":
    main()
