"""
Configuration management for PullData.

Handles loading, validation, and management of configuration from YAML files
with environment variable substitution and preset support.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Literal, Optional

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from pulldata.core.exceptions import (
    ConfigError,
    ConfigFileNotFoundError,
    ConfigValidationError,
)


# ============================================================
# Storage Configuration
# ============================================================


class PostgresConfig(BaseModel):
    """PostgreSQL storage configuration."""

    host: str = "localhost"
    port: int = Field(default=5432, gt=0, le=65535)
    database: str = "pulldata"
    user: str = "pulldata_user"
    password: str = Field(default="", description="Database password")
    vector_dimension: int = Field(default=384, gt=0)
    pool_size: int = Field(default=5, gt=0)
    max_overflow: int = Field(default=10, ge=0)
    echo: bool = Field(default=False, description="Log SQL queries")


class LocalStorageConfig(BaseModel):
    """Local SQLite storage configuration."""

    sqlite_path: str = "./data/pulldata.db"
    faiss_index_path: str = "./data/faiss_indexes"
    create_if_missing: bool = True


class ChromaDBConfig(BaseModel):
    """ChromaDB storage configuration."""

    persist_directory: str = "./data/chroma_db"
    create_if_missing: bool = True


class StorageConfig(BaseModel):
    """Storage backend configuration."""

    backend: Literal["local", "postgres", "chromadb"] = "local"
    postgres: PostgresConfig = Field(default_factory=PostgresConfig)
    local: LocalStorageConfig = Field(default_factory=LocalStorageConfig)
    chromadb: ChromaDBConfig = Field(default_factory=ChromaDBConfig)


# ============================================================
# Model Configuration
# ============================================================


class EmbedderConfig(BaseModel):
    """Embedding model configuration."""

    name: str = "BAAI/bge-small-en-v1.5"
    dimension: int = Field(default=384, gt=0)
    batch_size: int = Field(default=32, gt=0)
    device: Literal["cuda", "cpu"] = "cuda"
    normalize_embeddings: bool = True
    cache_dir: str = "./models/embeddings"


class LocalLLMConfig(BaseModel):
    """Local LLM configuration (transformers)."""

    name: str = "Qwen/Qwen2.5-3B-Instruct"
    quantization: Literal["none", "int8", "int4", "fp16"] = "int8"
    device: Literal["cuda", "cpu"] = "cuda"
    cache_dir: str = "./models/llm"
    trust_remote_code: bool = True


class APILLMConfig(BaseModel):
    """API-based LLM configuration (OpenAI-compatible)."""

    base_url: str = "http://localhost:1234/v1"
    api_key: str = Field(..., description="API key (use 'sk-dummy' for local servers)")
    model: str = "local-model"
    timeout: int = Field(default=60, gt=0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, ge=0)


class GenerationConfig(BaseModel):
    """LLM generation parameters."""

    max_tokens: int = Field(default=2048, gt=0)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    top_k: int = Field(default=50, ge=1)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)


class LLMConfig(BaseModel):
    """Language model configuration supporting both local and API providers."""

    provider: Literal["local", "api"] = "local"
    local: LocalLLMConfig = Field(default_factory=LocalLLMConfig)
    api: APILLMConfig = Field(default_factory=lambda: APILLMConfig(api_key="sk-dummy"))
    generation: GenerationConfig = Field(default_factory=GenerationConfig)

    @model_validator(mode="after")
    def validate_provider_config(self) -> "LLMConfig":
        """Ensure required config exists for selected provider."""
        if self.provider == "api" and not self.api.api_key:
            raise ValueError("api_key is required when provider='api'")
        return self


class ModelConfig(BaseModel):
    """Model configuration (embedder + LLM)."""

    embedder: EmbedderConfig = Field(default_factory=EmbedderConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)


# ============================================================
# Document Processing Configuration
# ============================================================


class PDFParsingConfig(BaseModel):
    """PDF parsing configuration."""

    backend: Literal["pymupdf", "pdfplumber"] = "pymupdf"
    extract_images: bool = False
    extract_tables: bool = True
    table_settings: dict[str, Any] = Field(
        default_factory=lambda: {
            "min_words_vertical": 3,
            "min_words_horizontal": 3,
            "intersection_tolerance": 3,
        }
    )


class ChunkingConfig(BaseModel):
    """Text chunking configuration."""

    strategy: Literal["semantic", "fixed", "sentence"] = "semantic"
    chunk_size: int = Field(default=512, gt=0, description="Chunk size in tokens")
    chunk_overlap: int = Field(default=50, ge=0)
    min_chunk_size: int = Field(default=100, gt=0)
    respect_sentence_boundary: bool = True


class HashingConfig(BaseModel):
    """Content hashing configuration."""

    algorithm: Literal["sha256", "md5"] = "sha256"
    enabled: bool = True


class ParsingConfig(BaseModel):
    """Document parsing configuration."""

    pdf: PDFParsingConfig = Field(default_factory=PDFParsingConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    hashing: HashingConfig = Field(default_factory=HashingConfig)


# ============================================================
# Retrieval Configuration
# ============================================================


class VectorSearchConfig(BaseModel):
    """Vector search configuration."""

    index_type: Literal["flat", "ivf", "hnsw"] = "flat"
    metric: Literal["cosine", "l2", "ip"] = "cosine"
    top_k: int = Field(default=5, gt=0)
    nprobe: int = Field(default=10, gt=0, description="For IVF index")


class RetrievalFiltersConfig(BaseModel):
    """Metadata filtering configuration."""

    enabled: bool = True
    default_filters: dict[str, Any] = Field(default_factory=dict)


class RerankingConfig(BaseModel):
    """Reranking configuration."""

    enabled: bool = False
    model: str = "BAAI/bge-reranker-base"
    top_n: int = Field(default=3, gt=0)


class RetrievalConfig(BaseModel):
    """Retrieval configuration."""

    vector_search: VectorSearchConfig = Field(default_factory=VectorSearchConfig)
    filters: RetrievalFiltersConfig = Field(default_factory=RetrievalFiltersConfig)
    reranking: RerankingConfig = Field(default_factory=RerankingConfig)


# ============================================================
# Cache Configuration
# ============================================================


class LLMCacheConfig(BaseModel):
    """LLM output cache configuration."""

    enabled: bool = True
    ttl_hours: int = Field(default=24, gt=0)
    max_entries: int = Field(default=10000, gt=0)
    eviction_policy: Literal["lru", "lfu", "ttl"] = "lru"


class EmbeddingCacheConfig(BaseModel):
    """Embedding cache configuration."""

    enabled: bool = True
    ttl_hours: int = Field(default=168, gt=0)  # 7 days
    max_entries: int = Field(default=50000, gt=0)


class CacheConfig(BaseModel):
    """Cache configuration."""

    llm_output: LLMCacheConfig = Field(default_factory=LLMCacheConfig)
    embedding: EmbeddingCacheConfig = Field(default_factory=EmbeddingCacheConfig)


# ============================================================
# Project Configuration
# ============================================================


class ProjectIsolationConfig(BaseModel):
    """Project isolation strategy per backend."""

    postgres: Literal["schema"] = "schema"
    local: Literal["database"] = "database"
    chromadb: Literal["collection"] = "collection"


class ProjectConfig(BaseModel):
    """Project-specific configuration."""

    name: str = "default_project"
    description: str = "Default PullData project"
    metadata: dict[str, Any] = Field(default_factory=dict)
    isolation: ProjectIsolationConfig = Field(default_factory=ProjectIsolationConfig)


# ============================================================
# Output Configuration
# ============================================================


class ExcelOutputConfig(BaseModel):
    """Excel output configuration."""

    engine: Literal["openpyxl", "xlsxwriter"] = "openpyxl"
    default_sheet_name: str = "Sheet1"
    include_metadata: bool = True
    styling: dict[str, Any] = Field(
        default_factory=lambda: {
            "header_bold": True,
            "auto_filter": True,
            "freeze_panes": "A2",
        }
    )


class MarkdownOutputConfig(BaseModel):
    """Markdown output configuration."""

    include_toc: bool = True
    code_theme: str = "github"
    heading_level: int = Field(default=2, ge=1, le=6)


class JSONOutputConfig(BaseModel):
    """JSON output configuration."""

    indent: int = Field(default=2, ge=0)
    ensure_ascii: bool = False
    sort_keys: bool = False


class OutputConfig(BaseModel):
    """Output generation configuration."""

    excel: ExcelOutputConfig = Field(default_factory=ExcelOutputConfig)
    markdown: MarkdownOutputConfig = Field(default_factory=MarkdownOutputConfig)
    json: JSONOutputConfig = Field(default_factory=JSONOutputConfig)


# ============================================================
# Logging Configuration
# ============================================================


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    format: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    log_to_file: bool = True
    log_file: str = "./logs/pulldata.log"
    rotation: str = "10 MB"
    retention: str = "30 days"
    compression: str = "zip"


# ============================================================
# Performance Configuration
# ============================================================


class PerformanceConfig(BaseModel):
    """Performance tuning configuration."""

    batch_size: int = Field(default=32, gt=0)
    num_workers: int = Field(default=4, gt=0)
    max_memory_gb: int = Field(default=6, gt=0)
    clear_cache_after_ingest: bool = False
    show_progress: bool = True


# ============================================================
# Feature Flags
# ============================================================


class FeatureFlags(BaseModel):
    """Feature flags for enabling/disabling features."""

    differential_updates: bool = True
    multi_project: bool = True
    advanced_filtering: bool = True
    llm_caching: bool = True
    streaming_generation: bool = False
    table_embeddings: bool = False


# ============================================================
# Main Configuration
# ============================================================


class Config(BaseModel):
    """
    Main PullData configuration.

    This is the root configuration object that contains all settings.
    """

    storage: StorageConfig = Field(default_factory=StorageConfig)
    models: ModelConfig = Field(default_factory=ModelConfig)
    parsing: ParsingConfig = Field(default_factory=ParsingConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    features: FeatureFlags = Field(default_factory=FeatureFlags)


# ============================================================
# Configuration Loading
# ============================================================


def substitute_env_vars(value: Any) -> Any:
    """
    Recursively substitute environment variables in configuration values.

    Supports ${VAR_NAME} syntax. If variable is not found, raises ConfigError.

    Args:
        value: Configuration value (can be string, dict, list, etc.)

    Returns:
        Value with environment variables substituted

    Raises:
        ConfigError: If referenced environment variable doesn't exist
    """
    if isinstance(value, str):
        # Find all ${VAR_NAME} patterns
        pattern = r"\$\{([^}]+)\}"
        matches = re.findall(pattern, value)

        for var_name in matches:
            env_value = os.environ.get(var_name)
            if env_value is None:
                raise ConfigError(
                    f"Environment variable '{var_name}' not found",
                    details={"variable": var_name, "value": value},
                )
            value = value.replace(f"${{{var_name}}}", env_value)

        return value

    elif isinstance(value, dict):
        return {k: substitute_env_vars(v) for k, v in value.items()}

    elif isinstance(value, list):
        return [substitute_env_vars(item) for item in value]

    else:
        return value


def load_yaml_config(config_path: str | Path) -> dict[str, Any]:
    """
    Load YAML configuration file.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Dictionary with configuration data

    Raises:
        ConfigFileNotFoundError: If file doesn't exist
        ConfigError: If YAML parsing fails
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise ConfigFileNotFoundError(
            f"Configuration file not found: {config_path}",
            details={"path": str(config_path)},
        )

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        if config_data is None:
            config_data = {}

        # Substitute environment variables
        config_data = substitute_env_vars(config_data)

        return config_data

    except yaml.YAMLError as e:
        raise ConfigError(
            f"Failed to parse YAML configuration: {e}",
            details={"path": str(config_path), "error": str(e)},
        )
    except Exception as e:
        raise ConfigError(
            f"Failed to load configuration: {e}",
            details={"path": str(config_path), "error": str(e)},
        )


