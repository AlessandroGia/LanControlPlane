from pydantic import BaseModel, ConfigDict


class MessageBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
