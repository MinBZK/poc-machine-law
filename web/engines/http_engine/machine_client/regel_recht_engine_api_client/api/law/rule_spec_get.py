import datetime
from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.rule_spec_get_response_200 import RuleSpecGetResponse200
from ...models.rule_spec_get_response_400 import RuleSpecGetResponse400
from ...models.rule_spec_get_response_500 import RuleSpecGetResponse500
from ...types import UNSET, Response


def _get_kwargs(
    *,
    service: str,
    law: str,
    reference_date: datetime.date,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["service"] = service

    params["law"] = law

    json_reference_date = reference_date.isoformat()
    params["referenceDate"] = json_reference_date

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/rule-spec",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[RuleSpecGetResponse200, RuleSpecGetResponse400, RuleSpecGetResponse500]]:
    if response.status_code == 200:
        response_200 = RuleSpecGetResponse200.from_dict(response.json())

        return response_200
    if response.status_code == 400:
        response_400 = RuleSpecGetResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 500:
        response_500 = RuleSpecGetResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[RuleSpecGetResponse200, RuleSpecGetResponse400, RuleSpecGetResponse500]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    service: str,
    law: str,
    reference_date: datetime.date,
) -> Response[Union[RuleSpecGetResponse200, RuleSpecGetResponse400, RuleSpecGetResponse500]]:
    """Get rule spec

    Args:
        service (str):  Example: TOESLAGEN.
        law (str):  Example: zorgtoeslagwet.
        reference_date (datetime.date): reference date Example: 2025-01-31.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[RuleSpecGetResponse200, RuleSpecGetResponse400, RuleSpecGetResponse500]]
    """

    kwargs = _get_kwargs(
        service=service,
        law=law,
        reference_date=reference_date,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    service: str,
    law: str,
    reference_date: datetime.date,
) -> Optional[Union[RuleSpecGetResponse200, RuleSpecGetResponse400, RuleSpecGetResponse500]]:
    """Get rule spec

    Args:
        service (str):  Example: TOESLAGEN.
        law (str):  Example: zorgtoeslagwet.
        reference_date (datetime.date): reference date Example: 2025-01-31.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[RuleSpecGetResponse200, RuleSpecGetResponse400, RuleSpecGetResponse500]
    """

    return sync_detailed(
        client=client,
        service=service,
        law=law,
        reference_date=reference_date,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    service: str,
    law: str,
    reference_date: datetime.date,
) -> Response[Union[RuleSpecGetResponse200, RuleSpecGetResponse400, RuleSpecGetResponse500]]:
    """Get rule spec

    Args:
        service (str):  Example: TOESLAGEN.
        law (str):  Example: zorgtoeslagwet.
        reference_date (datetime.date): reference date Example: 2025-01-31.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[RuleSpecGetResponse200, RuleSpecGetResponse400, RuleSpecGetResponse500]]
    """

    kwargs = _get_kwargs(
        service=service,
        law=law,
        reference_date=reference_date,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    service: str,
    law: str,
    reference_date: datetime.date,
) -> Optional[Union[RuleSpecGetResponse200, RuleSpecGetResponse400, RuleSpecGetResponse500]]:
    """Get rule spec

    Args:
        service (str):  Example: TOESLAGEN.
        law (str):  Example: zorgtoeslagwet.
        reference_date (datetime.date): reference date Example: 2025-01-31.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[RuleSpecGetResponse200, RuleSpecGetResponse400, RuleSpecGetResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            service=service,
            law=law,
            reference_date=reference_date,
        )
    ).parsed
