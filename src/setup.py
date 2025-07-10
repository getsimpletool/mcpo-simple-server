#!/usr/bin/env python
from setuptools import setup
import os

def read_requirements():
    """Read the requirements.txt file and return a list of requirements."""
    req_path = os.path.join('mcpo_simple_server', 'requirements.txt')
    with open(req_path) as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

# This file is maintained for compatibility with older packaging tools
# The actual configuration is in pyproject.toml, except for dependencies
# which are read from mcpo_simple_server/requirements.txt
setup(
    install_requires=read_requirements()
)
