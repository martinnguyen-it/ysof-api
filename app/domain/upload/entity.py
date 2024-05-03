from typing import Optional
from pydantic import BaseModel


class GoogleDriveAPIRes(BaseModel):
    id: str
    mimeType: str
    name: Optional[str] = None


class ImageRes(BaseModel):
    url: str
