from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.case_based_on_bsn_service_law_response_200 import CaseBasedOnBSNServiceLawResponse200
from ...models.case_based_on_bsn_service_law_response_400 import CaseBasedOnBSNServiceLawResponse400
from ...models.case_based_on_bsn_service_law_response_404 import CaseBasedOnBSNServiceLawResponse404
from ...models.case_based_on_bsn_service_law_response_500 import CaseBasedOnBSNServiceLawResponse500
from ...types import Response


def _get_kwargs(
    bsn: str,
    service: str,
    law: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/cases/{bsn}/{service}/{law}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CaseBasedOnBSNServiceLawResponse200
    | CaseBasedOnBSNServiceLawResponse400
    | CaseBasedOnBSNServiceLawResponse404
    | CaseBasedOnBSNServiceLawResponse500
    | None
):
    if response.status_code == 200:
        response_200 = CaseBasedOnBSNServiceLawResponse200.from_dict(response.json())

        return response_200
    if response.status_code == 400:
        response_400 = CaseBasedOnBSNServiceLawResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 404:
        response_404 = CaseBasedOnBSNServiceLawResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 500:
        response_500 = CaseBasedOnBSNServiceLawResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    CaseBasedOnBSNServiceLawResponse200
    | CaseBasedOnBSNServiceLawResponse400
    | CaseBasedOnBSNServiceLawResponse404
    | CaseBasedOnBSNServiceLawResponse500
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    bsn: str,
    service: str,
    law: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    CaseBasedOnBSNServiceLawResponse200
    | CaseBasedOnBSNServiceLawResponse400
    | CaseBasedOnBSNServiceLawResponse404
    | CaseBasedOnBSNServiceLawResponse500
]:
    """Get a case based on bsn, service and law

    Args:
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.
        service (str):  Example: TOESLAGEN.
        law (str):  Example: zorgtoeslagwet.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CaseBasedOnBSNServiceLawResponse200, CaseBasedOnBSNServiceLawResponse400, CaseBasedOnBSNServiceLawResponse404, CaseBasedOnBSNServiceLawResponse500]]
    """

    kwargs = _get_kwargs(
        bsn=bsn,
        service=service,
        law=law,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    bsn: str,
    service: str,
    law: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    CaseBasedOnBSNServiceLawResponse200
    | CaseBasedOnBSNServiceLawResponse400
    | CaseBasedOnBSNServiceLawResponse404
    | CaseBasedOnBSNServiceLawResponse500
    | None
):
    """Get a case based on bsn, service and law

    Args:
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.
        service (str):  Example: TOESLAGEN.
        law (str):  Example: zorgtoeslagwet.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CaseBasedOnBSNServiceLawResponse200, CaseBasedOnBSNServiceLawResponse400, CaseBasedOnBSNServiceLawResponse404, CaseBasedOnBSNServiceLawResponse500]
    """

    return sync_detailed(
        bsn=bsn,
        service=service,
        law=law,
        client=client,
    ).parsed


async def asyncio_detailed(
    bsn: str,
    service: str,
    law: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    CaseBasedOnBSNServiceLawResponse200
    | CaseBasedOnBSNServiceLawResponse400
    | CaseBasedOnBSNServiceLawResponse404
    | CaseBasedOnBSNServiceLawResponse500
]:
    """Get a case based on bsn, service and law

    Args:
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.
        service (str):  Example: TOESLAGEN.
        law (str):  Example: zorgtoeslagwet.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CaseBasedOnBSNServiceLawResponse200, CaseBasedOnBSNServiceLawResponse400, CaseBasedOnBSNServiceLawResponse404, CaseBasedOnBSNServiceLawResponse500]]
    """

    kwargs = _get_kwargs(
        bsn=bsn,
        service=service,
        law=law,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    bsn: str,
    service: str,
    law: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    CaseBasedOnBSNServiceLawResponse200
    | CaseBasedOnBSNServiceLawResponse400
    | CaseBasedOnBSNServiceLawResponse404
    | CaseBasedOnBSNServiceLawResponse500
    | None
):
    """Get a case based on bsn, service and law

    Args:
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.
        service (str):  Example: TOESLAGEN.
        law (str):  Example: zorgtoeslagwet.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CaseBasedOnBSNServiceLawResponse200, CaseBasedOnBSNServiceLawResponse400, CaseBasedOnBSNServiceLawResponse404, CaseBasedOnBSNServiceLawResponse500]
    """

    return (
        await asyncio_detailed(
            bsn=bsn,
            service=service,
            law=law,
            client=client,
        )
    ).parsed
