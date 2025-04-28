from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_cases_service_law_response_200 import GetCasesServiceLawResponse200
from ...models.get_cases_service_law_response_400 import GetCasesServiceLawResponse400
from ...models.get_cases_service_law_response_500 import GetCasesServiceLawResponse500
from ...types import Response


def _get_kwargs(
    service: str,
    law: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/cases/{service}/{law}",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetCasesServiceLawResponse200, GetCasesServiceLawResponse400, GetCasesServiceLawResponse500]]:
    if response.status_code == 200:
        response_200 = GetCasesServiceLawResponse200.from_dict(response.json())

        return response_200
    if response.status_code == 400:
        response_400 = GetCasesServiceLawResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 500:
        response_500 = GetCasesServiceLawResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[GetCasesServiceLawResponse200, GetCasesServiceLawResponse400, GetCasesServiceLawResponse500]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    service: str,
    law: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[GetCasesServiceLawResponse200, GetCasesServiceLawResponse400, GetCasesServiceLawResponse500]]:
    """Get all cases based on service and law

    Args:
        service (str):  Example: TOESLAGEN.
        law (str):  Example: zorgtoeslagwet.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetCasesServiceLawResponse200, GetCasesServiceLawResponse400, GetCasesServiceLawResponse500]]
    """

    kwargs = _get_kwargs(
        service=service,
        law=law,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    service: str,
    law: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[GetCasesServiceLawResponse200, GetCasesServiceLawResponse400, GetCasesServiceLawResponse500]]:
    """Get all cases based on service and law

    Args:
        service (str):  Example: TOESLAGEN.
        law (str):  Example: zorgtoeslagwet.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetCasesServiceLawResponse200, GetCasesServiceLawResponse400, GetCasesServiceLawResponse500]
    """

    return sync_detailed(
        service=service,
        law=law,
        client=client,
    ).parsed


async def asyncio_detailed(
    service: str,
    law: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[GetCasesServiceLawResponse200, GetCasesServiceLawResponse400, GetCasesServiceLawResponse500]]:
    """Get all cases based on service and law

    Args:
        service (str):  Example: TOESLAGEN.
        law (str):  Example: zorgtoeslagwet.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetCasesServiceLawResponse200, GetCasesServiceLawResponse400, GetCasesServiceLawResponse500]]
    """

    kwargs = _get_kwargs(
        service=service,
        law=law,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    service: str,
    law: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[GetCasesServiceLawResponse200, GetCasesServiceLawResponse400, GetCasesServiceLawResponse500]]:
    """Get all cases based on service and law

    Args:
        service (str):  Example: TOESLAGEN.
        law (str):  Example: zorgtoeslagwet.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetCasesServiceLawResponse200, GetCasesServiceLawResponse400, GetCasesServiceLawResponse500]
    """

    return (
        await asyncio_detailed(
            service=service,
            law=law,
            client=client,
        )
    ).parsed
