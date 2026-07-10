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

The app includes a scenario dropdown with four demo cases:

- Typhoon approaching SGN
- Lightning ramp stop at SGN
- Maintenance cascade at SGN
- High-volume network stress

### Assets

The VietJet Air logo in `assets/vietjet-air-logo.svg` is sourced from Wikimedia Commons:
https://commons.wikimedia.org/wiki/File:VietJet_Air_logo.svg

The file is marked as a public-domain textlogo on Commons, but it remains a trademark of VietJet Air.

### Run Agent Orchestration Directly

```bash
python -m flightops.run_agents
```

### Optional LLM Briefing

The core recommendation is produced by deterministic specialist agents. The app also includes an optional LLM Explanation Agent for a natural-language operations briefing.

By default, it tries AWS Bedrock Claude if configured:

```bash
export FLIGHTOPS_LLM_PROVIDER=bedrock
export AWS_REGION=us-east-1
export AWS_PROFILE=<your-profile>
export BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
```

If AWS Bedrock is not configured, the app uses a deterministic fallback briefing and still runs normally.
