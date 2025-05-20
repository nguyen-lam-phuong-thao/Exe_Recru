"""Base model"""

from typing import TypeVar

from fastapi import Body
from pydantic import BaseModel, ConfigDict


T = TypeVar('T')


class RequestSchema(BaseModel):
	"""BaseRequest"""


class ResponseSchema(BaseModel):
	"""ResponseSchema"""

	model_config = ConfigDict(from_attributes=True)


class APIResponse(BaseModel):
	"""APIResponse"""

	error_code: int | None = Body(default=1, description='Mã lỗi', examples=[0])
	message: str | None = Body(default=None, description='Thông báo lỗi', examples=['Thao tác thành công'])
	description: str | None = Body(default=None, description='Chi tiết lỗi', examples=[''])
	data: T | None = Body(default=None, description='Dữ liệu trả về')
