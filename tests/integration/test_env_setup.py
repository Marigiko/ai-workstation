"""Tests that the gateway .env is correctly configured."""

from pathlib import Path

ENV_PATH = Path("/mnt/e/Projects/ai-workstation/.env")


def test_env_file_exists():
    assert ENV_PATH.exists(), ".env file missing"


def test_required_vars_present():
    content = ENV_PATH.read_text()
    for var in ["POSTGRES_PASSWORD", "DATABASE_URL", "REDIS_URL", "QDRANT_URL"]:
        assert var in content, f"Variable {var} missing from .env"


def test_at_least_one_api_key():
    content = ENV_PATH.read_text()
    keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"]
    assert any(
        k in content and len(content.split(k)[1].split("\n")[0].strip()) > 5
        for k in keys
    ), "At least one LLM API key required in .env"


def test_docker_compose_vars_present():
    content = ENV_PATH.read_text()
    for var in ["GRAFANA_ADMIN_PASSWORD", "POSTGRES_USER", "POSTGRES_DB"]:
        assert var in content, f"Docker-compose variable {var} missing"
