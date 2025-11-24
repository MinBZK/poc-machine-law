from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.claim_list_based_on_bsn_response_200 import ClaimListBasedOnBSNResponse200
from ...models.claim_list_based_on_bsn_response_400 import ClaimListBasedOnBSNResponse400
from ...models.claim_list_based_on_bsn_response_500 import ClaimListBasedOnBSNResponse500
from ...types import UNSET, Response, Unset


def _get_kwargs(
    bsn: str,
    *,
    approved: Union[Unset, bool] = UNSET,
    include_rejected: Union[Unset, bool] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["approved"] = approved

    params["includeRejected"] = include_rejected

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/claims/{bsn}",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ClaimListBasedOnBSNResponse200, ClaimListBasedOnBSNResponse400, ClaimListBasedOnBSNResponse500]]:
    if response.status_code == 200:
        response_200 = ClaimListBasedOnBSNResponse200.from_dict(response.json())

        return response_200
    if response.status_code == 400:
        response_400 = ClaimListBasedOnBSNResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 500:
        response_500 = ClaimListBasedOnBSNResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[ClaimListBasedOnBSNResponse200, ClaimListBasedOnBSNResponse400, ClaimListBasedOnBSNResponse500]]:
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
    approved: Union[Unset, bool] = UNSET,
    include_rejected: Union[Unset, bool] = UNSET,
) -> Response[Union[ClaimListBasedOnBSNResponse200, ClaimListBasedOnBSNResponse400, ClaimListBasedOnBSNResponse500]]:
    """Get all claims

    Args:
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.
        approved (Union[Unset, bool]):  Example: True.
        include_rejected (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ClaimListBasedOnBSNResponse200, ClaimListBasedOnBSNResponse400, ClaimListBasedOnBSNResponse500]]
    """

    kwargs = _get_kwargs(
        bsn=bsn,
        approved=approved,
        include_rejected=include_rejected,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    bsn: str,
    *,
    client: Union[AuthenticatedClient, Client],
    approved: Union[Unset, bool] = UNSET,
    include_rejected: Union[Unset, bool] = UNSET,
) -> Optional[Union[ClaimListBasedOnBSNResponse200, ClaimListBasedOnBSNResponse400, ClaimListBasedOnBSNResponse500]]:
    """Get all claims

    Args:
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.
        approved (Union[Unset, bool]):  Example: True.
        include_rejected (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ClaimListBasedOnBSNResponse200, ClaimListBasedOnBSNResponse400, ClaimListBasedOnBSNResponse500]
    """

    return sync_detailed(
        bsn=bsn,
        client=client,
        approved=approved,
        include_rejected=include_rejected,
    ).parsed


async def asyncio_detailed(
    bsn: str,
    *,
    client: Union[AuthenticatedClient, Client],
    approved: Union[Unset, bool] = UNSET,
    include_rejected: Union[Unset, bool] = UNSET,
) -> Response[Union[ClaimListBasedOnBSNResponse200, ClaimListBasedOnBSNResponse400, ClaimListBasedOnBSNResponse500]]:
    """Get all claims

    Args:
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.
        approved (Union[Unset, bool]):  Example: True.
        include_rejected (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ClaimListBasedOnBSNResponse200, ClaimListBasedOnBSNResponse400, ClaimListBasedOnBSNResponse500]]
    """

    kwargs = _get_kwargs(
        bsn=bsn,
        approved=approved,
        include_rejected=include_rejected,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    bsn: str,
    *,
    client: Union[AuthenticatedClient, Client],
    approved: Union[Unset, bool] = UNSET,
    include_rejected: Union[Unset, bool] = UNSET,
) -> Optional[Union[ClaimListBasedOnBSNResponse200, ClaimListBasedOnBSNResponse400, ClaimListBasedOnBSNResponse500]]:
    """Get all claims

    Args:
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.
        approved (Union[Unset, bool]):  Example: True.
        include_rejected (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ClaimListBasedOnBSNResponse200, ClaimListBasedOnBSNResponse400, ClaimListBasedOnBSNResponse500]
    """

    return (
        await asyncio_detailed(
            bsn=bsn,
            client=client,
            approved=approved,
            include_rejected=include_rejected,
        )
    ).parsed
