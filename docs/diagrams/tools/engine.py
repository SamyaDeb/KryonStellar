"""
Monochrome Excalidraw-style diagram engine for the Kryon documentation.

One layout model produces three artefacts per diagram:

  * ``<name>.excalidraw`` — a native Excalidraw document (editable source)
  * ``<name>.svg``        — vector export
  * ``<name>.png``        — raster export (2x scale)

The SVG and PNG renderers apply a small, deterministic stroke jitter so the
exports carry a subtle hand-drawn character without looking sketchy. The
Excalidraw source uses ``roughness: 1`` so the editor renders the same shapes
in its own hand-drawn style.

Only the Python standard library and Pillow are required.
"""

from __future__ import annotations

import json
import math
import os
import random
import zlib
from dataclasses import dataclass, field
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

# ── Visual tokens ────────────────────────────────────────────────────────────
INK = "#1e1e1e"        # primary outline / text
INK2 = "#495057"       # secondary outline / text
INK3 = "#868e96"       # tertiary: planned elements, frames, lifelines
FILL_CHAIN = "#f1f3f5"  # on-chain components
FILL_STORE = "#e9ecef"  # persistent stores
FILL_NOTE = "#f8f9fa"   # annotations
WHITE = "#ffffff"

FONT_STACK = "Virgil, 'Segoe Print', 'Comic Sans MS', cursive"
# Virgil is Excalidraw's hand-drawn font (SIL Open Font License), bundled here
# so the SVG and PNG exports match what the Excalidraw editor shows.
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts", "Virgil.woff2")
EXCALIDRAW_FONT_FAMILY = 1  # Virgil

# Characters Virgil has no glyph for, mapped to plain equivalents. Applied to
# every string before layout so all three outputs show the same text.
_SANITIZE = {"\u2014": "-", "\u2013": "-", "\u2192": "->", "\u2190": "<-", "\u2194": "<->", "\u21d2": "=>",
             "\u2264": "<=", "\u2265": ">=", "\u2260": "!=", "\u2248": "~", "\u0394": "d", "\u1d62": "i",
             "\u2074": "^4", "\u2075": "^5", "\u2076": "^6", "\u2080": "0", "\u2081": "1", "\u2212": "-",
             "\u2026": "...", "\u00b9": "1", "\u00b2": "2"}


def sanitize(s):
    if not s:
        return s
    for k, v in _SANITIZE.items():
        s = s.replace(k, v)
    return s
LINE_HEIGHT = 1.25
PNG_SCALE = 2
MARGIN = 40

_font_cache: dict = {}


def font(size: float, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = (round(size * 4) / 4, bold)
    if key not in _font_cache:
        try:
            _font_cache[key] = ImageFont.truetype(FONT_PATH, int(round(size)))
        except OSError:  # pragma: no cover - non-macOS fallback
            _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]


def text_width(s: str, size: float, bold: bool = False) -> float:
    return font(size, bold).getlength(s)


# ── Model ────────────────────────────────────────────────────────────────────
@dataclass
class Node:
    id: str
    x: float
    y: float
    w: float
    h: float
    title: str
    sub: str = ""
    kind: str = "box"  # box | chain | store | actor | ext | planned | note | decision | terminal
    align: str = "center"
    title_size: float = 16
    sub_size: float = 13

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2


@dataclass
class Edge:
    a: str
    b: str
    label: str = ""
    style: str = "solid"  # solid | dashed
    via: list = field(default_factory=list)
    both: bool = False
    head: bool = True
    label_pos: float = 0.5
    label_dx: float = 0
    label_dy: float = 0
    ap: object = None  # port on source: 'l'|'r'|'t'|'b' or (side, offset)
    bp: object = None  # port on target


@dataclass
class Frame:
    x: float
    y: float
    w: float
    h: float
    label: str = ""


@dataclass
class Text:
    x: float
    y: float
    s: str
    size: float = 14
    color: str = INK
    align: str = "left"
    bold: bool = False


@dataclass
class Line:
    pts: list
    style: str = "dotted"
    color: str = INK3
    width: float = 1


class Diagram:
    def __init__(self, name: str, title: str, subtitle: str = ""):
        self.name = name
        self.title = sanitize(title)
        self.subtitle = sanitize(subtitle)
        self.nodes: dict[str, Node] = {}
        self.order: list[str] = []
        self.edges: list[Edge] = []
        self.frames: list[Frame] = []
        self.texts: list[Text] = []
        self.lines: list[Line] = []
        self.legend_items: list[tuple[str, str]] = []

    # construction helpers -------------------------------------------------
    def node(self, id, x, y, w, h, title, sub="", kind="box", **kw) -> Node:
        n = Node(id, x, y, w, h, sanitize(title), sanitize(sub), kind, **kw)
        self.nodes[id] = n
        self.order.append(id)
        return n

    def edge(self, a, b, label="", style="solid", **kw) -> Edge:
        e = Edge(a, b, sanitize(label), style, **kw)
        self.edges.append(e)
        return e

    def frame(self, x, y, w, h, label=""):
        self.frames.append(Frame(x, y, w, h, sanitize(label)))

    def text(self, x, y, s, size=14, color=INK, align="left", bold=False):
        self.texts.append(Text(x, y, sanitize(s), size, color, align, bold))

    def line(self, pts, style="dotted", color=INK3, width=1):
        self.lines.append(Line(pts, style, color, width))

    def legend(self, *items):
        """items: (kind, description) with kind in box/chain/store/ext/planned/solid/dashed."""
        self.legend_items.extend((k, sanitize(v)) for k, v in items)


