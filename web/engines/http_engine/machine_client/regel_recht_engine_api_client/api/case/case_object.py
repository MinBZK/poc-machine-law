from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.case_object_body import CaseObjectBody
from ...models.case_object_response_200 import CaseObjectResponse200
from ...models.case_object_response_400 import CaseObjectResponse400
from ...models.case_object_response_404 import CaseObjectResponse404
from ...models.case_object_response_500 import CaseObjectResponse500
from ...types import Response


def _get_kwargs(
    case_id: UUID,
    *,
    body: CaseObjectBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/cases/{case_id}/object",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[CaseObjectResponse200, CaseObjectResponse400, CaseObjectResponse404, CaseObjectResponse500]]:
    if response.status_code == 200:
        response_200 = CaseObjectResponse200.from_dict(response.json())

        return response_200
    if response.status_code == 400:
        response_400 = CaseObjectResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 404:
        response_404 = CaseObjectResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 500:
        response_500 = CaseObjectResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[CaseObjectResponse200, CaseObjectResponse400, CaseObjectResponse404, CaseObjectResponse500]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    case_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    body: CaseObjectBody,
) -> Response[Union[CaseObjectResponse200, CaseObjectResponse400, CaseObjectResponse404, CaseObjectResponse500]]:
    """Object to a decision on a case

     Submit a objection to a decision of a case

    Args:
        case_id (UUID): Identifier of a case
        body (CaseObjectBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CaseObjectResponse200, CaseObjectResponse400, CaseObjectResponse404, CaseObjectResponse500]]
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
    client: Union[AuthenticatedClient, Client],
    body: CaseObjectBody,
) -> Optional[Union[CaseObjectResponse200, CaseObjectResponse400, CaseObjectResponse404, CaseObjectResponse500]]:
    """Object to a decision on a case

     Submit a objection to a decision of a case

    Args:
        case_id (UUID): Identifier of a case
        body (CaseObjectBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CaseObjectResponse200, CaseObjectResponse400, CaseObjectResponse404, CaseObjectResponse500]
    """

    return sync_detailed(
        case_id=case_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    case_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    body: CaseObjectBody,
) -> Response[Union[CaseObjectResponse200, CaseObjectResponse400, CaseObjectResponse404, CaseObjectResponse500]]:
    """Object to a decision on a case

     Submit a objection to a decision of a case

    Args:
        case_id (UUID): Identifier of a case
        body (CaseObjectBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CaseObjectResponse200, CaseObjectResponse400, CaseObjectResponse404, CaseObjectResponse500]]
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
    client: Union[AuthenticatedClient, Client],
    body: CaseObjectBody,
) -> Optional[Union[CaseObjectResponse200, CaseObjectResponse400, CaseObjectResponse404, CaseObjectResponse500]]:
    """Object to a decision on a case

     Submit a objection to a decision of a case

    Args:
        case_id (UUID): Identifier of a case
        body (CaseObjectBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CaseObjectResponse200, CaseObjectResponse400, CaseObjectResponse404, CaseObjectResponse500]
    """

    return (
        await asyncio_detailed(
            case_id=case_id,
            client=client,
            body=body,
        )
    ).parsed
