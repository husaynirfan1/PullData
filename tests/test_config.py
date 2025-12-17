"""Tests for pulldata.core.config."""

import os
import tempfile
from pathlib import Path

import pytest

from pulldata.core.config import (
    Config,
    LLMConfig,
    load_config,
    load_yaml_config,
    save_config,
    substitute_env_vars,
)
from pulldata.core.exceptions import ConfigError, ConfigFileNotFoundError


class TestSubstituteEnvVars:
    """Tests for environment variable substitution."""

    def test_substitute_single_var(self):
        """Test substituting a single environment variable."""
        os.environ["TEST_VAR"] = "test_value"
        result = substitute_env_vars("${TEST_VAR}")
        assert result == "test_value"

    def test_substitute_in_string(self):
        """Test substituting variable within a string."""
        os.environ["TEST_HOST"] = "localhost"
        result = substitute_env_vars("http://${TEST_HOST}:8000")
        assert result == "http://localhost:8000"

    def test_substitute_multiple_vars(self):
        """Test substituting multiple variables."""
        os.environ["HOST"] = "example.com"
        os.environ["PORT"] = "443"
        result = substitute_env_vars("https://${HOST}:${PORT}/api")
        assert result == "https://example.com:443/api"

    def test_substitute_in_dict(self):
        """Test substituting variables in a dictionary."""
        os.environ["DB_HOST"] = "dbserver"
        os.environ["DB_PORT"] = "5432"
        data = {"host": "${DB_HOST}", "port": "${DB_PORT}"}
        result = substitute_env_vars(data)
        assert result["host"] == "dbserver"
        assert result["port"] == "5432"

    def test_substitute_missing_var(self):
        """Test error when environment variable doesn't exist."""
        with pytest.raises(ConfigError) as exc_info:
            substitute_env_vars("${NONEXISTENT_VAR}")
        assert "NONEXISTENT_VAR" in str(exc_info.value)

    def test_no_substitution_needed(self):
        """Test strings without variables pass through unchanged."""
        result = substitute_env_vars("plain_string")
        assert result == "plain_string"


class TestLoadYamlConfig:
    """Tests for YAML configuration loading."""

    def test_load_valid_yaml(self):
        """Test loading a valid YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("key: value\nnumber: 42\n")
            temp_path = f.name

        try:
            config = load_yaml_config(temp_path)
            assert config["key"] == "value"
            assert config["number"] == 42
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_file(self):
        """Test error when file doesn't exist."""
        with pytest.raises(ConfigFileNotFoundError):
            load_yaml_config("/nonexistent/path/config.yaml")

    def test_load_yaml_with_env_vars(self):
        """Test loading YAML with environment variable substitution."""
        os.environ["TEST_KEY"] = "test_value"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("api_key: ${TEST_KEY}\n")
            temp_path = f.name

        try:
            config = load_yaml_config(temp_path)
            assert config["api_key"] == "test_value"
        finally:
            os.unlink(temp_path)


class TestLLMConfig:
    """Tests for LLM configuration."""

    def test_local_provider_config(self):
        """Test local provider configuration."""
        config = LLMConfig(
            provider="local",
            local={"name": "Qwen/Qwen2.5-3B-Instruct", "quantization": "int8", "device": "cuda"},
        )
        assert config.provider == "local"
        assert config.local.name == "Qwen/Qwen2.5-3B-Instruct"
        assert config.local.quantization == "int8"

    def test_api_provider_config(self):
        """Test API provider configuration."""
        config = LLMConfig(
            provider="api",
            api={
                "base_url": "http://localhost:1234/v1",
                "api_key": "sk-dummy",
                "model": "local-model",
            },
        )
        assert config.provider == "api"
        assert config.api.base_url == "http://localhost:1234/v1"
        assert config.api.model == "local-model"

    def test_generation_params(self):
        """Test generation parameters."""
        config = LLMConfig(
            provider="local",
            generation={
                "max_tokens": 1024,
                "temperature": 0.8,
                "top_p": 0.95,
            },
        )
        assert config.generation.max_tokens == 1024
        assert config.generation.temperature == 0.8
        assert config.generation.top_p == 0.95


class TestConfig:
    """Tests for main Config class."""

    def test_create_default_config(self):
        """Test creating config with all defaults."""
        config = Config()
        assert config.storage.backend == "local"
        assert config.models.llm.provider == "local"
        assert config.features.differential_updates is True

    def test_config_with_overrides(self):
        """Test creating config with overrides."""
        config = Config(
            storage={"backend": "postgres"},
            models={"llm": {"provider": "api"}},
        )
        assert config.storage.backend == "postgres"
        assert config.models.llm.provider == "api"

    def test_config_serialization(self):
        """Test config serialization to dict."""
        config = Config()
        config_dict = config.model_dump()
        assert "storage" in config_dict
        assert "models" in config_dict
        assert config_dict["storage"]["backend"] == "local"


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_from_file(self):
        """Test loading config from file."""
        yaml_content = """
storage:
  backend: local
models:
  llm:
    provider: local
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert config.storage.backend == "local"
            assert config.models.llm.provider == "local"
        finally:
            os.unlink(temp_path)

    def test_load_with_overrides(self):
        """Test loading config with overrides."""
        yaml_content = """
storage:
  backend: local
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # Override storage backend
            config = load_config(temp_path, storage={"backend": "postgres"})
            assert config.storage.backend == "postgres"
        finally:
            os.unlink(temp_path)


class TestSaveConfig:
    """Tests for save_config function."""

    def test_save_and_load_config(self):
        """Test saving config to file and loading it back."""
        config = Config(
            storage={"backend": "postgres"},
            models={"llm": {"provider": "api"}},
        )

        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            temp_path = f.name

        try:
            # Save
            save_config(config, temp_path)
            assert Path(temp_path).exists()

            # Load back
            loaded_config = load_config(temp_path)
            assert loaded_config.storage.backend == "postgres"
            assert loaded_config.models.llm.provider == "api"
        finally:
            if Path(temp_path).exists():
                os.unlink(temp_path)


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_invalid_temperature(self):
        """Test validation of temperature parameter."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            Config(
                models={
                    "llm": {
                        "generation": {
                            "temperature": 3.0,  # Out of range (0.0-2.0)
                        }
                    }
                }
            )

    def test_invalid_batch_size(self):
        """Test validation of batch size."""
        with pytest.raises(Exception):
            Config(performance={"batch_size": -1})  # Must be positive

    def test_invalid_port(self):
        """Test validation of port number."""
        with pytest.raises(Exception):
            Config(storage={"postgres": {"port": 99999}})  # Out of range
