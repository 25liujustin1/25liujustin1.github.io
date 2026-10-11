"""Convert a KiCad .kicad_pcb file into an interactive SVG for the home page.

Usage:
    python tools/kicad_to_svg.py path/to/board.kicad_pcb _includes/board.svg [--links links.json]

Draws the board outline, copper pours, tracks, vias, pads and front silkscreen.
Every copper item gets a class for its net (net-SDA, net-3V3, ...) so the page can
highlight nets, and footprints listed in the links file become clickable.
"""
import argparse
import json
import math
import re
import sys
from html import escape


# ---------------------------------------------------------------- s-expressions
TOKEN = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+')


def parse(text):
    stack, cur = [], []
    for m in TOKEN.finditer(text):
        tok = m.group(0)
        if tok == "(":
            stack.append(cur)
            cur = []
        elif tok == ")":
            done = cur
            cur = stack.pop()
            cur.append(done)
        elif tok.startswith('"'):
            cur.append(tok[1:-1].replace('\\"', '"'))
        else:
            cur.append(tok)
    return cur[0]


def kids(node, name):
    return [c for c in node[1:] if isinstance(c, list) and c and c[0] == name]


def kid(node, name):
    found = kids(node, name)
    return found[0] if found else None


def val(node, name, default=None):
    k = kid(node, name)
    return k[1] if k and len(k) > 1 else default


def xy(node, name):
    k = kid(node, name)
    return (float(k[1]), float(k[2])) if k else None


def layer_of(node):
    k = kid(node, "layer")
    return k[1] if k else None


def layers_of(node):
    k = kid(node, "layers")
    return k[1:] if k else []


# ---------------------------------------------------------------- geometry
def rotate(px, py, deg):
    # KiCad rotates counter-clockwise on screen with y pointing down
    a = math.radians(-deg)
    return px * math.cos(a) - py * math.sin(a), px * math.sin(a) + py * math.cos(a)


class Placement:
    def __init__(self, x, y, rot):
        self.x, self.y, self.rot = x, y, rot

    def apply(self, px, py):
        rx, ry = rotate(px, py, self.rot)
        return self.x + rx, self.y + ry


def f(n):
    return f"{n:.3f}".rstrip("0").rstrip(".")


def net_class(name):
    if not name:
        return ""
    return "net-" + re.sub(r"[^A-Za-z0-9_-]", "_", name)


