from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.set_source_data_frame_body import SetSourceDataFrameBody
from ...models.set_source_data_frame_response_400 import SetSourceDataFrameResponse400
from ...models.set_source_data_frame_response_500 import SetSourceDataFrameResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: SetSourceDataFrameBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/source-dataframe",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, SetSourceDataFrameResponse400, SetSourceDataFrameResponse500]]:
    if response.status_code == 201:
        response_201 = cast(Any, None)
        return response_201
    if response.status_code == 400:
        response_400 = SetSourceDataFrameResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 500:
        response_500 = SetSourceDataFrameResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Any, SetSourceDataFrameResponse400, SetSourceDataFrameResponse500]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: SetSourceDataFrameBody,
) -> Response[Union[Any, SetSourceDataFrameResponse400, SetSourceDataFrameResponse500]]:
    """Set a source data frame

     Inserts data into the engine by setting a source data frame for a specific service and table

    Args:
        body (SetSourceDataFrameBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, SetSourceDataFrameResponse400, SetSourceDataFrameResponse500]]
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
    body: SetSourceDataFrameBody,
) -> Optional[Union[Any, SetSourceDataFrameResponse400, SetSourceDataFrameResponse500]]:
    """Set a source data frame

     Inserts data into the engine by setting a source data frame for a specific service and table

    Args:
        body (SetSourceDataFrameBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, SetSourceDataFrameResponse400, SetSourceDataFrameResponse500]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: SetSourceDataFrameBody,
) -> Response[Union[Any, SetSourceDataFrameResponse400, SetSourceDataFrameResponse500]]:
    """Set a source data frame

     Inserts data into the engine by setting a source data frame for a specific service and table

    Args:
        body (SetSourceDataFrameBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, SetSourceDataFrameResponse400, SetSourceDataFrameResponse500]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: SetSourceDataFrameBody,
) -> Optional[Union[Any, SetSourceDataFrameResponse400, SetSourceDataFrameResponse500]]:
    """Set a source data frame

     Inserts data into the engine by setting a source data frame for a specific service and table

    Args:
        body (SetSourceDataFrameBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, SetSourceDataFrameResponse400, SetSourceDataFrameResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
