from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.claim_approve_body import ClaimApproveBody
from ...models.claim_approve_response_200 import ClaimApproveResponse200
from ...models.claim_approve_response_400 import ClaimApproveResponse400
from ...models.claim_approve_response_404 import ClaimApproveResponse404
from ...models.claim_approve_response_500 import ClaimApproveResponse500
from ...types import Response


def _get_kwargs(
    claim_id: UUID,
    *,
    body: ClaimApproveBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/claims/{claim_id}/approve",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[ClaimApproveResponse200, ClaimApproveResponse400, ClaimApproveResponse404, ClaimApproveResponse500]
]:
    if response.status_code == 200:
        response_200 = ClaimApproveResponse200.from_dict(response.json())

        return response_200
    if response.status_code == 400:
        response_400 = ClaimApproveResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 404:
        response_404 = ClaimApproveResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 500:
        response_500 = ClaimApproveResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[ClaimApproveResponse200, ClaimApproveResponse400, ClaimApproveResponse404, ClaimApproveResponse500]
]:
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
    body: ClaimApproveBody,
) -> Response[
    Union[ClaimApproveResponse200, ClaimApproveResponse400, ClaimApproveResponse404, ClaimApproveResponse500]
]:
    """Approve a claim

     Approve a claim with verified value

    Args:
        claim_id (UUID): Identifier of a claim
        body (ClaimApproveBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ClaimApproveResponse200, ClaimApproveResponse400, ClaimApproveResponse404, ClaimApproveResponse500]]
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
    body: ClaimApproveBody,
) -> Optional[
    Union[ClaimApproveResponse200, ClaimApproveResponse400, ClaimApproveResponse404, ClaimApproveResponse500]
]:
    """Approve a claim

     Approve a claim with verified value

    Args:
        claim_id (UUID): Identifier of a claim
        body (ClaimApproveBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ClaimApproveResponse200, ClaimApproveResponse400, ClaimApproveResponse404, ClaimApproveResponse500]
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
    body: ClaimApproveBody,
) -> Response[
    Union[ClaimApproveResponse200, ClaimApproveResponse400, ClaimApproveResponse404, ClaimApproveResponse500]
]:
    """Approve a claim

     Approve a claim with verified value

    Args:
        claim_id (UUID): Identifier of a claim
        body (ClaimApproveBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ClaimApproveResponse200, ClaimApproveResponse400, ClaimApproveResponse404, ClaimApproveResponse500]]
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
    body: ClaimApproveBody,
) -> Optional[
    Union[ClaimApproveResponse200, ClaimApproveResponse400, ClaimApproveResponse404, ClaimApproveResponse500]
]:
    """Approve a claim

     Approve a claim with verified value

    Args:
        claim_id (UUID): Identifier of a claim
        body (ClaimApproveBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ClaimApproveResponse200, ClaimApproveResponse400, ClaimApproveResponse404, ClaimApproveResponse500]
    """

    return (
        await asyncio_detailed(
            claim_id=claim_id,
            client=client,
            body=body,
        )
    ).parsed
