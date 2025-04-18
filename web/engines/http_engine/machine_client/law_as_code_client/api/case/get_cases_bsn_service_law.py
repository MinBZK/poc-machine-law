from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_cases_bsn_service_law_response_200 import GetCasesBsnServiceLawResponse200
from ...models.get_cases_bsn_service_law_response_400 import GetCasesBsnServiceLawResponse400
from ...models.get_cases_bsn_service_law_response_404 import GetCasesBsnServiceLawResponse404
from ...models.get_cases_bsn_service_law_response_500 import GetCasesBsnServiceLawResponse500
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
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        GetCasesBsnServiceLawResponse200,
        GetCasesBsnServiceLawResponse400,
        GetCasesBsnServiceLawResponse404,
        GetCasesBsnServiceLawResponse500,
    ]
]:
    if response.status_code == 200:
        response_200 = GetCasesBsnServiceLawResponse200.from_dict(response.json())

        return response_200
    if response.status_code == 400:
        response_400 = GetCasesBsnServiceLawResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 404:
        response_404 = GetCasesBsnServiceLawResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 500:
        response_500 = GetCasesBsnServiceLawResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        GetCasesBsnServiceLawResponse200,
        GetCasesBsnServiceLawResponse400,
        GetCasesBsnServiceLawResponse404,
        GetCasesBsnServiceLawResponse500,
    ]
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
    client: Union[AuthenticatedClient, Client],
) -> Response[
    Union[
        GetCasesBsnServiceLawResponse200,
        GetCasesBsnServiceLawResponse400,
        GetCasesBsnServiceLawResponse404,
        GetCasesBsnServiceLawResponse500,
    ]
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
        Response[Union[GetCasesBsnServiceLawResponse200, GetCasesBsnServiceLawResponse400, GetCasesBsnServiceLawResponse404, GetCasesBsnServiceLawResponse500]]
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
    client: Union[AuthenticatedClient, Client],
) -> Optional[
    Union[
        GetCasesBsnServiceLawResponse200,
        GetCasesBsnServiceLawResponse400,
        GetCasesBsnServiceLawResponse404,
        GetCasesBsnServiceLawResponse500,
    ]
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
        Union[GetCasesBsnServiceLawResponse200, GetCasesBsnServiceLawResponse400, GetCasesBsnServiceLawResponse404, GetCasesBsnServiceLawResponse500]
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
    client: Union[AuthenticatedClient, Client],
) -> Response[
    Union[
        GetCasesBsnServiceLawResponse200,
        GetCasesBsnServiceLawResponse400,
        GetCasesBsnServiceLawResponse404,
        GetCasesBsnServiceLawResponse500,
    ]
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
        Response[Union[GetCasesBsnServiceLawResponse200, GetCasesBsnServiceLawResponse400, GetCasesBsnServiceLawResponse404, GetCasesBsnServiceLawResponse500]]
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
    client: Union[AuthenticatedClient, Client],
) -> Optional[
    Union[
        GetCasesBsnServiceLawResponse200,
        GetCasesBsnServiceLawResponse400,
        GetCasesBsnServiceLawResponse404,
        GetCasesBsnServiceLawResponse500,
    ]
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
        Union[GetCasesBsnServiceLawResponse200, GetCasesBsnServiceLawResponse400, GetCasesBsnServiceLawResponse404, GetCasesBsnServiceLawResponse500]
    """

    return (
        await asyncio_detailed(
            bsn=bsn,
            service=service,
            law=law,
            client=client,
        )
    ).parsed
