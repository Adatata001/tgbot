#!/usr/bin/env python3
"""
Supabase Database Setup Script
==============================

This script creates all necessary tables in your Supabase database.

Usage:
1. Open your Supabase dashboard: https://app.supabase.com/
2. Go to SQL Editor
3. Create a new query
4. Copy and paste the SQL from this script
5. Click "Run"

Or run this script to see the SQL:
    python migrate_supabase.py
"""

import os
from pathlib import Path

# SQL Schema to create all tables
SQL_SCHEMA = """
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

CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_users_is_premium ON users(is_premium);

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

CREATE INDEX IF NOT EXISTS idx_analyses_user_id ON analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at DESC);

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

-- File Uploads Table (NEW - For screenshots/videos/strategy files)
CREATE TABLE IF NOT EXISTS file_uploads (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  file_id VARCHAR(255) NOT NULL,
  file_name VARCHAR(255),
  file_type VARCHAR(50),
  file_size INTEGER,
  upload_type VARCHAR(50),
  analysis_result TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_uploads_user_id ON file_uploads(user_id);
CREATE INDEX idx_uploads_type ON file_uploads(upload_type);

CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);

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

CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_created_at ON trades(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);

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

CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);

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

CREATE INDEX IF NOT EXISTS idx_signals_user_id ON tradingview_signals(user_id);
CREATE INDEX IF NOT EXISTS idx_signals_symbol ON tradingview_signals(symbol);

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

CREATE INDEX IF NOT EXISTS idx_market_data_symbol ON market_data(symbol);
CREATE INDEX IF NOT EXISTS idx_market_data_updated_at ON market_data(updated_at DESC);

-- Feedback Table
CREATE TABLE IF NOT EXISTS feedback (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  analysis_id BIGINT REFERENCES analyses(id) ON DELETE SET NULL,
  rating INTEGER CHECK (rating >= 1 AND rating <= 5),
  comment TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id);
"""


def print_setup_instructions():
    """Print setup instructions"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║           SUPABASE DATABASE SETUP INSTRUCTIONS                ║
╚════════════════════════════════════════════════════════════════╝

STEP 1: Open Supabase Dashboard
  → Go to: https://app.supabase.com
  → Select your project: muvqwpyridjbxmnqkeal
  → Click "SQL Editor" in the left menu

STEP 2: Create Database Tables
  → Click "New Query"
  → Copy and paste the SQL below:
  
""")
    print("─" * 70)
    print(SQL_SCHEMA)
    print("─" * 70)
    
    print("""
  → Click "Run" button
  → Wait for completion ✅

STEP 3: Verify Tables Created
  → Go to "Table Editor" in the left menu
  → You should see:
    ✅ users
    ✅ analyses
    ✅ payments
    ✅ trades
    ✅ subscriptions
    ✅ tradingview_signals
    ✅ market_data
    ✅ feedback

STEP 4: Your Bot is Ready!
  → Run: python main.py
  → Bot will automatically use Supabase
  → Data will persist across restarts

⚠️  IMPORTANT: Do NOT share your API key publicly!

════════════════════════════════════════════════════════════════
""")


def save_sql_to_file():
    """Save SQL schema to a file"""
    output_file = Path(__file__).parent / "supabase_schema.sql"
    with open(output_file, "w") as f:
        f.write(SQL_SCHEMA)
    print(f"✅ SQL schema saved to: {output_file}")


if __name__ == "__main__":
    print("\n")
    print_setup_instructions()
    save_sql_to_file()
