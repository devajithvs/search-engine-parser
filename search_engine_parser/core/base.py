"""@desc
		Base class inherited by every search engine
"""

import random
from abc import ABCMeta, abstractmethod
from contextlib import suppress
from enum import Enum, unique
from urllib.parse import urlencode, urlparse

import requests
from bs4 import BeautifulSoup

from search_engine_parser.core import utils
from search_engine_parser.core.exceptions import NoResultsOrTrafficError


@unique
class ReturnType(Enum):
    FULL = "full"
    TITLE = "titles"
    DESCRIPTION = "descriptions"
    LINK = "links"


# All results returned are each items of search
class SearchItem(dict):
    pass


class SearchResult():
    # Hold the results
    def __init__(self):
        self.results = {}

    def add(self, value):
        for key in value.keys():
            self.results[key] = value[key]

    def append(self, value):
        for key in value.keys():
            if key not in self.keys():
                self.results[key] = list([value[key]])
            else:
                self.results[key].append(value[key])

    def __getitem__(self, value):
        return self.results[value]

    def keys(self):
        return self.results.keys()


class BaseSearch:

    __metaclass__ = ABCMeta

    """
    Search base to be extended by search parsers
    Every subclass must have two methods `search` amd `parse_single_result`
    """
    # Summary of engine
    summary = None
    # Search Engine Name
    name = None
    # Search Engine unformatted URL
    search_url = None
    # The url after all query params have been set
    _parsed_url = None

    @abstractmethod
    def parse_soup(self, soup):
        """
        Defines the results contained in a soup
        """
        raise NotImplementedError("subclasses must define method <parse_soup>")

    @abstractmethod
    def parse_single_result(self, single_result):
        """
        Every div/span containing a result is passed here to retrieve
        `title`, `link` and `descr`
        """
        raise NotImplementedError(
            "subclasses must define method <parse_results>")


    def parse_result(self, results, **kwargs):
        """
        Runs every entry on the page through parse_single_result

        :param results: Result of main search to extract individual results
        :type results: list[`bs4.element.ResultSet`]
        :returns: dictionary. Containing lists of titles, links, descriptions and other possible\
            returns.
        :rtype: dict
        """
        search_results = SearchResult()
        for each in results:
            try:
                rdict = self.parse_single_result(each, **kwargs)
                search_results.append(rdict)
            except Exception as e:  # pylint: disable=invalid-name, broad-except
                print("Exception: %s" % str(e))
                
        try: 
            direct_answer = self.parse_direct_answer(results[0])
            rdict = {'direct_answer': direct_answer}
            if direct_answer is not None:
                search_results.add(rdict)
        except Exception: 
            pass

        return search_results
        
        
    def get_params(self, query=None, page=None, offset=None, **kwargs):
        """ This  function should be overwritten to return a dictionary of query params"""
        return {'q': query, 'page': page}

    def headers(self):
        headers = {
            "Cache-Control": 'no-cache',
            "Connection": "keep-alive",
            "User-Agent": utils.get_rand_user_agent()
        }
        return headers

    def get_source(self, url):
        """
        Returns the source code of a webpage.

        :rtype: string
        :param url: URL to pull it's source code
        :return: html source code of a given URL.
        """
        try:
            session = requests.Session()
            resp = session.get(url, headers=self.headers())
            html =  resp.text
        except Exception as exc:
            raise Exception('ERROR: {}\n'.format(exc))
        return str(html)

    def get_soup(self, url):
        """
        Get the html soup of a query

        :rtype: `bs4.element.ResultSet`
        """
        html =  self.get_source(url)
        return BeautifulSoup(html, 'lxml')

    def get_search_url(self, query=None, page=None, **kwargs):
        """
        Return a formatted search url
        """
        if not self._parsed_url:
            # Some URLs use offsets
            offset = (page * 10) - 9
            params = self.get_params(
                query=query, page=page, offset=offset, **kwargs)
            url = self.search_url + urlencode(params)
            self._parsed_url = urlparse(url)
        return self._parsed_url.geturl()

    def get_results(self, soup, **kwargs):
        """ Get results from soup"""

        results = self.parse_soup(soup)
        # TODO Check if empty results is caused by traffic or answers to query
        # were not found
        if not results:
            raise NoResultsOrTrafficError(
                "The result parsing was unsuccessful. It is either your query could not be found" +
                " or it was flagged as unusual traffic")
        search_results = self.parse_result(results, **kwargs)
        return search_results

    def search(self, query=None, page=None, **kwargs):
        """
        Query the search engine

        :param query: the query to search for
        :type query: str
        :param page: Page to be displayed, defaults to 1
        :type page: int
        :return: dictionary. Containing titles, links, netlocs and descriptions.
        """
        # Get search Page Results
        soup = self.get_soup(self.get_search_url(query, page, **kwargs))
        return self.get_results(soup, **kwargs)

    def _search(self, query=None, page=None, callback=None, **kwargs):
        """
        Query the search engine but in  mode

        :param query: the query to search for
        :type query: str
        :param page: Page to be displayed, defaults to 1
        :type page: int
        :param callback: The callback function to execute when results are returned
        :type page: function
        :return: dictionary. Containing titles, links, netlocs and descriptions.
        """
        # TODO callback should be called
        if callback:
            pass
        soup =  self.get_soup(self.get_search_url(query, page, **kwargs))
        return self.get_results(soup, **kwargs)
