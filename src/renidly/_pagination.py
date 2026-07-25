"""List containers with transparent auto-pagination.

``RenidlyList`` normalizes the three pagination styles (cursor, page, offset):
each resource records ``has_more`` plus the params for the next page and a
``_pager`` callback, so ``.auto_paging_iter()`` spans all pages lazily while the
raw ``.data`` / ``.next_cursor`` stay available for manual control.
"""
from __future__ import annotations

from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    TypeVar,
)

T = TypeVar("T")


class _BaseList(Generic[T]):
    """Common list container: holds one page of items + the next-page cursor/pager."""

    def __init__(
        self,
        data: List[T],
        *,
        has_more: bool = False,
        next_params: Optional[Dict[str, Any]] = None,
        next_cursor: Optional[str] = None,
        pager: Optional[Callable[[Dict[str, Any]], Any]] = None,
        raw: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.data: List[T] = data
        self.has_more = has_more
        self.next_cursor = next_cursor
        self._next_params = next_params
        self._pager = pager
        self._raw = raw or {}

    # list-like ergonomics over the CURRENT page
    def __iter__(self) -> Iterator[T]:
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, i: int) -> T:
        return self.data[i]

    def __bool__(self) -> bool:
        return bool(self.data)

    def __repr__(self) -> str:  # pragma: no cover
        return f"{type(self).__name__}(data=[{len(self.data)} items], has_more={self.has_more})"


class RenidlyList(_BaseList[T]):
    """One page of results that behaves like a list.

    Indexing (``page[0]``), ``len(page)``, and ``for x in page`` all operate on
    the CURRENT page. To walk every page transparently, use
    :meth:`auto_paging_iter`. ``.has_more`` and ``.next_cursor`` let you page
    manually if you prefer.
    """

    def auto_paging_iter(self) -> Iterator[T]:
        """Iterate over EVERY result across all pages, fetching lazily.

        Yields each item on the current page, then transparently requests the
        next page (via the stored pager + cursor/offset) and continues, until
        there are no more pages. Only one page is held in memory at a time.

        Example::

            for person in client.data.people.search(title="cto").auto_paging_iter():
                print(person.headline)
        """
        page: RenidlyList[T] = self
        while True:
            for item in page.data:
                yield item
            if not (page.has_more and page._pager and page._next_params is not None):
                return
            page = page._pager(page._next_params)


class AsyncRenidlyList(_BaseList[T]):
    """Async page of results. Iterate all pages with ``async for`` (or
    :meth:`auto_paging_iter`, an async generator)."""

    def __aiter__(self) -> AsyncIterator[T]:
        return self.auto_paging_iter()

    async def auto_paging_iter(self) -> AsyncIterator[T]:
        """Async version of :meth:`RenidlyList.auto_paging_iter`.

        Example::

            async for person in client.data.people.search(title="cto").auto_paging_iter():
                print(person.headline)
        """
        page: AsyncRenidlyList[T] = self
        while True:
            for item in page.data:
                yield item
            if not (page.has_more and page._pager and page._next_params is not None):
                return
            page = await page._pager(page._next_params)
