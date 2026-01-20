from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.case_review_body import CaseReviewBody
from ...models.case_review_response_200 import CaseReviewResponse200
from ...models.case_review_response_400 import CaseReviewResponse400
from ...models.case_review_response_404 import CaseReviewResponse404
from ...models.case_review_response_500 import CaseReviewResponse500
from ...types import Response


def _get_kwargs(
    case_id: UUID,
    *,
    body: CaseReviewBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/cases/{case_id}/review",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CaseReviewResponse200 | CaseReviewResponse400 | CaseReviewResponse404 | CaseReviewResponse500 | None:
    if response.status_code == 200:
        response_200 = CaseReviewResponse200.from_dict(response.json())

        return response_200
    if response.status_code == 400:
        response_400 = CaseReviewResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 404:
        response_404 = CaseReviewResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 500:
        response_500 = CaseReviewResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[CaseReviewResponse200 | CaseReviewResponse400 | CaseReviewResponse404 | CaseReviewResponse500]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    case_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: CaseReviewBody,
) -> Response[CaseReviewResponse200 | CaseReviewResponse400 | CaseReviewResponse404 | CaseReviewResponse500]:
    """Complete a manual review for a case

     Submit a verification decision for a case that requires manual review

    Args:
        case_id (UUID): Identifier of a case
        body (CaseReviewBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CaseReviewResponse200, CaseReviewResponse400, CaseReviewResponse404, CaseReviewResponse500]]
    """

    kwargs = _get_kwargs(
        case_id=case_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    case_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: CaseReviewBody,
) -> CaseReviewResponse200 | CaseReviewResponse400 | CaseReviewResponse404 | CaseReviewResponse500 | None:
    """Complete a manual review for a case

     Submit a verification decision for a case that requires manual review

    Args:
        case_id (UUID): Identifier of a case
        body (CaseReviewBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CaseReviewResponse200, CaseReviewResponse400, CaseReviewResponse404, CaseReviewResponse500]
    """

    return sync_detailed(
        case_id=case_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    case_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: CaseReviewBody,
) -> Response[CaseReviewResponse200 | CaseReviewResponse400 | CaseReviewResponse404 | CaseReviewResponse500]:
    """Complete a manual review for a case

     Submit a verification decision for a case that requires manual review

    Args:
        case_id (UUID): Identifier of a case
        body (CaseReviewBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CaseReviewResponse200, CaseReviewResponse400, CaseReviewResponse404, CaseReviewResponse500]]
    """

    kwargs = _get_kwargs(
        case_id=case_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    case_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: CaseReviewBody,
) -> CaseReviewResponse200 | CaseReviewResponse400 | CaseReviewResponse404 | CaseReviewResponse500 | None:
    """Complete a manual review for a case

     Submit a verification decision for a case that requires manual review

    Args:
        case_id (UUID): Identifier of a case
        body (CaseReviewBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CaseReviewResponse200, CaseReviewResponse400, CaseReviewResponse404, CaseReviewResponse500]
    """

    return (
        await asyncio_detailed(
            case_id=case_id,
            client=client,
            body=body,
        )
    ).parsed
