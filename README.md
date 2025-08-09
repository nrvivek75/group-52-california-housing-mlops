# California Housing MLOps Pipeline

A complete MLOps pipeline for predicting California housing prices using machine learning.

## Project Structure
- `data/`: Raw and processed data
- `src/`: Source code for data processing and modeling
- `notebooks/`: Jupyter notebooks for exploration
- `tests/`: Unit tests
- `configs/`: Configuration files
- `scripts/`: Utility scripts

## Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Download data: `python scripts/download_data.py`
4. Preprocess data: `python -m src.data.preprocessing`

## DVC Commands
- `dvc pull`: Download data from remote storage
- `dvc push`: Upload data to remote storage
- `dvc repro`: Reproduce the entire pipeline