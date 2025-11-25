import random
import datetime
from openai import OpenAI
import requests
import os
from dotenv import load_dotenv
from personality_prompt import PersonalityPrompt
from constants.action_types import ActionType

try:
    load_dotenv()
except:
    pass

# Tasks:
# 1. Repeat messages until user responds
# 2. Make the messages actually funny/ entertaining
# 3. Make other people able to use this app

class AIModel:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4.1-mini"
        self.use_grok = True
        self.grok_api_key = os.getenv('GROK_API_KEY')
        self.grok_base_url = "https://api.x.ai/v1"
        self.grok_model = "grok-4-latest"
        self.personality_prompt = PersonalityPrompt()
        self.personality = self.personality_prompt.get_prompt("schmidt")

    def _call_grok_api(self, user_message: str, system_prompt: str = "") -> str:
        headers = {
            "Authorization": f"Bearer {self.grok_api_key}",
            "Content-Type": "application/json"
        }
    
        data = {
            "messages": [
                {"role": "user", "content": user_message + " " + system_prompt}
            ],
            "model": self.grok_model,
            "stream": False,
            "temperature": 0.7
        }
        
        response = requests.post(f"https://api.x.ai/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    
    def first_message(self, user_interests: str) -> str:
        user_message = f"Based on the user's interests: {user_interests}. Generate a motivating, rude question to get them started on their habits. Keep it under 100 characters. Return only the question, nothing else."
        return self._call_grok_api(user_message, self.personality)
    
    # Given a user's input, choose a tag for the note
    def choose_tag(self, user_input: str, tags: list[str]):
        prompt = f"""Analyze this text and choose the most appropriate tag from these options:
            {tags}
            
            Text: "{user_input}"
            
            Return only the tag name, nothing else."""
        
        if self.use_grok:
            return self._call_grok_api(prompt, self.personality)
        else:
            response = self.client.responses.create(
                model=self.model,
                instructions=self.personality,
                input=prompt
            )
            
            return response.output_text
    
    # Given a user's input, choose a title for the note
    def choose_title(self, user_input: str):
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        prompt = f"""Based on this text, generate a concise, descriptive title (under 20 characters):
            "{user_input}"
            
            If it's a daily log, use today's date format: YYYY-MM-DD - {date} as the title
            Otherwise, create a meaningful title that captures the essence.
            Return only the title, nothing else."""
        
        if self.use_grok:
            return self._call_grok_api(prompt, self.personality)
        else:
            response = self.client.responses.create(
                model=self.model,
                instructions=prompt,
                input=f"Based on this text, generate a concise, descriptive title: '{user_input}'"
            )
            
            return response.output_text
    
    def choose_action_type(self, user_input: str):
        return ActionType.HABITIFY
    
    def habitify_action(self, user_input: str, actions: list[str]) -> str:
        prompt = f"""Based on this text, choose the most appropriate action from these options:
            {actions}

            Text: "{user_input}"

            Return only the action, nothing else."""

        return self._call_grok_api(prompt)

    def parse_calendar_event(self, user_input: str) -> dict:
        """
        Parse natural language text into calendar event details
        Returns dict with: summary, start_datetime, end_datetime, description
        """
        current_datetime = datetime.datetime.now()
        prompt = f"""Parse this text into calendar event details. Today is {current_datetime.strftime('%A, %B %d, %Y')} at {current_datetime.strftime('%I:%M %p')}.

Text: "{user_input}"

Return a JSON object with these fields:
- summary: (string) A concise event title
- start_datetime: (ISO 8601 format) When the event starts
- end_datetime: (ISO 8601 format) When the event ends (if not specified, default to 1 hour after start)
- description: (string) Any additional details from the text

Example response format:
{{"summary": "Team Meeting", "start_datetime": "2025-11-24T14:00:00", "end_datetime": "2025-11-24T15:00:00", "description": "Discuss project updates"}}

Return ONLY valid JSON, nothing else."""

        response = self._call_grok_api(prompt)

        # Parse the JSON response
        import json
        try:
            # Clean up response in case there's extra text
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                event_data = json.loads(json_str)

                # Convert ISO strings to datetime objects
                event_data['start_datetime'] = datetime.datetime.fromisoformat(event_data['start_datetime'])
                event_data['end_datetime'] = datetime.datetime.fromisoformat(event_data['end_datetime'])

                return event_data
            else:
                raise ValueError("No JSON found in response")
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # Return default event if parsing fails
            start_time = current_datetime + datetime.timedelta(hours=1)
            return {
                'summary': user_input[:50],  # Use first 50 chars as title
                'start_datetime': start_time,
                'end_datetime': start_time + datetime.timedelta(hours=1),
                'description': user_input
            }