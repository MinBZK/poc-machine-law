from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.claim_submit_body import ClaimSubmitBody
from ...models.claim_submit_response_201 import ClaimSubmitResponse201
from ...models.claim_submit_response_400 import ClaimSubmitResponse400
from ...models.claim_submit_response_500 import ClaimSubmitResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: ClaimSubmitBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/claims",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ClaimSubmitResponse201, ClaimSubmitResponse400, ClaimSubmitResponse500]]:
    if response.status_code == 201:
        response_201 = ClaimSubmitResponse201.from_dict(response.json())

        return response_201
    if response.status_code == 400:
        response_400 = ClaimSubmitResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 500:
        response_500 = ClaimSubmitResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[ClaimSubmitResponse201, ClaimSubmitResponse400, ClaimSubmitResponse500]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ClaimSubmitBody,
) -> Response[Union[ClaimSubmitResponse201, ClaimSubmitResponse400, ClaimSubmitResponse500]]:
    """Submit a new claim

     Submit a new claim. Can be linked to an existing case or standalone. If autoApprove is true, the
    claim will be automatically approved.

    Args:
        body (ClaimSubmitBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ClaimSubmitResponse201, ClaimSubmitResponse400, ClaimSubmitResponse500]]
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
    body: ClaimSubmitBody,
) -> Optional[Union[ClaimSubmitResponse201, ClaimSubmitResponse400, ClaimSubmitResponse500]]:
    """Submit a new claim

     Submit a new claim. Can be linked to an existing case or standalone. If autoApprove is true, the
    claim will be automatically approved.

    Args:
        body (ClaimSubmitBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ClaimSubmitResponse201, ClaimSubmitResponse400, ClaimSubmitResponse500]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ClaimSubmitBody,
) -> Response[Union[ClaimSubmitResponse201, ClaimSubmitResponse400, ClaimSubmitResponse500]]:
    """Submit a new claim

     Submit a new claim. Can be linked to an existing case or standalone. If autoApprove is true, the
    claim will be automatically approved.

    Args:
        body (ClaimSubmitBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ClaimSubmitResponse201, ClaimSubmitResponse400, ClaimSubmitResponse500]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ClaimSubmitBody,
) -> Optional[Union[ClaimSubmitResponse201, ClaimSubmitResponse400, ClaimSubmitResponse500]]:
    """Submit a new claim

     Submit a new claim. Can be linked to an existing case or standalone. If autoApprove is true, the
    claim will be automatically approved.

    Args:
        body (ClaimSubmitBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ClaimSubmitResponse201, ClaimSubmitResponse400, ClaimSubmitResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
