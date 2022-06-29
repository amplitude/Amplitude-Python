import sys
from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
sys.path.insert(0, str(here / 'src'))

from amplitude.constants import SDK_VERSION

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="amplitude-analytics",
    version=SDK_VERSION,
    description="The official Amplitude backend Python SDK for server-side instrumentation.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/amplitude/Amplitude-Python",  # Optional
    author="Amplitude Inc.",
    author_email="sdk.dev@amplitude.com",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        # Indicate who your project is intended for
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    keywords="amplitude, python, backend",
    package_dir={"": "src"},
    packages=["amplitude"],
    python_requires=">=3.6, <4",
    license='MIT License',
    project_urls={
        "Bug Reports": "https://github.com/amplitude/Amplitude-Python/issues",
        "Source": "https://github.com/amplitude/Amplitude-Python",
        "Developer Doc": "https://developers.amplitude.com/docs/python-beta"
    },
)
