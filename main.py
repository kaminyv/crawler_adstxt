import concurrent
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import NamedTuple, Optional, Dict, List
from urllib.parse import urlparse


import requests
import re


TEST_ONCE_DOMAIN = [
    'http://google.com/',
]

TEST_MANY_DOMAINS = [
    'userbenchmark.com',
    'humaverse.com',
    'homeaway.com',
    'google.com',
    'facebook.com',
    'youtube.com',
    'twitter.com',
    'instagram.com',
    'linkedin.com',
    'apple.com',
    'microsoft.com',
    'wikipedia.org',
    'wordpress.org',
    'googletagmanager.com',
    'hibid.com',
    'laopinion.com',
]


class Status(Enum):
    SUCCESS = 0
    FAILED_RESPONSE = 1
    INTERNAL_ERROR = 2
    INCORRECT_INPUT = 3
    SIGNATURE_NOT_FOUND = 4


class AdsTxtResponse(NamedTuple):
    status: Status
    domain: str
    data: Optional[Dict] = None
    error: Optional[Exception] = None


class IncorrectInputError(Exception):
    pass


class CrawlerAdsTxt:
    @staticmethod
    def __validate_domain(domain: str) -> str:
        if not domain:
            raise IncorrectInputError('Invalid domain')

        domain_parse = urlparse(domain)
        domain = domain_parse.netloc if not domain_parse.path else domain_parse.path

        return domain

    def __create_url(self, domain: str) -> str:
        domain = self.__validate_domain(domain)
        url = f'http://{domain}/ads.txt'

        return url

    @staticmethod
    def __request(url: str, timeout) -> requests:
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        return response

    @staticmethod
    def __is_signature_found(signature: str, text: str):
        signature = signature.split('|')
        name_signature = signature[0]
        type_signature = signature[1]
        pattern = name_signature + '.+' + type_signature
        search = re.search(pattern, text, re.IGNORECASE)

        if search is not None:
            return True

        return False

    def __find_signature_by_domain(self, domain_name, signature, timeout):
        try:
            url = self.__create_url(domain_name)
        except IncorrectInputError as e:
            return AdsTxtResponse(status=Status.INCORRECT_INPUT, error=e, domain=domain_name)

        response = self.__request(url, timeout)

        if response.status_code != 200:
            return AdsTxtResponse(status=Status.FAILED_RESPONSE, domain=domain_name)

        signature_found = self.__is_signature_found(signature, response.text)
        if signature_found:
            return AdsTxtResponse(
                status=Status.SUCCESS,
                data={'signature': signature},
                domain=domain_name
            )
        else:
            return AdsTxtResponse(
                status=Status.SIGNATURE_NOT_FOUND,
                data={'signature': signature},
                domain=domain_name
            )

    def find_adstxt(self, domains: list, signature: str, threads: int = 5, timeout: int = 3) -> List[AdsTxtResponse]:
        """
        Search for signature occurrences in ADS.TXT file

        :param domains: domain list
        :param signature: example: 'google.com|direct' or 'google.com|reseller'
        :param threads: number of threads
        :param timeout: the waiting time for a response from the domain
        """
        responses = []

        with ThreadPoolExecutor(max_workers=threads) as executor:
            future_to_domain = {
                executor.submit(self.__find_signature_by_domain, domain, signature, timeout): domain
                for domain in domains
            }
            for future in concurrent.futures.as_completed(future_to_domain):
                domain = future_to_domain[future]
                try:
                    data = future.result()
                    responses.append(data)
                except Exception as exc:
                    responses.append(AdsTxtResponse(status=Status.INTERNAL_ERROR, error=exc, domain=domain))

        return responses


if __name__ == '__main__':
    # print(CrawlerAdsTxt._CrawlerAdsTxt__validate_domain('dff.google.com'))
    print(CrawlerAdsTxt().find_adstxt(TEST_MANY_DOMAINS, 'google.com|DIRECT'))
