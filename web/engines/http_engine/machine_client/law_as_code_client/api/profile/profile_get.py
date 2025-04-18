from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.profile_get_response_200 import ProfileGetResponse200
from ...models.profile_get_response_400 import ProfileGetResponse400
from ...models.profile_get_response_404 import ProfileGetResponse404
from ...models.profile_get_response_500 import ProfileGetResponse500
from ...types import Response


def _get_kwargs(
    bsn: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/profiles/{bsn}",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ProfileGetResponse200, ProfileGetResponse400, ProfileGetResponse404, ProfileGetResponse500]]:
    if response.status_code == 200:
        response_200 = ProfileGetResponse200.from_dict(response.json())

        return response_200
    if response.status_code == 400:
        response_400 = ProfileGetResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 404:
        response_404 = ProfileGetResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 500:
        response_500 = ProfileGetResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[ProfileGetResponse200, ProfileGetResponse400, ProfileGetResponse404, ProfileGetResponse500]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    bsn: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[ProfileGetResponse200, ProfileGetResponse400, ProfileGetResponse404, ProfileGetResponse500]]:
    """Get all profiles

    Args:
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ProfileGetResponse200, ProfileGetResponse400, ProfileGetResponse404, ProfileGetResponse500]]
    """

    kwargs = _get_kwargs(
        bsn=bsn,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    bsn: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[ProfileGetResponse200, ProfileGetResponse400, ProfileGetResponse404, ProfileGetResponse500]]:
    """Get all profiles

    Args:
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ProfileGetResponse200, ProfileGetResponse400, ProfileGetResponse404, ProfileGetResponse500]
    """

    return sync_detailed(
        bsn=bsn,
        client=client,
    ).parsed


async def asyncio_detailed(
    bsn: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[ProfileGetResponse200, ProfileGetResponse400, ProfileGetResponse404, ProfileGetResponse500]]:
    """Get all profiles

    Args:
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ProfileGetResponse200, ProfileGetResponse400, ProfileGetResponse404, ProfileGetResponse500]]
    """

    kwargs = _get_kwargs(
        bsn=bsn,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    bsn: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[ProfileGetResponse200, ProfileGetResponse400, ProfileGetResponse404, ProfileGetResponse500]]:
    """Get all profiles

    Args:
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ProfileGetResponse200, ProfileGetResponse400, ProfileGetResponse404, ProfileGetResponse500]
    """

    return (
        await asyncio_detailed(
            bsn=bsn,
            client=client,
        )
    ).parsed
