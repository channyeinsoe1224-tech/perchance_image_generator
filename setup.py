from setuptools import setup, find_packages

setup(
    name="perchance-image-generator",
    version="1.0.0",
    description="An Object-Oriented Python library for Perchance AI Text-to-Image Generator",
    author="Antigravity",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "playwright>=1.40.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
