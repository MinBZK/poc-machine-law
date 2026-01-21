import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.profile_get_response_200 import ProfileGetResponse200
from ...models.profile_get_response_400 import ProfileGetResponse400
from ...models.profile_get_response_404 import ProfileGetResponse404
from ...models.profile_get_response_500 import ProfileGetResponse500
from ...types import UNSET, Response, Unset


def _get_kwargs(
    bsn: str,
    *,
    effective_date: Unset | datetime.date = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_effective_date: Unset | str = UNSET
    if not isinstance(effective_date, Unset):
        json_effective_date = effective_date.isoformat()
    params["effective_date"] = json_effective_date

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/profiles/{bsn}",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ProfileGetResponse200 | ProfileGetResponse400 | ProfileGetResponse404 | ProfileGetResponse500 | None:
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
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ProfileGetResponse200 | ProfileGetResponse400 | ProfileGetResponse404 | ProfileGetResponse500]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    bsn: str,
    *,
    client: AuthenticatedClient | Client,
    effective_date: Unset | datetime.date = UNSET,
) -> Response[ProfileGetResponse200 | ProfileGetResponse400 | ProfileGetResponse404 | ProfileGetResponse500]:
    """Get all profiles

    Args:
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.
        effective_date (Union[Unset, datetime.date]):  Example: 2025-01-31.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ProfileGetResponse200, ProfileGetResponse400, ProfileGetResponse404, ProfileGetResponse500]]
    """

    kwargs = _get_kwargs(
        bsn=bsn,
        effective_date=effective_date,
    )

    try:
        response = client.get_httpx_client().request(
            **kwargs,
        )
    except httpx.ConnectError as e:
        raise errors.UnexpectedStatus(0, f"Connection error: {str(e)}".encode())
    except httpx.RequestError as e:
        raise errors.UnexpectedStatus(0, f"Request error: {str(e)}".encode())

    return _build_response(client=client, response=response)


def sync(
    bsn: str,
    *,
    client: AuthenticatedClient | Client,
    effective_date: Unset | datetime.date = UNSET,
) -> ProfileGetResponse200 | ProfileGetResponse400 | ProfileGetResponse404 | ProfileGetResponse500 | None:
    """Get all profiles

    Args:
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.
        effective_date (Union[Unset, datetime.date]):  Example: 2025-01-31.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ProfileGetResponse200, ProfileGetResponse400, ProfileGetResponse404, ProfileGetResponse500]
    """

    return sync_detailed(
        bsn=bsn,
        client=client,
        effective_date=effective_date,
    ).parsed


async def asyncio_detailed(
    bsn: str,
    *,
    client: AuthenticatedClient | Client,
    effective_date: Unset | datetime.date = UNSET,
) -> Response[ProfileGetResponse200 | ProfileGetResponse400 | ProfileGetResponse404 | ProfileGetResponse500]:
    """Get all profiles

    Args:
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.
        effective_date (Union[Unset, datetime.date]):  Example: 2025-01-31.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ProfileGetResponse200, ProfileGetResponse400, ProfileGetResponse404, ProfileGetResponse500]]
    """

    kwargs = _get_kwargs(
        bsn=bsn,
        effective_date=effective_date,
    )

    try:
        response = await client.get_async_httpx_client().request(**kwargs)
    except httpx.ConnectError as e:
        raise errors.UnexpectedStatus(0, f"Connection error: {str(e)}".encode())
    except httpx.RequestError as e:
        raise errors.UnexpectedStatus(0, f"Request error: {str(e)}".encode())

    return _build_response(client=client, response=response)


async def asyncio(
    bsn: str,
    *,
    client: AuthenticatedClient | Client,
    effective_date: Unset | datetime.date = UNSET,
) -> ProfileGetResponse200 | ProfileGetResponse400 | ProfileGetResponse404 | ProfileGetResponse500 | None:
    """Get all profiles

    Args:
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.
        effective_date (Union[Unset, datetime.date]):  Example: 2025-01-31.

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
            effective_date=effective_date,
        )
    ).parsed
