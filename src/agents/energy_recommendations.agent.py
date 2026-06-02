
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


from langgraph.types import Command
from langgraph.graph import END
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).parent.parent))
from state import HouseholdProfileState


class EnergyRecommendationsAgent:
    def __init__(self):
        self.agent_name = "EnergyRecommendationsAgent"

    def process(self, state: HouseholdProfileState) -> Command:
        appliance_data = dict(state.get("appliance_data", {}))
        energy_metrics = dict(state.get("energy_metrics", {}))
        profile_data = dict(state.get("profile_data", {}))
        solar_roi = dict(state.get("solar_roi", {}))
        comparison = dict(state.get("comparison_summary", {}))

        messages = list(state.get("messages", []))
        errors = list(state.get("errors", []))
        updates: Dict[str, Any] = {"current_agent": self.agent_name}

        try:
            system_prompt = (
                "You are an expert energy efficiency advisor. Generate exactly 4-6 practical, prioritized, quantified energy-saving recommendations "
                "tailored to the household profile provided. For each action include these structured fields: title, description, estimated_monthly_kwh_savings, "
                "estimated_monthly_cost_savings, implementation_cost, priority (High/Medium/Low), and confidence_score (0-1). "
                "Use energy adjustment factors, climate/insulation impacts, and solar energy assumptions when estimating savings. If a feature is already efficient, "
                "acknowledge it without repeating it as a new recommendation. Return only valid JSON with a top-level key 'recommendations' containing a list of objects."
            )

            # Collate available data into user prompt
            user_context = {
                "profile_data": profile_data,
                "appliance_data": appliance_data,
                "energy_metrics": energy_metrics,
                "solar_roi": solar_roi,
                "comparison_summary": comparison,
                "note": "Use energy_adjustment_factors from energy_metrics, such as climate and insulation factors, when estimating savings and setting priorities."
            }

            user_prompt = (
                "Household data (JSON):\n" + json.dumps(user_context, default=str, indent=2) +
                "\n\nProvide the recommendations JSON as specified. If monetary tariff is missing, omit cost savings fields but still estimate monthly kWh savings."
            )

            response_text = self._call_openai_chat(system_prompt, user_prompt)

            # Try parse JSON from model; if fails, store raw text
            parsed: Optional[Dict[str, Any]] = None
            try:
                # Find first JSON object in response
                start = response_text.find('{')
                if start != -1:
                    parsed = json.loads(response_text[start:])
            except Exception:
                parsed = None

            if parsed is None:
                updates["recommendations"] = {"text": response_text}
            else:
                updates["recommendations"] = parsed

            updates["workflow_stage"] = "Complete"
            messages.append("[SUCCESS] Energy recommendations generated via LLM.")
        except Exception as exc:
            errors.append(str(exc))
            updates["workflow_stage"] = "Error"
            messages.append(f"[ERROR] {exc}")

        updates["messages"] = messages
        updates["errors"] = errors
        return Command(update=updates, goto=self.route(updates))

    def _call_openai_chat(self, system_prompt: str, user_prompt: str) -> str:
        #api_key = os.getenv('OPENAI_API_KEY')
        #if not api_key:        
            #raise RuntimeError("OPENAI_API_KEY is not set in environment variables.")

        print("Fetching recommendations. Please wait...")
    
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=450,
        )

        choice = response.choices[0]
        return choice.message.content.strip()

    def route(self, state: HouseholdProfileState) -> str:
        return END
