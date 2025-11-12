#!/usr/bin/env python3
"""
Performance Analysis Script

Identifies hot paths in the codebase and suggests optimizations.
Focuses on Python loops over large arrays/DataFrames and suggests vectorized alternatives.
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set


class PerformanceAnalyzer:
    """Analyzes Python code for performance issues."""

    def __init__(self, source_dirs: List[str] = None):
        self.source_dirs = source_dirs or ["src", "agents"]
        self.issues = []

    def analyze_file(self, file_path: Path) -> List[Dict]:
        """Analyze a single Python file for performance issues."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)
            issues = []

            # Find loops and function calls
            for node in ast.walk(tree):
                if isinstance(node, ast.For):
                    issues.extend(self._analyze_for_loop(node, file_path))
                elif isinstance(node, ast.Call):
                    issues.extend(self._analyze_function_call(node, file_path))
                elif isinstance(node, ast.ListComp):
                    issues.extend(self._analyze_list_comp(node, file_path))

            return issues

        except Exception as e:
            return [{"type": "error", "message": f"Failed to parse {file_path}: {e}"}]

    def _analyze_for_loop(self, node: ast.For, file_path: Path) -> List[Dict]:
        """Analyze for loops for potential vectorization."""
        issues = []

        # Check for DataFrame iteration patterns
        if self._is_dataframe_iteration(node):
            issues.append(
                {
                    "type": "dataframe_loop",
                    "line": node.lineno,
                    "message": "Consider vectorizing DataFrame operations instead of iterating",
                    "suggestion": "Use pandas vectorized operations: df['col'] = df['a'] + df['b']",
                    "file": str(file_path),
                }
            )

        # Check for large range loops
        if self._is_large_range_loop(node):
            issues.append(
                {
                    "type": "large_loop",
                    "line": node.lineno,
                    "message": "Large loop detected - consider vectorization",
                    "suggestion": "Use numpy vectorized operations or pandas operations",
                    "file": str(file_path),
                }
            )

        return issues

    def _analyze_function_call(self, node: ast.Call, file_path: Path) -> List[Dict]:
        """Analyze function calls for performance issues."""
        issues = []

        # Check for .apply(axis=1) patterns
        if self._is_apply_axis1_call(node):
            issues.append(
                {
                    "type": "apply_axis1",
                    "line": node.lineno,
                    "message": "df.apply(axis=1) is slow - consider vectorization",
                    "suggestion": "Use vectorized operations or df.apply(axis=0) if possible",
                    "file": str(file_path),
                }
            )

        # Check for .iterrows() calls
        if self._is_iterrows_call(node):
            issues.append(
                {
                    "type": "iterrows",
                    "line": node.lineno,
                    "message": "df.iterrows() is slow - consider vectorization",
                    "suggestion": "Use vectorized operations or df.itertuples() if iteration is needed",
                    "file": str(file_path),
                }
            )

        return issues

    def _analyze_list_comp(self, node: ast.ListComp, file_path: Path) -> List[Dict]:
        """Analyze list comprehensions for potential numpy/pandas optimization."""
        issues = []

        # Check for large list comprehensions
        if self._is_large_list_comp(node):
            issues.append(
                {
                    "type": "large_list_comp",
                    "line": node.lineno,
                    "message": "Large list comprehension detected - consider numpy/pandas",
                    "suggestion": "Use numpy array operations or pandas Series operations",
                    "file": str(file_path),
                }
            )

        return issues

    def _is_dataframe_iteration(self, node: ast.For) -> bool:
        """Check if loop iterates over DataFrame."""
        # Look for patterns like: for row in df.iterrows():
        if isinstance(node.iter, ast.Call):
            if isinstance(node.iter.func, ast.Attribute):
                return node.iter.func.attr in ["iterrows", "itertuples"]
        return False

    def _is_large_range_loop(self, node: ast.For) -> bool:
        """Check if loop uses large range."""
        if isinstance(node.iter, ast.Call):
            if isinstance(node.iter.func, ast.Name) and node.iter.func.id == "range":
                # Check for large range values
                for arg in node.iter.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, int):
                        if arg.value > 1000:  # Threshold for "large"
                            return True
        return False

    def _is_apply_axis1_call(self, node: ast.Call) -> bool:
        """Check for df.apply(axis=1) calls."""
        if isinstance(node.func, ast.Attribute) and node.func.attr == "apply":
            for keyword in node.keywords:
                if keyword.arg == "axis" and isinstance(keyword.value, ast.Constant):
                    if keyword.value.value == 1:
                        return True
        return False

    def _is_iterrows_call(self, node: ast.Call) -> bool:
        """Check for df.iterrows() calls."""
        if isinstance(node.func, ast.Attribute) and node.func.attr == "iterrows":
            return True
        return False

    def _is_large_list_comp(self, node: ast.ListComp) -> bool:
        """Check if list comprehension might be large."""
        # Simple heuristic: check for range in generator
        for generator in node.generators:
            if isinstance(generator.iter, ast.Call):
                if isinstance(generator.iter.func, ast.Name) and generator.iter.func.id == "range":
                    return True
        return False

    def analyze_all(self) -> List[Dict]:
        """Analyze all Python files in source directories."""
        all_issues = []

        for source_dir in self.source_dirs:
            if not Path(source_dir).exists():
                continue

            for py_file in Path(source_dir).rglob("*.py"):
                if "test" not in str(py_file) and "__pycache__" not in str(py_file):
                    issues = self.analyze_file(py_file)
                    all_issues.extend(issues)

        return all_issues

    def generate_report(self, issues: List[Dict]) -> str:
        """Generate a formatted performance report."""
        if not issues:
            return "✅ No performance issues detected!"

        report = ["🔍 Performance Analysis Report", ""]

        # Group issues by type
        by_type = {}
        for issue in issues:
            issue_type = issue.get("type", "unknown")
            if issue_type not in by_type:
                by_type[issue_type] = []
            by_type[issue_type].append(issue)

        # Report by type
        for issue_type, type_issues in by_type.items():
            report.append(f"📊 {issue_type.upper()} Issues ({len(type_issues)} found):")
            for issue in type_issues:
                report.append(f"  • {issue['file']}:{issue['line']} - {issue['message']}")
                if "suggestion" in issue:
                    report.append(f"    💡 Suggestion: {issue['suggestion']}")
            report.append("")

        return "\n".join(report)


def main():
    """Main function to run performance analysis."""
    print("🔍 Starting performance analysis...")

    analyzer = PerformanceAnalyzer()
    issues = analyzer.analyze_all()

    report = analyzer.generate_report(issues)
    print(report)

    if issues:
        print(f"\n📈 Found {len(issues)} potential performance issues")
        print("💡 Consider running 'make perf-check' for Ruff-based performance analysis")
    else:
        print("\n✅ No performance issues detected!")


if __name__ == "__main__":
    main()
