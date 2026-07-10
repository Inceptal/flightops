from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any


DEFAULT_BEDROCK_MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"


@dataclass(frozen=True)
class LLMBriefing:
    provider: str
    model: str
    enabled: bool
    text: str
    evidence_bundle: dict[str, Any]
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "enabled": self.enabled,
            "text": self.text,
            "evidence_bundle": self.evidence_bundle,
            "error": self.error,
        }


class LLMExplanationAgent:
    name = "llm_explanation_agent"

    def run(self, data: dict[str, Any], decision: dict[str, Any]) -> LLMBriefing:
        evidence_bundle = self._build_evidence_bundle(data, decision)
        provider = os.getenv("FLIGHTOPS_LLM_PROVIDER", "bedrock").lower()

        if provider != "bedrock":
            return self._fallback(evidence_bundle, f"Unsupported provider: {provider}")

        if not self._bedrock_configured():
            return self._fallback(evidence_bundle, "AWS Bedrock environment is not configured.")

        model_id = os.getenv("BEDROCK_MODEL_ID", DEFAULT_BEDROCK_MODEL_ID)
        region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"

        try:
            import boto3
            from botocore.exceptions import BotoCoreError, ClientError

            client = boto3.client("bedrock-runtime", region_name=region)
            response = client.converse(
                modelId=model_id,
                system=[
                    {
                        "text": (
                            "You are FlightOps AI's LLM Explanation Agent. Explain only the supplied "
                            "structured operations evidence. Do not invent flights, aircraft, costs, "
                            "weather, or actions. Keep the briefing concise for an airline operations manager."
                        )
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": (
                                    "Create an operations-manager briefing from this JSON evidence. "
                                    "Include: decision, why, residual risks, and immediate next actions.\n\n"
                                    f"{json.dumps(evidence_bundle, indent=2)}"
                                )
                            }
                        ],
                    }
                ],
                inferenceConfig={"maxTokens": 700, "temperature": 0.2},
            )
            text = response["output"]["message"]["content"][0]["text"].strip()
            return LLMBriefing(
                provider="aws-bedrock",
                model=model_id,
                enabled=True,
                text=text,
                evidence_bundle=evidence_bundle,
            )
        except (BotoCoreError, ClientError, KeyError, IndexError, ImportError) as exc:
            return self._fallback(evidence_bundle, str(exc))

    def _bedrock_configured(self) -> bool:
        has_region = bool(os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION"))
        has_profile = bool(os.getenv("AWS_PROFILE"))
        has_keys = bool(os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"))
        return has_region and (has_profile or has_keys)

    def _fallback(self, evidence_bundle: dict[str, Any], error: str | None = None) -> LLMBriefing:
        actions = evidence_bundle["recommended_actions"]
        metrics = evidence_bundle["metrics"]
        scenario = evidence_bundle["scenario"]["name"]
        text = (
            f"For {scenario}, FlightOps AI recommends: {actions[0]}; {actions[1]}; {actions[2]}. "
            "The recommendation is based on the coordinated weather, aircraft, crew, maintenance and cost "
            "agent findings, prioritizing the action sequence with the lowest modeled disruption cascade. "
            "Estimated savings are "
            f"{metrics['estimated_savings']}, with {metrics['misconnections_prevented']} misconnections "
            "prevented. Residual risk remains if SGN flow control tightens earlier than forecast."
        )
        return LLMBriefing(
            provider="deterministic-fallback",
            model="none",
            enabled=False,
            text=text,
            evidence_bundle=evidence_bundle,
            error=error,
        )

    def _build_evidence_bundle(self, data: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
        recommended_actions = []
        for action in decision["recommended_actions"][:3]:
            if action["type"] == "aircraft_swap":
                recommended_actions.append(f"Swap {action['flight']} onto {action['to_tail']}")
            elif action["type"] == "controlled_delay":
                recommended_actions.append(f"Delay {action['flight']} by {action['delay_minutes']} minutes")
            elif action["type"] == "gate_change":
                recommended_actions.append(f"Move {action['flight']} to {action['to_resource']}")
            elif action["type"] == "ground_hold":
                recommended_actions.append(f"Hold {action['flight']} for {action['hold_minutes']} minutes")
            elif action["type"] == "maintenance_protection":
                recommended_actions.append(f"Protect {action['tail']} for maintenance")
            elif action["type"] == "crew_reallocation":
                recommended_actions.append(f"Reassign {action['flight']} to {action['to_crew']}")
            elif action["type"] == "capacity_rebalance":
                recommended_actions.append(f"Prioritize {action['flight_bank']}")
            elif action["type"] == "departure_metering":
                recommended_actions.append(f"Meter {action['flight_bank']}")
            elif action["type"] == "passenger_protection":
                recommended_actions.append(f"Protect {action['connection_groups']} connection groups")
            elif action["type"] == "recovery_buffer":
                recommended_actions.append(f"Add {action['buffer_minutes']} minute recovery buffers")

        return {
            "scenario": {
                "name": data["scenario"].get("name"),
                "status": data["scenario"].get("status_label"),
                "snapshot_time_local": data["scenario"].get("snapshot_time_local"),
            },
            "recommended_actions": recommended_actions,
            "metrics": {
                "confidence": f"{decision['confidence']:.0%}",
                "estimated_savings": f"US${decision['projected_outcome']['total_estimated_savings_usd']:,}",
                "delay_minutes_avoided": decision["projected_outcome"]["delay_minutes_avoided"],
                "misconnections_prevented": decision["projected_outcome"]["misconnections_prevented"],
            },
            "agent_findings": [
                {
                    "agent": finding["agent"],
                    "risk_score": finding["risk_score"],
                    "summary": finding["summary"],
                    "evidence": finding["evidence"],
                }
                for finding in decision["agent_findings"]
            ],
            "alternatives_rejected": decision["alternatives_considered"],
            "explanation_chain": decision["explainability_payload"]["decision_chain"],
        }
