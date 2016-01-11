#!/usr/bin/env bash
set -e

# Download NLTK data
echo
echo "[BrainsCopyPaste installer] Installing WordNet and CMU data..."
python -m nltk.downloader cmudict wordnet wordnet_ic crubadan

# Download Free Association Norms
echo
echo "[BrainsCopyPaste installer] Installing Free Association Norms data..."
echo
mkdir -p data/FreeAssociation
cd data/FreeAssociation
wget http://w3.usf.edu/FreeAssociation/AppendixA/Cue_Target_Pairs.A-B
wget http://w3.usf.edu/FreeAssociation/AppendixA/Cue_Target_Pairs.C
wget http://w3.usf.edu/FreeAssociation/AppendixA/Cue_Target_Pairs.D-F
wget http://w3.usf.edu/FreeAssociation/AppendixA/Cue_Target_Pairs.G-K
wget http://w3.usf.edu/FreeAssociation/AppendixA/Cue_Target_Pairs.L-O
wget http://w3.usf.edu/FreeAssociation/AppendixA/Cue_Target_Pairs.P-R
wget http://w3.usf.edu/FreeAssociation/AppendixA/Cue_Target_Pairs.S
wget http://w3.usf.edu/FreeAssociation/AppendixA/Cue_Target_Pairs.T-Z
cd ../..

# Copy Age-of-Acquisition Norms
echo
echo "[BrainsCopyPaste installer] Installing Age-of-Acquisition Norms data..."
echo
#This is already present in the repository (since it needs conversion from xlsx to csv)

# Download MemeTracker data
echo
echo "[BrainsCopyPaste installer] Installing MemeTracker dataset..."
echo
mkdir -p data/MemeTracker
cd data/MemeTracker
wget http://snap.stanford.edu/data/d/quotes/Old-UniqUrls/clust-qt08080902w3mfq5.txt.gz
gunzip clust-qt08080902w3mfq5.txt.gz
