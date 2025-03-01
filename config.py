"""
Configuration Module

This module loads environment variables and defines global configuration settings 
for the application, such as database connection details, authentication settings.

Dependencies:
    - dotenv for loading environment variables
    - logging for application warnings
"""
import os
import logging
from dotenv import load_dotenv, find_dotenv
from datetime import datetime, timedelta, timezone

# Load environment variables from the .env file
if not load_dotenv(find_dotenv()):
    raise RuntimeError("Missing .env file!")

# -----------------------------------
# Database Configuration
# -----------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test.db")

# -----------------------------------
# Security Configuration
# -----------------------------------
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = "secretkey123"  # Use a fixed fallback or generate manually
    logging.info("!!!WARNING!!!: SECRET_KEY is not set in .env! Using an insecure default.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 3000
