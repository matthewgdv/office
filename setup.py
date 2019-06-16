from setuptools import setup, find_packages
from os import path

__version__ = "0.0.1"

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="office",
    version=__version__,
    description="[short_project_description]",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/matthewgdv/office",
    license="MIT",
    classifiers=[
      "Development Status :: 3 - Alpha",
      "Intended Audience :: Developers",
      "Programming Language :: Python :: 3.7",
    ],
    packages=find_packages(exclude=["tests*"]),
    install_requires=[

    ],
    author="Matt GdV",
    author_email="matthewgdv@gmail.com"
)