# ── Geometry ─────────────────────────────────────────────────────────────────
def _clip_rect(n: Node, tx: float, ty: float) -> tuple[float, float]:
    """Point where the ray from the node centre toward (tx, ty) leaves the node."""
    cx, cy = n.cx, n.cy
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    if n.kind == "actor":
        a, b = n.w / 2, n.h / 2
        t = 1 / math.sqrt((dx * dx) / (a * a) + (dy * dy) / (b * b))
        return cx + dx * t, cy + dy * t
    if n.kind == "decision":
        a, b = n.w / 2, n.h / 2
        t = 1 / (abs(dx) / a + abs(dy) / b)
        return cx + dx * t, cy + dy * t
    hw, hh = n.w / 2, n.h / 2
    tx_ = hw / abs(dx) if dx else math.inf
    ty_ = hh / abs(dy) if dy else math.inf
    t = min(tx_, ty_)
    return cx + dx * t, cy + dy * t


def _port(n: Node, spec):
    side, off = (spec, 0) if isinstance(spec, str) else spec
    if side == "l":
        return (n.x, n.cy + off)
    if side == "r":
        return (n.x + n.w, n.cy + off)
    if side == "t":
        return (n.cx + off, n.y)
    return (n.cx + off, n.y + n.h)


def edge_points(d: Diagram, e: Edge) -> list[tuple[float, float]]:
    a, b = d.nodes[e.a], d.nodes[e.b]
    via = [tuple(p) for p in e.via]
    if not via and not e.ap and not e.bp and a.kind not in ("actor", "decision", "anchor") \
            and b.kind not in ("actor", "decision", "anchor"):
        gx = max(b.x - (a.x + a.w), a.x - (b.x + b.w))
        gy = max(b.y - (a.y + a.h), a.y - (b.y + b.h))
        if gx > 0 and gx >= gy:
            ap, bp = ("r", "l") if b.cx > a.cx else ("l", "r")
            return _finish([_port(a, ap), _port(b, bp)])
        if gy > 0:
            ap, bp = ("b", "t") if b.cy > a.cy else ("t", "b")
            return _finish([_port(a, ap), _port(b, bp)])
    first_target = via[0] if via else (b.cx, b.cy)
    last_source = via[-1] if via else (a.cx, a.cy)
    p0 = _port(a, e.ap) if e.ap else _clip_rect(a, *first_target)
    pn = _port(b, e.bp) if e.bp else _clip_rect(b, *last_source)
    if e.ap and not via and not e.bp:
        pn = _clip_rect(b, *p0)
    if e.bp and not via and not e.ap:
        p0 = _clip_rect(a, *pn)
    return _finish([p0, *via, pn])


def _finish(pts):
    # small gap so arrowheads do not touch outlines
    pts[0] = _shorten(pts[0], pts[1], 3)
    pts[-1] = _shorten(pts[-1], pts[-2], 4)
    return pts


def _shorten(p, toward, by):
    dx, dy = toward[0] - p[0], toward[1] - p[1]
    L = math.hypot(dx, dy)
    if L < 2 * by or L == 0:
        return p
    return (p[0] + dx / L * by, p[1] + dy / L * by)


def _label_anchor(pts, pos):
    segs = [(pts[i], pts[i + 1], math.dist(pts[i], pts[i + 1])) for i in range(len(pts) - 1)]
    total = sum(s[2] for s in segs) or 1
    target = total * pos
    acc = 0
    for p, q, L in segs:
        if acc + L >= target:
            t = (target - acc) / L if L else 0
            return p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
        acc += L
    return pts[-1]


# ── Styles ───────────────────────────────────────────────────────────────────
def node_style(kind: str) -> dict:
    base = dict(stroke=INK, fill=WHITE, width=1.5, dash="solid", text=INK, sub=INK2)
    if kind == "chain":
        base.update(fill=FILL_CHAIN, width=2)
    elif kind == "store":
        base.update(fill=FILL_STORE)
    elif kind == "ext":
        base.update(stroke=INK2, width=1.25, text=INK2, sub=INK2)
    elif kind == "planned":
        base.update(stroke=INK3, width=1.25, dash="dashed", text=INK3, sub=INK3)
    elif kind == "note":
        base.update(stroke=INK3, fill=FILL_NOTE, width=1, text=INK2, sub=INK2)
    elif kind == "terminal":
        base.update(fill=FILL_STORE, width=1.5)
    return base


# ── Layout of text inside a node ─────────────────────────────────────────────
def node_text_blocks(n: Node):
    """Yield (lines, size, color_key, bold, top_y, align, x) blocks for a node."""
    t_lines = n.title.split("\n") if n.title else []
    s_lines = n.sub.split("\n") if n.sub else []
    ts, ss = fitted_sizes(n)
    th = len(t_lines) * ts * LINE_HEIGHT
    sh = len(s_lines) * ss * LINE_HEIGHT
    gap = 4 if (t_lines and s_lines) else 0
    total = th + gap + sh
    top = n.cy - total / 2
    pad = 12
    x = n.cx if n.align == "center" else n.x + pad
    blocks = []
    if t_lines:
        blocks.append((t_lines, ts, "text", False, top, n.align, x))
    if s_lines:
        blocks.append((s_lines, ss, "sub", False, top + th + gap, n.align, x))
    return blocks


PAD_X, PAD_Y = 12, 6


