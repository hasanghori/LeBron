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
        return ActionType.NOTION