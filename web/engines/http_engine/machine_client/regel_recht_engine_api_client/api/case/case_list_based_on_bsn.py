from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.case_list_based_on_bsn_response_200 import CaseListBasedOnBSNResponse200
from ...models.case_list_based_on_bsn_response_400 import CaseListBasedOnBSNResponse400
from ...models.case_list_based_on_bsn_response_404 import CaseListBasedOnBSNResponse404
from ...models.case_list_based_on_bsn_response_500 import CaseListBasedOnBSNResponse500
from ...types import Response


def _get_kwargs(
    bsn: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/cases/{bsn}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CaseListBasedOnBSNResponse200
    | CaseListBasedOnBSNResponse400
    | CaseListBasedOnBSNResponse404
    | CaseListBasedOnBSNResponse500
    | None
):
    if response.status_code == 200:
        response_200 = CaseListBasedOnBSNResponse200.from_dict(response.json())

        return response_200
    if response.status_code == 400:
        response_400 = CaseListBasedOnBSNResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 404:
        response_404 = CaseListBasedOnBSNResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 500:
        response_500 = CaseListBasedOnBSNResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    CaseListBasedOnBSNResponse200
    | CaseListBasedOnBSNResponse400
    | CaseListBasedOnBSNResponse404
    | CaseListBasedOnBSNResponse500
]:
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
) -> Response[
    CaseListBasedOnBSNResponse200
    | CaseListBasedOnBSNResponse400
    | CaseListBasedOnBSNResponse404
    | CaseListBasedOnBSNResponse500
]:
    """Get all cases based on a bsn

    Args:
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CaseListBasedOnBSNResponse200, CaseListBasedOnBSNResponse400, CaseListBasedOnBSNResponse404, CaseListBasedOnBSNResponse500]]
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
    client: AuthenticatedClient | Client,
) -> (
    CaseListBasedOnBSNResponse200
    | CaseListBasedOnBSNResponse400
    | CaseListBasedOnBSNResponse404
    | CaseListBasedOnBSNResponse500
    | None
):
    """Get all cases based on a bsn

    Args:
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CaseListBasedOnBSNResponse200, CaseListBasedOnBSNResponse400, CaseListBasedOnBSNResponse404, CaseListBasedOnBSNResponse500]
    """

    return sync_detailed(
        bsn=bsn,
        client=client,
    ).parsed


async def asyncio_detailed(
    bsn: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    CaseListBasedOnBSNResponse200
    | CaseListBasedOnBSNResponse400
    | CaseListBasedOnBSNResponse404
    | CaseListBasedOnBSNResponse500
]:
    """Get all cases based on a bsn

    Args:
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CaseListBasedOnBSNResponse200, CaseListBasedOnBSNResponse400, CaseListBasedOnBSNResponse404, CaseListBasedOnBSNResponse500]]
    """

    kwargs = _get_kwargs(
        bsn=bsn,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    bsn: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    CaseListBasedOnBSNResponse200
    | CaseListBasedOnBSNResponse400
    | CaseListBasedOnBSNResponse404
    | CaseListBasedOnBSNResponse500
    | None
):
    """Get all cases based on a bsn

    Args:
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CaseListBasedOnBSNResponse200, CaseListBasedOnBSNResponse400, CaseListBasedOnBSNResponse404, CaseListBasedOnBSNResponse500]
    """

    return (
        await asyncio_detailed(
            bsn=bsn,
            client=client,
        )
    ).parsed
