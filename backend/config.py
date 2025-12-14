import os
from datetime import timedelta

class Config:
    """Base configuration"""
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///linkedin_insights.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
   
    JSON_SORT_KEYS = False
    
   
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
    
    
    SELENIUM_TIMEOUT = 10
    SCROLL_PAUSE_TIME = 2
    MAX_POSTS_TO_SCRAPE = 25
    MAX_EMPLOYEES_TO_SCRAPE = 50

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}