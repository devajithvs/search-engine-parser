from search_engine_parser.core import YahooSearch, GoogleSearch, BingSearch
from search_engine_parser.core import cli

search_args = ('preaching to the choir', 1)

def test_yahoo_search():
    engine = YahooSearch()
    results = engine.search(*search_args)
    assert len(results['titles']) == 10


def test_google_search():
    engine = GoogleSearch()
    results = engine.search(*search_args)
    assert len(results['titles']) == 10


def test_bing_search():
    engine = BingSearch()
    results = engine.search(*search_args)
    assert len(results['titles']) == 10