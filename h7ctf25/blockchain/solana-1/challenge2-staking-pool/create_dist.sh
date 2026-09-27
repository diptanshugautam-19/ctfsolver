#!/bin/bash

# H7CTF 2025 - Staking Pool Challenge Distribution Package Creator
# This script creates a clean distribution package for players

CHALLENGE_NAME="h7ctf-2025-staking-pool"
DIST_DIR="dist"
OUTPUT_DIR="releases"

echo "[*] Creating distribution package for Staking Pool challenge..."

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Create temporary build directory
TEMP_DIR=$(mktemp -d)
PACKAGE_DIR="$TEMP_DIR/$CHALLENGE_NAME"
mkdir -p "$PACKAGE_DIR/src"

echo "[+] Copying source files..."

# Copy clean source files
cp "$DIST_DIR/Cargo.toml" "$PACKAGE_DIR/"
cp "$DIST_DIR/README.md" "$PACKAGE_DIR/"
cp "$DIST_DIR/lib.rs" "$PACKAGE_DIR/src/"
cp "$DIST_DIR/entrypoint.rs" "$PACKAGE_DIR/src/"

# Create src/lib.rs that includes the processor module
cat > "$PACKAGE_DIR/src/lib.rs" << 'EOF'
mod entrypoint;
mod processor;

pub use processor::*;
EOF

# Rename processor file
mv "$PACKAGE_DIR/src/lib.rs" "$PACKAGE_DIR/src/temp.rs"
mv "$PACKAGE_DIR/src/entrypoint.rs" "$PACKAGE_DIR/src/lib.rs"
cat > "$PACKAGE_DIR/src/processor.rs" < "$DIST_DIR/lib.rs"

echo "[+] Creating archive..."

# Create tarball
cd "$TEMP_DIR"
tar -czf "$CHALLENGE_NAME.tar.gz" "$CHALLENGE_NAME/"

# Move to output directory
mv "$CHALLENGE_NAME.tar.gz" "$(dirname "$TEMP_DIR")/$OUTPUT_DIR/"

# Cleanup
rm -rf "$TEMP_DIR"

echo "[✓] Distribution package created: $OUTPUT_DIR/$CHALLENGE_NAME.tar.gz"
echo ""
echo "Players can extract and build with:"
echo "  tar -xzf $CHALLENGE_NAME.tar.gz"
echo "  cd $CHALLENGE_NAME"
echo "  cargo build-sbf"
