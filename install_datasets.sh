#!/usr/bin/env bash
set -e

# Find python3 command
if which python3; then
  PYTHON=python3
else
  PYTHON=python
fi

# Download NLTK data
echo
echo "[BrainsCopyPaste installer] Installing WordNet and CMU data..."
$PYTHON -m nltk.downloader cmudict wordnet wordnet_ic

# Download Free Association Norms
echo
echo "[BrainsCopyPaste installer] Installing Free Association Norms data..."
echo
mkdir -p data/FreeAssociation
cd data/FreeAssociation
if [ ! -e "Cue_Target_Pairs.A-B" ]; then
  wget http://w3.usf.edu/FreeAssociation/AppendixA/Cue_Target_Pairs.A-B
fi
if [ ! -e "Cue_Target_Pairs.C" ]; then
  wget http://w3.usf.edu/FreeAssociation/AppendixA/Cue_Target_Pairs.C
fi
if [ ! -e "Cue_Target_Pairs.D-F" ]; then
  wget http://w3.usf.edu/FreeAssociation/AppendixA/Cue_Target_Pairs.D-F
fi
if [ ! -e "Cue_Target_Pairs.G-K" ]; then
  wget http://w3.usf.edu/FreeAssociation/AppendixA/Cue_Target_Pairs.G-K
fi
if [ ! -e "Cue_Target_Pairs.L-O" ]; then
  wget http://w3.usf.edu/FreeAssociation/AppendixA/Cue_Target_Pairs.L-O
fi
if [ ! -e "Cue_Target_Pairs.P-R" ]; then
  wget http://w3.usf.edu/FreeAssociation/AppendixA/Cue_Target_Pairs.P-R
fi
if [ ! -e "Cue_Target_Pairs.S" ]; then
  wget http://w3.usf.edu/FreeAssociation/AppendixA/Cue_Target_Pairs.S
fi
if [ ! -e "Cue_Target_Pairs.T-Z" ]; then
  wget http://w3.usf.edu/FreeAssociation/AppendixA/Cue_Target_Pairs.T-Z
fi
cd ../..

# Copy Phonological Neighborhood Density data
echo
echo "[BrainsCopyPaste installer] Installing Phonological Neighborhood Density data..."
echo
mkdir -p data/clearpond
cd data/clearpond
if [ ! -e "englishCPdatabase2.txt" ]; then
  wget http://clearpond.northwestern.edu/englishCPdatabase2.zip
  unzip englishCPdatabase2.zip
  rm englishCPdatabase2.zip
fi
cd ../..

# Download MemeTracker data
echo
echo "[BrainsCopyPaste installer] Installing MemeTracker dataset..."
echo
mkdir -p data/MemeTracker
cd data/MemeTracker
if [ ! -e "clust-qt08080902w3mfq5.txt" ]; then
  wget http://snap.stanford.edu/data/d/quotes/Old-UniqUrls/clust-qt08080902w3mfq5.txt.gz
  gunzip clust-qt08080902w3mfq5.txt.gz
fi
cd ../..
