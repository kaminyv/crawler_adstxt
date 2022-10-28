from concurrent.futures import ThreadPoolExecutor
import requests
import re


TEST_ONCE_DOMAIN = [
    'humaverse.com'
]

TEST_MENY_DOMAINS = [
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


class CrawlerAdsTxt:
    @staticmethod
    def __response_by_url(domain: str, timeout) -> requests:
        url = 'http://' + domain + '/ads.txt'
        response = requests.get(url, timeout=timeout,allow_redirects=True)
        return response

    def __find_signature_by_domain(self, domain_name, signature, timeout, data_domain):
        response = self.__response_by_url(domain_name, timeout)
        signature = signature.split('|')
        name_signature = signature[0]
        type_signature = signature[1]
        pattern = name_signature + '.+' + type_signature
        if response.status_code == 200:
            search = re.search(pattern, response.text, re.IGNORECASE)
            if search is not None:
                data_domain[domain_name] = True
            else:
                data_domain[domain_name] = False
        else:
            data_domain[domain_name] = 'Not exist'

    def find_adstxt(self, domains: list, signature: str, threads: int = 5, timeout: int = 3) -> dict:
        """
        Search for signature occurrences in ADS.TXT file

        :param domains: domain list
        :param signature: example: 'google.com|direct' or 'google.com|reseller'
        :param threads: number of threads
        :param timeout: the waiting time for a response from the domain
        """
        data_domain = dict()

        with ThreadPoolExecutor(max_workers=threads) as executor:
            for domain_name in domains:
                executor.submit(self.__find_signature_by_domain, domain_name, signature, timeout, data_domain)

        return data_domain


if __name__ == '__main__':
    print(CrawlerAdsTxt().find_adstxt(TEST_MENY_DOMAINS, 'google.com|DIRECT'))
