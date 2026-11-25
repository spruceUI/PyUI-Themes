#!/usr/bin/env python3
"""Graft PyUI glyphs into theme fonts.

Two donor fonts are used as donors only; they are never grafted themselves:

* ``Resources/fonts/promptfont.ttf`` supplies sixteen gamepad outlines,
  written into the private-use slots U+E3E4..U+E3F3 of every other theme
  font. Those slots are force-overwritten (AdobeBlank pre-maps them to
  empty glyphs).
* ``Themes/SPRUCE/nunwen.ttf`` supplies the seven Unicode keyboard symbols
  ``←↑→↓↵⇪✓`` at their own codepoints, only where the target lacks them.

The destination/source pairs live inline in ``PUA_GLYPHS`` below. A versioned
marker in the ``name`` table makes the PUA graft idempotent; bump
``GRAFT_MARKER`` when the map changes and a re-graft is needed.

Usage: patch_theme_fonts.py [theme_dir ...]   (default: every dir in Themes/)
"""
import os
import sys

from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
FONT_EXTS = (".ttf", ".otf")
PER_GLYPH_TABLES = ("hdmx", "LTSH", "DSIG", "HVAR", "VVAR")
GLYPH_INDEXED_TABLES = ("glyf", "loca", "hmtx", "vmtx", "gvar", "post", "CFF ", "VORG")

DONORS = {
    "promptfont": "Resources/fonts/promptfont.ttf",
    "nunwen": "Themes/SPRUCE/nunwen.ttf",
}
DONOR_BASENAMES = {os.path.basename(path).lower() for path in DONORS.values()}

# Symbolic name -> (private-use destination codepoint, promptfont source codepoint).
PUA_GLYPHS = {
    "BTN_A": (0xE3E4, 0x21D3),
    "BTN_B": (0xE3E5, 0x21D2),
    "BTN_X": (0xE3E6, 0x21D0),
    "BTN_Y": (0xE3E7, 0x21D1),
    "DPAD_UP": (0xE3E8, 0x227B),
    "DPAD_DOWN": (0xE3E9, 0x227D),
    "DPAD_LEFT": (0xE3EA, 0x227A),
    "DPAD_RIGHT": (0xE3EB, 0x227C),
    "BTN_START": (0xE3EC, 0x21F8),
    "BTN_SELECT": (0xE3ED, 0x21F7),
    "L1": (0xE3EE, 0x21B0),
    "L2": (0xE3EF, 0x21B2),
    "L3": (0xE3F0, 0x21EF),
    "R1": (0xE3F1, 0x21B1),
    "R2": (0xE3F2, 0x21B3),
    "R3": (0xE3F3, 0x21F0),
}
UNICODE_SYMBOLS = "←↑→↓↵⇪✓"

PROMPTFONT_NOTICE = (
    "PromptFont glyphs Copyright 2018-2026, Yukari Hafner; "
    "based on Xolonium by Severin Meyer (SIL Open Font License 1.1)."
)
MARKER_NAME_ID = 256
GRAFT_MARKER = "PyUI-PUA-graft:1"
NAME_RECORDS = ((3, 1, 0x409), (1, 0, 0))


def load_donors():
    donors = {}
    for key, relpath in DONORS.items():
        font = TTFont(os.path.join(ROOT, relpath))
        donors[key] = (font, font.getBestCmap(), cap_height(font))
    return donors


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


def unique_name(font, codepoint_value):
    existing = set(font.getGlyphOrder())
    name = "uni%04X" % codepoint_value
    n = 1
    while name in existing:
        name = "uni%04X.%d" % (codepoint_value, n)
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


def has_graft_marker(font):
    """True when the font already carries the current PUA graft version."""
    if "name" not in font:
        return False
    return any(
        record.nameID == MARKER_NAME_ID and record.toUnicode() == GRAFT_MARKER
        for record in font["name"].names
    )


def set_graft_marker(font):
    if "name" not in font:
        return
    names = font["name"]
    for platform, encoding, lang in NAME_RECORDS:
        names.setName(GRAFT_MARKER, MARKER_NAME_ID, platform, encoding, lang)


