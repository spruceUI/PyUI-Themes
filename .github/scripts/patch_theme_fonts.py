#!/usr/bin/env python3
"""Copy the symbols PyUI draws into any theme font that lacks them.

Usage: patch_theme_fonts.py [theme_dir ...]   (default: every dir in Themes/)
"""
import os
import sys

from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

SYMBOLS = "←↑→↓↵⇪✓"
DONOR = "Themes/SPRUCE/nunwen.ttf"
FONT_EXTS = (".ttf", ".otf")
PER_GLYPH_TABLES = ("hdmx", "LTSH", "DSIG", "HVAR", "VVAR")
GLYPH_INDEXED_TABLES = ("glyf", "loca", "hmtx", "vmtx", "gvar", "post", "CFF ", "VORG")


def cap_height(font):
    os2 = font.get("OS/2")
    if os2 is not None and getattr(os2, "sCapHeight", 0) > 0:
        return os2.sCapHeight
    name = font.getBestCmap().get(ord("H"))
    if name:
        pen = BoundsPen(font.getGlyphSet())
        font.getGlyphSet()[name].draw(pen)
        if pen.bounds and pen.bounds[3] > 0:
            return pen.bounds[3]
    return None


def unique_name(font, codepoint):
    existing = set(font.getGlyphOrder())
    name = "uni%04X" % codepoint
    n = 1
    while name in existing:
        name = "uni%04X.%d" % (codepoint, n)
        n += 1
    return name


def add_ttf_glyph(font, name, draw, width):
    pen = TTGlyphPen(None)
    draw(pen)
    font["glyf"][name] = pen.glyph()
    glyph = font["glyf"][name]
    glyph.recalcBounds(font["glyf"])
    return getattr(glyph, "xMin", 0)


def add_cff_glyph(font, name, draw, width):
    cff = font["CFF "].cff
    top = cff.topDictIndex[0]
    is_cid = hasattr(top, "ROS")
    private = top.FDArray[0].Private if is_cid else top.Private
    nominal = getattr(private, "nominalWidthX", 0)
    pen = T2CharStringPen(width - nominal, None)
    draw(pen)
    charstring = pen.getCharString(private=private, globalSubrs=cff.GlobalSubrs)
    if is_cid:
        charstring.fdSelectIndex = 0
        top.FDSelect.append(0)
    strings = top.CharStrings
    strings.charStringsIndex.append(charstring)
    strings.charStrings[name] = len(strings.charStringsIndex) - 1
    top.charset.append(name)
    bounds = BoundsPen(None)
    draw(bounds)
    return round(bounds.bounds[0]) if bounds.bounds else 0


def cff_cid_name(font):
    top = font["CFF "].cff.topDictIndex[0]
    if not hasattr(top, "ROS"):
        return None
    cids = [int(n[3:]) for n in font.getGlyphOrder() if n.startswith("cid")]
    return "cid%05d" % (max(cids, default=0) + 1)


def patch_font(path, donor, donor_cap):
    font = TTFont(path)
    cmap = font.getBestCmap() or {}
    missing = [ord(c) for c in SYMBOLS if ord(c) not in cmap]
    if not missing:
        return []
    is_cff = "CFF " in font
    if not is_cff and "glyf" not in font:
        print(f"skip (unsupported outlines): {path}")
        return []
    subtables = [t for t in font["cmap"].tables if t.isUnicode()]
    if not subtables:
        print(f"skip (no unicode cmap): {path}")
        return []
    for tag in GLYPH_INDEXED_TABLES:
        if tag in font:
            font[tag]

    target_cap = cap_height(font)
    if target_cap and donor_cap:
        scale = target_cap / donor_cap
    else:
        scale = font["head"].unitsPerEm / donor["head"].unitsPerEm

    donor_cmap = donor.getBestCmap()
    donor_glyphs = donor.getGlyphSet()
    order = list(font.getGlyphOrder())
    added = []
    for cp in missing:
        src = donor_cmap.get(cp)
        if src is None:
            continue
        name = cff_cid_name(font) if is_cff else None
        name = name or unique_name(font, cp)
        width = round(donor["hmtx"][src][0] * scale)

        def draw(pen, src=src):
            donor_glyphs[src].draw(TransformPen(pen, (scale, 0, 0, scale, 0, 0)))

        order.append(name)
        font.setGlyphOrder(order)
        if is_cff:
            lsb = add_cff_glyph(font, name, draw, width)
        else:
            font["glyf"].glyphOrder = order
            lsb = add_ttf_glyph(font, name, draw, width)
        font["hmtx"][name] = (width, lsb)
        if "vmtx" in font:
            font["vmtx"][name] = (font["head"].unitsPerEm, 0)
        if "gvar" in font:
            font["gvar"].variations.setdefault(name, [])
        for table in subtables:
            if table.format == 4 and cp > 0xFFFF:
                continue
            table.cmap[cp] = name
        added.append(chr(cp))

    if not added:
        return []
    for tag in PER_GLYPH_TABLES:
        if tag in font:
            del font[tag]
    font["maxp"].numGlyphs = len(order)
    if not is_cff:
        flags = font["head"].flags
        font["maxp"].recalc(font)
        font["head"].flags = flags
        font.recalcBBoxes = False
    font.save(path)
    return added


def main():
    root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
    themes = sys.argv[1:] or [
        os.path.join("Themes", d) for d in sorted(os.listdir(os.path.join(root, "Themes")))
    ]
    donor = TTFont(os.path.join(root, DONOR))
    donor_cap = cap_height(donor)
    for theme in themes:
        theme_dir = os.path.join(root, theme)
        if not os.path.isdir(theme_dir):
            continue
        for dirpath, _, files in os.walk(theme_dir):
            for f in sorted(files):
                if not f.lower().endswith(FONT_EXTS):
                    continue
                path = os.path.join(dirpath, f)
                if os.path.samefile(path, os.path.join(root, DONOR)):
                    continue
                try:
                    added = patch_font(path, donor, donor_cap)
                except Exception as e:
                    print(f"::warning::{os.path.relpath(path, root)}: {e}")
                    continue
                if added:
                    print(f"patched {os.path.relpath(path, root)}: {''.join(added)}")


if __name__ == "__main__":
    main()
