#!/usr/bin/env bash
set -e

# Prepare folders
echo
echo "[BrainsCopyPaste installer] Preparing folders..."
echo
mkdir -p treetagger
cd treetagger

# Download necessary zips
echo "[BrainsCopyPaste installer] Downloading executables and parameter files..."
echo
wget ftp://ftp.ims.uni-stuttgart.de/pub/corpora/tree-tagger-linux-3.2.tar.gz
wget ftp://ftp.ims.uni-stuttgart.de/pub/corpora/tagger-scripts.tar.gz
wget ftp://ftp.ims.uni-stuttgart.de/pub/corpora/install-tagger.sh
wget ftp://ftp.ims.uni-stuttgart.de/pub/corpora/english-par-linux-3.2.bin.gz
wget ftp://ftp.ims.uni-stuttgart.de/pub/corpora/english-chunker-par-linux-3.2.bin.gz

# Run the installer
echo "[BrainsCopyPaste installer] Installing files..."
echo
chmod +x install-tagger.sh
./install-tagger.sh

# Warn about the warning that `install-tagger.sh` will give
echo
echo "[BrainsCopyPaste installer] There is no need to add environment variables as"
echo "                            suggested in the message above! These are added"
echo "                            automatically in the brainscopypaste python scripts."
