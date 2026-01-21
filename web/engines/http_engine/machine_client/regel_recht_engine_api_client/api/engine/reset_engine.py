from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.reset_engine_response_400 import ResetEngineResponse400
from ...models.reset_engine_response_500 import ResetEngineResponse500
from ...types import Response


def _get_kwargs() -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/engine/reset",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | ResetEngineResponse400 | ResetEngineResponse500 | None:
    if response.status_code == 201:
        response_201 = cast(Any, None)
        return response_201
    if response.status_code == 400:
        response_400 = ResetEngineResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 500:
        response_500 = ResetEngineResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | ResetEngineResponse400 | ResetEngineResponse500]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | ResetEngineResponse400 | ResetEngineResponse500]:
    """Reset the engine

     Resets the entire engine, clearing all data and returning it to its initial state

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, ResetEngineResponse400, ResetEngineResponse500]]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
) -> Any | ResetEngineResponse400 | ResetEngineResponse500 | None:
    """Reset the engine

     Resets the entire engine, clearing all data and returning it to its initial state

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, ResetEngineResponse400, ResetEngineResponse500]
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | ResetEngineResponse400 | ResetEngineResponse500]:
    """Reset the engine

     Resets the entire engine, clearing all data and returning it to its initial state

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, ResetEngineResponse400, ResetEngineResponse500]]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> Any | ResetEngineResponse400 | ResetEngineResponse500 | None:
    """Reset the engine

     Resets the entire engine, clearing all data and returning it to its initial state

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, ResetEngineResponse400, ResetEngineResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
