#!/bin/zsh

# Compression script - creates highly compressed archives

if [ $# -eq 0 ]; then
    echo "Usage: ./compress.sh <file_or_directory>"
    echo ""
    echo "This script will create compressed archives using multiple formats:"
    echo "  - .tar.xz (best built-in compression)"
    echo "  - .tar.bz2 (good compression)"
    echo "  - .zip (standard, for compatibility)"
    echo "  - .7z (best compression, if 7z is installed)"
    exit 1
fi

TARGET="$1"
BASENAME=$(basename "$TARGET")

echo "Compressing: $TARGET"
echo ""

# XZ compression (usually best built-in option)
echo "Creating ${BASENAME}.tar.xz..."
tar -cJf "${BASENAME}.tar.xz" "$TARGET"
XZ_SIZE=$(du -h "${BASENAME}.tar.xz" | cut -f1)
echo "✓ XZ size: $XZ_SIZE"
echo ""

# BZ2 compression
echo "Creating ${BASENAME}.tar.bz2..."
tar -cjf "${BASENAME}.tar.bz2" "$TARGET"
BZ2_SIZE=$(du -h "${BASENAME}.tar.bz2" | cut -f1)
echo "✓ BZ2 size: $BZ2_SIZE"
echo ""

# ZIP compression (for compatibility)
echo "Creating ${BASENAME}.zip..."
zip -r -9 "${BASENAME}.zip" "$TARGET" > /dev/null
ZIP_SIZE=$(du -h "${BASENAME}.zip" | cut -f1)
echo "✓ ZIP size: $ZIP_SIZE"
echo ""

# 7z compression (if available)
if command -v 7z &> /dev/null; then
    echo "Creating ${BASENAME}.7z..."
    7z a -t7z -m0=lzma2 -mx=9 "${BASENAME}.7z" "$TARGET" > /dev/null
    SEVENZ_SIZE=$(du -h "${BASENAME}.7z" | cut -f1)
    echo "✓ 7Z size: $SEVENZ_SIZE"
    echo ""
else
    echo "⚠ 7z not installed. To install: brew install p7zip"
    echo ""
fi

echo "Compression complete! Size comparison:"
echo "  ZIP:    $ZIP_SIZE"
echo "  BZ2:    $BZ2_SIZE"
echo "  XZ:     $XZ_SIZE"
if command -v 7z &> /dev/null; then
    echo "  7Z:     $SEVENZ_SIZE (usually smallest)"
fi
