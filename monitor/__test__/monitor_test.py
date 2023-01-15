import unittest
import requests
from unittest.mock import patch
from unittest import mock
from bs4 import BeautifulSoup
from monitor.monitor import HtmlMonitor


class TestMinimalMonitor(HtmlMonitor):
    def __init__(self, session=requests.Session()):
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


bad_response = TestResponse(400, "does not matter")
ok_match_response = TestResponse(200, "<div class='target-element'>target-element-string</div>")
ok_nomatch_response = TestResponse(200, "<div class='target-element'>target-element-string</div>")


class TestMonitorTestCase(unittest.TestCase):
    @patch('monitor.monitor.stderr')
    def test_missing_url_returns_an_error(self, serr):
        expected_message = "TestNoUrlMonitor - [ERROR]: No URL provided.\n"

        class TestNoUrlMonitor(TestMinimalMonitor):
            def url(self) -> str:
                return None

        TestNoUrlMonitor().process()
        self.__assert_output_calls(serr, [expected_message])

    @patch.object(requests.Session, 'get', return_value=bad_response)
    @patch('monitor.monitor.stderr')
    def test_unsuccessful_get_request(self, serr, mock_response):
        expected_message = 'TestMinimalMonitor - [ERROR]: Response from url:https://fakeurl was not successful.\n'
        TestMinimalMonitor().process()
        self.__assert_output_calls(serr, [expected_message])

    @patch.object(requests.Session, 'get', return_value=ok_match_response)
    @patch('monitor.monitor.stderr')
    def test_nothing_returned_from_parsing(self, serr, mock_response):
        expected_message = 'TestNoParsedReturnMonitor - [ERROR]: Nothing returned from parsing.\n'

        class TestNoParsedReturnMonitor(TestMinimalMonitor):
            def parse(self, html: BeautifulSoup) -> object:
                return None

        TestNoParsedReturnMonitor().process()
        self.__assert_output_calls(serr, [expected_message])

    @patch.object(requests.Session, 'get', return_value=ok_match_response)
    @patch('monitor.monitor.stdout')
    def test_alert_displayed(self, sout, mock_response):
        expected_message = 'TestMinimalMonitor - [ALERT]: target-element-string\n'
        TestMinimalMonitor().process()
        self.__assert_output_calls(sout, [expected_message])

    @patch.object(requests.Session, 'get', return_value=ok_nomatch_response)
    @patch('monitor.monitor.stdout')
    def test_alert_displayed(self, sout, mock_response):
        TestMinimalMonitor().process()
        self.__assert_output_calls(sout, [])

    @staticmethod
    def __assert_output_calls(out, messages=[]):
        out.write.assert_has_calls([mock.call(m) for m in messages])


if __name__ == "__main__":
    unittest.main()
