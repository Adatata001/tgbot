"""
Deployment Guide for Trading Bot Pro
"""

# DEPLOYMENT OPTIONS

## Option 1: Railway (RECOMMENDED - Easiest)

### Steps:
1. Push code to GitHub
2. Go to railway.app
3. Create new project -> Deploy from GitHub
4. Select repository
5. Set environment variables:
   - TELEGRAM_BOT_TOKEN
   - OPENAI_API_KEY
   - ADMIN_IDS
6. Deploy automatically

### Benefits:
- Free tier available
- Automatic deployments on push
- Easy scaling
- Good performance

### Cost:
- Free: $5/month credits
- Pay as you go after credits

---

## Option 2: Render

### Steps:
1. Go to render.com
2. Create new Web Service
3. Connect GitHub repository
4. Set Build Command: pip install -r requirements.txt
5. Set Start Command: python main.py
6. Add environment variables
7. Deploy

### Benefits:
- Free tier available
- Simple setup
- Auto-deploys on push

---

## Option 3: DigitalOcean Droplet

### Steps:
1. Create Ubuntu droplet ($6/month)
2. SSH into droplet
3. Install Python 3.9+
4. Clone repository
5. Setup virtual environment
6. Install dependencies
7. Use systemd to run bot continuously

### Commands:
```bash
ssh root@your_ip
apt update && apt upgrade
apt install python3.9 python3.9-venv git

git clone <your-repo>
cd tgbot
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create systemd service
sudo nano /etc/systemd/system/trading-bot.service
```

### Service file (/etc/systemd/system/trading-bot.service):
```ini
[Unit]
Description=Trading Bot Pro
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/tgbot
Environment="PATH=/root/tgbot/venv/bin"
ExecStart=/root/tgbot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Commands:
```bash
sudo systemctl daemon-reload
sudo systemctl start trading-bot
sudo systemctl enable trading-bot
sudo systemctl status trading-bot
```

---

## Option 4: AWS Lambda + API Gateway

### Setup:
- More complex
- Event-driven (webhooks instead of polling)
- Better scalability
- Higher cost for low volume

---

## Environment Variables for Production

Required:
```
TELEGRAM_BOT_TOKEN=your_token
OPENAI_API_KEY=your_key
ADMIN_IDS=your_id
```

Optional:
```
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
BINANCE_API_KEY=your_key
BINANCE_SECRET_KEY=your_secret
FREE_ANALYSES_PER_DAY=5
ENABLE_PREMIUM=true
```

---

## Monitoring

### Railway
- Built-in logs and metrics
- Automatic alerts available

### DigitalOcean
```bash
# Check logs
sudo journalctl -u trading-bot -f

# Monitor resources
htop
```

### Uptime Monitoring
- Use Uptime Robot (free)
- Monitor telegram connectivity
- Setup alerts

---

## Database Setup (Next Phase)

### Supabase
1. Create account at supabase.com
2. Create new project
3. Create tables:
   - users (user_id, username, is_premium, created_at)
   - analyses (user_id, strategy, analysis, created_at)
   - subscriptions (user_id, tier, expires_at)

4. Get credentials:
   - SUPABASE_URL
   - SUPABASE_KEY

5. Add to .env

---

## Scaling

### Phase 1: Current (Working)
- Single bot instance
- In-memory user storage
- Perfect for MVP

### Phase 2: Basic Production
- Database storage (Supabase)
- Multiple bot instances
- Redis for caching

### Phase 3: Advanced
- Multiple regions
- Load balancing
- Advanced caching
- Webhook instead of polling

---

## Cost Breakdown

### Current MVP Cost:
- Hosting: $6-20/month (Railway/Render free tier or DigitalOcean)
- OpenAI: Pay per token (~$0.001-0.01 per analysis)
- Domain: $10/year (optional)

### At Scale (1000 users):
- Hosting: $20-50/month
- OpenAI: $100-500/month (depends on usage)
- Database: $15-25/month

---

## Troubleshooting

### Bot stops after deployment
- Check logs for errors
- Verify TELEGRAM_BOT_TOKEN
- Ensure OPENAI_API_KEY has credits

### Slow responses
- Check OpenAI API latency
- Verify internet connection
- Consider upgrading plan

### High costs
- Implement caching
- Use cheaper APIs where possible
- Limit free tier analyses

---

## Next Steps

1. ✅ Develop locally
2. Push to GitHub
3. Deploy to Railway (quick test)
4. Monitor and optimize
5. Setup Supabase
6. Add payment system
7. Scale as needed
