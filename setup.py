from setuptools import setup, find_packages

setup(
    name="california-housing-mlops",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
        "mlflow>=2.7.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.20.0",
    ],
    author="Your Name",
    description="MLOps pipeline for California Housing price prediction",
    python_requires=">=3.8",
)