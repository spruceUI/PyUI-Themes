#!/bin/sh

REF="SPRUCE"
OUT="theme_comparison_report.txt"

# Ensure SPRUCE exists
if [ ! -d "$REF" ]; then
    echo "Error: Reference theme '$REF' not found."
    exit 1
fi

echo "Building normalized (extension-agnostic) file list for $REF ..."

# Normalize a list: strip leading folder, strip extension
normalize() {
    sed "s|^$1/||" | sed 's|\.[^.]*$||' | sort -u
}

# Reference file list
find "$REF" -type f | normalize "$REF" > .ref_files

# Begin output
{
    echo "Theme Comparison Report — EXTENSION-AGNOSTIC"
    echo "Reference theme: $REF"
    echo "Generated: $(date)"
    echo "====================================================="
    echo
} > "$OUT"

# Loop through themes
for theme in */ ; do
    theme="${theme%/}"

    # Skip reference
    [ "$theme" = "$REF" ] && continue

    echo "Comparing $theme ..."

    # Build normalized list for theme
    find "$theme" -type f | normalize "$theme" > ".${theme}_files"

    {
        echo
        echo "-----------------------------------------------------"
        echo "Theme: $theme"
        echo "-----------------------------------------------------"
        echo
        echo "Files present in $theme but NOT in $REF (ignoring extensions):"
        echo "-----------------------------------------------------"
        comm -23 ".${theme}_files" .ref_files || true
        echo
        echo "Files present in $REF but NOT in $theme (ignoring extensions):"
        echo "-----------------------------------------------------"
        comm -13 ".${theme}_files" .ref_files || true
        echo
    } >> "$OUT"
done

echo "Cleaning up temp files."
rm -f ./.*_files

echo "Done. See $OUT"
