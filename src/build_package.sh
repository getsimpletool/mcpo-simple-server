#!/usr/bin/env bash
# Script to test and build the mcpo-simple-server package

set -euo pipefail  # Exit on error, undefined vars fail, pipefail

# Source environment variables if file exists
ENV_FILE="$(dirname "$0")/build.env"
if [ -f "$ENV_FILE" ]; then
  echo "=== Loading environment variables from $ENV_FILE ==="
  # shellcheck source=/dev/null
  source "$ENV_FILE"
fi

echo "=== Testing package imports ===="
cd "$(dirname "$0")"
# Uncomment when you have tests
# python tests/test_imports.py

echo "=== Cleaning previous builds ==="
rm -rf build/ dist/ *.egg-info/

echo "=== Building package ==="
python -m pip install --upgrade pip
python -m pip install build twine
python -m build

echo "=== Package build complete ===="
echo "Distribution files:"
ls -l dist/
echo ""

echo "=== ======================= ==="
echo "To install locally for testing:"
echo "pip install dist/*.whl"
echo ""
echo "To publish to TestPyPI:"
echo "python -m twine upload --repository testpypi dist/*"
echo ""
echo "To publish to PyPI:"
echo "python -m twine upload dist/*"

echo "=== WE ARE DONE! WHAT NEXT? ==="

# Check if LOCAL_INSTALL is defined in environment, otherwise ask user
if [ -n "${LOCAL_INSTALL+x}" ]; then
  # Variable is defined, use its value
  if [ "$LOCAL_INSTALL" = true ]; then
    install_locally="y"
    echo "=== Environment variable LOCAL_INSTALL=true, installing locally ==="
  else
    install_locally="n"
    echo "=== Environment variable LOCAL_INSTALL=false, skipping local install ==="
  fi
else
  # Variable is not defined, ask user
  read -r -p "Install mcpo-simple-server locally for testing? [y/N]: " install_locally
fi

case "$install_locally" in
  [Yy]*)
    echo "Removing any existing mcpo-simple-server package..."
    pip uninstall -y mcpo-simple-server || true
    echo "Installing mcpo-simple-server package locally..."
    pip install --force-reinstall dist/*.whl
    pip show mcpo-simple-server
    ;;
  *) ;;
esac

# Check if TESTPYPI is defined in environment, otherwise ask user
if [ -n "${TESTPYPI+x}" ]; then
  # Variable is defined, use its value
  if [ "$TESTPYPI" = true ]; then
    publish_test="y"
    echo "=== Environment variable TESTPYPI=true, publishing to TestPyPI ==="
  else
    publish_test="n"
    echo "=== Environment variable TESTPYPI=false, skipping TestPyPI publish ==="
  fi
else
  # Variable is not defined, ask user
  read -r -p "Publish to TestPyPI? [y/N]: " publish_test
fi

case "$publish_test" in
  [Yy]*)
    echo "Publishing mcpo-simple-server package to TestPyPI..."
    # Set Twine credentials if API key is provided in environment
    if [ -z "${TWINE_USERNAME:-}" ] || [ -z "${TWINE_PASSWORD:-}" ]; then
      echo "Error: TWINE_USERNAME and TWINE_PASSWORD must be set for TestPyPI publishing"
      echo "Please set these variables in your environment or build.env file"
      exit 1
    fi
    python -m twine upload --repository testpypi dist/*
    ;;
  *) ;;
esac

# Check if PUBLISHPYPI is defined in environment, otherwise ask user
if [ -n "${PUBLISHPYPI+x}" ]; then
  # Variable is defined, use its value
  if [ "$PUBLISHPYPI" = true ]; then
    publish_pypi="y"
    echo "=== Environment variable PUBLISHPYPI=true, publishing to PyPI ==="
  else
    publish_pypi="n"
    echo "=== Environment variable PUBLISHPYPI=false, skipping PyPI publish ==="
  fi
else
  # Variable is not defined, ask user
  read -r -p "Publish to PyPI? [y/N]: " publish_pypi
fi

case "$publish_pypi" in
  [Yy]*)
    echo "Publishing mcpo-simple-server package to PyPI..."
    # Set Twine credentials if API key is provided in environment
    if [ -z "${TWINE_USERNAME:-}" ] || [ -z "${TWINE_PASSWORD:-}" ]; then
      echo "Error: TWINE_USERNAME and TWINE_PASSWORD must be set for TestPyPI publishing"
      echo "Please set these variables in your environment or build.env file"
      exit 1
    fi
    python -m twine upload dist/*
    ;;
  *) ;;
esac

echo "Build script completed."
