import unittest
import requests
from unittest.mock import patch
from unittest import mock
from bs4 import BeautifulSoup
from monitor.monitor import HtmlMonitor


class TestMinimalMonitor(HtmlMonitor):
    def __init__(self, session):
        super(TestMinimalMonitor, self).__init__(session)

    def url(self) -> str:
        return "https://fakeurl"

    def parse(self, html: BeautifulSoup = None) -> object:
        return html.find("div", {"class": "target-element"}).string

    def alert_if(self, parsed: object = None) -> bool:
        return parsed == "target-element-string"

    def alert_message(self, parsed: object = None) -> list:
        return [parsed]


# Mock the GET response. All we use is 'status_code' and 'content' so we can
# ignore all the other attributes in the requests.Response object. We do not
# need the object to be the exact Response type.
class TestResponse:
    def __init__(self, status_code, content):
        self.status_code = status_code
        self.content = content


class TestMonitorTestCase(unittest.TestCase):
    @patch('monitor.monitor.stderr')
    def test_missing_url_returns_an_error(self, serr):
        class TestNoUrlMonitor(TestMinimalMonitor):
            def __init__(self, session):
                super(TestNoUrlMonitor, self).__init__(session)

            def url(self) -> str:
                return None

        self.__check_output(serr, TestNoUrlMonitor(requests.Session()), "TestNoUrlMonitor - [ERROR]: No URL provided.\n")

    @patch.object(requests.Session, 'get', return_value=TestResponse(400, "does not matter"))
    @patch('monitor.monitor.stderr')
    def test_unsuccessful_get_request(self, serr, mock_response):
        self.__check_output(serr, TestMinimalMonitor(requests.Session()), 'TestMinimalMonitor - [ERROR]: Response from url:https://fakeurl was not successful.\n')

    @patch.object(requests.Session, 'get', return_value=TestResponse(200, "<div class='target-element'>target-element-string</div>"))
    @patch('monitor.monitor.stderr')
    def test_nothing_returned_from_parsing(self, serr, mock_response):
        class TestNoParsedReturnMonitor(TestMinimalMonitor):
            def __init__(self, session):
                super(TestNoParsedReturnMonitor, self).__init__(session)

            def parse(self, html: BeautifulSoup) -> object:
                return None

        self.__check_output(serr, TestNoParsedReturnMonitor(requests.Session()), 'TestNoParsedReturnMonitor - [ERROR]: Nothing returned from parsing.\n')

    @patch.object(requests.Session, 'get', return_value=TestResponse(200, "<div class='target-element'>target-element-string</div>"))
    @patch('monitor.monitor.stdout')
    def test_alert_displayed(self, sout, mock_response):
        self.__check_output(sout, TestMinimalMonitor(requests.Session()), 'TestMinimalMonitor - [ALERT]: target-element-string\n')

    @patch.object(requests.Session, 'get', return_value=TestResponse(200, "<div class='target-element'>not-target-element-string</div>"))
    @patch('monitor.monitor.stdout')
    def test_alert_displayed(self, sout, mock_response):
        monitor = TestMinimalMonitor(requests.Session())
        monitor.process()
        sout.write.assert_has_calls([])

    @staticmethod
    def __check_output(out, monitor, message):
        monitor.process()
        out.write.assert_has_calls([
            mock.call(message)
        ])


if __name__ == "__main__":
    unittest.main()