def add_notice(font):
    """Append the PromptFont attribution to nameID 0 only.

    The font's own nameID 13/14 license metadata is deliberately untouched:
    this graft does not relicense the target font.
    """
    if "name" not in font:
        return
    names = font["name"]
    original = names.getDebugName(0) or ""
    if PROMPTFONT_NOTICE in original:
        return
    combined = (original + " " + PROMPTFONT_NOTICE).strip()
    for platform, encoding, lang in NAME_RECORDS:
        names.setName(combined, 0, platform, encoding, lang)


def patch_font(path, donors):
    # Donor fonts are never targets: leave them completely untouched.
    if os.path.basename(path).lower() in DONOR_BASENAMES:
        print(f"skip (donor font): {path}")
        return []

    font = TTFont(path)
    cmap = font.getBestCmap() or {}
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
    donor_glyphs = {key: donor.getGlyphSet() for key, (donor, _, _) in donors.items()}
    order = list(font.getGlyphOrder())

    def scale_for(donor_key):
        donor, _, donor_cap = donors[donor_key]
        if target_cap and donor_cap:
            return target_cap / donor_cap
        return font["head"].unitsPerEm / donor["head"].unitsPerEm

    def add_glyph(donor_key, src, name, scale):
        donor = donors[donor_key][0]
        width = round(donor["hmtx"][src][0] * scale)
        order.append(name)
        font.setGlyphOrder(order)

        def draw(pen, src=src, donor_key=donor_key):
            donor_glyphs[donor_key][src].draw(
                TransformPen(pen, (scale, 0, 0, scale, 0, 0)))

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

    pua_added = []
    if not has_graft_marker(font):
        donor_cmap = donors["promptfont"][1]
        scale = scale_for("promptfont")
        for label, (dest_cp, src_cp) in PUA_GLYPHS.items():
            src = donor_cmap.get(src_cp)
            if src is None:
                print(f"::warning::{label} U+{dest_cp:04X}: donor promptfont lacks U+{src_cp:04X}")
                continue
            name = cff_cid_name(font) if is_cff else None
            name = name or unique_name(font, dest_cp)
            add_glyph("promptfont", src, name, scale)
            # Force the private-use slot even if the font already maps it
            # (AdobeBlank maps every PUA codepoint to an empty glyph).
            for table in subtables:
                table.cmap[dest_cp] = name
            pua_added.append(label)

    symbols_added = []
    donor_cmap = donors["nunwen"][1]
    scale = scale_for("nunwen")
    for symbol in UNICODE_SYMBOLS:
        cp = ord(symbol)
        if cp in cmap:
            continue
        src = donor_cmap.get(cp)
        if src is None:
            print(f"::warning::{symbol} U+{cp:04X}: donor nunwen lacks the codepoint")
            continue
        name = cff_cid_name(font) if is_cff else None
        name = name or unique_name(font, cp)
        add_glyph("nunwen", src, name, scale)
        for table in subtables:
            if table.format == 4 and cp > 0xFFFF:
                continue
            table.cmap[cp] = name
        symbols_added.append(symbol)

    if not pua_added and not symbols_added:
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
    add_notice(font)
    if pua_added:
        set_graft_marker(font)
    font.save(path)
    return pua_added + symbols_added


def main():
    donors = load_donors()
    themes = sys.argv[1:] or [
        os.path.join("Themes", d) for d in sorted(os.listdir(os.path.join(ROOT, "Themes")))
    ]
    for theme in themes:
        theme_dir = os.path.join(ROOT, theme)
        if not os.path.isdir(theme_dir):
            continue
        for dirpath, _, files in os.walk(theme_dir):
            for filename in sorted(files):
                if not filename.lower().endswith(FONT_EXTS):
                    continue
                path = os.path.normpath(os.path.join(dirpath, filename))
                try:
                    added = patch_font(path, donors)
                except Exception as exc:
                    print(f"::warning::{os.path.relpath(path, ROOT)}: {exc}")
                    continue
                if added:
                    print(f"grafted {os.path.relpath(path, ROOT)}: {', '.join(added)}")


if __name__ == "__main__":
    main()
