from pydantic import BaseModel
from typing import List

class Course(BaseModel):
    id: str
    name: str
    code: str
    credits: float
    cycle: str
    semester: int
    category: str
    type: str
    approved: bool = False
    prereq: List[str] = []