from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from flightops.supervisor import SupervisorAgent


def load_data(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def run_scenario(path: Path) -> dict[str, Any]:
    data = load_data(path)
    return SupervisorAgent().decide(data)


if __name__ == "__main__":
    scenario_path = Path("demo-data/flightops-ai-typhoon-sgn-2026-07-12.json")
    decision = run_scenario(scenario_path)
    print(json.dumps(decision, indent=2))
