from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.event_list_response_200 import EventListResponse200
from ...models.event_list_response_400 import EventListResponse400
from ...models.event_list_response_500 import EventListResponse500
from ...types import Response


def _get_kwargs() -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/events",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> EventListResponse200 | EventListResponse400 | EventListResponse500 | None:
    if response.status_code == 200:
        response_200 = EventListResponse200.from_dict(response.json())

        return response_200
    if response.status_code == 400:
        response_400 = EventListResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 500:
        response_500 = EventListResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[EventListResponse200 | EventListResponse400 | EventListResponse500]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[EventListResponse200 | EventListResponse400 | EventListResponse500]:
    """Get a list of events

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[EventListResponse200, EventListResponse400, EventListResponse500]]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
) -> EventListResponse200 | EventListResponse400 | EventListResponse500 | None:
    """Get a list of events

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[EventListResponse200, EventListResponse400, EventListResponse500]
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[EventListResponse200 | EventListResponse400 | EventListResponse500]:
    """Get a list of events

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[EventListResponse200, EventListResponse400, EventListResponse500]]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> EventListResponse200 | EventListResponse400 | EventListResponse500 | None:
    """Get a list of events

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[EventListResponse200, EventListResponse400, EventListResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
