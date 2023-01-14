#!/usr/bin/env python3

import sys
import abc
import re
import requests
from bs4 import BeautifulSoup
from datetime import date


class HtmlMonitor(abc.ABC):
    def __init__(self, session):
        self.session = session

    @abc.abstractmethod
    def url(self):
        pass

    @abc.abstractmethod
    def parse(self, html=None):
        pass

    @abc.abstractmethod
    def alert_if(self, parsed=None):
        pass

    @abc.abstractmethod
    def alert_message(self, parsed=None):
        pass

    def process(self):
        url = self.url()
        if not url:
            print("No URL provided.")
            sys.exit(1)

        response = self.session.get(url)
        if response.status_code != 200:
            print(f"Response from url:{url} was not successful.")
            sys.exit(1)

        parsed = self.parse(BeautifulSoup(response.content, "html.parser"))
        if not parsed:
            print("Nothing returned from parsing.")
            sys.exit(1)

        if self.alert_if(parsed):
            message = self.alert_message(parsed)
            print(f"[ALERT]: {message}")
        else:
            print("Nothing to alert.")
        sys.exit(0)


class StandardFareMonitor(HtmlMonitor):
    def __init__(self, session, keywords=[]):
        super(StandardFareMonitor, self).__init__(session)
        self.keywords = keywords

    def url(self):
        return "https://www.standardfareberkeley.com/lunch"

    def parse(self, html):
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
            for keyword in self.keywords:
                if keyword in sandwich_item.string.lower():
                    sandwich_match = (sandwich_item.string, sandwich_desc[0].string)
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

    def alert_if(self, parsed):
        return parsed["date"] == date.today().strftime("%B %d") and parsed["sandwich"]

    def alert_message(self, parsed):
        return f"{parsed['sandwich']} ({parsed['date']}) - {parsed['desc']}"


if __name__ == "__main__":
    sf = StandardFareMonitor(requests.Session(), keywords=["pork", "beet", "beets", "roast beef", "roastbeef", "sausage"])
    sf.process()
