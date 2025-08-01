# ABOUTME: Installation script for typing pattern analyzer with proper macOS configuration
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="typing-analyzer",
    version="1.0.0",
    author="Braydon Fuller",
    description="Advanced macOS typing pattern analyzer with comprehensive behavioral insights",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "typing-analyzer=src.keylogger:main",
            "typing-analyze=src.analyzer:main",
        ],
    },
    package_data={
        "": ["config.yaml"],
    },
    include_package_data=True,
)