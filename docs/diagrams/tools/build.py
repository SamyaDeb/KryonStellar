"""Regenerate every documentation diagram.

    python3 docs/diagrams/tools/build.py [name-filter]

Writes docs/diagrams/{excalidraw,svg,png}/<name>.* from the definitions in
defs_*.py. The .excalidraw files are the editable sources; if a diagram is
edited by hand in Excalidraw, stop regenerating it from here (remove it from
the definitions) so the manual edit is not overwritten.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from engine import write_all, check_layout  # noqa: E402
import defs_architecture  # noqa: E402

MODULES = [defs_architecture]
for extra in ("defs_contracts", "defs_trading", "defs_oracle", "defs_backend", "defs_security"):
    try:
        MODULES.append(__import__(extra))
    except ModuleNotFoundError:
        pass

ROOT = os.path.abspath(os.path.join(HERE, ".."))


def main():
    flt = sys.argv[1] if len(sys.argv) > 1 else ""
    out = os.environ.get("DIAGRAM_OUT", ROOT)
    names = []
    problems = []
    for m in MODULES:
        for fn in m.ALL:
            d = fn()
            if flt and flt not in d.name:
                continue
            write_all(d, out)
            names.append(d.name)
            for p in check_layout(d):
                problems.append(f"{d.name}: {p}")
    print(f"wrote {len(names)} diagrams to {out}")
    for p in problems:
        print("  !", p)
    print(f"{len(problems)} layout problem(s)")


if __name__ == "__main__":
    main()
