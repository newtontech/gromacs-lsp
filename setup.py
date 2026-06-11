from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f_:
    long_description = f_.read()

requirements_map = {
    "test": "-test"
    }

requirements = {}
for category, fname in requirements_map.items():
    with open(f"requirements{fname}.txt") as fp:
        requirements[category] = fp.read().strip().split("\n")

setup(
    name='gromacs-lsp',
    version="0.0.3",
    author="Jan-Oliver Joswig",
    author_email="jan.joswig@fu-berlin.de",
    description="GROMACS LSP scaffold layered on MDParser topology parsers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/newtontech/gromacs-lsp",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    extras_require={
        "test": requirements["test"],
        },
    python_requires='>=3.9',
    entry_points={
        "console_scripts": [
            "gromacs-lsp=gromacs_lsp.cli:lsp_main",
            "gromacs-lint=gromacs_lsp.cli:lint_main",
            "gromacs-fmt=gromacs_lsp.cli:fmt_main",
            "gromacs-test=gromacs_lsp.cli:test_main",
            "gromacs-lsp-tool=gromacs_lsp.tool:main",
        ],
    },
)
