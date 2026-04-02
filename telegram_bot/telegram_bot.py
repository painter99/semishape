"""
SemiShape Telegram Bot

Telegram bot interface for SemiShape CAD assistant.
Allows users to generate build123d models from text descriptions via Telegram.

Usage:
    python -m telegram.telegram_bot

Environment variables:
    TELEGRAM_BOT_TOKEN: Bot token from @BotFather
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv("/a0/usr/.env", override=True)

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("Warning: python-telegram-bot not installed. Run: pip install python-telegram-bot")

from src.semishape import SemiShape


class SemiShapeBot:
    """Telegram bot for SemiShape CAD assistant."""
    
    def __init__(self, token: str):
        self.token = token
        self.semishape = SemiShape(language="cs")
        self.app = Application.builder().token(token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up bot command handlers."""
        self.app.add_handler(CommandHandler("start", self._cmd_start))
        self.app.add_handler(CommandHandler("help", self._cmd_help))
        self.app.add_handler(CommandHandler("gen", self._cmd_generate))
        self.app.add_handler(CommandHandler("en", self._cmd_english))
        self.app.add_handler(CommandHandler("cs", self._cmd_czech))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
    
    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome = (
            "🏗️ *SemiShape CAD Assistant*\\n\\n"
            "Vítejte! Jsem AI asistent pro vytváření 3D CAD modelů.\\n\\n"
            "*Jak mě použít:*\\n"
            "1. Napište popis modelu (česky nebo anglicky)\\n"
            "2. Já vygeneruji build123d Python kód\\n"
            "3. Spustím kód a vytvořím STL soubor\\n\\n"
            "*Příkazy:*\\n"
            "/gen <popis> – Generovat model\\n"
            "/cs – Přepnout do češtiny\\n"
            "/en – Switch to English\\n"
            "/help – Zobrazit nápovědu"
        )
        await update.message.reply_text(welcome, parse_mode="Markdown")
    
    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = (
            "📚 *Nápověda SemiShape*\\n\\n"
            "*Příklady příkazů:*\\n"
            "• Vytvoř kvádr 80x60x10mm s dírou uprostřed\\n"
            "• Create a cylinder with diameter 50mm and height 100mm\\n"
            "• Udělej držák na kabel s výřezem 20mm\\n\\n"
            "*Tipy:*\\n"
            "• Buďte konkrétní s rozměry\\n"
            "• Používejte jednoduché tvary jako základ\\n"
            "• Specifikujte materiál/účel pro lepší výsledky"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    async def _cmd_czech(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Switch to Czech language."""
        self.semishape = SemiShape(language="cs")
        await update.message.reply_text("✅ Přepnuto do českého jazyka.")
    
    async def _cmd_english(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Switch to English language."""
        self.semishape = SemiShape(language="en")
        await update.message.reply_text("✅ Switched to English language.")
    
    async def _cmd_generate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /gen command with inline prompt."""
        if not context.args:
            await update.message.reply_text("❌ Použití: /gen <popis modelu>")
            return
        
        prompt = " ".join(context.args)
        await self._process_request(update, prompt)
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages as generation requests."""
        prompt = update.message.text
        await self._process_request(update, prompt)
    
    async def _process_request(self, update: Update, prompt: str):
        """Process a generation request."""
        status_msg = await update.message.reply_text("⏳ Zpracovávám požadavek...")
        
        try:
            # Generate code
            await status_msg.edit_text("📝 Generuji kód...")
            result = self.semishape.generate_code(prompt)
            
            if not result.success:
                await status_msg.edit_text(f"❌ Chyba: {result.error}")
                return
            
            # Send generated code
            code_preview = result.code[:500] + "..." if len(result.code) > 500 else result.code
            await update.message.reply_text(
                f"```python\\n{code_preview}\\n```",
                parse_mode="Markdown"
            )
            
            # Execute and export
            await status_msg.edit_text("🔧 Spouštím kód a exportuji STL...")
            exec_result = self.semishape.generate_and_execute(prompt, export_format="stl")
            
            if exec_result.get("success") and exec_result.get("output_file"):
                # Send STL file
                output_path = Path(exec_result["output_file"])
                if output_path.exists():
                    await update.message.reply_document(
                        document=open(output_path, "rb"),
                        filename=output_path.name,
                        caption="✅ Model připraven!"
                    )
                    await status_msg.delete()
                else:
                    await status_msg.edit_text("❌ Soubor se nepodařilo vytvořit.")
            else:
                error = exec_result.get("error", "Neznámá chyba")
                await status_msg.edit_text(f"❌ Chyba při spouštění: {error}")
                
        except Exception as e:
            await status_msg.edit_text(f"❌ Chyba: {str(e)}")
    
    def run(self):
        """Start the bot."""
        print("🤖 SemiShape Telegram Bot starting...")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Main entry point."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not set.")
        print("\\nTo get a token:")
        print("1. Open Telegram and search for @BotFather")
        print("2. Send /newbot and follow instructions")
        print("3. Copy the token and set it:")
        print("   export TELEGRAM_BOT_TOKEN='your-token-here'")
        sys.exit(1)
    
    if not TELEGRAM_AVAILABLE:
        print("Error: python-telegram-bot not installed.")
        print("Run: pip install python-telegram-bot")
        sys.exit(1)
    
    bot = SemiShapeBot(token)
    bot.run()


if __name__ == "__main__":
    main()
