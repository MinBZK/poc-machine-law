import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.profile_list_response_200 import ProfileListResponse200
from ...models.profile_list_response_400 import ProfileListResponse400
from ...models.profile_list_response_500 import ProfileListResponse500
from ...types import UNSET, Response, Unset


def _get_kwargs(
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
        "url": "/profiles",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ProfileListResponse200 | ProfileListResponse400 | ProfileListResponse500 | None:
    if response.status_code == 200:
        response_200 = ProfileListResponse200.from_dict(response.json())

        return response_200
    if response.status_code == 400:
        response_400 = ProfileListResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 500:
        response_500 = ProfileListResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ProfileListResponse200 | ProfileListResponse400 | ProfileListResponse500]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    effective_date: Unset | datetime.date = UNSET,
) -> Response[ProfileListResponse200 | ProfileListResponse400 | ProfileListResponse500]:
    """Get all profiles

    Args:
        effective_date (Union[Unset, datetime.date]):  Example: 2025-01-31.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ProfileListResponse200, ProfileListResponse400, ProfileListResponse500]]
    """

    kwargs = _get_kwargs(
        effective_date=effective_date,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    effective_date: Unset | datetime.date = UNSET,
) -> ProfileListResponse200 | ProfileListResponse400 | ProfileListResponse500 | None:
    """Get all profiles

    Args:
        effective_date (Union[Unset, datetime.date]):  Example: 2025-01-31.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ProfileListResponse200, ProfileListResponse400, ProfileListResponse500]
    """

    return sync_detailed(
        client=client,
        effective_date=effective_date,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    effective_date: Unset | datetime.date = UNSET,
) -> Response[ProfileListResponse200 | ProfileListResponse400 | ProfileListResponse500]:
    """Get all profiles

    Args:
        effective_date (Union[Unset, datetime.date]):  Example: 2025-01-31.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ProfileListResponse200, ProfileListResponse400, ProfileListResponse500]]
    """

    kwargs = _get_kwargs(
        effective_date=effective_date,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    effective_date: Unset | datetime.date = UNSET,
) -> ProfileListResponse200 | ProfileListResponse400 | ProfileListResponse500 | None:
    """Get all profiles

    Args:
        effective_date (Union[Unset, datetime.date]):  Example: 2025-01-31.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ProfileListResponse200, ProfileListResponse400, ProfileListResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            effective_date=effective_date,
        )
    ).parsed
