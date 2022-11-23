import concurrent
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import NamedTuple, Optional, List
from urllib.parse import urlparse, ParseResult

import requests
import re
from requests import Response

TEST_ONCE_DOMAIN = [
    'http://google.com/',
]

TEST_MANY_DOMAINS = [
    'http://userbenchmark.com/fsfdaf',
    'http://humaverse.com',
    'http://homeaway.com',
    'https://google.com/fsdfdsaaa/dfsasf',
    'http://facebook.com',
    'http://youtube.com',
    'http://twitter.com',
    'http://instagram.com',
    'http://linkedin.com',
    'http://apple.com',
    'http://microsoft.com',
    'http://wikipedia.org',
    'http://wordpress.org',
    'http://googletagmanager.com',
    'http://hibid.com',
    'http://laopinion.com',
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
    data: Optional[List] = None
    error: Optional[Exception] = None


class IncorrectInputError(Exception):
    pass


class CrawlerAdsTxt:
    @staticmethod
    def __validate_input(input_str: str) -> str:
        pattern = r'^(https?\:\/\/)?((?:[-a-zа-яё0-9]{1,63}\.)' \
                  r'?([-a-zа-яё0-9]{1,63})\.[a-za-яё]{2,6}){1,255}'

        match = re.match(pattern, input_str)

        if match is None:
            raise IncorrectInputError('Invalid domain')

        return match.group(0)

    def __create_url(self, domain: str) -> str:
        domain = self.__validate_input(domain)
        url = f"{domain}/ads.txt" if re.match(r'^https?', domain) \
            else f'http://{domain}/ads.txt'

        return url

    @staticmethod
    def __request(url: str, timeout) -> requests:
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        return response

    @staticmethod
    def __find_signature(signature: str, text: str) -> list:
        signature = signature.split('|')
        name_signature = signature[0]
        type_signature = signature[1]
        pattern = f'{name_signature}.+{type_signature}'

        search = re.findall(pattern, text, re.IGNORECASE)

        return search

    def _crawl(self, domain_name, timeout) -> Response:
        url = self.__create_url(domain_name)
        response = self.__request(url, timeout)
        return response

    def _find(self, domain_name, signature, timeout) -> AdsTxtResponse:
        try:
            response = self._crawl(domain_name, timeout)
        except IncorrectInputError as e:
            return AdsTxtResponse(status=Status.INCORRECT_INPUT, error=e, domain=domain_name)

        if response.status_code != 200:
            return AdsTxtResponse(status=Status.FAILED_RESPONSE, domain=domain_name)

        found_signature = self.__find_signature(signature, response.text)

        if found_signature:
            return AdsTxtResponse(
                status=Status.SUCCESS,
                data=found_signature,
                domain=domain_name
            )

        return AdsTxtResponse(
            status=Status.SIGNATURE_NOT_FOUND,
            data=found_signature,
            domain=domain_name
        )

    def find(self, domains: list, signature: str,
             threads: int = 5, timeout: int = 3) -> List[AdsTxtResponse]:
        """
        Search for signature occurrences in ADS.TXT file

        :param domains: domain list (http://example.com)
        :param signature: example: 'google.com|direct' or 'google.com|reseller'
        :param threads: number of threads
        :param timeout: the waiting time for a response from the domain
        """
        responses = []

        with ThreadPoolExecutor(max_workers=threads) as executor:
            future_to_domain = {
                executor.submit(self._find, domain,
                                signature, timeout): domain
                for domain in domains
            }
            for future in concurrent.futures.as_completed(future_to_domain):
                domain = future_to_domain[future]
                try:
                    data = future.result()
                    responses.append(data)
                except Exception as exc:
                    responses.append(AdsTxtResponse(
                        status=Status.INTERNAL_ERROR,
                        error=exc, domain=domain))

        return responses


if __name__ == '__main__':
    # print(CrawlerAdsTxt._CrawlerAdsTxt__validate_domain('.com/fsdfdsaaa/dfsasf'))
    print(CrawlerAdsTxt().find(TEST_MANY_DOMAINS, 'google.com|DIRECT'))
