from sqlmodel import SQLModel, Field
from typing import List, Optional
import json

class Course(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    code: str
    credits: float
    cycle: str
    semester: int
    category: str
    type: str
    approved: bool = False
    prereq_json: str = "[]"

    @property
    def prereq(self) -> List[str]:
        return json.loads(self.prereq_json)

    @prereq.setter
    def prereq(self, value: List[str]):
        self.prereq_json = json.dumps(value)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str

class UserCreate(SQLModel):
    username: str
    password: str