from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, __version__ as pydantic_version

T = TypeVar("T")

if pydantic_version.startswith("1."):
    from pydantic.generics import GenericModel
    class APIResponse(GenericModel, Generic[T]):
        status: str
        message: str
        data: Optional[T] = None
else:
    class APIResponse(BaseModel, Generic[T]):
        status: str
        message: str
        data: Optional[T] = None
