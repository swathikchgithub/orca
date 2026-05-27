from setuptools import setup, find_packages

setup(
    name="orca",
    version="1.0.0",
    packages=find_packages(exclude=["tests*", "data*"]),
    py_modules=["config"],
)
