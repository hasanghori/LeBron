import random
import datetime
from openai import OpenAI
import os

class AIModel:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4.1-mini"
    
    def first_message(self, user_interests: str):
        # use chatGPT to decide what the first message should be
        prompt = f"""Based on the user's interests: {user_interests}
        Generate a friendly, engaging question to ask them about their day or activities.
        Keep it conversational and under 100 characters.
        Return only the question, nothing else."""
        
        response = self.client.responses.create(
            model=self.model,
            instructions="You are a helpful assistant that generates engaging questions. Keep responses under 100 characters and conversational.",
            input=f"Based on the user's interests: {user_interests}. Generate a friendly, engaging question to ask them about their day or activities. Return only the question, nothing else."
        )
        
        return response.output_text
    
    # Given a user's input, choose a tag for the note
    def choose_tag(self, user_input: str):
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
        # use chatGPT to decide what title to use for a note
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        
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