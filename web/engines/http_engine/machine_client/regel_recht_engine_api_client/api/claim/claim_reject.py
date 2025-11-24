from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.claim_reject_body import ClaimRejectBody
from ...models.claim_reject_response_200 import ClaimRejectResponse200
from ...models.claim_reject_response_400 import ClaimRejectResponse400
from ...models.claim_reject_response_404 import ClaimRejectResponse404
from ...models.claim_reject_response_500 import ClaimRejectResponse500
from ...types import Response


def _get_kwargs(
    claim_id: UUID,
    *,
    body: ClaimRejectBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/claims/{claim_id}/reject",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ClaimRejectResponse200, ClaimRejectResponse400, ClaimRejectResponse404, ClaimRejectResponse500]]:
    if response.status_code == 200:
        response_200 = ClaimRejectResponse200.from_dict(response.json())

        return response_200
    if response.status_code == 400:
        response_400 = ClaimRejectResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 404:
        response_404 = ClaimRejectResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 500:
        response_500 = ClaimRejectResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[ClaimRejectResponse200, ClaimRejectResponse400, ClaimRejectResponse404, ClaimRejectResponse500]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    claim_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    body: ClaimRejectBody,
) -> Response[Union[ClaimRejectResponse200, ClaimRejectResponse400, ClaimRejectResponse404, ClaimRejectResponse500]]:
    """Reject a claim

     Reject a claim with reason

    Args:
        claim_id (UUID): Identifier of a claim
        body (ClaimRejectBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ClaimRejectResponse200, ClaimRejectResponse400, ClaimRejectResponse404, ClaimRejectResponse500]]
    """

    kwargs = _get_kwargs(
        claim_id=claim_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    claim_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    body: ClaimRejectBody,
) -> Optional[Union[ClaimRejectResponse200, ClaimRejectResponse400, ClaimRejectResponse404, ClaimRejectResponse500]]:
    """Reject a claim

     Reject a claim with reason

    Args:
        claim_id (UUID): Identifier of a claim
        body (ClaimRejectBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ClaimRejectResponse200, ClaimRejectResponse400, ClaimRejectResponse404, ClaimRejectResponse500]
    """

    return sync_detailed(
        claim_id=claim_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    claim_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    body: ClaimRejectBody,
) -> Response[Union[ClaimRejectResponse200, ClaimRejectResponse400, ClaimRejectResponse404, ClaimRejectResponse500]]:
    """Reject a claim

     Reject a claim with reason

    Args:
        claim_id (UUID): Identifier of a claim
        body (ClaimRejectBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ClaimRejectResponse200, ClaimRejectResponse400, ClaimRejectResponse404, ClaimRejectResponse500]]
    """

    kwargs = _get_kwargs(
        claim_id=claim_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    claim_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    body: ClaimRejectBody,
) -> Optional[Union[ClaimRejectResponse200, ClaimRejectResponse400, ClaimRejectResponse404, ClaimRejectResponse500]]:
    """Reject a claim

     Reject a claim with reason

    Args:
        claim_id (UUID): Identifier of a claim
        body (ClaimRejectBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ClaimRejectResponse200, ClaimRejectResponse400, ClaimRejectResponse404, ClaimRejectResponse500]
    """

    return (
        await asyncio_detailed(
            claim_id=claim_id,
            client=client,
            body=body,
        )
    ).parsed
