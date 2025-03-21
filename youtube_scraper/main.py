#!/usr/bin/env python3
"""
YouTube Scraper for The Rollup Podcast
Main entry point for the YouTube scraper application
"""
import os
import sys

# Make sure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the youtube_scraper module
from youtube_scraper import main

if __name__ == "__main__":
    # Run the main function
    main() 