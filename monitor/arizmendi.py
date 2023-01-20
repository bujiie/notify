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
        [month, daterange] = daterange_element.string.strip().split(" ")[-2:]
        # Note this will probably fail when the week is spread across the end of
        # one month and the beginning of the next assuming the format will be
        # 'January 31 - February 4'
        [startdate, enddate] = [int(d) for d in daterange.split("-")]

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

            for keyword in self.keywords:
                if all([i in pizza for i in keyword]):
                    weekly_menu[day] = pizza
                    break

        return {
            "month": month,
            "startdate": startdate,
            "enddate": enddate,
            "menu": weekly_menu
        }

    def alert_if(self, parsed: object = None) -> bool:
        [month, today] = date.today().strftime("%B %d").split(" ")
        menu = parsed['menu']
        return (parsed["month"] == month
                and int(today) in range(parsed["startdate"], parsed["enddate"]+1)
                and len([d for d in menu.keys() if menu[d]]) > 0)

    def alert_message(self, parsed: object = None) -> list:
        return [f"{day} - {pizza}" for day, pizza in parsed['menu'].items() if pizza]
