"""
Start command handler
"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from app.keyboards import get_main_keyboard
from app.utils import UserManager
from config import Config

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):
    """Handle /start command"""
    user_id = message.from_user.id
    username = message.from_user.username or "Trader"
    
    # Create or get user
    await UserManager.get_or_create_user(
        user_id=user_id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or "",
        last_name=message.from_user.last_name or "",
    )
    
    welcome_text = f"""
👋 Welcome to **Trading Bot Pro**, {username}!

I'm your AI-powered trading strategy analyst. I help traders like you:

🔍 **Analyze Strategies** - Get detailed breakdowns of your trading setups
📊 **Market Insights** - Real-time market summaries for crypto assets
⚠️ **Risk Management** - Calculate optimal position sizes and stop losses
💎 **Premium Features** - Unlimited analyses and advanced analytics

**What I do:**
- Professional strategy analysis
- Risk/reward assessments
- Market sentiment analysis
- Position sizing recommendations

**Free Tier:** 5 analyses per day
**Premium:** Unlimited access + advanced features

Let's get started! Choose an option below:
"""
    
    await message.answer(welcome_text, reply_markup=get_main_keyboard(Config.is_admin(message.from_user)))


@router.message(Command("help"))
async def help_handler(message: Message):
    """Handle /help command"""
    help_text = """
📚 **How to Use Trading Bot Pro**

**Available Commands:**
/start - Start the bot and see main menu
/help - Show this help message
/analyze - Analyze a trading strategy
/market - Get market summary
/risk - Calculate risk parameters
/pricing - View premium pricing
/profile - View your profile

**Features:**

🔍 **Strategy Analysis**
Send a description of your strategy and get AI-powered analysis covering:
- Strengths of your approach
- Potential weaknesses
- Risk assessment
- Market suitability rating

📊 **Market Summary**
Get real-time market insights for BTC, ETH, SOL, and other major assets including:
- Price movements
- Market sentiment
- Trading patterns

⚠️ **Risk Calculator**
Input your trade setup and get:
- Recommended stop loss levels
- Position sizing suggestions
- Risk/reward ratio analysis

💎 **Premium Features**
Unlimited analyses, advanced portfolio insights, and priority support.

**Tips for Best Results:**
- Be specific when describing your strategy
- Include entry and exit conditions
- Mention your risk tolerance
- Ask follow-up questions if needed

Need help? Feel free to ask questions anytime!
"""
    await message.answer(help_text, reply_markup=get_main_keyboard(Config.is_admin(message.from_user)))
