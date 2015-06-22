"""
Demonstrates how to use the background scheduler to schedule a job that executes on 3 second intervals.
"""

from datetime import datetime
import time
import os
from code_scraper import GithubCodeScraper

from apscheduler.schedulers.background import BackgroundScheduler


def tick():
    print datetime.now()
    scraper = GithubCodeScraper(collection_name='python-repos')
    scraper.insert_code_into_repos()


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(tick, 'interval', hours=1, minutes=10)
    scheduler.start()
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

    try:
        # This is here to simulate application activity (which keeps the main thread alive).
        while True:
            time.sleep(2)
    except (KeyboardInterrupt):
        scheduler.shutdown()  # Not strictly necessary if daemonic mode is enabled but should be done if possible