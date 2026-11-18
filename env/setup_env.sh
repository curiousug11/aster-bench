#!/usr/bin/env bash
# Build the shared science environment for ASTER-Bench (about 1.9 GB of line lists).
# Usage: env/setup_env.sh /path/to/aster-bench-env
set -euo pipefail
E="${1:?usage: setup_env.sh TARGET_DIR}"
ASTER_COMMIT=31be77f          # ASTER version under test; change deliberately and record it with results

mkdir -p "$E/linelists/xsec" "$E/linelists/cia" "$E/dl"

python3 -m venv "$E/venv"
"$E/venv/bin/pip" install -q taurex pyfastchem nestle matplotlib spectres pyyaml astropy pandas requests \
    tqdm corner h5py numpy
"$E/venv/bin/pip" install -q orchestral-ai mcp python-dotenv     # only needed by the MCP condition

git clone -q https://github.com/emipanek/aster "$E/aster"
git -C "$E/aster" checkout -q "$ASTER_COMMIT"

# FastChem data outside the ASTER clone, so the bare condition is never pointed at ASTER's code
cp -r "$E/aster/fastchem_input" "$E/fastchem_input"

# ExoMol R=15000 cross-sections (Zenodo copies of the files ASTER's download_linelists.py fetches;
# CH4 is the newer YT34to10 list). NH3 and HCN are deliberately absent: t6_missing_linelist relies on it.
cd "$E/linelists/xsec"
for f in 5722861/files/1H2-16O__POKAZATEL__R15000_0.3-50mu.xsec.TauREx.h5 \
         5716786/files/12C-16O2__UCL-4000.R15000_0.3-50mu.xsec.TauREx.h5 \
         5716864/files/12C-1H4__YT34to10.R15000_0.3-50mu.xsec.TauREx.h5 \
         5716770/files/C-O-NatAbund__Li2015.R15000_0.3-50mu.xsec.TauREx.h5; do
    curl -sS -L --retry 4 -o "$(basename "$f")" "https://zenodo.org/api/records/$f/content" &
done
wait

# HITRAN CIA (H2-H2, H2-He) from the TauREx reference bundle
curl -sS -L --retry 4 -o "$E/dl/cia.zip" "https://zenodo.org/api/records/15495830/files/2025_CIA_HITRAN.zip/content"
unzip -q -o -j "$E/dl/cia.zip" 2025_CIA_HITRAN/H2-H2.cia 2025_CIA_HITRAN/H2-He.cia -d "$E/linelists/cia"
rm -r "$E/dl"

# The ASTER skill finds line lists at $ASTER_HOME/workspace/linelists
mkdir -p "$E/aster/workspace"
ln -sfn "$E/linelists" "$E/aster/workspace/linelists"

echo "Done. Put these paths in bench.yaml:"
echo "python: $E/venv/bin/python"
echo "aster_home: $E/aster"
echo "linelists: $E/linelists"
echo "fastchem_input: $E/fastchem_input"
