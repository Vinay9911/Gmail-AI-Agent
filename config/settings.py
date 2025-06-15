import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    def __init__(self):
        # Groq Configuration
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        
        # Gmail Configuration
        gmail_scopes_str = os.getenv("GMAIL_SCOPES", "")
        if gmail_scopes_str:
            self.gmail_scopes = [scope.strip() for scope in gmail_scopes_str.split(",")]
        else:
            self.gmail_scopes = [
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/gmail.compose"
            ]
        
        self.gmail_credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", "config/credentials.json")
        self.gmail_token_path = os.getenv("GMAIL_TOKEN_PATH", "config/token.json")
        
        # AI Agent Configuration
        self.max_emails_to_process = int(os.getenv("MAX_EMAILS_TO_PROCESS", "10"))
        self.reply_temperature = float(os.getenv("REPLY_TEMPERATURE", "0.7"))
        self.reply_max_tokens = int(os.getenv("REPLY_MAX_TOKENS", "500"))
        
        # Logging
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", "logs/gmail_agent.log")

settings = Settings()