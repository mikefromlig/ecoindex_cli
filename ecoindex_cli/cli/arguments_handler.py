from tempfile import NamedTemporaryFile
from typing import List, Set, Tuple
from urllib.parse import urlparse

from click.exceptions import BadParameter
from ecoindex.models import WindowSize
from ecoindex_cli.crawl import EcoindexSpider
from pydantic import validate_arguments
from pydantic.error_wrappers import ErrorWrapper, ValidationError
from pydantic.networks import HttpUrl
from pydantic.types import FilePath
from scrapy.crawler import CrawlerProcess


@validate_arguments
def validate_list_of_urls(urls: List[HttpUrl]) -> HttpUrl:
    return urls


@validate_arguments
def get_urls_from_file(urls_file: FilePath) -> List[HttpUrl]:
    with open(urls_file) as fp:
        urls_from_file = set()

        for url in fp.readlines():
            url = url.strip()
            urls_from_file.add(url)

    if validate_list_of_urls(urls_from_file):
        return urls_from_file


def get_urls_recursive(main_url: str) -> Tuple[str]:
    parsed_url = urlparse(main_url)
    domain = parsed_url.netloc
    main_url = f"{parsed_url.scheme}://{domain}"
    process = CrawlerProcess()

    with NamedTemporaryFile(mode="w+t") as temp_file:
        process.crawl(
            crawler_or_spidercls=EcoindexSpider,
            allowed_domains=[domain],
            start_urls=[main_url],
            temp_file=temp_file,
        )
        process.start()
        temp_file.seek(0)
        urls = temp_file.readlines()

    if validate_list_of_urls(urls):
        return urls


@validate_arguments
def get_url_from_args(urls_arg: List[HttpUrl]) -> Set[HttpUrl]:
    urls_from_args = set()
    for url in urls_arg:
        urls_from_args.add(url)

    return urls_from_args


def get_window_sizes_from_args(window_sizes: List[str]) -> List[WindowSize]:
    result = []
    errors = []
    for window_size in window_sizes:
        try:
            width, height = window_size.split(",")
            result.append(WindowSize(width=int(width), height=int(height)))
        except ValueError:
            errors.append(
                ErrorWrapper(
                    BadParameter(
                        message=f"🔥 `{window_size}` is not a valid window size. Must be of type `1920,1080`"
                    ),
                    loc="window_size",
                )
            )

    if errors:
        raise ValidationError(errors=errors, model=WindowSize)

    return result
