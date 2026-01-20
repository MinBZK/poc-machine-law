"""Contains some shared types for properties"""

from collections.abc import MutableMapping
from http import HTTPStatus
from typing import BinaryIO, Generic, Literal, TypeVar

from attrs import define


class Unset:
    def __bool__(self) -> Literal[False]:
        return False


UNSET: Unset = Unset()

FileJsonType = tuple[str | None, BinaryIO, str | None]


@define
class File:
    """Contains information for file uploads"""

    payload: BinaryIO
    file_name: str | None = None
    mime_type: str | None = None

    def to_tuple(self) -> FileJsonType:
        """Return a tuple representation that httpx will accept for multipart/form-data"""
        return self.file_name, self.payload, self.mime_type


T = TypeVar("T")


@define
class Response(Generic[T]):
    """A response from an endpoint"""

    status_code: HTTPStatus
    content: bytes
    headers: MutableMapping[str, str]
    parsed: T | None


__all__ = ["UNSET", "File", "FileJsonType", "Response", "Unset"]
