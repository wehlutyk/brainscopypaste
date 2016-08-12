#!/bin/bash
set -e

# Start postgres and run command.
sudo service postgresql start
cd /home/brainscopypaste
brainscopypaste "$@"
