#!/usr/bin/env python3
"""
Configuration Verification Script
Run this to verify everything is set up correctly
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
END = '\033[0m'

def print_check(message, status):
    """Print a check result"""
    symbol = f"{GREEN}[OK]{END}" if status else f"{RED}[FAIL]{END}"
    print(f"{symbol} {message}")

def verify_env_file():
    """Verify .env file exists"""
    env_path = Path('.env')
    print(f"\n{BLUE}1. Checking .env file...{END}")
    print_check(".env file exists", env_path.exists())
    return env_path.exists()

def load_env():
    """Load environment variables"""
    load_dotenv()

def verify_config():
    """Verify configuration"""
    print(f"\n{BLUE}2. Checking configuration...{END}")
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    openai_key = os.getenv('OPENAI_API_KEY')
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    print_check("TELEGRAM_BOT_TOKEN set", bool(bot_token))
    print_check("AI key set (OpenRouter or OpenAI)", bool(openrouter_key or openai_key))
    print_check("SUPABASE_SERVICE_ROLE_KEY set", bool(supabase_service_key))
    
    if bot_token:
        print(f"   Bot ID: {bot_token.split(':')[0]}")
    if openrouter_key:
        print("   OpenRouter API key loaded")
    elif openai_key:
        print("   OpenAI API key loaded")
    
    return bool(bot_token and (openrouter_key or openai_key))

def verify_dependencies():
    """Verify dependencies are installed"""
    print(f"\n{BLUE}3. Checking dependencies...{END}")
    
    dependencies = {
        'aiogram': 'Telegram Bot Framework',
        'openai': 'OpenAI API Client',
        'dotenv': 'Environment Configuration',
        'aiohttp': 'Async HTTP Client',
        'requests': 'HTTP Library',
        'PyPDF2': 'PDF Text Extraction',
        'cv2': 'Video Frame Extraction',
    }
    
    all_installed = True
    for package, description in dependencies.items():
        try:
            __import__(package)
            print_check(f"{package} ({description})", True)
        except ImportError:
            print_check(f"{package} ({description})", False)
            all_installed = False
    
    return all_installed

def verify_project_structure():
    """Verify project structure"""
    print(f"\n{BLUE}4. Checking project structure...{END}")
    
    files = [
        ('main.py', 'Main bot file'),
        ('config.py', 'Configuration'),
        ('requirements.txt', 'Dependencies'),
        ('app/__init__.py', 'App package'),
        ('app/handlers/__init__.py', 'Handlers package'),
        ('app/services/__init__.py', 'Services package'),
        ('app/utils/__init__.py', 'Utils package'),
        ('app/models/__init__.py', 'Models package'),
        ('app/keyboards/__init__.py', 'Keyboards package'),
    ]
    
    all_exist = True
    for filepath, description in files:
        exists = Path(filepath).exists()
        print_check(f"{filepath} ({description})", exists)
        if not exists:
            all_exist = False
    
    return all_exist

def verify_imports():
    """Verify key imports work"""
    print(f"\n{BLUE}5. Checking imports...{END}")
    
    imports = [
        ('config', 'Configuration'),
        ('app.handlers', 'Handlers'),
        ('app.services', 'Services'),
        ('app.utils', 'Utils'),
    ]
    
    all_import = True
    for module, description in imports:
        try:
            __import__(module)
            print_check(f"{module} ({description})", True)
        except Exception as e:
            print_check(f"{module} ({description})", False)
            print(f"   Error: {str(e)}")
            all_import = False
    
    return all_import

def print_summary(all_checks):
    """Print summary"""
    print(f"\n{BLUE}{'='*60}{END}")
    if all_checks:
        print(f"{GREEN}ALL CHECKS PASSED!{END}")
        print(f"\n{YELLOW}You're ready to start the bot!{END}")
        print(f"\n{BLUE}Run:{END} python main.py")
    else:
        print(f"{RED}SOME CHECKS FAILED{END}")
        print(f"\n{YELLOW}Please fix the issues above and try again.{END}")
        print(f"\n{BLUE}Need help?{END} Check SETUP.md or README.md")
    print(f"\n{BLUE}{'='*60}{END}")

def main():
    """Main verification"""
    print(f"\n{BLUE}{'='*60}{END}")
    print(f"{BLUE}Trading Bot Pro - Configuration Verification{END}")
    print(f"{BLUE}{'='*60}{END}")
    
    all_checks = True
    
    # Run checks
    if not verify_env_file():
        print(f"{RED}Missing .env file!{END}")
        print(f"{YELLOW}Run: cp .env.example .env{END}")
        return False
    
    load_env()
    
    all_checks &= verify_config()
    all_checks &= verify_project_structure()
    all_checks &= verify_dependencies()
    all_checks &= verify_imports()
    
    print_summary(all_checks)
    return all_checks

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Verification interrupted{END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Error: {str(e)}{END}")
        sys.exit(1)
