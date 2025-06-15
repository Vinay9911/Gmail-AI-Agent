import time
import json
import os
from typing import List, Dict, Set
from loguru import logger
from src.gmail_client import GmailClient
from src.groq_client import GroqClient
from config.settings import settings

class GmailAIAgent:
    def __init__(self):
        self.gmail_client = GmailClient()
        self.groq_client = GroqClient()
        self.processed_messages_file = "processed_messages.json"
        self.processed_messages = self._load_processed_messages()
        self.last_check_time = time.time()
    
    def _load_processed_messages(self) -> Set[str]:
        """Load previously processed message IDs from file"""
        if os.path.exists(self.processed_messages_file):
            try:
                with open(self.processed_messages_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('processed_ids', []))
            except Exception as e:
                logger.warning(f"Could not load processed messages: {e}")
        return set()
    
    def _save_processed_messages(self):
        """Save processed message IDs to file"""
        try:
            with open(self.processed_messages_file, 'w') as f:
                json.dump({
                    'processed_ids': list(self.processed_messages),
                    'last_updated': time.time()
                }, f)
        except Exception as e:
            logger.error(f"Could not save processed messages: {e}")
    
    def _get_new_messages(self) -> List[Dict]:
        """Get only new unread messages that haven't been processed"""
        all_unread = self.gmail_client.get_unread_messages(
            max_results=settings.max_emails_to_process,
            since_time=self.last_check_time
        )
        
        new_messages = [
            msg for msg in all_unread 
            if msg['id'] not in self.processed_messages
        ]
        
        logger.info(f"Found {len(new_messages)} new unread messages after {self.last_check_time}")
        return new_messages
    
    def run_agent(self, mode: str = "auto", dry_run: bool = True):
        """
        Main agent loop
        
        Args:
            mode: "auto" for automatic replies, "draft" for saving as drafts
            dry_run: If True, only logs what would be done
        """
        logger.info(f"Starting Gmail AI Agent in {mode} mode (dry_run: {dry_run})...")
        
        try:
            previous_check_time = self.last_check_time
            self.last_check_time = time.time()
            messages = self.gmail_client.get_unread_messages(
                max_results=settings.max_emails_to_process,
                since_time=previous_check_time
            )
            new_messages = [
                msg for msg in messages 
                if msg['id'] not in self.processed_messages
            ]
            
            if not new_messages:
                logger.info("No new unread messages found")
                return
            
            processed_count = 0
            
            for message in new_messages:
                logger.info(f"Processing new message from {message['sender']}")
                
                intent = self.groq_client.analyze_email_intent(
                    message['subject'], 
                    message['body'],
                    sender=message['sender']
                )
                logger.info(f"Email intent: {intent}")
                
                if intent in ['SPAM']:
                    logger.info("Skipping spam email")
                    self.processed_messages.add(message['id'])
                    continue
                
                reply = self.groq_client.generate_reply(
                    sender=message['sender'],
                    subject=message['subject'],
                    body=message['body'],
                    context=f"Email category: {intent}"
                )
                
                if reply:
                    logger.info(f"Generated reply: {reply[:100]}...")
                    
                    if dry_run:
                        logger.info("DRY RUN MODE - Reply not sent/saved")
                        self._log_reply_details(message, reply, intent, mode)
                    else:
                        sender_email = self._extract_email_address(message['sender'])
                        
                        if mode == "auto":
                            success = self.gmail_client.send_reply(
                                thread_id=message['thread_id'],
                                to_email=sender_email,
                                subject=message['subject'],
                                body=reply
                            )
                            
                            if success:
                                self.gmail_client.mark_as_read(message['id'])
                                logger.info(f"Reply sent automatically and message marked as read")
                                processed_count += 1
                        
                        elif mode == "draft":
                            success = self.gmail_client.save_as_draft(
                                thread_id=message['thread_id'],
                                to_email=sender_email,
                                subject=message['subject'],
                                body=reply
                            )
                            
                            if success:
                                logger.info(f"Reply saved as draft for manual review")
                                processed_count += 1
                
                self.processed_messages.add(message['id'])
                
                time.sleep(2)
            
            self._save_processed_messages()
            
            logger.info(f"Processed {processed_count} new messages successfully")
                
        except Exception as error:
            logger.error(f"Error in agent execution: {error}")
    
    def run_auto_reply(self, dry_run: bool = False):
        """Run agent in automatic reply mode"""
        self.run_agent(mode="auto", dry_run=dry_run)
    
    def run_draft_mode(self, dry_run: bool = False):
        """Run agent in draft mode - saves replies as drafts for manual review"""
        self.run_agent(mode="draft", dry_run=dry_run)
    
    def _extract_email_address(self, sender_string: str) -> str:
        """Extract email address from sender string"""
        if '<' in sender_string and '>' in sender_string:
            return sender_string.split('<')[1].split('>')[0]
        return sender_string
    
    def _log_reply_details(self, message: Dict, reply: str, intent: str, mode: str):
        """Log reply details for review"""
        logger.info("=" * 80)
        logger.info(f"MODE: {mode.upper()}")
        logger.info(f"FROM: {message['sender']}")
        logger.info(f"SUBJECT: {message['subject']}")
        logger.info(f"INTENT: {intent}")
        logger.info(f"ORIGINAL MESSAGE:\n{message['body'][:200]}...")
        logger.info(f"GENERATED REPLY:\n{reply}")
        logger.info("=" * 80)
    
    def monitor_continuously(self, mode: str = "auto", interval_minutes: int = 5):
        """
        Continuously monitor for new emails
        
        Args:
            mode: "auto" for automatic replies, "draft" for saving as drafts
            interval_minutes: How often to check for new emails
        """
        logger.info(f"Starting continuous monitoring in {mode} mode (checking every {interval_minutes} minutes)")
        
        while True:
            try:
                self.run_agent(mode=mode, dry_run=False)
                logger.info(f"Sleeping for {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as error:
                logger.error(f"Error in continuous monitoring: {error}")
                time.sleep(60)
    
    def clear_processed_history(self):
        """Clear the history of processed messages"""
        self.processed_messages.clear()
        self._save_processed_messages()
        logger.info("Cleared processed messages history")
    
    def get_stats(self):
        """Get statistics about processed messages"""
        stats = {
            'total_processed': len(self.processed_messages),
            'history_file_exists': os.path.exists(self.processed_messages_file)
        }
        
        if stats['history_file_exists']:
            try:
                with open(self.processed_messages_file, 'r') as f:
                    data = json.load(f)
                    stats['last_updated'] = data.get('last_updated', 'Unknown')
            except:
                stats['last_updated'] = 'Error reading file'
        
        return stats