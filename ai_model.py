import random
import datetime
from openai import OpenAI
import requests
import os
from dotenv import load_dotenv

try:
    load_dotenv()
except:
    pass

# Tasks:
# 1. Repeat messages until user responds
# 2. Make the messages actually funny/ entertaining
# 3. Make other people able to use this app

class AIModel:
    def __init__(self, use_grok=True):
        self.use_grok = use_grok
        if not use_grok:
            self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            self.model = "gpt-4.1-mini"
        else:
            self.grok_api_key = os.getenv('GROK_API_KEY')
            self.grok_base_url = "https://api.x.ai/v1"
            self.grok_model = "grok-4-latest"
            self.rude_coach_prompt = "Act as a hella rude coach who is tryna motivate me to do my habits. When I talk to you, respond in that tone. Make sure you use hella swear words."
    
    def _call_grok_api(self, user_message, system_prompt=""):
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
    
    def first_message(self, user_interests: str):
        user_message = f"Based on the user's interests: {user_interests}. Generate a motivating, rude question to get them started on their habits. Keep it under 100 characters. Return only the question, nothing else."
        return self._call_grok_api(user_message, self.rude_coach_prompt)
    
    # Given a user's input, choose a tag for the note
    def choose_tag(self, user_input: str):
        if self.use_grok:
            user_message = f"""Analyze this text and choose the most appropriate tag from these options:
            - prayer
            - joke_idea
            - daily_log
            - project_idea
            - reflection
            - gratitude
            
            Text: "{user_input}"
            
            Return only the tag name, nothing else."""
            return self._call_grok_api(user_message, self.rude_coach_prompt)
        else:
            # use chatGPT to decide what tags to add to a note
            prompt = f"""Analyze this text and choose the most appropriate tag from these options:
            - prayer
            - joke_idea
            - daily_log
            - project_idea
            - reflection
            - gratitude
            
            Text: "{user_input}"
            
            Return only the tag name, nothing else."""
            
            response = self.client.responses.create(
                model=self.model,
                instructions="You are a helpful assistant that categorizes text with appropriate tags. Choose from: prayer, joke_idea, daily_log, project_idea, reflection, gratitude. Return only the tag name, nothing else.",
                input=f"Analyze this text and choose the most appropriate tag: '{user_input}'"
            )
            
            return response.output_text
    
    # Given a user's input, choose a title for the note
    def choose_title(self, user_input: str):
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        if self.use_grok:
            user_message = f"""Based on this text, generate a concise, descriptive title (under 20 characters):
            "{user_input}"
            
            If it's a daily log, use today's date format: YYYY-MM-DD - {date}
            Otherwise, create a meaningful title that captures the essence.
            Return only the title, nothing else."""
            return self._call_grok_api(user_message, self.rude_coach_prompt)
        else:
            # use chatGPT to decide what title to use for a note
            prompt = f"""Based on this text, generate a concise, descriptive title (under 20 characters):
            "{user_input}"
            
            If it's a daily log, use today's date format: YYYY-MM-DD - {date}
            Otherwise, create a meaningful title that captures the essence.
            Return only the title, nothing else."""
            
            response = self.client.responses.create(
                model=self.model,
                instructions="You are a helpful assistant that creates concise, descriptive titles. If it's a daily log, use today's date format: YYYY-MM-DD. Otherwise, create a meaningful title under 20 characters. Return only the title, nothing else.",
                input=f"Based on this text, generate a concise, descriptive title: '{user_input}'"
            )
            
            return response.output_text