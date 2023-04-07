from pydantic import BaseModel
from typing import Optional, Dict


class ResponseSchema(BaseModel):
    status: str = "success"
    message: str
