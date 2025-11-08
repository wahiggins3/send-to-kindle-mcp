#!/usr/bin/env python3
"""
Standalone SMTP connection test script.

This script tests your SMTP configuration independently of Claude Desktop
to help debug authentication issues.
"""

import os
import smtplib
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_smtp_connection():
    """Test SMTP connection and authentication."""
    print("=" * 60)
    print("SMTP Connection Test")
    print("=" * 60)
    
    # Get configuration
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port_str = os.getenv("SMTP_PORT", "587")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    kindle_email = os.getenv("KINDLE_EMAIL")
    from_email = os.getenv("FROM_EMAIL", smtp_user)
    
    # Display configuration (mask password)
    print("\nConfiguration:")
    print(f"  SMTP_HOST: {smtp_host}")
    print(f"  SMTP_PORT: {smtp_port_str}")
    print(f"  SMTP_USER: {smtp_user}")
    print(f"  SMTP_PASSWORD: {'*' * len(smtp_password) if smtp_password else 'NOT SET'}")
    print(f"  KINDLE_EMAIL: {kindle_email}")
    print(f"  FROM_EMAIL: {from_email}")
    
    # Validate configuration
    print("\n" + "=" * 60)
    print("Validating Configuration...")
    print("=" * 60)
    
    missing = []
    if not smtp_host:
        missing.append("SMTP_HOST")
    if not smtp_user:
        missing.append("SMTP_USER")
    if not smtp_password:
        missing.append("SMTP_PASSWORD")
    if not kindle_email:
        missing.append("KINDLE_EMAIL")
    
    if missing:
        print(f"\n❌ ERROR: Missing configuration: {', '.join(missing)}")
        print("\nMake sure your .env file contains all required variables.")
        return False
    
    # Validate port
    try:
        smtp_port = int(smtp_port_str)
    except ValueError:
        print(f"\n❌ ERROR: Invalid SMTP_PORT value '{smtp_port_str}'. Must be a number.")
        return False
    
    print("✅ All required configuration present")
    
    # Test connection
    print("\n" + "=" * 60)
    print("Testing SMTP Connection...")
    print("=" * 60)
    
    try:
        print(f"\n1. Connecting to {smtp_host}:{smtp_port}...")
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        print("   ✅ Connection established")
        
        print("\n2. Starting TLS encryption...")
        server.starttls()
        print("   ✅ TLS started successfully")
        
        print(f"\n3. Attempting to authenticate as {smtp_user}...")
        print("   (This may take a few seconds...)")
        server.login(smtp_user, smtp_password)
        print("   ✅ Authentication successful!")
        
        print("\n4. Closing connection...")
        server.quit()
        print("   ✅ Connection closed")
        
        print("\n" + "=" * 60)
        print("✅ SUCCESS: All tests passed!")
        print("=" * 60)
        print("\nYour SMTP configuration is working correctly.")
        print("If you're still having issues in Claude Desktop, try restarting it.")
        return True
        
    except smtplib.SMTPConnectError as e:
        print(f"\n❌ ERROR: Could not connect to SMTP server")
        print(f"   Details: {e}")
        print("\nTroubleshooting:")
        print("  - Check your internet connection")
        print("  - Verify SMTP_HOST and SMTP_PORT are correct")
        print("  - For Gmail: smtp.gmail.com:587")
        return False
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ ERROR: Authentication failed")
        print(f"   Details: {e}")
        print("\nCommon causes:")
        print("  - Using regular password instead of App Password (for Gmail)")
        print("  - App Password is incorrect or expired")
        print("  - 2FA not enabled (required for App Passwords)")
        print("  - Username/email address is incorrect")
        print("\nFor Gmail App Passwords:")
        print("  1. Go to https://myaccount.google.com/apppasswords")
        print("  2. Generate a new App Password for 'Mail'")
        print("  3. Copy the 16-character password (no spaces)")
        print("  4. Use this password in your .env file")
        return False
        
    except smtplib.SMTPException as e:
        print(f"\n❌ ERROR: SMTP error occurred")
        print(f"   Details: {e}")
        print(f"   Error code: {e.smtp_code if hasattr(e, 'smtp_code') else 'N/A'}")
        print(f"   Error message: {e.smtp_error if hasattr(e, 'smtp_error') else str(e)}")
        return False
        
    except Exception as e:
        print(f"\n❌ ERROR: Unexpected error")
        print(f"   Type: {type(e).__name__}")
        print(f"   Details: {e}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_smtp_connection()
    sys.exit(0 if success else 1)

