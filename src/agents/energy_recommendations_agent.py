import os
import sys
from pathlib import Path
from typing import Dict, Any

from openai import OpenAI

# Add parent directory to path so state can be imported.
sys.path.insert(0, str(Path(__file__).parent.parent))

from state import HouseholdProfileState


class EnergyRecommendationsAgent:
    def __init__(self):
        self.agent_name = "Agent_EnergyRecommendations"
        self.model = "gpt-3.5-turbo"

    def process(self, state: HouseholdProfileState) -> HouseholdProfileState:
        state['current_agent'] = self.agent_name
        state['messages'] = state.get('messages', [])
        state['errors'] = state.get('errors', [])

        profile_data = state.get('profile_data') or {}
        if not profile_data:
            error = "No profile data found in state.profile_data."
            state['errors'].append(error)
            state['messages'].append(f"[ERROR] {error}")
            state['workflow_stage'] = 'Error'
            return state

        try:
            prompt = self._build_prompt(profile_data)
            recommendations = self._query_openai(prompt)

            state['energy_recommendations'] = {
                'recommendations': recommendations,
                'prompt': prompt,
                'model': self.model,
            }

            print(f"recommendations: {recommendations}")
            state['workflow_stage'] = 'Complete'
            state['messages'].append("[SUCCESS] Energy-saving recommendations generated.")

        except Exception as e:
            state['errors'].append(str(e))
            state['messages'].append(f"[ERROR] {str(e)}")
            state['workflow_stage'] = 'Error'

        return state

    def _build_prompt(self, profile_data: Dict[str, Any]) -> str:
        summary_items = []
        for key in sorted(profile_data.keys()):
            value = profile_data.get(key)
            summary_items.append(f"- {key}: {value}")

        summary_text = "\n".join(summary_items)

        return (
            "You are an energy efficiency consultant.\n"
            "Review the household profile and computed energy metrics below.\n"
            "Produce a prioritized list of 4-6 practical energy-saving recommendations.\n"
            "Each recommendation should be tailored to the house profile and should include a brief quantified impact or rationale.\n"
            "Focus on LED lighting, AC thermostat/usage, water heater efficiency, insulation/window improvements, solar optimization, and any high-impact appliance actions.\n"
            "If the household already has an efficient feature, say that it is already good and do not recommend it again.\n"
            "Return the answer as a numbered list with short action items and expected benefits.\n\n"
            "Household profile and energy state:\n"
            f"{summary_text}\n\n"
            "Do not invent values. Use only the values provided above.\n"
        )

    def _query_openai(self, prompt: str) -> str:
        api_key = os.getenv('OPENAI_API_KEY')
        
            raise RuntimeError("OPENAI_API_KEY is not set in environment variables.")


        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful energy efficiency advisor."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=450,
        )

        choice = response.choices[0]
        return choice.message.content.strip()
