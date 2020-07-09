import setuptools

from loio_metrics import version

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="loio_metrics",
    version=version(),
    author="Serge Sotnyk, Phase One: Karma",
    author_email="s.sotnyk@p1k.org",
    description="Metrics calculator for the Loio project.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/s.sotnyk/loio_metrics",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    python_requires='>=3.6',
    extras_require={
        ':python_version == "3.6"': [
            'dataclasses>=0.7',
        ],
    },
)
