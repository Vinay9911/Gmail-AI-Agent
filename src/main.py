import sys
import os
import argparse
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.ai_agent import GmailAIAgent
from config.settings import settings

def setup_logging():
    """Setup logging configuration"""
    Path(settings.log_file).parent.mkdir(exist_ok=True)
    
    logger.remove()
    
    logger.add(
        settings.log_file,
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="30 days"
    )
    
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description='Gmail AI Agent - Process only new emails')
    
    parser.add_argument('--mode', choices=['auto', 'draft', 'monitor-auto', 'monitor-draft'], 
                       default='draft',
                       help='Operation mode:\n'
                            'auto: Automatically send replies to new emails\n'
                            'draft: Save replies as drafts for manual review\n'
                            'monitor-auto: Continuously monitor and auto-reply\n'
                            'monitor-draft: Continuously monitor and save as drafts')
    
    parser.add_argument('--dry-run', action='store_true',
                       help='Run in dry-run mode (generate replies but don\'t send/save)')
    parser.add_argument('--interval', type=int, default=1,
                       help='Monitoring interval in minutes for monitor modes (default: 1)')
    
    parser.add_argument('--clear-history', action='store_true',
                       help='Clear the history of processed messages')
    parser.add_argument('--stats', action='store_true',
                       help='Show statistics about processed messages')
    parser.add_argument('--list-drafts', action='store_true',
                       help='List current draft messages')
    
    args = parser.parse_args()
    
    setup_logging()
    
    logger.info("Gmail AI Agent starting...")
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Dry-run: {args.dry_run}")
    
    try:
        agent = GmailAIAgent()
        
        if args.clear_history:
            agent.clear_processed_history()
            logger.info("Processed messages history cleared")
            return
        
        if args.stats:
            stats = agent.get_stats()
            logger.info("=== AGENT STATISTICS ===")
            logger.info(f"Total processed messages: {stats['total_processed']}")
            logger.info(f"History file exists: {stats['history_file_exists']}")
            if 'last_updated' in stats:
                logger.info(f"Last updated: {stats['last_updated']}")
            return
        
        if args.list_drafts:
            drafts = agent.gmail_client.get_drafts()
            logger.info(f"=== DRAFT MESSAGES ({len(drafts)}) ===")
            for i, draft in enumerate(drafts, 1):
                logger.info(f"{i}. TO: {draft['to']}")
                logger.info(f"   SUBJECT: {draft['subject']}")
                logger.info(f"   DRAFT ID: {draft['draft_id']}")
                logger.info(f"   BODY: {draft['body'][:100]}...")
                logger.info("   " + "-"*50)
            return
        
        if args.mode == 'auto':
            logger.info("Running in AUTO mode - will send replies automatically")
            agent.run_auto_reply(dry_run=args.dry_run)
            
        elif args.mode == 'draft':
            logger.info("Running in DRAFT mode - will save replies as drafts")
            agent.run_draft_mode(dry_run=args.dry_run)
            
        elif args.mode == 'monitor-auto':
            logger.info(f"Starting continuous monitoring in AUTO mode (interval: {args.interval} min)")
            agent.monitor_continuously(mode="auto", interval_minutes=args.interval)
            
        elif args.mode == 'monitor-draft':
            logger.info(f"Starting continuous monitoring in DRAFT mode (interval: {args.interval} min)")
            agent.monitor_continuously(mode="draft", interval_minutes=args.interval)
            
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as error:
        logger.error(f"Application error: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()