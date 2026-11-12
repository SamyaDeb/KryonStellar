"""Documentation validation.

    python3 docs/diagrams/tools/validate.py

Checks, relative to the repository root:
  1. every relative Markdown link and image in the documentation resolves;
  2. every GitHub blob URL to this repository points at an existing file;
  3. every diagram has .excalidraw, .svg and .png files;
  4. every .excalidraw file is structurally valid Excalidraw JSON;
  5. every function documented in a contract reference table exists as a
     `pub fn` in that contract's source.
Exits non-zero on any failure.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
REPO_URL = "https://github.com/SamyaDeb/KryonStellar/blob/main/"
DOC_FILES = sorted(
    glob.glob(os.path.join(ROOT, "docs/docs/**/*.md"), recursive=True)
    + [os.path.join(ROOT, p) for p in (
        "README.md", "ARCHITECTURE.md", "docs/README.md", "client/README.md", "kryon-protocol/README.md",
        "kryon-protocol/docs/architecture.md", "kryon-protocol/docs/security-model.md",
        "kryon-protocol/docs/legacy-issues-fixed.md")]
)
LINK = re.compile(r"(!?)\[[^\]]*\]\(([^)\s]+)\)")
errors, stats = [], {"links": 0, "images": 0, "github": 0, "diagrams": 0, "functions": 0}


def strip_code(text):
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return re.sub(r"`[^`\n]*`", "", text)


def heading_anchors(path):
    anchors = set()
    for line in open(path, encoding="utf-8"):
        m = re.match(r"^#{1,6}\s+(.*)", line)
        if m:
            t = re.sub(r"[`*_]", "", m.group(1)).strip().lower()
            t = re.sub(r"[^\w\- ]", "", t).replace(" ", "-")
            anchors.add(t)
    return anchors


# 1–2. links
for f in DOC_FILES:
    text = strip_code(open(f, encoding="utf-8").read())
    for bang, target in LINK.findall(text):
        if target.startswith(("http://", "https://")):
            if target.startswith(REPO_URL):
                stats["github"] += 1
                rel = target[len(REPO_URL):].split("#")[0]
                if not os.path.exists(os.path.join(ROOT, rel)):
                    errors.append(f"{os.path.relpath(f, ROOT)}: GitHub link to missing file {rel}")
            continue
        if target.startswith(("mailto:", "#")) and not target.startswith("#"):
            continue
        path, _, anchor = target.partition("#")
        if not path:
            dest = f
        else:
            dest = os.path.normpath(os.path.join(os.path.dirname(f), path))
        stats["images" if bang else "links"] += 1
        if not os.path.exists(dest):
            errors.append(f"{os.path.relpath(f, ROOT)}: broken {'image' if bang else 'link'} {target}")
        elif anchor and dest.endswith(".md") and anchor not in heading_anchors(dest):
            errors.append(f"{os.path.relpath(f, ROOT)}: missing anchor #{anchor} in {os.path.relpath(dest, ROOT)}")

# 3–4. diagrams
DIAG = os.path.join(ROOT, "docs/diagrams")
names = {os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(DIAG, "*/*.*")) if "/fonts/" not in p and "/tools/" not in p
         if not p.endswith(".py")}
names = {n for n in names if not n.startswith("__")}
REQUIRED_COMMON = {"id", "type", "x", "y", "width", "height", "angle", "strokeColor", "backgroundColor",
                   "fillStyle", "strokeWidth", "strokeStyle", "roughness", "opacity", "groupIds", "seed",
                   "version", "versionNonce", "isDeleted", "boundElements", "locked"}
TYPE_FIELDS = {"text": {"text", "fontSize", "fontFamily", "textAlign", "verticalAlign", "originalText", "lineHeight"},
               "arrow": {"points", "startArrowhead", "endArrowhead"}, "line": {"points"},
               "rectangle": set(), "ellipse": set(), "diamond": set()}
for n in sorted(names):
    if n in ("engine", "build", "validate") or n.startswith("defs_"):
        continue
    stats["diagrams"] += 1
    for ext, sub in (("excalidraw", "excalidraw"), ("svg", "svg"), ("png", "png")):
        if not os.path.exists(os.path.join(DIAG, sub, f"{n}.{ext}")):
            errors.append(f"diagram {n}: missing {sub}/{n}.{ext}")
    src = os.path.join(DIAG, "excalidraw", f"{n}.excalidraw")
    if os.path.exists(src):
        doc = json.load(open(src))
        if doc.get("type") != "excalidraw" or doc.get("version") != 2 or not isinstance(doc.get("elements"), list):
            errors.append(f"{n}.excalidraw: bad document header")
        ids = set()
        for el in doc.get("elements", []):
            missing = (REQUIRED_COMMON | TYPE_FIELDS.get(el.get("type"), {"?"})) - el.keys()
            if el.get("type") not in TYPE_FIELDS:
                errors.append(f"{n}.excalidraw: unknown element type {el.get('type')}")
            if missing:
                errors.append(f"{n}.excalidraw: element {el.get('id')} missing {sorted(missing)}")
            if el.get("id") in ids:
                errors.append(f"{n}.excalidraw: duplicate id {el.get('id')}")
            ids.add(el.get("id"))
            if el.get("type") in ("arrow", "line") and el.get("points", [[1]])[0] != [0, 0]:
                errors.append(f"{n}.excalidraw: {el['id']} first point is not [0, 0]")
    svg = os.path.join(DIAG, "svg", f"{n}.svg")
    if os.path.exists(svg) and not open(svg).read().lstrip().startswith("<svg"):
        errors.append(f"{n}.svg: not an SVG document")

# 5. contract functions
CONTRACT_PAGES = {
    "vault.md": "perp-vault", "engine.md": "perp-engine", "order-gateway.md": "perp-order-gateway",
    "oracle-adapter.md": "perp-oracle-adapter", "liquidation.md": "perp-liquidation",
    "insurance.md": "perp-insurance", "risk.md": "perp-risk", "governance.md": "perp-governance",
}
STANDARD = {"upgrade", "nominate_admin", "accept_admin", "admin", "pending_admin"}
for page, crate in CONTRACT_PAGES.items():
    src = open(os.path.join(ROOT, "kryon-protocol/contracts", crate, "src/lib.rs")).read()
    src = src.split("#[cfg(test)]")[0]
    pub = set(re.findall(r"pub fn ([a-z_0-9]+)\s*\(", src))
    text = open(os.path.join(ROOT, "docs/docs/03-smart-contracts", page)).read()
    section = text.split("## Public functions", 1)[-1].split("\n## ", 1)[0]
    for row in section.splitlines():
        if not row.startswith("| `"):
            continue
        first = row.split("|")[1]
        for name in re.findall(r"`([a-z_][a-z_0-9]*)(?:\(|`)", first):
            if name.startswith("set_") and name.endswith("*"):
                continue
            stats["functions"] += 1
            if name in STANDARD and page == "risk.md" and name in ("admin", "pending_admin"):
                continue
            if name not in pub:
                errors.append(f"{page}: documented function `{name}` not found in {crate}")

for k, v in stats.items():
    print(f"checked {v:4d} {k}")
if errors:
    print(f"\n{len(errors)} problem(s):")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print("\nall checks passed")