def load_config(
    config_path: Optional[str | Path] = None,
    preset: Optional[str] = None,
    **overrides,
) -> Config:
    """
    Load and create configuration.

    Args:
        config_path: Path to configuration file (default: configs/default.yaml)
        preset: Optional preset name from models.yaml
        **overrides: Override specific configuration values

    Returns:
        Validated Config object

    Raises:
        ConfigError: If configuration loading or validation fails
    """
    # Default config path
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "configs" / "default.yaml"
    else:
        config_path = Path(config_path)

    # Load main configuration
    config_data = load_yaml_config(config_path)

    # Load preset if specified
    if preset:
        models_yaml_path = config_path.parent / "models.yaml"
        if models_yaml_path.exists():
            models_data = load_yaml_config(models_yaml_path)
            if preset in models_data:
                preset_data = models_data[preset]
                # Merge preset into config (preset values override defaults)
                if "embedder" in preset_data:
                    config_data.setdefault("models", {}).setdefault("embedder", {}).update(
                        preset_data["embedder"]
                    )
                if "llm" in preset_data:
                    config_data.setdefault("models", {}).setdefault("llm", {}).update(
                        preset_data["llm"]
                    )
            else:
                raise ConfigError(
                    f"Preset '{preset}' not found in {models_yaml_path}",
                    details={"preset": preset, "file": str(models_yaml_path)},
                )

    # Apply overrides
    if overrides:
        config_data.update(overrides)

    # Validate and create Config object
    try:
        config = Config(**config_data)
        return config
    except Exception as e:
        raise ConfigValidationError(
            f"Configuration validation failed: {e}", details={"error": str(e)}
        )


def save_config(config: Config, output_path: str | Path) -> None:
    """
    Save configuration to YAML file.

    Args:
        config: Config object to save
        output_path: Path where to save the configuration

    Raises:
        ConfigError: If saving fails
    """
    output_path = Path(output_path)

    try:
        # Convert to dict
        config_dict = config.model_dump(mode="json", exclude_none=False)

        # Save to YAML
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

    except Exception as e:
        raise ConfigError(
            f"Failed to save configuration: {e}",
            details={"path": str(output_path), "error": str(e)},
        )
