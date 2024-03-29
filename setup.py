#!/usr/bin/env python

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
    packages=setuptools.find_packages(),
    install_requires=[
        "tzlocal>=2.1,<2.2",
        "torch>=1.11.0,<1.12.0",
        "sentence_transformers>=2.2.0,<2.3.0",
        "numpy>=1.19.0,<1.23.0",
        "requests>=2.27.1,<2.28.0",
        "elasticsearch[async]>=8.4.0,<8.5.0",
        "fastapi>=0.89.0,<0.90.0",
        "uvicorn[standard]>=0.17.6,<0.18.0",
        "pydantic>=1.10.0,<1.11.0",
        "pandas>=1.4.3,<1.5.0",
        "pyarrow>=11.0.0,<12.0.0",
        "pygeos>=0.13,<0.14",
        "redisai>=1.2.2,<1.3.0",
        "celery[redis]>=5.2.7,<5.3.0",
        "typing-extensions>=4.4.0,<=4.5.0",
        "aiohttp>=3.8.4,<3.9.0",
        "beautifulsoup4>=4.12.2,<4.13.0",
        "lxml>=4.9.3,<4.10",
        "clean-text>=0.6.0,<0.7.0",
    ],
    package_data={'geoss_search': ['logging.conf']},
    python_requires='>=3.7',
    entry_points = {
        'console_scripts': ['geoss_search=geoss_search.cli:cli'],
    },
    zip_safe=False,
)