# ---------------------------------------------------------------- main
def convert(pcb_path, links, rotate_deg=0):
    tree = parse(open(pcb_path, encoding="utf-8").read())

    copper = {"F.Cu": [], "B.Cu": []}
    zones = {"F.Cu": [], "B.Cu": []}
    silk = []
    vias = []
    pads = {"F.Cu": [], "B.Cu": []}
    hits = []          # clickable footprint areas
    outline = []
    xs, ys = [], []

    def grow(*pts):
        for px, py in pts:
            xs.append(px)
            ys.append(py)

    # board outline: Edge.Cuts graphics, or a lone rectangle if Edge.Cuts is empty
    edge = [g for g in tree[1:] if isinstance(g, list) and g and g[0].startswith("gr_") and layer_of(g) == "Edge.Cuts"]
    if not edge:
        edge = [g for g in tree[1:] if isinstance(g, list) and g and g[0] == "gr_rect"]
    for g in edge:
        if g[0] == "gr_rect":
            (x1, y1), (x2, y2) = xy(g, "start"), xy(g, "end")
            outline.append(f'<rect x="{f(min(x1,x2))}" y="{f(min(y1,y2))}" width="{f(abs(x2-x1))}" height="{f(abs(y2-y1))}" rx="0.6"/>')
            grow((x1, y1), (x2, y2))
        elif g[0] == "gr_line":
            (x1, y1), (x2, y2) = xy(g, "start"), xy(g, "end")
            outline.append(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}"/>')
            grow((x1, y1), (x2, y2))

    if not outline:
        # no Edge.Cuts at all: use the outer boundary of the copper pours
        zx, zy = [], []
        for z in kids(tree, "zone"):
            poly = kid(z, "polygon")
            if poly is None:
                continue
            for p in kid(poly, "pts")[1:]:
                if p[0] == "xy":
                    zx.append(float(p[1]))
                    zy.append(float(p[2]))
        if zx:
            x1, y1, x2, y2 = min(zx), min(zy), max(zx), max(zy)
            outline.append(f'<rect x="{f(x1)}" y="{f(y1)}" width="{f(x2-x1)}" height="{f(y2-y1)}" rx="1.5"/>')
            grow((x1, y1), (x2, y2))
            print("note: no Edge.Cuts outline found; using the copper pour boundary", file=sys.stderr)

    # tracks and vias
    for s in kids(tree, "segment"):
        (x1, y1), (x2, y2) = xy(s, "start"), xy(s, "end")
        lay = layer_of(s)
        if lay in copper:
            copper[lay].append(f'<line class="{net_class(val(s, "net"))}" x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" stroke-width="{f(float(val(s, "width")))}"/>')
    for v in kids(tree, "via"):
        x, y = xy(v, "at")
        size = float(val(v, "size"))
        drill = float(val(v, "drill"))
        vias.append(f'<g class="via {net_class(val(v, "net"))}"><circle cx="{f(x)}" cy="{f(y)}" r="{f(size/2)}"/>'
                    f'<circle class="hole" cx="{f(x)}" cy="{f(y)}" r="{f(drill/2)}"/></g>')

    # copper pours (filled polygons only; unfilled zones have nothing to draw)
    for z in kids(tree, "zone"):
        for fp in kids(z, "filled_polygon"):
            lay = layer_of(fp)
            pts = kid(fp, "pts")
            coords = [(float(p[1]), float(p[2])) for p in pts[1:] if p[0] == "xy"]
            if lay in zones and coords:
                d = "M" + " L".join(f"{f(a)} {f(b)}" for a, b in coords) + " Z"
                zones[lay].append(f'<path class="{net_class(val(z, "net"))}" d="{d}"/>')

    # footprints
    for fpt in kids(tree, "footprint"):
        fx, fy = xy(fpt, "at")
        at = kid(fpt, "at")
        frot = float(at[3]) if len(at) > 3 else 0.0
        place = Placement(fx, fy, frot)
        side = layer_of(fpt)
        ref = next((p[2] for p in kids(fpt, "property") if p[1] == "Reference"), "")
        value = next((p[2] for p in kids(fpt, "property") if p[1] == "Value"), "")
        fpts = []

        for p in kids(fpt, "pad"):
            pat = kid(p, "at")
            px, py = float(pat[1]), float(pat[2])
            prot = float(pat[3]) if len(pat) > 3 else 0.0
            w, h = xy(p, "size")
            shape = p[3]
            cx, cy = place.apply(px, py)
            fpts.append((cx, cy))
            total = prot  # pad rotation in KiCad files is absolute (already includes footprint rotation)
            nc = net_class(val(p, "net"))
            lays = layers_of(p)
            targets = [l for l in ("F.Cu", "B.Cu") if l in lays or "*.Cu" in lays]
            if shape in ("circle",):
                el = f'<circle class="pad {nc}" cx="{f(cx)}" cy="{f(cy)}" r="{f(w/2)}"/>'
            else:
                rx = min(w, h) / 2 if shape == "oval" else (min(w, h) * 0.25 if shape == "roundrect" else 0)
                el = (f'<rect class="pad {nc}" x="{f(cx-w/2)}" y="{f(cy-h/2)}" width="{f(w)}" height="{f(h)}" rx="{f(rx)}" '
                      f'transform="rotate({f(-total)} {f(cx)} {f(cy)})"/>')
            drill = kid(p, "drill")
            if drill is not None and len(drill) > 1:
                try:
                    dr = float(drill[1])
                    el += f'<circle class="hole" cx="{f(cx)}" cy="{f(cy)}" r="{f(dr/2)}"/>'
                except ValueError:
                    pass
            for t in targets:
                pads[t].append(el)

        # front silkscreen graphics (back silk is hidden, like viewing the top side)
        for g in fpt[1:]:
            if not (isinstance(g, list) and g and g[0].startswith("fp_")):
                continue
            lay = layer_of(g)
            if lay not in ("F.SilkS",):
                continue
            sw = float(val(kid(g, "stroke") or ["stroke"], "width", 0.12) or 0.12)
            if g[0] == "fp_line":
                (x1, y1), (x2, y2) = place.apply(*xy(g, "start")), place.apply(*xy(g, "end"))
                silk.append(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" stroke-width="{f(sw)}"/>')
                fpts += [(x1, y1), (x2, y2)]
            elif g[0] == "fp_rect":
                (x1, y1), (x2, y2) = xy(g, "start"), xy(g, "end")
                corners = [place.apply(x1, y1), place.apply(x2, y1), place.apply(x2, y2), place.apply(x1, y2)]
                d = "M" + " L".join(f"{f(a)} {f(b)}" for a, b in corners) + " Z"
                silk.append(f'<path d="{d}" stroke-width="{f(sw)}"/>')
            elif g[0] == "fp_poly":
                pts = [place.apply(float(q[1]), float(q[2])) for q in kid(g, "pts")[1:] if q[0] == "xy"]
                if pts:
                    filled = val(g, "fill") in ("yes", "solid")
                    d = "M" + " L".join(f"{f(a)} {f(b)}" for a, b in pts) + " Z"
                    silk.append(f'<path class="{"fill" if filled else ""}" d="{d}" stroke-width="{f(sw)}"/>')
            elif g[0] == "fp_arc":
                (x1, y1), (xm, ym), (x2, y2) = (place.apply(*xy(g, k)) for k in ("start", "mid", "end"))
                # circle through three points
                dd = 2 * (x1 * (ym - y2) + xm * (y2 - y1) + x2 * (y1 - ym))
                if abs(dd) > 1e-9:
                    ux = ((x1**2 + y1**2) * (ym - y2) + (xm**2 + ym**2) * (y2 - y1) + (x2**2 + y2**2) * (y1 - ym)) / dd
                    uy = ((x1**2 + y1**2) * (x2 - xm) + (xm**2 + ym**2) * (x1 - x2) + (x2**2 + y2**2) * (xm - x1)) / dd
                    r = math.hypot(x1 - ux, y1 - uy)
                    cross = (xm - x1) * (y2 - y1) - (ym - y1) * (x2 - x1)
                    sweep = 1 if cross < 0 else 0
                    a1 = math.atan2(y1 - uy, x1 - ux); am = math.atan2(ym - uy, xm - ux); a2 = math.atan2(y2 - uy, x2 - ux)
                    span = (a2 - a1) % (2 * math.pi) if sweep else (a1 - a2) % (2 * math.pi)
                    large = 1 if span > math.pi else 0
                    silk.append(f'<path d="M{f(x1)} {f(y1)} A{f(r)} {f(r)} 0 {large} {sweep} {f(x2)} {f(y2)}" stroke-width="{f(sw)}"/>')
            elif g[0] == "fp_circle":
                (cx, cy) = place.apply(*xy(g, "center"))
                ex, ey = place.apply(*xy(g, "end"))
                r = math.hypot(ex - cx, ey - cy)
                silk.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" stroke-width="{f(sw)}"/>')

        # reference designator on the silkscreen (front parts only)
        refprop = next((p for p in kids(fpt, "property") if p[1] == "Reference"), None)
        if refprop is not None and side == "F.Cu" and val(refprop, "hide") != "yes":
            rat = kid(refprop, "at")
            tx, ty = place.apply(float(rat[1]), float(rat[2]))
            size = float(kid(kid(kid(refprop, "effects"), "font"), "size")[1])
            silk.append(f'<text x="{f(tx)}" y="{f(ty)}" font-size="{f(min(size * 1.25, 0.75))}">{escape(ref)}</text>')

        # clickable area around the footprint
        if ref in links and fpts:
            bx = [p[0] for p in fpts]
            by = [p[1] for p in fpts]
            pad_mm = 0.6
            x0, y0 = min(bx) - pad_mm, min(by) - pad_mm
            w, h = max(bx) - min(bx) + 2 * pad_mm, max(by) - min(by) + 2 * pad_mm
            link = links[ref]
            nets = sorted({net_class(val(p, "net")) for p in kids(fpt, "pad") if val(p, "net")})
            hits.append(
                f'<a class="part-link" href="{escape(link["href"])}" data-ref="{escape(ref)}" data-label="{escape(link["label"])}" '
                f'data-nets="{" ".join(nets)}" aria-label="{escape(link["label"])} ({escape(ref)} {escape(value)})">'
                f'<title>{escape(ref)} · {escape(value)} → {escape(link["label"])}</title>'
                f'<rect x="{f(x0)}" y="{f(y0)}" width="{f(w)}" height="{f(h)}" rx="0.4"/></a>'
            )

    if not xs:
        sys.exit("No board outline found")
    margin = 1.2
    vx, vy = min(xs) - margin, min(ys) - margin
    vw, vh = max(xs) - min(xs) + 2 * margin, max(ys) - min(ys) + 2 * margin

    if rotate_deg % 180 == 90:
        cx, cy = vx + vw / 2, vy + vh / 2
        view = f"{f(cx - vh/2)} {f(cy - vw/2)} {f(vh)} {f(vw)}"
        wrap_open = f'<g transform="rotate({rotate_deg} {f(cx)} {f(cy)})">'
    else:
        view = f"{f(vx)} {f(vy)} {f(vw)} {f(vh)}"
        wrap_open = "<g>"
    out = [f'<svg class="pcb" viewBox="{view}" xmlns="http://www.w3.org/2000/svg">', wrap_open]
    out.append('<defs><clipPath id="board-clip">' + "".join(outline) + "</clipPath></defs>")
    out.append('<g class="board-outline">' + "".join(outline) + "</g>")
    out.append('<g clip-path="url(#board-clip)">')
    out.append('<g class="layer b-cu">' + "".join(zones["B.Cu"]) + '<g class="tracks">' + "".join(copper["B.Cu"]) + "</g>" + "".join(pads["B.Cu"]) + "</g>")
    out.append('<g class="layer f-cu">' + "".join(zones["F.Cu"]) + '<g class="tracks">' + "".join(copper["F.Cu"]) + "</g>" + "".join(pads["F.Cu"]) + "</g>")
    out.append('<g class="vias">' + "".join(vias) + "</g>")
    out.append('<g class="silk">' + "".join(silk) + "</g>")
    out.append("</g>")
    out.append('<g class="hits">' + "".join(hits) + "</g>")
    out.append("</g></svg>")
    return "\n".join(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pcb")
    ap.add_argument("out")
    ap.add_argument("--links", help="JSON file mapping reference designators to {href, label}")
    ap.add_argument("--rotate", type=int, default=0, help="rotate the board for display (0 or 90)")
    args = ap.parse_args()
    links = json.load(open(args.links, encoding="utf-8")) if args.links else {}
    svg = convert(args.pcb, links, args.rotate)
    open(args.out, "w", encoding="utf-8").write(svg)
    print(f"wrote {args.out} ({len(svg)} bytes)")
