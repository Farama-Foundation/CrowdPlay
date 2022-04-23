"""A setuptools based setup module.

See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
"""

import pathlib

# Always prefer setuptools over distutils
from setuptools import find_packages, setup

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8")

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(
    name="crowdplay_datasets",  # Required
    version="0.1.0",  # Required
    description="A collection of crowdsourced human demonstration datasets for offline learning",  # Optional
    long_description=long_description,  # Optional
    long_description_content_type="text/markdown",  # Optional (see note above)
    url="https://github.com/mgerstgrasser/crowdplay",
    author="Matthias Gerstgrasser",  # Optional
    author_email="matthias@seas.harvard.edu",  # Optional
    # For a list of valid classifiers, see https://pypi.org/classifiers/
    classifiers=[  # Optional
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    # keywords='sample, setuptools, development',  # Optional
    # When your source code is in a subdirectory under the project root, e.g.
    # `src/`, it is necessary to specify the `package_dir` argument.
    # package_dir={'': 'src'},  # Optional
    packages=find_packages(where="crowdplay_datasets"),
    python_requires=">=3.7, <4",
    install_requires=[
        "SQLAlchemy>=1.3.20",
        "gym>=0.23.1",
        "opencv-python>=4.4.0.46",
    ],
    # entry_points={  # Optional
    #     'console_scripts': [
    #         'sample=sample:main',
    #     ],
    # },
    project_urls={  # Optional
        "Documentation": "https://mgerstgrasser.github.io/crowdplay/",
        "Paper": "https://openreview.net/pdf?id=qyTBxTztIpQ",
        "Bug Reports": "https://github.com/mgerstgrasser/crowdplay/issues",
        "Source": "https://github.com/mgerstgrasser/crowdplay",
    },
)
