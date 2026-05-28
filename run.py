#!/usr/bin/env python3
"""
Development run script with auto-reload
"""
import os
import sys
import time
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Verify configuration
if not os.getenv("TELEGRAM_BOT_TOKEN"):
    print("❌ Error: TELEGRAM_BOT_TOKEN not set in .env")
    sys.exit(1)

if not os.getenv("OPENAI_API_KEY"):
    print("❌ Error: OPENAI_API_KEY not set in .env")
    sys.exit(1)

print("✅ Configuration verified")
print(f"🤖 Starting Trading Bot Pro...")
print(f"📱 Bot: @Eneh_bot")
print()

# Run main.py
try:
    subprocess.run([sys.executable, "main.py"])
except KeyboardInterrupt:
    print("\n❌ Bot stopped")
    sys.exit(0)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
