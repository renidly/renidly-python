"""Batch job handles for the async enrichment / verify / find endpoints.

``submit`` returns a job id immediately; the handle then lets you either block
with ``.wait()`` or consume results lazily with ``.stream()`` (a generator that
yields items as pages resolve). Results page by an integer ``after`` cursor until
``next_cursor`` stops advancing and ``status`` is terminal.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Iterator, List, Optional, Type

from ._models import RenidlyModel


class BatchResult:
    """Everything a finished (or drained) job produced."""

    def __init__(self, status: str, total: int, resolved: int, errors: int, results: List[Any], not_found: List[str]):
        self.status = status
        self.total = total
        self.resolved = resolved
        self.errors = errors
        self.results = results
        self.not_found = not_found

    def __repr__(self) -> str:  # pragma: no cover
        return f"BatchResult(status={self.status!r}, resolved={self.resolved}/{self.total}, errors={self.errors})"


def _rows(data: Dict[str, Any], results_key: str, keyed: bool, model: Type[RenidlyModel]) -> List[Any]:
    container = data.get(results_key)
    out: List[Any] = []
    if keyed and isinstance(container, dict):
        for k, v in container.items():
            payload = {**v, "matched_input": k} if isinstance(v, dict) else {"value": v, "matched_input": k}
            out.append(model._build(payload, None))
    elif isinstance(container, list):
        for item in container:
            out.append(model._build(item, None))
    return out


class _BaseJob:
    """Shared state + cursor helpers for sync/async batch job handles."""

    def __init__(self, client, service, path, job_id, *, results_key, keyed, model, options=None):
        self._client = client
        self._service = service
        self._path = path
        self.id = job_id
        self._results_key = results_key
        self._keyed = keyed
        self._model = model
        self._options = options

    def _params(self, after: int) -> Dict[str, Any]:
        return {"job_id": self.id, "after": after}


class BatchJob(_BaseJob):
    """A handle to an async batch job. Collect results with :meth:`wait` or :meth:`stream`."""

    def _poll(self, after: int) -> Dict[str, Any]:
        r = self._client._transport.request(
            "GET", self._service, self._path, params=self._params(after), options=self._options
        )
        if r.error is not None:
            raise r.error
        return r.data or {}

    def status(self) -> Dict[str, Any]:
        """Current job meta (status / total / resolved / errors) without collecting."""
        d = self._poll(0)
        return {k: d.get(k) for k in ("status", "total", "resolved", "errors")}

    def stream(self, *, poll_interval: float = 1.5, timeout: Optional[float] = None) -> Iterator[Any]:
        """Yield each result as it resolves (a generator).

        Polls the job and yields rows as pages complete, returning when the job
        is finished. Use this to process results progressively instead of
        blocking for the whole job with :meth:`wait`.

        Example::

            for row in client.emails.verify_batch(emails).stream():
                print(row.email, row.deliverable)
        """
        after = 0
        deadline = None if timeout is None else time.monotonic() + timeout
        not_found: List[str] = []
        while True:
            d = self._poll(after)
            for row in _rows(d, self._results_key, self._keyed, self._model):
                yield row
            for nf in d.get("not_found") or []:
                not_found.append(nf)
            self._last_meta = d
            nc = d.get("next_cursor")
            if nc is not None and nc != after:
                after = nc
                continue
            if d.get("status") in ("completed", "error"):
                self._not_found = not_found
                return
            if deadline is not None and time.monotonic() >= deadline:
                self._not_found = not_found
                return
            time.sleep(poll_interval)

    def wait(self, *, poll_interval: float = 1.5, timeout: Optional[float] = None, on_progress=None) -> BatchResult:
        """Block until the job finishes, returning all results."""
        results: List[Any] = []
        for row in self.stream(poll_interval=poll_interval, timeout=timeout):
            results.append(row)
            if on_progress is not None:
                on_progress(len(results))
        m = getattr(self, "_last_meta", {})
        return BatchResult(
            m.get("status", "unknown"), m.get("total", 0), m.get("resolved", len(results)),
            m.get("errors", 0), results, getattr(self, "_not_found", []),
        )


class AsyncBatchJob(_BaseJob):
    """Async handle to a batch job. See :class:`BatchJob`."""

    async def _poll(self, after: int) -> Dict[str, Any]:
        r = await self._client._transport.request(
            "GET", self._service, self._path, params=self._params(after), options=self._options
        )
        if r.error is not None:
            raise r.error
        return r.data or {}

    async def status(self) -> Dict[str, Any]:
        """Current job meta (status/total/resolved/errors). See :meth:`BatchJob.status`."""
        d = await self._poll(0)
        return {k: d.get(k) for k in ("status", "total", "resolved", "errors")}

    async def stream(self, *, poll_interval: float = 1.5, timeout: Optional[float] = None):
        """Async generator yielding results as they resolve. See :meth:`BatchJob.stream`."""
        after = 0
        deadline = None if timeout is None else time.monotonic() + timeout
        not_found: List[str] = []
        while True:
            d = await self._poll(after)
            for row in _rows(d, self._results_key, self._keyed, self._model):
                yield row
            for nf in d.get("not_found") or []:
                not_found.append(nf)
            self._last_meta = d
            nc = d.get("next_cursor")
            if nc is not None and nc != after:
                after = nc
                continue
            if d.get("status") in ("completed", "error"):
                self._not_found = not_found
                return
            if deadline is not None and time.monotonic() >= deadline:
                self._not_found = not_found
                return
            await asyncio.sleep(poll_interval)

    async def wait(self, *, poll_interval: float = 1.5, timeout: Optional[float] = None, on_progress=None) -> BatchResult:
        """Await until the job finishes, returning all results. See :meth:`BatchJob.wait`."""
        results: List[Any] = []
        async for row in self.stream(poll_interval=poll_interval, timeout=timeout):
            results.append(row)
            if on_progress is not None:
                on_progress(len(results))
        m = getattr(self, "_last_meta", {})
        return BatchResult(
            m.get("status", "unknown"), m.get("total", 0), m.get("resolved", len(results)),
            m.get("errors", 0), results, getattr(self, "_not_found", []),
        )
