#!/bin/bash

# Script to download Tabler UI library files
# Created for MCPoSimpleServer project

# Set the target directory
TARGET_DIR="/mnt/github/getsimpletool/mcpo-simple-server/src/mcpo_simple_server/assets/dist"

# Create the target directory if it doesn't exist
mkdir -p "$TARGET_DIR"
mkdir -p "$TARGET_DIR/js"
mkdir -p "$TARGET_DIR/css"

# Download Tabler CSS files
echo "Downloading Tabler UI library files..."

# Download tabler.min.css
curl -o "$TARGET_DIR/css/tabler.min.css" \
  "https://cdn.jsdelivr.net/npm/@tabler/core@1.3.2/dist/css/tabler.min.css"

# Download tabler-flags.min.css
curl -o "$TARGET_DIR/css/tabler-flags.min.css" \
  "https://cdn.jsdelivr.net/npm/@tabler/core@1.3.2/dist/css/tabler-flags.min.css"

# Download tabler-payments.min.css
curl -o "$TARGET_DIR/css/tabler-payments.min.css" \
  "https://cdn.jsdelivr.net/npm/@tabler/core@1.3.2/dist/css/tabler-payments.min.css"

# Download tabler-vendors.min.css
curl -o "$TARGET_DIR/css/tabler-vendors.min.css" \
  "https://cdn.jsdelivr.net/npm/@tabler/core@1.3.2/dist/css/tabler-vendors.min.css"

echo "Download complete. Files saved to $TARGET_DIR"
