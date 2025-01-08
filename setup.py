
from setuptools import setup, find_packages
from setuptools.command.install import install

with open("README.md", "r") as readme:
    long_description = readme.read()

setup(
    name="MdXLogseqTODOSync",
    version="0.0.19",
    description="Script to always sync a Logseq TODO list with a markdown file",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/thiswillbeyourgithub/MdXLogseqTODOSync",
    packages=find_packages(),

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    license="GPLv3",
    keywords=["logseq", "todo", "list", "markdown", "md", "organization", "productivity"],
    python_requires=">=3.11",

    entry_points={
        'console_scripts': [
            'MdXLogseqTODOSync=MdXLogseqTODOSync.__init__:cli_launcher',
        ],
    },

    install_requires=[
        'fire >= 0.6.0',
        'beartype >= 0.18.5',
        "LogseqMarkdownParser >= 3.3"
    ],
)
