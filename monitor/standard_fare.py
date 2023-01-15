import re
import requests
from datetime import date
from bs4 import BeautifulSoup
from monitor.monitor import HtmlMonitor


class StandardFareMonitor(HtmlMonitor):
    def __init__(self, session: requests.Session, keywords: list = []):
        super(StandardFareMonitor, self).__init__(session)
        self.keywords = list(map(lambda k: k.lower(), keywords))

    def url(self) -> str:
        return "https://www.standardfareberkeley.com/lunch"

    def parse(self, html: BeautifulSoup) -> object:
        # Locate the general area of the menu's date by looking up the service
        # days which is always constant on the page.
        datetime_element = html.find("h2", string="Served Tuesday - Friday")
        if not datetime_element:
            return None

        # Look for the menu date now that we are in the general service days
        # area.
        date_element = datetime_element.find_next_siblings("h1")
        if not date_element or len(date_element) < 1:
            return None

        # If we find a sandwich name match, we will store it here.
        sandwich_match = None
        # Start by finding all the menu items with the word 'sandwich'. Then
        # filter for the items with a description to narrow the options down.
        sandwich_items = html.find_all("div", {"class": "menu-item-title"}, string=re.compile('sandwich', re.IGNORECASE))
        for sandwich_item in sandwich_items:
            sandwich_desc = sandwich_item.find_next_siblings("div", {"class": "menu-item-description"})
            if not sandwich_desc or len(sandwich_desc) < 1:
                continue

            # Check to see if any of the keywords exist in the names of the
            # filtered list of sandwiches.
            sandwich_item_str = sandwich_item.string.lower()
            for keyword in self.keywords:
                if keyword in sandwich_item_str:
                    sandwich_match = (sandwich_item_str, sandwich_desc[0].string)
                    break

            # Once we have found a sandwich with a matching keyword, we are done
            # and do not have to continue search.
            if sandwich_match:
                break

        # Whatever we return will be passed to the alert_if and alert_message
        # functions for use.
        return {
            "date": date_element[0].string,
            "sandwich": " ".join(sandwich_match[0].split(" ")[:-1]).strip() if sandwich_match else None,
            "desc": sandwich_match[1] if sandwich_match else None
        }

    def alert_if(self, parsed: object) -> bool:
        return parsed["date"] == date.today().strftime("%B %d") and parsed["sandwich"]

    def alert_message(self, parsed: object) -> list:
        return [f"{parsed['sandwich']} ({parsed['date']}) - {parsed['desc']}"]
