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
    name='mdparser',
    version="0.0.3",
    author="Jan-Oliver Joswig",
    author_email="jan.joswig@fu-berlin.de",
    description="Parsers for Molecular Dynamics related file types",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/janjoswig/MDParser",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    extras_require={
        "test": requirements["test"],
        },
    python_requires='>=3.6'
)
