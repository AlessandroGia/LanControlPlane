from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class UserMeRead(BaseModel):
    id: str
    username: str
    role: str