def _block_size(n: Node, ts, ss):
    t_lines = n.title.split("\n") if n.title else []
    s_lines = n.sub.split("\n") if n.sub else []
    w = max([text_width(l, ts) for l in t_lines] + [text_width(l, ss) for l in s_lines] + [0])
    h = len(t_lines) * ts * LINE_HEIGHT + len(s_lines) * ss * LINE_HEIGHT + (4 if t_lines and s_lines else 0)
    return w, h


def fitted_sizes(n: Node):
    """Shrink a node's fonts (to at most 70 %) until its text fits inside it."""
    if n.kind == "anchor":
        return n.title_size, n.sub_size
    avail_w = n.w - 2 * PAD_X
    avail_h = n.h - 2 * PAD_Y
    if n.kind == "decision":
        avail_w, avail_h = n.w * 0.62, n.h * 0.62
    if n.kind == "actor":
        avail_w, avail_h = n.w * 0.78, n.h * 0.72
    f = 1.0
    while f > 0.7:
        w, h = _block_size(n, n.title_size * f, n.sub_size * f)
        if w <= avail_w and h <= avail_h:
            break
        f -= 0.025
    return round(n.title_size * f, 2), round(n.sub_size * f, 2)


# ── Bounds ───────────────────────────────────────────────────────────────────
def bounds(d: Diagram):
    xs, ys = [], []
    for n in d.nodes.values():
        xs += [n.x, n.x + n.w]
        ys += [n.y, n.y + n.h]
    for f in d.frames:
        xs += [f.x, f.x + f.w]
        ys += [f.y, f.y + f.h]
    for t in d.texts:
        w = max(text_width(s, t.size, t.bold) for s in t.s.split("\n"))
        h = len(t.s.split("\n")) * t.size * LINE_HEIGHT
        x0 = t.x - (w / 2 if t.align == "center" else 0)
        xs += [x0, x0 + w]
        ys += [t.y, t.y + h]
    for e in d.edges:
        for p in edge_points(d, e):
            xs.append(p[0])
            ys.append(p[1])
    for ln in d.lines:
        for p in ln.pts:
            xs.append(p[0])
            ys.append(p[1])
    return min(xs), min(ys), max(xs), max(ys)


def finalize(d: Diagram):
    """Place the title block and legend relative to the content bounds."""
    x0, y0, x1, y1 = bounds(d)
    # title
    d._title_xy = (x0, y0 - 64)
    # legend under content
    if d.legend_items:
        lx, ly = x0, y1 + 28
        cur = lx
        d._legend = []
        for kind, label in d.legend_items:
            w = 34 + text_width(label, 12) + 26
            d._legend.append((kind, label, cur, ly))
            cur += w
    else:
        d._legend = []


# ── Deterministic jitter ─────────────────────────────────────────────────────
class Jitter:
    def __init__(self, key: str, amount: float = 0.7):
        self.r = random.Random(zlib.crc32(key.encode()))
        self.a = amount

    def j(self):
        return self.r.uniform(-self.a, self.a)


