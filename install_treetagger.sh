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
wget http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tree-tagger-linux-3.2.1.tar.gz
wget http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tagger-scripts.tar.gz
wget http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/install-tagger.sh
wget http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/english-par-linux-3.2-utf8.bin.gz
wget http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/english-chunker-par-linux-3.2-utf8.bin.gz

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
