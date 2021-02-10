from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f_:
    long_description = f_.read()

setup(
    name='mdparser',
    version="0.0.1",
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
    python_requires='>=3.6'
)
