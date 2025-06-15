# Gmail AI Agent 🤖📧

An intelligent Gmail automation agent that processes unread emails and generates AI-powered responses using Groq's LLM API. The agent can automatically reply to emails or save responses as drafts for manual review.


![Gmail-AI_Agent](https://github.com/user-attachments/assets/280e65d5-0fd8-4563-acb6-e855511582dc)


## 🌟 Features

- **Intelligent Email Processing**: Automatically categorizes emails by intent (business, personal, spam, etc.)
- **AI-Powered Replies**: Generates contextually appropriate responses using Groq's language models
- **Multiple Operation Modes**: 
  - Auto-reply mode for immediate responses
  - Draft mode for manual review before sending
  - Continuous monitoring with configurable intervals
- **Smart Filtering**: Tracks processed messages to avoid duplicate responses
- **Flexible Configuration**: Customizable via environment variables
- **Comprehensive Logging**: Detailed logs with rotation and retention policies
- **Dry-Run Mode**: Test the agent without actually sending emails

## 🛠️ Prerequisites

- Python 3.7+
- Gmail account with API access enabled
- Groq API account and key
- Google Cloud Console project with Gmail API enabled

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Vinay9911/Gmail-AI-Agent.git
cd Gmail-AI-Agent
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Google Gmail API

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API for your project
4. Create credentials (OAuth 2.0 Client ID) for a desktop application
5. Download the credentials JSON file and save it as `config/credentials.json`

### 4. Get Groq API Key

1. Sign up at [Groq Console](https://console.groq.com/)
2. Generate an API key
3. Copy the API key for the next step

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit the `.env` file with your credentials:

```env
# Groq Configuration
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant

# Gmail Configuration
GMAIL_SCOPES=https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/gmail.send,https://www.googleapis.com/auth/gmail.compose
GMAIL_CREDENTIALS_PATH=config/credentials.json
GMAIL_TOKEN_PATH=config/token.json

# AI Agent Configuration
MAX_EMAILS_TO_PROCESS=10
REPLY_TEMPERATURE=0.7
REPLY_MAX_TOKENS=500

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/gmail_agent.log
```

### 6. First Run (Authentication)

Run the agent for the first time to complete OAuth authentication:

```bash
python src/main.py --mode draft --dry-run
```

This will open a browser window for Gmail authentication. Grant the necessary permissions.

## 📖 Usage

### Basic Commands

#### Run in Draft Mode (Recommended for first use)
```bash
python src/main.py --mode draft
```

#### Run in Auto-Reply Mode
```bash
python src/main.py --mode auto
```

#### Dry Run (Test without sending/saving)
```bash
python src/main.py --mode draft --dry-run
```

### Continuous Monitoring

#### Monitor and save as drafts every 5 minutes
```bash
python src/main.py --mode monitor-draft --interval 5
```

#### Monitor and auto-reply every 2 minutes
```bash
python src/main.py --mode monitor-auto --interval 2
```

### Utility Commands

#### View Statistics
```bash
python src/main.py --stats
```

#### List Current Drafts
```bash
python src/main.py --list-drafts
```

#### Clear Processing History
```bash
python src/main.py --clear-history
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Your Groq API key | Required |
| `GROQ_MODEL` | Groq model to use | `llama-3.1-8b-instant` |
| `MAX_EMAILS_TO_PROCESS` | Maximum emails per run | `10` |
| `REPLY_TEMPERATURE` | AI response creativity (0.0-1.0) | `0.7` |
| `REPLY_MAX_TOKENS` | Maximum tokens in AI response | `500` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Gmail Scopes

The agent requires these Gmail API scopes:
- `gmail.readonly` - Read emails
- `gmail.send` - Send replies
- `gmail.compose` - Create drafts

## 🔄 Operation Modes

### 1. Draft Mode (`--mode draft`)
- Generates AI replies and saves them as Gmail drafts
- Allows manual review before sending
- Recommended for initial testing and sensitive emails

### 2. Auto Mode (`--mode auto`)
- Automatically sends AI-generated replies
- Marks processed emails as read
- Use with caution - replies are sent immediately

### 3. Monitor Modes (`--mode monitor-draft` / `--mode monitor-auto`)
- Continuously monitors for new emails
- Runs in specified intervals
- Can be stopped with Ctrl+C

## 🧠 AI Email Processing

The agent uses a two-step AI process:

1. **Intent Analysis**: Categorizes emails into:
   - QUESTION (requesting information)
   - REQUEST (asking for action)
   - COMPLAINT (expressing dissatisfaction)
   - COMPLIMENT (positive feedback)
   - MEETING (scheduling related)
   - BUSINESS (general business)
   - PERSONAL (personal communication)
   - SPAM (potentially unwanted)
   - OTHER (uncategorized)

2. **Response Generation**: Creates contextually appropriate replies based on:
   - Email content and subject
   - Sender information
   - Categorized intent
   - Professional tone and structure

## 📁 Project Structure

```
Gmail-AI-Agent/
├── src/
│   ├── __init__.py
│   ├── main.py              # Main application entry point
│   ├── ai_agent.py          # Core agent logic
│   ├── gmail_client.py      # Gmail API wrapper
│   └── groq_client.py       # Groq API wrapper
├── config/
│   ├── __init__.py
│   ├── settings.py          # Configuration management
│   ├── credentials.json     # Google OAuth credentials (not in repo)
│   └── credentials.json.example  # Template file
├── logs/
│   └── gmail_agent.log      # Application logs (not in repo)
├── .env                     # Environment variables (not in repo)
├── .env.example             # Environment template
├── .gitignore               # Git ignore file
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🔒 Security Best Practices

- **Never commit sensitive files**: `.env`, `credentials.json`, `token.json`
- **Use draft mode initially** to review AI responses
- **Monitor logs** for any unusual activity
- **Regularly rotate API keys**
- **Review Gmail API permissions** periodically
- **Test with dry-run mode** before live deployment

## 🐛 Troubleshooting

### Common Issues

#### Authentication Errors
```bash
# Clear existing tokens and re-authenticate
rm config/token.json
python src/main.py --mode draft --dry-run
```

#### Groq API Errors
- Verify your API key in `.env`
- Check your Groq account quota/limits
- Try a different model if rate limited

#### Gmail API Quota Exceeded
- Gmail API has daily quotas
- Reduce `MAX_EMAILS_TO_PROCESS`
- Increase monitoring intervals

#### No New Messages Found
- Agent only processes truly new unread emails
- Check `processed_messages.json` for tracking history
- Use `--clear-history` to reset if needed

### Logs and Debugging

Logs are stored in `logs/gmail_agent.log` with automatic rotation. Check logs for detailed error information:

```bash
tail -f logs/gmail_agent.log
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📋 Requirements

See `requirements.txt` for the complete list of dependencies:

- `google-auth-oauthlib` - Google OAuth authentication
- `google-auth-httplib2` - Google API HTTP library
- `google-api-python-client` - Gmail API client
- `groq` - Groq API client
- `loguru` - Advanced logging
- `beautifulsoup4` - HTML parsing
- `python-dotenv` - Environment variable management
- `requests` - HTTP requests

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool automatically processes and responds to emails. Use responsibly:

- Test thoroughly in draft mode before using auto-reply
- Monitor the agent's responses regularly
- Be aware of your organization's email policies
- The AI may occasionally generate unexpected responses
- Always review important communications manually

## 🆘 Support

If you encounter issues:

1. Check the [troubleshooting section](#-troubleshooting)
2. Review the logs in `logs/gmail_agent.log`
3. Open an issue on GitHub with:
   - Error messages (remove sensitive info)
   - Steps to reproduce
   - Your configuration (remove credentials)

## 📈 Roadmap

- [ ] Support for multiple Gmail accounts
- [ ] Custom response templates
- [ ] Integration with calendar for meeting requests
- [ ] Sentiment analysis for better response tone
- [ ] Web dashboard for monitoring and control
- [ ] Support for attachments in responses
- [ ] Machine learning for improved categorization

---

**Made with ❤️ for email automation**
