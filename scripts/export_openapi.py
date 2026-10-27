"""Generate the API contract without inspecting developer configuration or secrets."""

import json
from pathlib import Path

from apps.api.config import Settings
from apps.api.main import create_app


def export() -> None:
    app = create_app(Settings(_env_file=None))
    Path("docs").mkdir(exist_ok=True)
    Path("docs/openapi.json").write_text(json.dumps(app.openapi(), indent=2) + "\n")


if __name__ == "__main__":
    export()
