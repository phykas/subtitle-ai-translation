import yaml
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv


@dataclass
class OpenAIConfig:
    model: str
    max_tokens: int
    temperature: float
    context_buffer: int


@dataclass
class ChunkingConfig:
    max_chunk_size: int
    overlap_lines: int


@dataclass
class AppConfig:
    openai: OpenAIConfig
    chunking: ChunkingConfig


class ConfigManager:
    def __init__(self, config_path: str = "config.yaml"):
        load_dotenv()
        self.config_path = Path(config_path)
        self._config = None
    
    def load_config(self) -> AppConfig:
        if self._config is None:
            self._config = self._load_from_file()
        return self._config
    
    def _load_from_file(self) -> AppConfig:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as file:
            data = yaml.safe_load(file)
        
        openai_config = OpenAIConfig(
            model=data['openai']['model'],
            max_tokens=data['openai']['max_tokens'],
            temperature=data['openai']['temperature'],
            context_buffer=data['openai']['context_buffer']
        )
        
        chunking_config = ChunkingConfig(
            max_chunk_size=data['chunking']['max_chunk_size'],
            overlap_lines=data['chunking']['overlap_lines']
        )
        
        return AppConfig(
            openai=openai_config,
            chunking=chunking_config
        )
    
    def get_openai_api_key(self) -> str:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        return api_key