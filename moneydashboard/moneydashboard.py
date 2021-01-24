import logging

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class MoneyDashboardException(Exception):
    pass


class LoginFailedException(MoneyDashboardException):
    pass


class MoneyDashboard():
    def __init__(self, email, password, session=None):
        self.__session = session
        self._email = email
        self._password = password
        self._request_verification_token = None

    def get_session(self):
        # Session expires every 10 minutes or so, so we'll login again anyway.
        self._login()
        return self.__session

    def set_session(self, session):
        self.__session = session

    def _login(self):
        logger.info('Logging in...')

        self.set_session(requests.session())

        landing_url = "https://my.moneydashboard.com/landing"
        landing_response = self.__session.get(landing_url)
        soup = BeautifulSoup(landing_response.text, "html.parser")
        self._request_verification_token = soup.find("input", {"name": "__RequestVerificationToken"})['value']

        cookies = self.__session.cookies.get_dict()
        cookie_string = "; ".join([str(x) + "=" + str(y) for x, y in cookies.items()])

        self.set_session(requests.session())
        url = "https://my.moneydashboard.com/landing/login"

        payload = {
            "Password": self._password,
            "Email": self._email,
        }
        headers = {
            'X-Requested-With': 'XMLHttpRequest',
            '__requestverificationtoken': self._request_verification_token,
            'Cookie': cookie_string,
        }
        try:
            response = self.__session.post(url, json=payload, headers=headers)
            response.raise_for_status()
        except Exception as err:
            logger.error('Failed to login (%s)', err)
            raise LoginFailedException from err
        else:
            response_data = response.json()
            if response_data["IsSuccess"]:
                return response_data['IsSuccess']
            logger.error('[Error]: Failed to login (%s)', {response_data["ErrorCode"]})
            raise LoginFailedException

    @property
    def common_headers(self):
        return {
            '__requestverificationtoken': self._request_verification_token,
        }

    def get_accounts(self):
        logger.info('Getting Accounts...')
        url = "https://my.moneydashboard.com/api/Account/"

        try:
            response = self.get_session().request("GET", url, headers=self.common_headers)
            response.raise_for_status()
        except Exception as err:
            logger.error('[Error]: Failed to get Account List (%s)', err)
            raise MoneyDashboardException from err
        else:
            return response.json()

    def get_transactions(self, limit=999):
        logger.info('Getting Transactions...')
        url = "https://my.moneydashboard.com/transaction/GetTransactions?limitTo=%s" % limit
        try:
            response = self.get_session().request("GET", url, headers=self.common_headers)
            response.raise_for_status()
        except Exception as err:
            logger.error('[Error]: Failed to get Transactions (%s)', err)
            raise MoneyDashboardException from err
        else:
            return response.json()
