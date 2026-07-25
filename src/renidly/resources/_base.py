"""Resource base classes. These translate a transport ``Result`` into the
public return shape according to the client's behavior flags:

- ``unwrap_data_obj=False`` -> always return the full ``APIResponse`` envelope.
- single lookups -> the model, or ``None`` when nothing resolved
  (``raise_on_not_found`` flips that to a ``NotFoundError``).
- other API errors -> raised when ``raise_on_api_error`` (default), else ``None``
  / empty list.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from .._errors import NotFoundError
from .._models import APIResponse, LastResponse, RenidlyModel
from .._pagination import AsyncRenidlyList, RenidlyList
from .._transport import Result

# paginator(envelope, params) -> (items, has_more, next_params, next_cursor)
Paginator = Callable[[Dict[str, Any], Dict[str, Any]], Tuple[List[Any], bool, Optional[Dict[str, Any]], Optional[str]]]


def _models(items: List[Any], model: Type[RenidlyModel], last: LastResponse) -> List[Any]:
    return [model._build(it, last) for it in items]


class _Base:
    """Shared policy application (flags -> models/lists/None) for sync + async resources."""

    def __init__(self, client: Any) -> None:
        self._client = client

    @property
    def _cfg(self):
        return self._client._config

    # ── policy application (shared by sync + async) ──
    def _apply_one(self, r: Result, model: Type[RenidlyModel]) -> Optional[Any]:
        cfg = self._cfg
        if not cfg.unwrap_data_obj:
            return APIResponse._build(r.envelope, r.last_response)
        if r.error is not None:
            if isinstance(r.error, NotFoundError):
                if cfg.raise_on_not_found:
                    raise r.error
                return None
            if cfg.raise_on_api_error:
                raise r.error
            return None
        return None if r.data is None else model._build(r.data, r.last_response)

    def _apply_list(
        self,
        r: Result,
        model: Type[RenidlyModel],
        paginator: Paginator,
        params: Dict[str, Any],
        pager: Optional[Callable[[Dict[str, Any]], Any]],
        list_cls: type,
    ) -> Any:
        cfg = self._cfg
        if not cfg.unwrap_data_obj:
            return APIResponse._build(r.envelope, r.last_response)
        if r.error is not None:
            if cfg.raise_on_api_error:
                raise r.error
            return list_cls([], has_more=False)
        items, has_more, next_params, next_cursor = paginator(r.envelope, params)
        return list_cls(
            _models(items, model, r.last_response),
            has_more=has_more,
            next_params=next_params,
            next_cursor=next_cursor,
            pager=pager,
            raw=r.envelope.get("pagination") or {},
        )


class SyncResource(_Base):
    """Base for synchronous resource groups."""

    def _one(self, service, method, path, *, params=None, json=None, model=RenidlyModel, options=None) -> Optional[RenidlyModel]:
        r = self._client._transport.request(method, service, path, params=params, json=json, options=options)
        return self._apply_one(r, model)

    def _list(self, service, method, path, *, params=None, model=RenidlyModel, paginator, options=None) -> RenidlyList[RenidlyModel]:
        params = params or {}
        r = self._client._transport.request(method, service, path, params=params, options=options)

        def pager(next_params: Dict[str, Any]) -> RenidlyList[RenidlyModel]:
            return self._list(
                service, method, path, params=next_params, model=model, paginator=paginator, options=options
            )

        return self._apply_list(r, model, paginator, params, pager, RenidlyList)


class AsyncResource(_Base):
    """Base for asynchronous resource groups."""

    async def _one(self, service, method, path, *, params=None, json=None, model=RenidlyModel, options=None) -> Optional[RenidlyModel]:
        r = await self._client._transport.request(method, service, path, params=params, json=json, options=options)
        return self._apply_one(r, model)

    async def _list(self, service, method, path, *, params=None, model=RenidlyModel, paginator, options=None) -> AsyncRenidlyList[RenidlyModel]:
        params = params or {}
        r = await self._client._transport.request(method, service, path, params=params, options=options)

        async def pager(next_params: Dict[str, Any]) -> AsyncRenidlyList[RenidlyModel]:
            return await self._list(
                service, method, path, params=next_params, model=model, paginator=paginator, options=options
            )

        return self._apply_list(r, model, paginator, params, pager, AsyncRenidlyList)
