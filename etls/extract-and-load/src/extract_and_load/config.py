"""
Configuration module for Brazilian Police Criminal Data ETL CLI.
"""

import configparser
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class DatabaseConfig(BaseModel):
    """Single database configuration for Brazilian police criminal data."""
    
    host: str = "localhost"
    port: int = 5432
    database: str = "../../data/bronze.db"
    username: str = ""
    password: str = ""
    driver: str = "sqlite"


class LoggingConfig(BaseModel):
    """Logging configuration."""
    
    level: str = "INFO"


class Config:
    """Main configuration class for Brazilian police criminal data ETL."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration."""
        self.database = DatabaseConfig()
        self.logging = LoggingConfig()
        
        # Load from config file if provided or found
        config_file = self._find_config_file(config_path)
        if config_file and config_file.exists():
            self._load_from_file(config_file)
    
    def _find_config_file(self, config_path: Optional[Path]) -> Optional[Path]:
        """Find configuration file."""
        if config_path:
            return config_path
            
        # Look for config file in common locations
        possible_paths = [
            Path.cwd() / "config.ini",
            Path.cwd() / "config.cfg",
            Path.home() / ".config.ini",
            Path.home() / ".config.cfg",
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    def _load_from_file(self, config_path: Path) -> None:
        """Load configuration from INI file."""
        config = configparser.ConfigParser()
        config.read(config_path)
        
        # Load database configuration
        if config.has_section('database'):
            db_section = config['database']
            self.database = DatabaseConfig(
                host=db_section.get('host', self.database.host),
                port=db_section.getint('port', self.database.port),
                database=db_section.get('database', self.database.database),
                username=db_section.get('username', self.database.username),
                password=db_section.get('password', self.database.password),
                driver=db_section.get('driver', self.database.driver),
            )
        
        # Load logging configuration
        if config.has_section('logging'):
            log_section = config['logging']
            self.logging = LoggingConfig(
                level=log_section.get('level', self.logging.level),
            )
    
    def get_database_url(self) -> str:
        """Get database connection URL."""
        db = self.database
        
        if db.driver == "sqlite":
            return f"sqlite:///{db.database}"
        elif db.driver == "postgresql":
            return f"postgresql://{db.username}:{db.password}@{db.host}:{db.port}/{db.database}"
        elif db.driver == "mysql":
            return f"mysql://{db.username}:{db.password}@{db.host}:{db.port}/{db.database}"
        else:
            raise ValueError(f"Unsupported database driver: {db.driver}")
