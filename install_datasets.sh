#!/usr/bin/env bash

# Download NLTK data
echo
echo "[WebQuotes installer] Installing WordNet and CMU data..."
echo
mkdir -p usr/share
python -m nltk.downloader -d usr/share/nltk_data cmudict wordnet wordnet_ic

# Download Free Association Norms
echo
echo "[WebQuotes installer] Installing Free Association Norms data..."
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
echo "[WebQuotes installer] Installing Age-of-Acquisition Norms data..."
echo
#This is already present in the repository (since it needs conversion from xlsx to csv)

# Download MemeTracker data
echo
echo "[WebQuotes installer] Installing MemeTracker dataset..."
echo
mkdir -p data/MemeTracker
cd data/MemeTracker
wget http://snap.stanford.edu/data/d/quotes/Old-UniqUrls/clust-qt08080902w3mfq5.txt.gz
gunzip clust-qt08080902w3mfq5.txt.gz
