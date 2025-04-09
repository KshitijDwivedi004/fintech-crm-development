from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Successful(BaseModel):
    detail: Optional[str] = None 



class ProfilePic(BaseModel):
    id: str
    filename: str
    filetype: str
    filesize: int
    container: str
    filepath: str
    created_on: datetime
    updated_on: datetime
    image_url: str 
