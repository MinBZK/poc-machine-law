from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.case_submit_body import CaseSubmitBody
from ...models.case_submit_response_201 import CaseSubmitResponse201
from ...models.case_submit_response_400 import CaseSubmitResponse400
from ...models.case_submit_response_500 import CaseSubmitResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: CaseSubmitBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/case",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[CaseSubmitResponse201, CaseSubmitResponse400, CaseSubmitResponse500]]:
    if response.status_code == 201:
        response_201 = CaseSubmitResponse201.from_dict(response.json())

        return response_201
    if response.status_code == 400:
        response_400 = CaseSubmitResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 500:
        response_500 = CaseSubmitResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[CaseSubmitResponse201, CaseSubmitResponse400, CaseSubmitResponse500]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: CaseSubmitBody,
) -> Response[Union[CaseSubmitResponse201, CaseSubmitResponse400, CaseSubmitResponse500]]:
    """Submit a case

    Args:
        body (CaseSubmitBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CaseSubmitResponse201, CaseSubmitResponse400, CaseSubmitResponse500]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: CaseSubmitBody,
) -> Optional[Union[CaseSubmitResponse201, CaseSubmitResponse400, CaseSubmitResponse500]]:
    """Submit a case

    Args:
        body (CaseSubmitBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CaseSubmitResponse201, CaseSubmitResponse400, CaseSubmitResponse500]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: CaseSubmitBody,
) -> Response[Union[CaseSubmitResponse201, CaseSubmitResponse400, CaseSubmitResponse500]]:
    """Submit a case

    Args:
        body (CaseSubmitBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CaseSubmitResponse201, CaseSubmitResponse400, CaseSubmitResponse500]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: CaseSubmitBody,
) -> Optional[Union[CaseSubmitResponse201, CaseSubmitResponse400, CaseSubmitResponse500]]:
    """Submit a case

    Args:
        body (CaseSubmitBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CaseSubmitResponse201, CaseSubmitResponse400, CaseSubmitResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
