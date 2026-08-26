#!/usr/bin/env python3
"""Check that replay-gate helpers use one literal gate-id regex contract."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path
import sys


CANONICAL_GATE_ID_PATTERN = r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z"


class ContractError(ValueError):
    """Raised when a helper does not expose the required literal contract."""


class _ModuleBindingCollector(ast.NodeVisitor):
    """Collect bindings visible in module scope without entering nested scopes."""

    def __init__(self, variable: str) -> None:
        self.variable = variable
        self.bindings: list[ast.AST] = []

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Store) and node.id == self.variable:
            self.bindings.append(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.name == self.variable:
            self.bindings.append(node)
        self._visit_function_header(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        if node.name == self.variable:
            self.bindings.append(node)
        self._visit_function_header(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if node.name == self.variable:
            self.bindings.append(node)
        for decorator in node.decorator_list:
            self.visit(decorator)
        for base in node.bases:
            self.visit(base)
        for keyword in node.keywords:
            self.visit(keyword.value)
        for type_parameter in getattr(node, "type_params", ()):
            self.visit(type_parameter)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self.visit(node.args)

    def _visit_function_header(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        for decorator in node.decorator_list:
            self.visit(decorator)
        self.visit(node.args)
        if node.returns is not None:
            self.visit(node.returns)
        for type_parameter in getattr(node, "type_params", ()):
            self.visit(type_parameter)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            bound_name = alias.asname or alias.name.split(".", 1)[0]
            if bound_name == self.variable:
                self.bindings.append(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            bound_name = alias.asname or alias.name
            if bound_name == self.variable:
                self.bindings.append(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name == self.variable:
            self.bindings.append(node)
        if node.type is not None:
            self.visit(node.type)
        for statement in node.body:
            self.visit(statement)

    def visit_MatchAs(self, node: ast.MatchAs) -> None:
        if node.name == self.variable:
            self.bindings.append(node)
        if node.pattern is not None:
            self.visit(node.pattern)

    def visit_MatchStar(self, node: ast.MatchStar) -> None:
        if node.name == self.variable:
            self.bindings.append(node)

    def visit_MatchMapping(self, node: ast.MatchMapping) -> None:
        if node.rest == self.variable:
            self.bindings.append(node)
        for pattern in node.patterns:
            self.visit(pattern)


def _is_direct_assignment(node: ast.stmt, variable: str) -> bool:
    return (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == variable
    )


def _literal_pattern(path: Path, variable: str) -> str:
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ContractError(f"cannot read {path}: {exc}") from exc
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        raise ContractError(f"cannot parse {path}: {exc}") from exc

    collector = _ModuleBindingCollector(variable)
    collector.visit(tree)
    if len(collector.bindings) != 1:
        raise ContractError(
            f"{path}: expected exactly one module-level binding to {variable}"
        )

    assignments = [node for node in tree.body if _is_direct_assignment(node, variable)]
    if len(assignments) != 1:
        raise ContractError(
            f"{path}: {variable} must use one direct assignment to a literal "
            "re.compile pattern with no flags"
        )

    value = assignments[0].value
    valid_call = (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Attribute)
        and isinstance(value.func.value, ast.Name)
        and value.func.value.id == "re"
        and value.func.attr == "compile"
        and len(value.args) == 1
        and not value.keywords
        and isinstance(value.args[0], ast.Constant)
        and isinstance(value.args[0].value, str)
    )
    if not valid_call:
        raise ContractError(
            f"{path}: {variable} must be assigned one literal re.compile pattern with no flags"
        )
    return value.args[0].value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recorder", type=Path, help="path to gate_command_once.py")
    parser.add_argument("monitor", type=Path, help="path to gate_live_monitor.py")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        recorder_pattern = _literal_pattern(args.recorder, "SAFE_ID")
        monitor_pattern = _literal_pattern(args.monitor, "_SAFE_ID")
    except ContractError as exc:
        print(f"gate-id contract error: {exc}", file=sys.stderr)
        return 2

    if recorder_pattern != CANONICAL_GATE_ID_PATTERN:
        print(
            "recorder gate-id pattern is not canonical: "
            f"expected={CANONICAL_GATE_ID_PATTERN} actual={recorder_pattern}",
            file=sys.stderr,
        )
        return 1

    if recorder_pattern != monitor_pattern:
        print(
            "gate-id patterns differ: "
            f"recorder={recorder_pattern} monitor={monitor_pattern}",
            file=sys.stderr,
        )
        return 1

    print(f"gate_id_contract=matched pattern={recorder_pattern}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
