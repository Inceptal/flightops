# AI Builders Week

Codex project workspace on Wraith.

Path: /home/daniel/Documents/AI Builders Week

## Note

Hackathon submission

## FlightOps AI

Autonomous operations copilot demo for airline operations managers.

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run

```bash
streamlit run app.py
```

The first demo dataset is in `demo-data/flightops-ai-typhoon-sgn-2026-07-12.json`.

### Assets

The VietJet Air logo in `assets/vietjet-air-logo.svg` is sourced from Wikimedia Commons:
https://commons.wikimedia.org/wiki/File:VietJet_Air_logo.svg

The file is marked as a public-domain textlogo on Commons, but it remains a trademark of VietJet Air.

### Run Agent Orchestration Directly

```bash
python -m flightops.run_agents
```
