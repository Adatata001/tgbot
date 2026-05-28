"""
Project README
"""

# 🤖 Trading Bot Pro

An AI-powered Telegram bot for professional trading strategy analysis, market insights, and risk management.

## Features

### 🔍 Strategy Analyzer
- AI-powered analysis of trading strategies
- Identifies strengths, weaknesses, and market suitability
- Risk assessment for each strategy
- Professional, trader-focused insights

### 📊 Market Intelligence
- Real-time market data (BTC, ETH, SOL, and more)
- AI market summaries
- Price movements and trends
- Market sentiment analysis

### ⚠️ Risk Management
- Position size calculator
- Stop loss recommendations
- Risk/reward analysis
- Leverage assessment

### 💎 Premium System
- Free tier: 5 analyses per day
- Premium: Unlimited access
- Coming soon: Portfolio analytics and custom alerts

## Tech Stack

- **Bot Framework**: aiogram 3.4.1
- **AI**: OpenAI GPT-4
- **Market Data**: CoinGecko API, Binance API
- **Backend**: Python
- **Storage**: In-memory (upgrade to database for production)

## Quick Start

### Prerequisites
- Python 3.8+
- Telegram Bot Token
- OpenAI API Key

### Installation

1. Clone the repository:
```bash
git clone <repo>
cd tgbot
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Setup environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials:
# - TELEGRAM_BOT_TOKEN
# - OPENAI_API_KEY
```

5. Run the bot:
```bash
python main.py
```

## Configuration

Edit `.env` file with your settings:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
OPENAI_API_KEY=your_openai_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
ADMIN_IDS=your_telegram_id
FREE_ANALYSES_PER_DAY=5
```

## Project Structure

```
tgbot/
├── main.py                 # Bot entry point
├── config.py              # Configuration
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
└── app/
    ├── handlers/
    │   ├── start.py      # /start and /help commands
    │   ├── analyze.py    # Strategy analysis
    │   ├── market.py     # Market summaries
    │   └── help.py       # Risk calculator and premium
    ├── services/
    │   ├── openai_service.py      # OpenAI integration
    │   └── market_service.py      # Market data
    ├── models/
    │   ├── user.py       # User model
    │   └── analysis.py   # Analysis model
    ├── utils/
    │   ├── user_manager.py        # User management
    │   └── analytics_limiter.py   # Rate limiting
    └── keyboards/
        └── main_menu.py  # Telegram keyboards
```

## Commands

- `/start` - Start the bot
- `/analyze` - Analyze a trading strategy
- `/market` - Get market summary
- `/risk` - Calculate trade risk
- `/help` - Show help message

## How to Use

### Analyze Strategy
1. Click "🔍 Analyze Strategy"
2. Describe your trading strategy
3. (Optional) Add trading rules
4. (Optional) Provide market context
5. Get AI analysis with strengths, weaknesses, and risk assessment

### Market Summary
1. Click "📊 Market Summary"
2. Select assets (BTC, ETH, SOL, or multiple)
3. Receive AI-powered market analysis with current prices

### Risk Calculator
1. Click "⚠️ Risk Calculator"
2. Describe your trade setup
3. Enter position size and leverage
4. Get risk analysis with recommendations

## Premium Features

### Free Tier
- 5 strategy analyses per day
- Basic market data
- Risk calculations

### Premium
- Unlimited analyses
- Advanced portfolio analytics
- Priority support
- Coming soon: Custom alerts

## API Integration

### OpenAI
Uses GPT-4 for professional strategy analysis and market insights.

### Market Data
- **CoinGecko API**: Free, no authentication required
- **Binance API**: Optional, for advanced features

### Future Integrations
- Supabase for user database
- TradingView webhooks for alert integration
- Portfolio management system

## Roadmap

### Phase 1 ✅ (Current)
- Core bot setup
- AI strategy analyzer
- Market summaries
- Risk calculator

### Phase 2
- Database integration (Supabase/PostgreSQL)
- User authentication and profiles
- Analysis history

### Phase 3
- Premium payment system
- Portfolio tracking
- Advanced analytics

### Phase 4
- TradingView integration
- Trading signals
- Automated alerts

## Performance Tips

- Free users: 5 analyses/day (to manage OpenAI costs)
- Premium users: Unlimited (premium pricing covers costs)
- Market data: Cached for 5 minutes
- User data: In-memory (upgrade to database)

## Error Handling

- Graceful error messages for failed API calls
- User-friendly error notifications
- Logging for debugging

## Security

- API keys stored in `.env` (never committed)
- No sensitive data logged
- Environment-based configuration

## Deployment

### Local Development
```bash
python main.py
```

### Production (Railway)
1. Connect GitHub repository
2. Deploy with `python main.py`
3. Set environment variables in Railway dashboard
4. Bot runs continuously

### Alternative Hosting
- Render
- Heroku
- DigitalOcean
- AWS Lambda

## Troubleshooting

### Bot not responding
- Check TELEGRAM_BOT_TOKEN in .env
- Verify bot is running: `python main.py`

### OpenAI errors
- Check OPENAI_API_KEY is valid
- Verify account has available credits
- Check API rate limits

### Market data errors
- CoinGecko API might be rate limited
- Verify internet connection
- Check symbol mapping

## Contributing

Contributions welcome! Please:
1. Fork repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## License

MIT License - see LICENSE file

## Support

For issues or questions:
- Check README and /help command
- Review error messages
- Check logs for debugging

## Roadmap Features

- [ ] Database integration
- [ ] Payment system
- [ ] Portfolio tracking
- [ ] TradingView webhooks
- [ ] Advanced ML analytics
- [ ] Multi-language support
- [ ] Mobile app
- [ ] Desktop dashboard

---

**Built with ❤️ for traders**
