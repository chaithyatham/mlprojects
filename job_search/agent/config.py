from __future__ import annotations

from pathlib import Path

import yaml

from .models import AgentConfig, CompanySeed


def load_config(config_path: Path, target_companies_path: Path | None = None) -> AgentConfig:
    """Load the primary config and optionally append explicitly targeted companies."""
    config_data = yaml.safe_load(config_path.read_text()) or {}
    config = AgentConfig.model_validate(config_data)

    if not target_companies_path:
        return config

    target_data = yaml.safe_load(target_companies_path.read_text()) or {}
    raw_companies = target_data.get("companies", target_data)
    if not isinstance(raw_companies, list):
        raise ValueError("target_companies.yaml must be a list or contain a 'companies' list.")

    config.companies.extend(
        CompanySeed.model_validate({**company, "source": company.get("source", "target-config")})
        for company in raw_companies
    )
    return config

