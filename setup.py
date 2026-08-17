from setuptools import setup, find_packages

setup(
    name="perchance-image-generator",
    version="2.0.0",
    description="An Object-Oriented Python library for Perchance AI Text-to-Image Generator",
    author="Antigravity",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "playwright>=1.40.0",
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.23.0",
        "pydantic>=2.0.0",
        "websockets>=11.0.0",
        "python-multipart>=0.0.6",
        "httpx>=0.25.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
