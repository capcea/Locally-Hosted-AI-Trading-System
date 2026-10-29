"""Regrant the existing AI-only identity after migrations; retain its password and all key files."""

import argparse
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy.engine import make_url

from apps.api.config import Settings
from scripts.configure_openrouter import private_config
from scripts.provision_ai import provision_database


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", required=True)
    parser.parse_args()
    private_config(Path(".env.ai"))
    url = make_url(dotenv_values(".env.ai").get("AI_WORKER_DATABASE_URL") or "")
    config = Settings()
    admin = config.migration_database_url
    if not admin or url.username != "research_ai" or not url.password:
        raise ValueError("Separate migration identity and existing restricted AI identity required")
    provision_database(admin.get_secret_value(), url.password)
    print(
        "Existing AI-only grants refreshed. Password, encrypted content key and volumes retained."
    )


if __name__ == "__main__":
    main()
