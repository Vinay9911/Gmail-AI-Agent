import os
import requests
import json
from typing import Optional
from loguru import logger
from config.settings import settings

class GroqClient:
    def __init__(self):
        try:
            from groq import Groq
            
            if not settings.groq_api_key:
                raise ValueError("GROQ_API_KEY not found in environment variables")
            
            try:
                self.client = Groq(api_key=settings.groq_api_key)
            except TypeError as e:
                if "proxies" in str(e):
                    try:
                        self.client = Groq()
                        self.client.api_key = settings.groq_api_key
                    except:
                        self.client = None
                        self.use_direct_api = True
                        logger.warning("Using direct API calls instead of Groq client")
                else:
                    raise
            
            self.model = settings.groq_model
            self.use_direct_api = getattr(self, 'use_direct_api', False)
            
            if not self.use_direct_api:
                logger.info("Groq client initialized successfully")
            
        except Exception as error:
            logger.error(f"Error initializing Groq client: {error}")
            self.client = None
            self.use_direct_api = True
            self.model = settings.groq_model
            logger.info("Falling back to direct API calls")
    
    def _make_direct_api_call(self, messages, temperature=0.7, max_tokens=500):
        """Make direct API call to Groq when client fails"""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def generate_reply(self, sender: str, subject: str, body: str, context: str = "") -> Optional[str]:
        """Generate an AI reply using Groq"""
        try:
            prompt = self._create_reply_prompt(sender, subject, body, context)
            
            messages = [
                {
                    "role": "system",
                    "content": "You are a professional email assistant. Generate appropriate, helpful, and contextually relevant email replies. Keep responses concise and professional."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            if self.use_direct_api:
                response_data = self._make_direct_api_call(
                    messages=messages,
                    temperature=settings.reply_temperature,
                    max_tokens=settings.reply_max_tokens
                )
                reply = response_data['choices'][0]['message']['content'].strip()
            else:
                response = self.client.chat.completions.create(
                    messages=messages,
                    model=self.model,
                    temperature=settings.reply_temperature,
                    max_tokens=settings.reply_max_tokens
                )
                reply = response.choices[0].message.content.strip()
            
            logger.info(f"Generated reply for email from {sender}")
            return reply
            
        except Exception as error:
            logger.error(f"Error generating reply with Groq: {error}")
            return None
    
    def _create_reply_prompt(self, sender: str, subject: str, body: str, context: str = "") -> str:
        """Create a detailed prompt for reply generation"""
        prompt = f"""
        Please generate a professional email reply based on the following information:
        
        FROM: {sender}
        SUBJECT: {subject}
        
        ORIGINAL MESSAGE:
        {body}
        
        {f"ADDITIONAL CONTEXT: {context}" if context else ""}
        
        INSTRUCTIONS:
        1. Generate a professional and appropriate reply
        2. Address the main points from the original message
        3. Keep the tone professional but friendly
        4. Include a proper greeting and closing
        5. Make the response helpful and actionable where appropriate
        6. Keep it concise (2-3 paragraphs maximum)
        
        REPLY:
        """
        
        return prompt
    
    def analyze_email_intent(self, subject: str, body: str, sender: str = "") -> str:
        """Analyze the intent/category of the email"""
        # Explicitly allow emails from vinaycollege1531@gmail.com
        if sender and 'vinaycollege1531@gmail.com' in sender.lower():
            return "BUSINESS"
        
        try:
            prompt = f"""
            Analyze the following email and categorize its intent/purpose:
            
            SUBJECT: {subject}
            BODY: {body}
            
            Categorize this email as one of the following:
            - QUESTION (asking for information)
            - REQUEST (asking for action/task)
            - COMPLAINT (expressing dissatisfaction)
            - COMPLIMENT (positive feedback)
            - MEETING (scheduling/meeting related)
            - BUSINESS (general business communication)
            - PERSONAL (personal communication)
            - SPAM (potentially spam/unwanted)
            - OTHER
            
            Respond with just the category name:
            """
            
            messages = [
                {
                    "role": "system",
                    "content": "You are an email classification assistant. Classify emails into the given categories."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            if self.use_direct_api:
                response_data = self._make_direct_api_call(
                    messages=messages,
                    temperature=0.3,
                    max_tokens=50
                )
                intent = response_data['choices'][0]['message']['content'].strip()
            else:
                response = self.client.chat.completions.create(
                    messages=messages,
                    model=self.model,
                    temperature=0.3,
                    max_tokens=50
                )
                intent = response.choices[0].message.content.strip()
            
            return intent
            
        except Exception as error:
            logger.error(f"Error analyzing email intent: {error}")
            return "OTHER"