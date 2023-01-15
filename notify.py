#!/usr/bin/env python3

import concurrent.futures
import requests

from monitor.arizmendi import ArizmendiMonitor
from monitor.standard_fare import StandardFareMonitor

if __name__ == "__main__":
    MAX_WORKERS = 10

    session = requests.Session()
    monitors = [
        StandardFareMonitor(session, keywords=["pork", "beet", "beets", "roast beef", "roastbeef", "sausage"]),
        ArizmendiMonitor(session, keywords=[
            ["roasted yellow potato", "leek", "parmesan", "garlic oil"]
        ])
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        executor.map(lambda m: m.process(), monitors)
