
from typing import Optional, List, Any
from pydantic import BaseModel

class OCRRequest(BaseModel):
    image_base64: str
    target_text: Optional[str] = ""
    max_side: Optional[int] = 480
    use_angle_cls: Optional[bool] = False
    
    # Optional: Region of interest (from old code)
    # region: Optional[List[int]] = None 

class OCRResponse(BaseModel):
    code: int
    data: Any
    msg: str = "success"
