#!/usr/bin/env python3

import sys
import abc
import re
import concurrent.futures
import threading
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
            return

        response = self.session.get(url)
        if response.status_code != 200:
            print(f"Response from url:{url} was not successful.")
            return

        parsed = self.parse(BeautifulSoup(response.content, "html.parser"))
        if not parsed:
            print("Nothing returned from parsing.")
            return

        if self.alert_if(parsed):
            message = self.alert_message(parsed)
            if isinstance(message, list):
                for m in message:
                    self.__alert(m)
            else:
                self.__alert(message)
        return

    def __alert(self, message):
        print(f"{self.__class__.__name__} - [ALERT]: {message}")


class StandardFareMonitor(HtmlMonitor):
    def __init__(self, session, keywords=[]):
        super(StandardFareMonitor, self).__init__(session)
        self.keywords = list(map(lambda k: k.lower(), keywords))

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

    def alert_if(self, parsed):
        return parsed["date"] == date.today().strftime("%B %d") and parsed["sandwich"]

    def alert_message(self, parsed):
        return f"{parsed['sandwich']} ({parsed['date']}) - {parsed['desc']}"


class ArizmendiMonitor(HtmlMonitor):
    def __init__(self, session, keywords=[]):
        super(ArizmendiMonitor, self).__init__(session)
        self.keywords = [[i.lower() for i in ingredients] for ingredients in keywords]

    def url(self):
        return "https://www.arizmendi-bakery.org/arizmendi-emeryville-pizza"

    def parse(self, html=None):
        daterange_element = html.find("p", string=re.compile('Pizza Forecast for'))
        if not daterange_element:
            return None

        # Assuming date range in format 'Month ##-##'
        [month, dayrange] = daterange_element.string.split(" ")[-2:]
        [startday, endday] = dayrange.split("-")

        weekly_menu = {
            "WEDNESDAY": None,
            "THURSDAY": None,
            "FRIDAY": None,
            "SATURDAY": None,
            "SUNDAY": None
        }
        # Search for the days of the week and their corresponding pizza
        for day in weekly_menu.keys():
            menu_element = html.select(f"p:-soup-contains('{day}')")
            if not menu_element or len(menu_element) < 1:
                continue
            pizza = menu_element[0].text.replace(day, "").strip().lower()

            keyword_match = False
            for keyword in self.keywords:
                keyword_inner_match = True
                for kw in keyword:
                    if kw not in pizza:
                        keyword_inner_match = False
                        break

                if keyword_inner_match:
                    weekly_menu[day] = pizza
                    keyword_match = True
                    break
        return {
            "month": month,
            "startday": int(startday),
            "endday": int(endday),
            "menu": weekly_menu
        }

    def alert_if(self, parsed=None):
        [month, day] = date.today().strftime("%B %d").split(" ")
        return parsed["month"] == month and int(day) in range(parsed["startday"], parsed["endday"]+1) and len([d for d in parsed['menu'].keys() if parsed['menu'][d]]) > 0

    def alert_message(self, parsed=None):
        menu = parsed['menu']
        days = []
        for day in menu.keys():
            if menu[day]:
                days.append(day)
        v = []
        for d in days:
            v.append((d, menu[d]))

        return [f"{day} - {pizza}" for day, pizza in v]


if __name__ == "__main__":
    MAX_WORKERS = 10

    monitors = [
        StandardFareMonitor(requests.Session(), keywords=["pork", "beet", "beets", "roast beef", "roastbeef", "sausage"]),
        ArizmendiMonitor(requests.Session(), keywords=[
            ["roasted yellow potato", "leek", "parmesan", "garlic oil"]
        ])
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        executor.map(lambda m: m.process(), monitors)
