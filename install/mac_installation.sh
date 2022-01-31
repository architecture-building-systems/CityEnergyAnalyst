if ! command -v brew &> /dev/null; then
    echo "brew is not installed. Make sure to install brew on your Mac before running this script." >&2 ; exit 1
fi

if ! command -v git &> /dev/null; then
    echo "git is not installed. Make sure Xcode command line tools is installed on your Mac." >&2 ; exit 1
fi

ARCH="$(uname -m)"
CEA_ENV_NAME="cea"
# TMPDIR="$(mktemp -d)"
# trap 'rm -rf -- "$TMPDIR"' EXIT

# Clone CEA
git clone https://github.com/architecture-building-systems/CityEnergyAnalyst
# Install conda if does not exist
if ! command -v conda &> /dev/null; then
    # Using miniforge here (could also use any conda-like e.g. miniconda)
    brew install miniforge
fi
# Install mamba
conda install mamba -n base -c conda-forge -y
eval "$(command conda 'shell.bash' 'hook' 2> /dev/null)"
# Install environment
CONDA_SUBDIR=osx-64 mamba env update --name $CEA_ENV_NAME --file ./CityEnergyAnalyst/environment.yml --prune
# Install CEA
conda activate $CEA_ENV_NAME
pip install -e ./CityEnergyAnalyst

# Install yarn if does not exist
if ! command -v yarn &> /dev/null; then
    brew install yarn
fi

# Clone CEA GUI
git clone https://github.com/architecture-building-systems/CityEnergyAnalyst-GUI
# Download deps
yarn --cwd ./CityEnergyAnalyst-GUI --cache-folder ./cache
# Compile GUI
yarn --cwd ./CityEnergyAnalyst-GUI package

mv ./CityEnergyAnalyst-GUI/out/CityEnergyAnalyst-GUI-darwin-$ARCH/CityEnergyAnalyst-GUI.app ./CityEnergyAnalyst-GUI.app

# Clean up
rm -rf ./CityEnergyAnalyst-GUI
