"""Auto-pagination for list endpoints.

The 24SevenOffice API paginates with an RFC 8288 ``Link`` header containing a
``rel="next"`` URL (page numbers for some endpoints, continuation tokens for
others). The paginators below follow that header transparently::

    for customer in client.customers.list():           # every customer, all pages
        ...

    for page in client.customers.list().pages():       # page by page
        print(len(page.items), page.next_url)

    first_ten = client.customers.list().to_list(max_items=10)

For page-number endpoints that omit the header, the next page is requested while
pages come back full; the loop stops on an empty, short or repeated page.
"""

from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Dict,
    Generic,
    Iterator,
    List,
    Mapping,
    Optional,
    Set,
    Type,
    TypeVar,
)

import httpx

if TYPE_CHECKING:
    from py24so._client import APIClient, AsyncAPIClient

T = TypeVar("T")

__all__ = ["Page", "Paginator", "AsyncPaginator"]


class Page(Generic[T]):
    """One page of results."""

    def __init__(self, items: List[T], response: httpx.Response, next_url: Optional[str]) -> None:
        self.items = items
        self.response = response
        #: The raw ``rel="next"`` link, or ``None`` if the API sent none.
        self.next_url = next_url

    @property
    def has_next(self) -> bool:
        return self.next_url is not None

    def __iter__(self) -> Iterator[T]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __repr__(self) -> str:
        return f"Page(items={len(self.items)}, next_url={self.next_url!r})"


def _next_link(response: httpx.Response) -> Optional[str]:
    try:
        link = response.links.get("next")
    except Exception:  # malformed Link header
        return None
    url = link.get("url") if link else None
    return url or None


class _PageState:
    """Bookkeeping shared by the sync and async paginators."""

    def __init__(
        self,
        path: str,
        params: Mapping[str, Any],
        page_param: Optional[str],
        page_size: Optional[int],
    ) -> None:
        self.url = path
        self.params: Optional[Dict[str, Any]] = dict(params)
        self.base_params = dict(params)
        self.page_param = page_param
        self.page_size = page_size
        self.page_number = int(params.get(page_param) or 1) if page_param else 1
        self.seen_urls: Set[str] = set()
        self.previous_content: Optional[bytes] = None

    def is_repeat(self, response: httpx.Response) -> bool:
        """Detect an API that ignores the page parameter and keeps returning the same page."""
        repeated = self.previous_content is not None and response.content == self.previous_content
        self.previous_content = response.content
        return repeated

    def advance(self, resolved_next: Optional[str], page: "Page[Any]") -> bool:
        """Move to the next page. Returns ``False`` when pagination is finished."""
        if not page.items:
            return False

        if resolved_next is not None:
            if resolved_next in self.seen_urls:
                return False
            self.seen_urls.add(resolved_next)
            self.url = resolved_next
            self.params = None  # the link already carries the query string
            return True

        if (
            self.page_param
            and page.response.links.get("next") is None
            and self.page_size is not None
            and len(page.items) >= self.page_size
        ):
            self.page_number += 1
            self.params = {**self.base_params, self.page_param: self.page_number}
            return True
        return False


class Paginator(Generic[T]):
    """Lazily iterates over every item of a paginated list endpoint."""

    def __init__(
        self,
        client: "APIClient",
        path: str,
        item_type: Type[T],
        params: Optional[Mapping[str, Any]] = None,
        *,
        page_param: Optional[str] = None,
        page_size: Optional[int] = None,
    ) -> None:
        self._client = client
        self._path = path
        self._item_type = item_type
        self._params = dict(params or {})
        self._page_param = page_param
        self._page_size = page_size

    def pages(self) -> Iterator[Page[T]]:
        """Yield one :class:`Page` per API request."""
        state = _PageState(self._path, self._params, self._page_param, self._page_size)
        while True:
            response = self._client.send("GET", state.url, params=state.params)
            if state.is_repeat(response):
                return
            items = self._client.parse_list(response, self._item_type)
            next_url = _next_link(response)
            page = Page(items, response, next_url)
            yield page
            resolved = self._client.resolve_link(next_url) if next_url else None
            if not state.advance(resolved, page):
                return

    def first_page(self) -> Page[T]:
        """Fetch only the first page."""
        return next(iter(self.pages()))

    def to_list(self, max_items: Optional[int] = None) -> List[T]:
        """Collect items into a list, stopping early once ``max_items`` is reached."""
        result: List[T] = []
        if max_items is not None and max_items <= 0:
            return result
        for item in self:
            result.append(item)
            if max_items is not None and len(result) >= max_items:
                break
        return result

    def __iter__(self) -> Iterator[T]:
        for page in self.pages():
            yield from page.items


class AsyncPaginator(Generic[T]):
    """Async counterpart of :class:`Paginator`; use with ``async for``."""

    def __init__(
        self,
        client: "AsyncAPIClient",
        path: str,
        item_type: Type[T],
        params: Optional[Mapping[str, Any]] = None,
        *,
        page_param: Optional[str] = None,
        page_size: Optional[int] = None,
    ) -> None:
        self._client = client
        self._path = path
        self._item_type = item_type
        self._params = dict(params or {})
        self._page_param = page_param
        self._page_size = page_size

    async def pages(self) -> AsyncIterator[Page[T]]:
        """Yield one :class:`Page` per API request."""
        state = _PageState(self._path, self._params, self._page_param, self._page_size)
        while True:
            response = await self._client.send("GET", state.url, params=state.params)
            if state.is_repeat(response):
                return
            items = self._client.parse_list(response, self._item_type)
            next_url = _next_link(response)
            page = Page(items, response, next_url)
            yield page
            resolved = self._client.resolve_link(next_url) if next_url else None
            if not state.advance(resolved, page):
                return

    async def first_page(self) -> Page[T]:
        """Fetch only the first page."""
        async for page in self.pages():
            return page
        raise RuntimeError("unreachable: pages() always yields at least once")

    async def to_list(self, max_items: Optional[int] = None) -> List[T]:
        """Collect items into a list, stopping early once ``max_items`` is reached."""
        result: List[T] = []
        if max_items is not None and max_items <= 0:
            return result
        async for item in self:
            result.append(item)
            if max_items is not None and len(result) >= max_items:
                break
        return result

    async def __aiter__(self) -> AsyncIterator[T]:
        async for page in self.pages():
            for item in page.items:
                yield item
