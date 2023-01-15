from sys import stderr, stdout
from abc import abstractmethod, ABC
from bs4 import BeautifulSoup


class HtmlMonitor(ABC):
    def __init__(self, session):
        self.session = session

    """Returns a URL that will be used to make a GET call. The response of this
    GET call is HTML that will get passed along to the parse() method.
    
    Return:
    str: URL (https)
    """
    @abstractmethod
    def url(self) -> str:
        pass

    """Accepts HTML for use in parsing. The return of this method is passed to
    alert methods to help form alert conditions and messages.
    
    Parameters:
    html: BeautifulSoup -> HTML response from GET URL as BeautifulSoup object
    
    Return:
    Any: Any object needed to form alert conditions/messages
    """
    @abstractmethod
    def parse(self, html: BeautifulSoup = None) -> object:
        pass

    """The return of alert_if determines if an alert message should be shown or
    not.
    
    Parameters:
    parsed: Any -> Return any object from the parse() method
    
    Return:
    bool: Returns TRUE if the alert message should be shown
    """
    @abstractmethod
    def alert_if(self, parsed: object = None) -> bool:
        pass

    """The return of alert_message is a list of alert messages that will be
    shown if the alert_if conditions return TRUE.
    
    Parameters:
    parsed: Any -> Return any object from the parse() method 
    
    Return:
    list(str): Alert messages that will be displayed on separate lines
    """
    @abstractmethod
    def alert_message(self, parsed: object = None) -> list:
        pass

    """Formats error message for the concrete monitor. This method can be called
    within the concrete monitor implementation where necessary.
    
    Parameters:
    message: str -> error message to print to stderr
    """
    def _error(self, message):
        stderr.write(f"{self.__class__.__name__} - [ERROR]: {message}\n")

    def process(self):
        url = self.url()
        if not url:
            self._error("No URL provided.")
            return

        response = self.session.get(url)
        if response.status_code != 200:
            self._error(f"Response from url:{url} was not successful.")
            return

        parsed = self.parse(BeautifulSoup(response.content, "html.parser"))
        if not parsed:
            self._error("Nothing returned from parsing.")
            return

        if self.alert_if(parsed):
            messages = self.alert_message(parsed)
            if messages:
                for message in messages:
                    self.__alert(message)
        return

    def __alert(self, message):
        stdout.write(f"{self.__class__.__name__} - [ALERT]: {message}\n")
