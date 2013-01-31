#!/usr/bin/env bash

# Download NLTK data
echo "Installing WordNet and CMU data ..."
mkdir -p usr/share
python -m nltk.downloader -d usr/share/nltk_data cmudict wordnet wordnet_ic
