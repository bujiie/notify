import re
from datetime import date

import requests
from bs4 import BeautifulSoup
from monitor.monitor import HtmlMonitor


class ArizmendiMonitor(HtmlMonitor):
    def __init__(self, session: requests.Session, keywords: list = []):
        super(ArizmendiMonitor, self).__init__(session)
        self.keywords = [[i.lower() for i in ingredients] for ingredients in keywords]

    def url(self) -> str:
        return "https://www.arizmendi-bakery.org/arizmendi-emeryville-pizza"

    def parse(self, html: BeautifulSoup = None) -> object:
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

    def alert_if(self, parsed: object = None) -> bool:
        [month, day] = date.today().strftime("%B %d").split(" ")
        return parsed["month"] == month and int(day) in range(parsed["startday"], parsed["endday"]+1) and len([d for d in parsed['menu'].keys() if parsed['menu'][d]]) > 0

    def alert_message(self, parsed: object = None) -> list:
        menu = parsed['menu']
        days = []
        for day in menu.keys():
            if menu[day]:
                days.append(day)
        v = []
        for d in days:
            v.append((d, menu[d]))

        return [f"{day} - {pizza}" for day, pizza in v]
