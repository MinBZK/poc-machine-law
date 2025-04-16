from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.evaluate_body import EvaluateBody
from ...models.evaluate_response_200 import EvaluateResponse200
from ...models.evaluate_response_400 import EvaluateResponse400
from ...models.evaluate_response_500 import EvaluateResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: EvaluateBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/evaluate",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[EvaluateResponse200, EvaluateResponse400, EvaluateResponse500]]:
    if response.status_code == 200:
        response_200 = EvaluateResponse200.from_dict(response.json())

        return response_200
    if response.status_code == 400:
        response_400 = EvaluateResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 500:
        response_500 = EvaluateResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[EvaluateResponse200, EvaluateResponse400, EvaluateResponse500]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: EvaluateBody,
) -> Response[Union[EvaluateResponse200, EvaluateResponse400, EvaluateResponse500]]:
    """Evaluate the law

    Args:
        body (EvaluateBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[EvaluateResponse200, EvaluateResponse400, EvaluateResponse500]]
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
    body: EvaluateBody,
) -> Optional[Union[EvaluateResponse200, EvaluateResponse400, EvaluateResponse500]]:
    """Evaluate the law

    Args:
        body (EvaluateBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[EvaluateResponse200, EvaluateResponse400, EvaluateResponse500]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: EvaluateBody,
) -> Response[Union[EvaluateResponse200, EvaluateResponse400, EvaluateResponse500]]:
    """Evaluate the law

    Args:
        body (EvaluateBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[EvaluateResponse200, EvaluateResponse400, EvaluateResponse500]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: EvaluateBody,
) -> Optional[Union[EvaluateResponse200, EvaluateResponse400, EvaluateResponse500]]:
    """Evaluate the law

    Args:
        body (EvaluateBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[EvaluateResponse200, EvaluateResponse400, EvaluateResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
