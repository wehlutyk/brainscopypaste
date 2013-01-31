#!/usr/bin/env bash

# Download NLTK data
echo
echo "[WebQuotes installer] Installing WordNet and CMU data ..."
echo
mkdir -p usr/share
python -m nltk.downloader -d usr/share/nltk_data cmudict wordnet wordnet_ic
