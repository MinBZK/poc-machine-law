from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.event_list_based_on_case_id_response_200 import EventListBasedOnCaseIDResponse200
from ...models.event_list_based_on_case_id_response_400 import EventListBasedOnCaseIDResponse400
from ...models.event_list_based_on_case_id_response_404 import EventListBasedOnCaseIDResponse404
from ...models.event_list_based_on_case_id_response_500 import EventListBasedOnCaseIDResponse500
from ...types import Response


def _get_kwargs(
    case_id: UUID,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/case/{case_id}/events",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        EventListBasedOnCaseIDResponse200,
        EventListBasedOnCaseIDResponse400,
        EventListBasedOnCaseIDResponse404,
        EventListBasedOnCaseIDResponse500,
    ]
]:
    if response.status_code == 200:
        response_200 = EventListBasedOnCaseIDResponse200.from_dict(response.json())

        return response_200
    if response.status_code == 400:
        response_400 = EventListBasedOnCaseIDResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 404:
        response_404 = EventListBasedOnCaseIDResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 500:
        response_500 = EventListBasedOnCaseIDResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        EventListBasedOnCaseIDResponse200,
        EventListBasedOnCaseIDResponse400,
        EventListBasedOnCaseIDResponse404,
        EventListBasedOnCaseIDResponse500,
    ]
]:
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
) -> Response[
    Union[
        EventListBasedOnCaseIDResponse200,
        EventListBasedOnCaseIDResponse400,
        EventListBasedOnCaseIDResponse404,
        EventListBasedOnCaseIDResponse500,
    ]
]:
    """Get a list of events based on a case id

    Args:
        case_id (UUID): Identifier of a case

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[EventListBasedOnCaseIDResponse200, EventListBasedOnCaseIDResponse400, EventListBasedOnCaseIDResponse404, EventListBasedOnCaseIDResponse500]]
    """

    kwargs = _get_kwargs(
        case_id=case_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    case_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[
    Union[
        EventListBasedOnCaseIDResponse200,
        EventListBasedOnCaseIDResponse400,
        EventListBasedOnCaseIDResponse404,
        EventListBasedOnCaseIDResponse500,
    ]
]:
    """Get a list of events based on a case id

    Args:
        case_id (UUID): Identifier of a case

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[EventListBasedOnCaseIDResponse200, EventListBasedOnCaseIDResponse400, EventListBasedOnCaseIDResponse404, EventListBasedOnCaseIDResponse500]
    """

    return sync_detailed(
        case_id=case_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    case_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[
    Union[
        EventListBasedOnCaseIDResponse200,
        EventListBasedOnCaseIDResponse400,
        EventListBasedOnCaseIDResponse404,
        EventListBasedOnCaseIDResponse500,
    ]
]:
    """Get a list of events based on a case id

    Args:
        case_id (UUID): Identifier of a case

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[EventListBasedOnCaseIDResponse200, EventListBasedOnCaseIDResponse400, EventListBasedOnCaseIDResponse404, EventListBasedOnCaseIDResponse500]]
    """

    kwargs = _get_kwargs(
        case_id=case_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    case_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[
    Union[
        EventListBasedOnCaseIDResponse200,
        EventListBasedOnCaseIDResponse400,
        EventListBasedOnCaseIDResponse404,
        EventListBasedOnCaseIDResponse500,
    ]
]:
    """Get a list of events based on a case id

    Args:
        case_id (UUID): Identifier of a case

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[EventListBasedOnCaseIDResponse200, EventListBasedOnCaseIDResponse400, EventListBasedOnCaseIDResponse404, EventListBasedOnCaseIDResponse500]
    """

    return (
        await asyncio_detailed(
            case_id=case_id,
            client=client,
        )
    ).parsed
