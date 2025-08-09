import yaml
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

def load_config(config_path: str = "configs/config.yaml") -> Dict[Any, Any]:
    """Load configuration from YAML file"""
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            logger.warning(f"Config file {config_path} not found, using default config")
            return get_default_config()
        
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        logger.info(f"Configuration loaded from {config_path}")
        return config
    
    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {str(e)}")
        logger.info("Using default configuration")
        return get_default_config()

def get_default_config() -> Dict[Any, Any]:
    """Get default configuration if config file is not available"""
    return {
        'data': {
            'raw_data_path': 'data/raw/california_housing.csv',
            'processed_data_path': 'data/processed/',
            'test_size': 0.2,
            'random_state': 42
        },
        'mlflow': {
            'experiment_name': 'california_housing_experiment',
            'tracking_uri': 'file:./mlruns',
            'registered_model_name': 'california_housing_best_model'
        },
        'training': {
            'cv_folds': 5,
            'scoring': 'neg_mean_squared_error'
        },
        'logging': {
            'level': 'INFO',
            'log_file': 'logs/training.log'
        }
    }

def get_data_paths(config: Dict[Any, Any]) -> Dict[str, Path]:
    """Get data paths from configuration"""
    return {
        'raw': Path(config['data']['raw_data_path']),
        'processed': Path(config['data']['processed_data_path'])
    }