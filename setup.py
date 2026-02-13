"""
Setup configuration for Shelley Bio package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text() if (this_directory / "README.md").exists() else ""

setup(
    name="shelley-bio",
    version="1.0.0",
    author="BioCommons",
    author_email="", 
    description="A powerful bioinformatics tool finder and module builder for CVMFS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/shelley-bio/shelley-bio",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "mcp>=1.0.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio",
            "black",
            "flake8",
            "mypy",
        ],
    },
    entry_points={
        "console_scripts": [
            "shelley-bio=shelley_bio.client.cli:main",
            "shelley-bio-batch=shelley_bio.scripts.batch_builder:main",
        ],
    },
    scripts=[
        "bin/shelley-bio",
        "bin/shelley-bio-batch",
    ],
    package_data={
        "shelley_bio": [
            "*.yaml",
            "*.json.gz",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)