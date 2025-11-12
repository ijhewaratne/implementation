#!/usr/bin/env python3
"""
Exposé Compliance Auditor

This script audits the repository against the thesis exposé compliance matrix,
checking for required files, functions, strings, and tests.
"""

import argparse
import os
import re
import sys
import json
import fnmatch
from pathlib import Path
import yaml


def list_files(root: Path):
    """List all files in the repository, excluding common ignore patterns."""
    ignore_patterns = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".DS_Store",
        "node_modules",
        "venv",
        "env",
        ".venv",
        ".env",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        "*.so",
        "*.dll",
        "*.dylib",
    }

    files = []
    for p in root.rglob("*"):
        if p.is_file():
            # Skip ignored patterns
            if any(pattern in str(p) for pattern in ignore_patterns):
                continue
            files.append(p)
    return files


def file_contains_any(path: Path, needles: list[str]) -> bool:
    """Check if file contains any of the specified strings (case-insensitive)."""
    try:
        txt = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    txt_low = txt.lower()
    return any(n.lower() in txt_low for n in needles)


def functions_any_in_file(path: Path, fn_names: list[str]) -> bool:
    """Check if file contains any of the specified functions or classes."""
    if not fn_names:
        return False
    try:
        txt = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False

    # Check for function/class definitions
    for name in fn_names:
        # Handle dotted names (e.g., "DiameterOptimizer.run")
        if "." in name:
            class_name, method_name = name.split(".", 1)
            # Look for class definition and method
            class_pattern = re.compile(rf"class\s+{re.escape(class_name)}\b")
            method_pattern = re.compile(rf"def\s+{re.escape(method_name)}\b")
            if class_pattern.search(txt) and method_pattern.search(txt):
                return True
        else:
            # Simple function/class name
            pattern = re.compile(rf"(def|class)\s+{re.escape(name)}\b")
            if pattern.search(txt):
                return True
    return False


def glob_any(paths: list[Path], patterns: list[str]) -> list[Path]:
    """Find files matching any of the glob patterns."""
    out = []
    for pat in patterns:
        out.extend([p for p in paths if fnmatch.fnmatch(str(p).replace("\\", "/"), f"*{pat}")])
    return list(set(out))  # Remove duplicates


def check_requirement(repo: Path, files: list[Path], req: dict) -> dict:
    """Check a single requirement against the repository."""
    ok = True
    evid = []
    ev = req.get("evidence", {})

    # files_any
    if pats := ev.get("files_any"):
        hits = glob_any(files, pats)
        ok &= len(hits) > 0
        evid.append(("files_any", [str(h) for h in hits]))

    # tests_any
    if pats := ev.get("tests_any"):
        tests = glob_any(files, pats)
        ok &= len(tests) > 0
        evid.append(("tests_any", [str(h) for h in tests]))

    # strings_any
    if strs := ev.get("strings_any"):
        hits = [str(p) for p in files if file_contains_any(p, strs)]
        ok &= len(hits) > 0
        evid.append(("strings_any", hits))

    # functions_any
    if fns := ev.get("functions_any"):
        hits = [str(p) for p in files if functions_any_in_file(p, fns)]
        ok &= len(hits) > 0
        evid.append(("functions_any", hits))

    return {"description": req.get("description", ""), "ok": bool(ok), "evidence": evid}


def main():
    """Main function to run the compliance audit."""
    ap = argparse.ArgumentParser(description="Audit repository against exposé compliance matrix")
    ap.add_argument(
        "--matrix",
        default="configs/expose_compliance.yml",
        help="Path to compliance matrix YAML file",
    )
    ap.add_argument("--repo", default=".", help="Repository root directory")
    ap.add_argument(
        "--out-json", default="results_test/audit/expose_audit.json", help="Output JSON report path"
    )
    ap.add_argument(
        "--fail-on-missing", action="store_true", help="Exit nonzero if any must_have item fails"
    )
    ap.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output with evidence details"
    )
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.exists():
        print(f"Error: Repository path does not exist: {repo}")
        sys.exit(1)

    matrix_path = Path(args.matrix)
    if not matrix_path.exists():
        print(f"Error: Compliance matrix not found: {matrix_path}")
        sys.exit(1)

    print(f"🔍 Scanning repository: {repo}")
    files = list_files(repo)
    print(f"📁 Found {len(files)} files")

    try:
        cfg = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Error: Failed to parse compliance matrix: {e}")
        sys.exit(1)

    report = {
        "project": cfg.get("project"),
        "version": cfg.get("version"),
        "summary": {},
        "areas": [],
    }

    any_fail = False
    total_requirements = 0
    passed_requirements = 0

    for area in cfg.get("areas", []):
        area_res = {"id": area["id"], "title": area["title"], "must_have": []}

        for req in area.get("must_have", []):
            r = check_requirement(repo, files, req)
            area_res["must_have"].append(r)
            total_requirements += 1
            if r["ok"]:
                passed_requirements += 1

        fails = [x for x in area_res["must_have"] if not x["ok"]]
        report["areas"].append(area_res)
        report["summary"][area["id"]] = {
            "passed": len(area_res["must_have"]) - len(fails),
            "total": len(area_res["must_have"]),
        }
        any_fail |= len(fails) > 0

    # Add overall summary
    report["summary"]["overall"] = {
        "passed": passed_requirements,
        "total": total_requirements,
        "percentage": round(
            (passed_requirements / total_requirements * 100) if total_requirements > 0 else 0, 1
        ),
    }

    # Write JSON report
    outp = Path(args.out_json)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Human-readable console summary
    print(f"\n# Exposé compliance audit: {report['project']}")
    print(
        f"📊 Overall: {passed_requirements}/{total_requirements} requirements passed ({report['summary']['overall']['percentage']}%)"
    )
    print()

    for a in report["areas"]:
        s = report["summary"][a["id"]]
        status = "✅" if s["passed"] == s["total"] else "⚠️" if s["passed"] > 0 else "❌"
        print(f"{status} {a['id']} {a['title']}: {s['passed']}/{s['total']} OK")

        for r in a["must_have"]:
            mark = "✅" if r["ok"] else "❌"
            print(f"  {mark} {r['description']}")

            if not r["ok"] and args.verbose:
                # Show hints (which evidence buckets were empty)
                for key, hits in r["evidence"]:
                    if not hits:
                        print(f"     ↳ missing: {key}")
                    elif args.verbose:
                        print(f"     ↳ {key}: {len(hits)} found")

    print(f"\n📄 Detailed report: {outp}")

    if args.fail_on_missing and any_fail:
        print(f"\n❌ Audit failed: {total_requirements - passed_requirements} requirements missing")
        sys.exit(2)
    elif any_fail:
        print(f"\n⚠️  Audit completed with {total_requirements - passed_requirements} gaps")
    else:
        print(f"\n✅ Audit passed: All requirements satisfied!")


if __name__ == "__main__":
    main()
