import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="readingdb",
    version="0.0.1",
    author="lewington",
    author_email="lewingtonpitsos@gmail.com",
    description="Backend and database interface for Frontline Data Systems' Magpeye app",
    long_description=long_description,
    url="https://github.com/Lewington-pitsos/readingdb",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "boto3",
        "tqdm",
        "moto",
        "botocore",
    ]
)