def _bowed_segment(p, q, jit: Jitter, n=10):
    """Points along p→q with a slight perpendicular bow."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    bow = jit.j() * min(1.6, L / 140)
    out = []
    for i in range(n + 1):
        t = i / n
        b = 4 * t * (1 - t) * bow
        out.append((p[0] + dx * t + nx * b, p[1] + dy * t + ny * b))
    return out


def rect_path(x, y, w, h, r, jit: Jitter):
    """Polyline approximating a rounded rectangle with slight hand-drawn bow."""
    r = min(r, w / 2, h / 2)
    pts = []

    def arc(cx, cy, a0, a1):
        for i in range(7):
            a = a0 + (a1 - a0) * i / 6
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))

    corners = [
        ((x + r, y), (x + w - r, y)),
        ((x + w, y + r), (x + w, y + h - r)),
        ((x + w - r, y + h), (x + r, y + h)),
        ((x, y + h - r), (x, y + r)),
    ]
    arcs = [
        (x + w - r, y + r, -math.pi / 2, 0),
        (x + w - r, y + h - r, 0, math.pi / 2),
        (x + r, y + h - r, math.pi / 2, math.pi),
        (x + r, y + r, math.pi, 1.5 * math.pi),
    ]
    for (p, q), a in zip(corners, arcs):
        pts.extend(_bowed_segment((p[0] + jit.j() * 0.4, p[1] + jit.j() * 0.4), q, jit))
        if r > 0:
            arc(*a)
    pts.append(pts[0])
    return pts


def ellipse_path(cx, cy, a, b, jit: Jitter):
    pts = []
    k = 1 + jit.j() * 0.004
    for i in range(73):
        t = 2 * math.pi * i / 72
        pts.append((cx + a * k * math.cos(t), cy + b * math.sin(t)))
    return pts


def diamond_path(n: Node, jit: Jitter):
    c = [(n.cx, n.y), (n.x + n.w, n.cy), (n.cx, n.y + n.h), (n.x, n.cy)]
    pts = []
    for i in range(4):
        pts.extend(_bowed_segment(c[i], c[(i + 1) % 4], jit, 6))
    return pts


def poly_path(pts, jit: Jitter, curved=True):
    out = []
    for i in range(len(pts) - 1):
        seg = _bowed_segment(pts[i], pts[i + 1], jit, 12 if curved else 1)
        out.extend(seg if not out else seg[1:])
    return out


def arrow_head(p_end, p_prev, size=11, spread=0.42):
    ang = math.atan2(p_end[1] - p_prev[1], p_end[0] - p_prev[0])
    l = (p_end[0] - size * math.cos(ang - spread), p_end[1] - size * math.sin(ang - spread))
    r = (p_end[0] - size * math.cos(ang + spread), p_end[1] - size * math.sin(ang + spread))
    return [l, p_end, r]


def _dash(style):
    return {"solid": None, "dashed": (8, 6), "dotted": (2, 4)}[style]


# ── SVG renderer ─────────────────────────────────────────────────────────────
def _svg_poly(pts, stroke, width, dash, fill="none", close=False):
    d = "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts) + (" Z" if close else "")
    da = f' stroke-dasharray="{dash[0]} {dash[1]}"' if dash else ""
    return (f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"'
            f' stroke-linecap="round" stroke-linejoin="round"{da}/>')


_FONT_FACE = None


def _svg_font_face():
    """Embed Virgil so the SVG renders identically when used as an <img>."""
    global _FONT_FACE
    if _FONT_FACE is None:
        import base64
        data = base64.b64encode(open(FONT_PATH, "rb").read()).decode()
        _FONT_FACE = ('<defs><style>@font-face{font-family:"Virgil";'
                      f'src:url(data:font/woff2;base64,{data}) format("woff2");}}</style></defs>')
    return _FONT_FACE


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _svg_text(lines, x, top, size, color, align, bold):
    anchor = {"center": "middle", "left": "start", "right": "end"}[align]
    out = []
    for i, ln in enumerate(lines):
        cy = top + (i + 0.5) * size * LINE_HEIGHT
        wt = ""
        out.append(f'<text x="{x:.2f}" y="{cy:.2f}" font-family="{FONT_STACK}" font-size="{size}"'
                   f'{wt} fill="{color}" text-anchor="{anchor}" dominant-baseline="central">{_esc(ln)}</text>')
    return out


def _label_box(e: Edge, d: Diagram, pts):
    lines = e.label.split("\n")
    size = 12
    w = max(text_width(l, size) for l in lines) + 10
    h = len(lines) * size * LINE_HEIGHT + 4
    ax, ay = _label_anchor(pts, e.label_pos)
    ax += e.label_dx
    ay += e.label_dy
    return lines, size, ax - w / 2, ay - h / 2, w, h, ax


def render_svg(d: Diagram) -> str:
    finalize(d)
    x0, y0, x1, y1 = bounds(d)
    tx, ty = d._title_xy
    if d._legend:
        y1 = max(y1, d._legend[-1][3] + 24)
        x1 = max(x1, d._legend[-1][2] + 34 + text_width(d._legend[-1][1], 12) + 10)
    x1 = max(x1, tx + text_width(d.title, 26, True))
    vx, vy = x0 - MARGIN, ty - MARGIN + 10
    W, H = (x1 - x0) + 2 * MARGIN, (y1 - vy) + MARGIN
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vx:.0f} {vy:.0f} {W:.0f} {H:.0f}"'
         f' width="{W:.0f}" height="{H:.0f}" role="img" aria-label="{_esc(d.title)}">',
         _svg_font_face(),
         f'<rect x="{vx:.0f}" y="{vy:.0f}" width="{W:.0f}" height="{H:.0f}" fill="#ffffff"/>']
    o += _svg_text([d.title], tx, ty, 26, INK, "left", True)
    if d.subtitle:
        o += _svg_text([d.subtitle], tx, ty + 30, 13, INK2, "left", False)
    for i, f in enumerate(d.frames):
        jit = Jitter(f"{d.name}-frame-{i}", 0.5)
        o.append(_svg_poly(rect_path(f.x, f.y, f.w, f.h, 10, jit), INK3, 1, None))
        if f.label:
            o += _svg_text([f.label], f.x + 14, f.y + 8, 13, INK2, "left", True)
    for i, ln in enumerate(d.lines):
        o.append(_svg_poly(ln.pts, ln.color, ln.width, _dash(ln.style)))
    for i, e in enumerate(d.edges):
        jit = Jitter(f"{d.name}-edge-{i}")
        pts = edge_points(d, e)
        path = poly_path(pts, jit)
        o.append(_svg_poly(path, INK, 1.5, _dash(e.style)))
        if e.head:
            o.append(_svg_poly(arrow_head(pts[-1], path[-2]), INK, 1.5, None))
        if e.both:
            o.append(_svg_poly(arrow_head(pts[0], path[1]), INK, 1.5, None))
    for i, e in enumerate(d.edges):
        if not e.label:
            continue
        lines, size, lx, ly, w, h, ax = _label_box(e, d, edge_points(d, e))
        o.append(f'<rect x="{lx:.2f}" y="{ly:.2f}" width="{w:.2f}" height="{h:.2f}" fill="#ffffff"/>')
        o += _svg_text(lines, ax, ly + 2, size, INK2, "center", False)
    for nid in d.order:
        n = d.nodes[nid]
        if n.kind == "anchor":
            continue
        st = node_style(n.kind)
        jit = Jitter(f"{d.name}-node-{nid}")
        if n.kind == "actor":
            pts = ellipse_path(n.cx, n.cy, n.w / 2, n.h / 2, jit)
        elif n.kind == "decision":
            pts = diamond_path(n, jit)
        else:
            pts = rect_path(n.x, n.y, n.w, n.h, 8 if n.kind != "note" else 4, jit)
        o.append(_svg_poly(pts, st["stroke"], st["width"], _dash(st["dash"]), st["fill"], True))
        if n.kind == "store":
            o.append(_svg_poly(poly_path([(n.x + 6, n.y + 5), (n.x + n.w - 6, n.y + 5)], jit), st["stroke"], 1, None))
        for lines, size, key, bold, top, align, x in node_text_blocks(n):
            o += _svg_text(lines, x, top, size, st[key], align, bold)
    for t in d.texts:
        o += _svg_text(t.s.split("\n"), t.x, t.y, t.size, t.color, t.align, t.bold)
    for kind, label, lx, ly in d._legend:
        o += _svg_legend_swatch(kind, lx, ly)
        o += _svg_text([label], lx + 34, ly, 12, INK2, "left", False)
    o.append("</svg>")
    return "\n".join(o) + "\n"


def _swatch_shapes(kind, lx, ly):
    """Return ('rect'|'line', params, style) for a legend swatch."""
    if kind in ("solid", "dashed"):
        return ("line", [(lx, ly + 8), (lx + 26, ly + 8)], kind)
    return ("rect", (lx, ly + 1, 26, 14), kind)


def _svg_legend_swatch(kind, lx, ly):
    shape, p, k = _swatch_shapes(kind, lx, ly)
    if shape == "line":
        return [_svg_poly(p, INK, 1.5, _dash(k)), _svg_poly(arrow_head(p[1], p[0], 7), INK, 1.5, None)]
    st = node_style(k)
    x, y, w, h = p
    return [_svg_poly(rect_path(x, y, w, h, 3, Jitter("legend" + k, 0.2)), st["stroke"], st["width"],
                      _dash(st["dash"]), st["fill"], True)]


# ── PNG renderer ─────────────────────────────────────────────────────────────
def _hex(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _png_poly(draw, pts, color, width, dash=None, fill=None, close=False, S=PNG_SCALE, ox=0, oy=0):
    P = [((x - ox) * S, (y - oy) * S) for x, y in pts]
    if fill and close:
        draw.polygon(P, fill=_hex(fill))
    w = max(1, int(round(width * S)))
    if not dash:
        draw.line(P, fill=_hex(color), width=w, joint="curve")
        return
    on, off = dash[0] * S, dash[1] * S
    acc, drawing = 0.0, True
    for i in range(len(P) - 1):
        (xa, ya), (xb, yb) = P[i], P[i + 1]
        L = math.hypot(xb - xa, yb - ya)
        t = 0.0
        while t < L:
            seg = (on if drawing else off) - acc
            step = min(seg, L - t)
            if drawing:
                p = (xa + (xb - xa) * t / L, ya + (yb - ya) * t / L)
                q = (xa + (xb - xa) * (t + step) / L, ya + (yb - ya) * (t + step) / L)
                draw.line([p, q], fill=_hex(color), width=w)
            t += step
            acc += step
            if acc >= (on if drawing else off) - 1e-6:
                acc, drawing = 0.0, not drawing


def _png_text(draw, lines, x, top, size, color, align, bold, S=PNG_SCALE, ox=0, oy=0):
    f = font(size * S, bold)
    anchor = {"center": "mm", "left": "lm", "right": "rm"}[align]
    for i, ln in enumerate(lines):
        cy = top + (i + 0.5) * size * LINE_HEIGHT
        ln = ln.replace("⇒", "=>").replace("↔", "<->").replace("→", "->").replace("←", "<-")
        draw.text(((x - ox) * S, (cy - oy) * S), ln, font=f, fill=_hex(color), anchor=anchor)


def render_png(d: Diagram, out_path: str):
    finalize(d)
    x0, y0, x1, y1 = bounds(d)
    tx, ty = d._title_xy
    if d._legend:
        y1 = max(y1, d._legend[-1][3] + 24)
        x1 = max(x1, d._legend[-1][2] + 34 + text_width(d._legend[-1][1], 12) + 10)
    x1 = max(x1, tx + text_width(d.title, 26, True))
    ox, oy = x0 - MARGIN, ty - MARGIN + 10
    W, H = (x1 - x0) + 2 * MARGIN, (y1 - oy) + MARGIN
    S = PNG_SCALE
    img = Image.new("RGB", (int(W * S), int(H * S)), (255, 255, 255))
    dr = ImageDraw.Draw(img)
    kw = dict(S=S, ox=ox, oy=oy)
    _png_text(dr, [d.title], tx, ty, 26, INK, "left", True, **kw)
    if d.subtitle:
        _png_text(dr, [d.subtitle], tx, ty + 30, 13, INK2, "left", False, **kw)
    for i, f in enumerate(d.frames):
        _png_poly(dr, rect_path(f.x, f.y, f.w, f.h, 10, Jitter(f"{d.name}-frame-{i}", 0.5)), INK3, 1, **kw)
        if f.label:
            _png_text(dr, [f.label], f.x + 14, f.y + 8, 13, INK2, "left", True, **kw)
    for ln in d.lines:
        _png_poly(dr, ln.pts, ln.color, ln.width, _dash(ln.style), **kw)
    for i, e in enumerate(d.edges):
        jit = Jitter(f"{d.name}-edge-{i}")
        pts = edge_points(d, e)
        path = poly_path(pts, jit)
        _png_poly(dr, path, INK, 1.5, _dash(e.style), **kw)
        if e.head:
            _png_poly(dr, arrow_head(pts[-1], path[-2]), INK, 1.5, **kw)
        if e.both:
            _png_poly(dr, arrow_head(pts[0], path[1]), INK, 1.5, **kw)
    for e in d.edges:
        if not e.label:
            continue
        lines, size, lx, ly, w, h, ax = _label_box(e, d, edge_points(d, e))
        dr.rectangle([(lx - ox) * S, (ly - oy) * S, (lx + w - ox) * S, (ly + h - oy) * S], fill=(255, 255, 255))
        _png_text(dr, lines, ax, ly + 2, size, INK2, "center", False, **kw)
    for nid in d.order:
        n = d.nodes[nid]
        if n.kind == "anchor":
            continue
        st = node_style(n.kind)
        jit = Jitter(f"{d.name}-node-{nid}")
        if n.kind == "actor":
            pts = ellipse_path(n.cx, n.cy, n.w / 2, n.h / 2, jit)
        elif n.kind == "decision":
            pts = diamond_path(n, jit)
        else:
            pts = rect_path(n.x, n.y, n.w, n.h, 8 if n.kind != "note" else 4, jit)
        _png_poly(dr, pts, st["stroke"], st["width"], _dash(st["dash"]), st["fill"], True, **kw)
        if n.kind == "store":
            _png_poly(dr, poly_path([(n.x + 6, n.y + 5), (n.x + n.w - 6, n.y + 5)], jit), st["stroke"], 1, **kw)
        for lines, size, key, bold, top, align, x in node_text_blocks(n):
            _png_text(dr, lines, x, top, size, st[key], align, bold, **kw)
    for t in d.texts:
        _png_text(dr, t.s.split("\n"), t.x, t.y, t.size, t.color, t.align, t.bold, **kw)
    for kind, label, lx, ly in d._legend:
        shape, p, k = _swatch_shapes(kind, lx, ly)
        if shape == "line":
            _png_poly(dr, p, INK, 1.5, _dash(k), **kw)
            _png_poly(dr, arrow_head(p[1], p[0], 7), INK, 1.5, **kw)
        else:
            st = node_style(k)
            x, y, w, h = p
            _png_poly(dr, rect_path(x, y, w, h, 3, Jitter("legend" + k, 0.2)), st["stroke"], st["width"],
                      _dash(st["dash"]), st["fill"], True, **kw)
        _png_text(dr, [label], lx + 34, ly, 12, INK2, "left", False, **kw)
    img.save(out_path, optimize=True)


# ── Excalidraw serialiser ────────────────────────────────────────────────────
class _Ids:
    def __init__(self, ns):
        self.ns = ns
        self.n = 0
        self.rng = random.Random(zlib.crc32(ns.encode()))

    def next(self, prefix):
        self.n += 1
        return f"{prefix}-{self.ns}-{self.n}"

    def seed(self):
        return self.rng.randint(1, 2**31 - 1)


def _base(ids: _Ids, typ, x, y, w, h, stroke=INK, fill="transparent", width=1, dash="solid",
          roundness=None, group=None):
    return {
        "id": ids.next(typ[:4]),
        "type": typ,
        "x": round(x, 2),
        "y": round(y, 2),
        "width": round(w, 2),
        "height": round(h, 2),
        "angle": 0,
        "strokeColor": stroke,
        "backgroundColor": fill,
        "fillStyle": "solid",
        "strokeWidth": width,
        "strokeStyle": dash,
        "roughness": 1,
        "opacity": 100,
        "groupIds": [group] if group else [],
        "frameId": None,
        "roundness": roundness,
        "seed": ids.seed(),
        "version": 1,
        "versionNonce": ids.seed(),
        "isDeleted": False,
        "boundElements": None,
        "updated": 1,
        "link": None,
        "locked": False,
    }


def _text_el(ids, lines, x, top, size, color, align, group=None):
    txt = "\n".join(lines)
    w = max(text_width(l, size) for l in lines) if lines else 0
    h = len(lines) * size * LINE_HEIGHT
    x0 = x - w / 2 if align == "center" else (x - w if align == "right" else x)
    el = _base(ids, "text", x0, top, w, h, stroke=color, group=group)
    el.update({
        "text": txt,
        "fontSize": size,
        "fontFamily": EXCALIDRAW_FONT_FAMILY,
        "textAlign": align,
        "verticalAlign": "top",
        "containerId": None,
        "originalText": txt,
        "autoResize": True,
        "lineHeight": LINE_HEIGHT,
    })
    return el


def _linear_el(ids, typ, pts, stroke=INK, width=1.5, dash="solid", start=None, end="arrow"):
    x0, y0 = pts[0]
    rel = [[round(px - x0, 2), round(py - y0, 2)] for px, py in pts]
    xs = [p[0] for p in rel]
    ys = [p[1] for p in rel]
    # Sharp segments (roundness None) so multi-point routes keep their elbows
    # in the Excalidraw editor, matching the SVG/PNG exports.
    el = _base(ids, typ, x0, y0, max(xs) - min(xs), max(ys) - min(ys), stroke=stroke, width=width,
               dash=dash, roundness=None)
    el.update({
        "points": rel,
        "lastCommittedPoint": None,
        "startBinding": None,
        "endBinding": None,
        "startArrowhead": start,
        "endArrowhead": end,
    })
    if typ == "arrow":
        el["elbowed"] = False
    else:
        el["polygon"] = False
    return el


def to_excalidraw(d: Diagram) -> dict:
    finalize(d)
    ids = _Ids(d.name)
    els = []
    tx, ty = d._title_xy
    els.append(_text_el(ids, [d.title], tx, ty, 26, INK, "left"))
    if d.subtitle:
        els.append(_text_el(ids, [d.subtitle], tx, ty + 30, 13, INK2, "left"))
    for f in d.frames:
        g = ids.next("grp")
        els.append(_base(ids, "rectangle", f.x, f.y, f.w, f.h, stroke=INK3, width=1,
                         roundness={"type": 3}, group=g))
        if f.label:
            els.append(_text_el(ids, [f.label], f.x + 14, f.y + 8, 13, INK2, "left", group=g))
    for ln in d.lines:
        els.append(_linear_el(ids, "line", ln.pts, stroke=ln.color, width=ln.width, dash=ln.style, end=None))
    for e in d.edges:
        pts = edge_points(d, e)
        els.append(_linear_el(ids, "arrow", pts, dash=e.style, start="arrow" if e.both else None,
                              end="arrow" if e.head else None))
    for e in d.edges:
        if not e.label:
            continue
        lines, size, lx, ly, w, h, ax = _label_box(e, d, edge_points(d, e))
        g = ids.next("grp")
        els.append(_base(ids, "rectangle", lx, ly, w, h, stroke="transparent", fill=WHITE, group=g))
        els.append(_text_el(ids, lines, ax, ly + 2, size, INK2, "center", group=g))
    for nid in d.order:
        n = d.nodes[nid]
        if n.kind == "anchor":
            continue
        st = node_style(n.kind)
        g = ids.next("grp")
        typ = {"actor": "ellipse", "decision": "diamond"}.get(n.kind, "rectangle")
        rnd = None if typ == "ellipse" else ({"type": 2} if typ == "diamond" else {"type": 3})
        els.append(_base(ids, typ, n.x, n.y, n.w, n.h, stroke=st["stroke"], fill=st["fill"],
                         width=st["width"], dash=st["dash"], roundness=rnd, group=g))
        if n.kind == "store":
            ln = _linear_el(ids, "line", [(n.x + 6, n.y + 5), (n.x + n.w - 6, n.y + 5)], stroke=st["stroke"],
                            width=1, end=None)
            ln["groupIds"] = [g]
            els.append(ln)
        for lines, size, key, bold, top, align, x in node_text_blocks(n):
            els.append(_text_el(ids, lines, x, top, size, st[key], align, group=g))
    for t in d.texts:
        els.append(_text_el(ids, t.s.split("\n"), t.x, t.y, t.size, t.color, t.align))
    for kind, label, lx, ly in d._legend:
        shape, p, k = _swatch_shapes(kind, lx, ly)
        g = ids.next("grp")
        if shape == "line":
            a = _linear_el(ids, "arrow", p, dash=k)
            a["groupIds"] = [g]
            els.append(a)
        else:
            st = node_style(k)
            x, y, w, h = p
            els.append(_base(ids, "rectangle", x, y, w, h, stroke=st["stroke"], fill=st["fill"],
                             width=st["width"], dash=st["dash"], roundness={"type": 3}, group=g))
        els.append(_text_el(ids, [label], lx + 34, ly + 1, 12, INK2, "left", group=g))
    return {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": els,
        "appState": {"viewBackgroundColor": "#ffffff", "gridSize": None},
        "files": {},
    }


# ── Layout checks ────────────────────────────────────────────────────────────
def _boxes_overlap(a, b, m=0.0):
    return a[0] < b[2] - m and b[0] < a[2] - m and a[1] < b[3] - m and b[1] < a[3] - m


def _seg_hits_box(p, q, b, m=2.0):
    """Liang-Barsky segment / rectangle intersection, rectangle shrunk by m."""
    x0, y0, x1, y1 = b[0] + m, b[1] + m, b[2] - m, b[3] - m
    dx, dy = q[0] - p[0], q[1] - p[1]
    t0, t1 = 0.0, 1.0
    for pp, qq in ((-dx, p[0] - x0), (dx, x1 - p[0]), (-dy, p[1] - y0), (dy, y1 - p[1])):
        if pp == 0:
            if qq < 0:
                return False
            continue
        r = qq / pp
        if pp < 0:
            t0 = max(t0, r)
        else:
            t1 = min(t1, r)
        if t0 > t1:
            return False
    return True


def text_boxes(d: Diagram):
    """(owner, bbox) for every rendered text block."""
    out = []
    for nid in d.order:
        n = d.nodes[nid]
        if n.kind == "anchor":
            continue
        for lines, size, _k, _b, top, align, x in node_text_blocks(n):
            w = max(text_width(l, size) for l in lines)
            h = len(lines) * size * LINE_HEIGHT
            x0 = x - w / 2 if align == "center" else x
            out.append((f"node:{nid}", (x0, top, x0 + w, top + h)))
    for i, f in enumerate(d.frames):
        if f.label:
            w = text_width(f.label, 13)
            out.append((f"frame:{i}", (f.x + 14, f.y + 8, f.x + 14 + w, f.y + 8 + 13 * LINE_HEIGHT)))
    for i, e in enumerate(d.edges):
        if e.label:
            lines, size, lx, ly, w, h, ax = _label_box(e, d, edge_points(d, e))
            out.append((f"label:{e.a}->{e.b}", (lx, ly, lx + w, ly + h)))
    for i, t in enumerate(d.texts):
        lines = t.s.split("\n")
        w = max(text_width(l, t.size) for l in lines)
        h = len(lines) * t.size * LINE_HEIGHT
        x0 = t.x - (w / 2 if t.align == "center" else 0)
        out.append((f"text:{i}", (x0, t.y, x0 + w, t.y + h)))
    return out


def check_layout(d: Diagram):
    """Return human-readable layout problems: overflow, collisions, arrows through boxes."""
    probs = []
    real = [d.nodes[i] for i in d.order if d.nodes[i].kind != "anchor"]
    nb = {n.id: (n.x, n.y, n.x + n.w, n.y + n.h) for n in real}
    tb = text_boxes(d)
    for owner, b in tb:
        if owner.startswith("node:"):
            n = d.nodes[owner[5:]]
            if n.kind in ("decision", "actor"):
                continue
            if b[0] < n.x + 3 or b[2] > n.x + n.w - 3 or b[1] < n.y + 2 or b[3] > n.y + n.h - 2:
                probs.append(f"text overflows {owner}")
    for i in range(len(tb)):
        for j in range(i + 1, len(tb)):
            if tb[i][0] == tb[j][0]:
                continue
            if tb[i][0].startswith("node:") and tb[j][0].startswith("node:"):
                continue
            if _boxes_overlap(tb[i][1], tb[j][1], 1):
                probs.append(f"text collision {tb[i][0]} / {tb[j][0]}")
    for owner, b in tb:
        if owner.startswith("node:"):
            continue
        for n in real:
            if _boxes_overlap(b, nb[n.id], 1):
                probs.append(f"{owner} overlaps box {n.id}")
    for i, a in enumerate(real):
        for b in real[i + 1:]:
            if _boxes_overlap(nb[a.id], nb[b.id], 1):
                probs.append(f"boxes overlap {a.id} / {b.id}")
    for e in d.edges:
        pts = edge_points(d, e)
        for k in range(len(pts) - 1):
            for n in real:
                if n.id in (e.a, e.b):
                    continue
                if _seg_hits_box(pts[k], pts[k + 1], nb[n.id]):
                    probs.append(f"arrow {e.a}->{e.b} crosses {n.id}")
    return sorted(set(probs))


# ── Output ───────────────────────────────────────────────────────────────────
def write_all(d: Diagram, root: str):
    for sub in ("excalidraw", "svg", "png"):
        os.makedirs(os.path.join(root, sub), exist_ok=True)
    with open(os.path.join(root, "excalidraw", f"{d.name}.excalidraw"), "w") as fh:
        json.dump(to_excalidraw(d), fh, indent=2)
        fh.write("\n")
    with open(os.path.join(root, "svg", f"{d.name}.svg"), "w") as fh:
        fh.write(render_svg(d))
    render_png(d, os.path.join(root, "png", f"{d.name}.png"))


# ── Layout helpers ───────────────────────────────────────────────────────────
def sequence(d: Diagram, x0: float, y0: float, participants, steps, col_w=210, box_w=180,
             box_h=56, row_h=46):
    """Lay out a sequence diagram.

    participants: list of (id, title, sub, kind)
    steps: list of tuples
      ("msg", from_id, to_id, label[, style])   horizontal message
      ("self", id, label)                       note box on one lifeline
      ("span", from_id, to_id, label)           note spanning lifelines
      ("gap", pixels)
    """
    xs = {}
    for i, (pid, title, sub, kind) in enumerate(participants):
        cx = x0 + i * col_w + box_w / 2
        xs[pid] = cx
        d.node(f"p_{pid}", cx - box_w / 2, y0, box_w, box_h, title, sub, kind, title_size=15, sub_size=12)
    y = y0 + box_h + 34
    k = 0
    anchors = []
    for st in steps:
        kind = st[0]
        if kind == "gap":
            y += st[1]
            continue
        if kind == "msg":
            _, a, b, label, *rest = st
            style = rest[0] if rest else "solid"
            k += 1
            ia, ib = f"_s{k}a", f"_s{k}b"
            d.node(ia, xs[a] - 0.5, y - 0.5, 1, 1, "", kind="anchor")
            d.node(ib, xs[b] - 0.5, y - 0.5, 1, 1, "", kind="anchor")
            d.edge(ia, ib, label, style, label_dy=-11)
            anchors += [ia, ib]
            y += row_h
        elif kind in ("self", "span"):
            if kind == "self":
                _, a, label = st
                lx, rx = xs[a] - box_w / 2 + 6, xs[a] + box_w / 2 - 6
            else:
                _, a, b, label = st
                lx = min(xs[a], xs[b]) - box_w / 2 + 6
                rx = max(xs[a], xs[b]) + box_w / 2 - 6
            lines = label.split("\n")
            need = max(text_width(l, 12) for l in lines) + 24
            if rx - lx < need:
                mid = (lx + rx) / 2
                lx, rx = mid - need / 2, mid + need / 2
            h = len(lines) * 12 * LINE_HEIGHT + 14
            k += 1
            d.node(f"_n{k}", lx, y - 10, rx - lx, h, "", label, "note", sub_size=12)
            y += h + 24
    bottom = y + 6
    for pid, cx in xs.items():
        d.line([(cx, y0 + box_h), (cx, bottom)], "dotted", INK3, 1)
    return bottom


def vflow(d: Diagram, x: float, y: float, w: float, items, gap=26, h=50, edge_labels=None):
    """Vertical chain of nodes. items: list of (id, title, sub, kind[, h])."""
    prev = None
    cy = y
    for it in items:
        nid, title, sub, kind = it[:4]
        hh = it[4] if len(it) > 4 else h
        d.node(nid, x, cy, w, hh, title, sub, kind)
        if prev:
            lbl = (edge_labels or {}).get(nid, "")
            d.edge(prev, nid, lbl, ap="b", bp="t")
        prev = nid
        cy += hh + gap
    return cy
