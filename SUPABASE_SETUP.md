"""
SUPABASE INTEGRATION - COMPLETE GUIDE
======================================

WHAT YOU NEED FOR SUPABASE
==========================

✅ PREREQUISITES:

1. Supabase Account
   - Sign up at supabase.com (free)
   - Create new project
   - Get URL and API key

2. Python Installation
   - pip install supabase

3. Environment Variables
   - SUPABASE_URL
   - SUPABASE_KEY


STEP-BY-STEP SETUP
==================

STEP 1: Create Supabase Account

1. Go to supabase.com
2. Click "Start your project"
3. Sign up with GitHub/Email
4. Create new organization
5. Create new project
   - Name: trading-bot
   - Database password: (save securely)
   - Region: (choose closest)
6. Wait for setup (2-5 minutes)


STEP 2: Get Credentials

1. Go to Project Settings
2. Find API section
3. Copy:
   - URL: https://[project-id].supabase.co
   - Public Key (anon): anon_...

4. Add to .env:
   SUPABASE_URL=https://[project-id].supabase.co
   SUPABASE_KEY=anon_key_here


STEP 3: Create Database Tables

In Supabase Dashboard:
1. Go to SQL Editor
2. Create new query
3. Copy/paste SQL schema below
4. Execute each table creation


COMPLETE SQL SCHEMA:
====================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users Table
CREATE TABLE IF NOT EXISTS users (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT UNIQUE NOT NULL,
  username VARCHAR(255),
  first_name VARCHAR(255),
  last_name VARCHAR(255),
  is_premium BOOLEAN DEFAULT FALSE,
  premium_until TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  analysis_count_today INTEGER DEFAULT 0,
  total_analyses INTEGER DEFAULT 0,
  total_pnl DECIMAL(20, 2) DEFAULT 0,
  profile JSONB DEFAULT '{}'
);

CREATE INDEX idx_users_user_id ON users(user_id);
CREATE INDEX idx_users_is_premium ON users(is_premium);

-- Analyses Table
CREATE TABLE IF NOT EXISTS analyses (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  strategy_description TEXT NOT NULL,
  analysis_result TEXT NOT NULL,
  market_conditions TEXT,
  tokens_used INTEGER,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_analyses_user_id ON analyses(user_id);
CREATE INDEX idx_analyses_created_at ON analyses(created_at DESC);

-- Payments Table
CREATE TABLE IF NOT EXISTS payments (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  amount_stars INTEGER NOT NULL,
  plan_duration INTEGER NOT NULL,
  payment_id VARCHAR(255) UNIQUE,
  transaction_id VARCHAR(255),
  status VARCHAR(50) DEFAULT 'completed',
  method VARCHAR(50) DEFAULT 'telegram_stars',
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_payments_status ON payments(status);

-- Trades Table
CREATE TABLE IF NOT EXISTS trades (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  symbol VARCHAR(20) NOT NULL,
  trade_type VARCHAR(20) NOT NULL,
  entry_price DECIMAL(20, 8) NOT NULL,
  exit_price DECIMAL(20, 8),
  position_size DECIMAL(20, 8) NOT NULL,
  pnl DECIMAL(20, 2),
  pnl_percent DECIMAL(10, 2),
  emotions VARCHAR(100),
  notes TEXT,
  entry_time TIMESTAMP WITH TIME ZONE,
  exit_time TIMESTAMP WITH TIME ZONE,
  status VARCHAR(50) DEFAULT 'open',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_trades_user_id ON trades(user_id);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_created_at ON trades(created_at DESC);
CREATE INDEX idx_trades_status ON trades(status);

-- Subscriptions Table
CREATE TABLE IF NOT EXISTS subscriptions (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
  plan VARCHAR(50) DEFAULT 'free',
  status VARCHAR(50) DEFAULT 'active',
  started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  expires_at TIMESTAMP WITH TIME ZONE,
  auto_renew BOOLEAN DEFAULT TRUE,
  renewal_date TIMESTAMP WITH TIME ZONE,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);

-- TradingView Signals Table
CREATE TABLE IF NOT EXISTS tradingview_signals (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(user_id) ON DELETE SET NULL,
  symbol VARCHAR(20) NOT NULL,
  action VARCHAR(20) NOT NULL,
  price DECIMAL(20, 8) NOT NULL,
  timeframe VARCHAR(10),
  confidence DECIMAL(3, 2),
  analysis TEXT,
  acknowledged BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_signals_user_id ON tradingview_signals(user_id);
CREATE INDEX idx_signals_symbol ON tradingview_signals(symbol);

-- Market Data Cache Table
CREATE TABLE IF NOT EXISTS market_data (
  id BIGSERIAL PRIMARY KEY,
  symbol VARCHAR(20) NOT NULL,
  price DECIMAL(20, 8),
  market_cap DECIMAL(20, 2),
  volume_24h DECIMAL(20, 2),
  change_24h DECIMAL(10, 2),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_market_data_symbol ON market_data(symbol);
CREATE INDEX idx_market_data_updated_at ON market_data(updated_at DESC);

-- Feedback Table
CREATE TABLE IF NOT EXISTS feedback (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  analysis_id BIGINT REFERENCES analyses(id) ON DELETE SET NULL,
  rating INTEGER CHECK (rating >= 1 AND rating <= 5),
  comment TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_feedback_user_id ON feedback(user_id);


PYTHON INTEGRATION
==================

Installation:
pip install supabase

Example: User Management

from supabase import create_client
import os
from datetime import datetime, timedelta

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Create/Update User
def create_user(user_id, username):
    response = supabase.table("users").upsert({
        "user_id": user_id,
        "username": username,
        "created_at": datetime.now().isoformat()
    }).execute()
    return response.data

# Get User
def get_user(user_id):
    response = supabase.table("users").select("*").eq(
        "user_id", user_id
    ).single().execute()
    return response.data

# Update to Premium
def upgrade_to_premium(user_id, months=1):
    premium_until = (
        datetime.now() + timedelta(days=30*months)
    ).isoformat()
    
    response = supabase.table("users").update({
        "is_premium": True,
        "premium_until": premium_until
    }).eq("user_id", user_id).execute()
    
    return response.data

# Log Trade
def log_trade(user_id, symbol, entry, exit, size, pnl):
    response = supabase.table("trades").insert({
        "user_id": user_id,
        "symbol": symbol,
        "entry_price": entry,
        "exit_price": exit,
        "position_size": size,
        "pnl": pnl,
        "status": "closed"
    }).execute()
    return response.data

# Get User Trades
def get_user_trades(user_id, limit=50):
    response = supabase.table("trades").select("*").eq(
        "user_id", user_id
    ).order("created_at", desc=True).limit(limit).execute()
    return response.data

# Get Performance Stats
def get_user_stats(user_id):
    response = supabase.table("trades").select("*").eq(
        "user_id", user_id
    ).execute()
    
    trades = response.data
    if not trades:
        return {"total_trades": 0, "total_pnl": 0}
    
    total_pnl = sum([t["pnl"] for t in trades if t["pnl"]])
    winning = len([t for t in trades if t["pnl"] and t["pnl"] > 0])
    
    return {
        "total_trades": len(trades),
        "total_pnl": total_pnl,
        "winning_trades": winning,
        "win_rate": (winning / len(trades) * 100) if trades else 0
    }


ROW-LEVEL SECURITY (RLS)
========================

Protect user data with RLS:

-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY "Users see own data"
  ON users FOR SELECT
  USING (user_id = current_user_id);

CREATE POLICY "Users update own data"
  ON users FOR UPDATE
  USING (user_id = current_user_id);

-- Trades policy
CREATE POLICY "Users see own trades"
  ON trades FOR SELECT
  USING (user_id = current_user_id);

CREATE POLICY "Users insert own trades"
  ON trades FOR INSERT
  WITH CHECK (user_id = current_user_id);


REAL-TIME SUBSCRIPTIONS
=======================

Subscribe to changes in real-time:

# Listen for premium status changes
def subscribe_to_user_updates(user_id):
    def callback(payload):
        print("User updated:", payload["new"])
    
    supabase.table("users").on(
        "UPDATE",
        lambda x: callback(x)
    ).eq("user_id", user_id).subscribe()


MIGRATION FROM IN-MEMORY
=========================

Strategy:
1. Keep UserManager working
2. Add Supabase functions alongside
3. Sync on-memory data to Supabase
4. Gradually migrate

Example Migration Function:

async def migrate_to_supabase():
    from app.utils import UserManager
    
    for user_id, user_data in UserManager.users.items():
        # Migrate user
        await create_user(
            user_id=user_id,
            username=user_data["username"]
        )
        
        # Migrate analyses (Phase 2)
        # Migrate trades (Phase 2)
    
    print("Migration complete!")


BACKUP & RECOVERY
=================

Automatic backups:
- Daily backups (7 days retention)
- Point-in-time recovery available
- Manual backups available

Export data:
1. Go to Backups section
2. Create manual backup
3. Download SQL dump


MONITORING & LOGGING
====================

View API usage:
1. Dashboard → API Health
2. Monitor response times
3. Track error rates

Logs:
1. Dashboard → Logs
2. Query logs available
3. Real-time monitoring


BEST PRACTICES
==============

✅ DO:
- Use indexes for frequent queries
- Implement RLS for security
- Cache frequently accessed data
- Use transactions for important operations
- Monitor API usage

❌ DON'T:
- Store sensitive data in text fields
- Run heavy queries frequently
- Skip error handling
- Use public key for admin operations
- Expose SUPABASE_KEY in frontend


COST OPTIMIZATION
=================

Free Tier: Perfect for MVP
- 500 MB storage
- 1 GB bandwidth/month
- Unlimited API calls
- Enough for 1000+ users

Paid Tier: When scaling
- $25/month base
- $0.125 per GB/month storage
- $0.125 per GB/month bandwidth


TROUBLESHOOTING
===============

Issue: "Invalid API key"
Solution: Check SUPABASE_KEY is public (anon) key, not secret

Issue: "Row level security violation"
Solution: Ensure RLS policies are set correctly

Issue: "Rate limit exceeded"
Solution: Implement caching, reduce API calls

Issue: "Connection timeout"
Solution: Check internet connection, Supabase status page


NEXT STEPS
==========

1. ✅ Setup Supabase account
2. ✅ Create database schema
3. ✅ Install supabase Python client
4. ✅ Migrate user data
5. ✅ Update bot to use Supabase
6. ✅ Implement RLS for security
7. ✅ Monitor and optimize


RESOURCES
=========

Supabase Docs: https://supabase.com/docs
Python Client: https://github.com/supabase/supabase-py
Database Functions: https://supabase.com/docs/guides/database/functions
Real-time: https://supabase.com/docs/guides/realtime


Ready to deploy! 🚀
"""
