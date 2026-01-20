from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.service_laws_discoverable_list_response_200 import ServiceLawsDiscoverableListResponse200
from ...models.service_laws_discoverable_list_response_400 import ServiceLawsDiscoverableListResponse400
from ...models.service_laws_discoverable_list_response_500 import ServiceLawsDiscoverableListResponse500
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    discoverable_by: Unset | str = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["discoverableBy"] = discoverable_by

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/discoverable-service-laws",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ServiceLawsDiscoverableListResponse200
    | ServiceLawsDiscoverableListResponse400
    | ServiceLawsDiscoverableListResponse500
    | None
):
    if response.status_code == 200:
        response_200 = ServiceLawsDiscoverableListResponse200.from_dict(response.json())

        return response_200
    if response.status_code == 400:
        response_400 = ServiceLawsDiscoverableListResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 500:
        response_500 = ServiceLawsDiscoverableListResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ServiceLawsDiscoverableListResponse200
    | ServiceLawsDiscoverableListResponse400
    | ServiceLawsDiscoverableListResponse500
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    discoverable_by: Unset | str = UNSET,
) -> Response[
    ServiceLawsDiscoverableListResponse200
    | ServiceLawsDiscoverableListResponse400
    | ServiceLawsDiscoverableListResponse500
]:
    """Get all discoverable service & laws

    Args:
        discoverable_by (Union[Unset, str]): DiscoverableBy is a string that can be used to filter
            lists Example: CITIZEN.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ServiceLawsDiscoverableListResponse200, ServiceLawsDiscoverableListResponse400, ServiceLawsDiscoverableListResponse500]]
    """

    kwargs = _get_kwargs(
        discoverable_by=discoverable_by,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    discoverable_by: Unset | str = UNSET,
) -> (
    ServiceLawsDiscoverableListResponse200
    | ServiceLawsDiscoverableListResponse400
    | ServiceLawsDiscoverableListResponse500
    | None
):
    """Get all discoverable service & laws

    Args:
        discoverable_by (Union[Unset, str]): DiscoverableBy is a string that can be used to filter
            lists Example: CITIZEN.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ServiceLawsDiscoverableListResponse200, ServiceLawsDiscoverableListResponse400, ServiceLawsDiscoverableListResponse500]
    """

    return sync_detailed(
        client=client,
        discoverable_by=discoverable_by,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    discoverable_by: Unset | str = UNSET,
) -> Response[
    ServiceLawsDiscoverableListResponse200
    | ServiceLawsDiscoverableListResponse400
    | ServiceLawsDiscoverableListResponse500
]:
    """Get all discoverable service & laws

    Args:
        discoverable_by (Union[Unset, str]): DiscoverableBy is a string that can be used to filter
            lists Example: CITIZEN.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ServiceLawsDiscoverableListResponse200, ServiceLawsDiscoverableListResponse400, ServiceLawsDiscoverableListResponse500]]
    """

    kwargs = _get_kwargs(
        discoverable_by=discoverable_by,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    discoverable_by: Unset | str = UNSET,
) -> (
    ServiceLawsDiscoverableListResponse200
    | ServiceLawsDiscoverableListResponse400
    | ServiceLawsDiscoverableListResponse500
    | None
):
    """Get all discoverable service & laws

    Args:
        discoverable_by (Union[Unset, str]): DiscoverableBy is a string that can be used to filter
            lists Example: CITIZEN.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ServiceLawsDiscoverableListResponse200, ServiceLawsDiscoverableListResponse400, ServiceLawsDiscoverableListResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            discoverable_by=discoverable_by,
        )
    ).parsed
