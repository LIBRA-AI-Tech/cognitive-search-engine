#!/usr/bin/env python

from gettext import install
from posixpath import dirname
import setuptools
from importlib.machinery import SourceFileLoader
import os

with open("README.md", "r") as fh:
    long_description = fh.read()

dirname = os.path.dirname(__file__)
path_version = os.path.join(dirname, "geoss_search", "_version.py")
version = SourceFileLoader('version', path_version).load_module()

setuptools.setup(
    name="geoss_search",
    version=version.__version__,
    description="GEOSS full text search using ElasticSearch dense vectors",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://dev.azure.com/LibraAI/eiffel/_git/Infrastructure",
    packages=['geoss_search'],
    install_requires=[
        "tzlocal>=2.1,<2.2",
        "torch>=1.11.0,<1.12.0",
        "sentence_transformers>=2.2.0,<2.3.0",
        "numpy>=1.19.0,<1.23.0",
        "requests>=2.27.1,<2.28.0",
        "elasticsearch[async]>=8.1.0,<8.2.0",
        "fastapi>=0.75.0,<0.76.0",
        "uvicorn[standard]>=0.17.6,<0.18.0",
        "pydantic>=1.9.0,<1.9.1",
    ],
    package_data={'geoss_search': ['logging.conf']},
    python_requires='>=3.7',
    entry_points = {
        'console_scripts': ['geoss_search=geoss_search.cli:cli'],
    },
    zip_safe=False,
)
