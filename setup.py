import setuptools


setuptools.setup(
    name="pytagged",
    version="0.0.1",
    author="1Karus",
    description="cli utility to help you comment out tagged python code",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
