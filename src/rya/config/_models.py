from pydantic import BaseModel


class RichClickCLITheme(BaseModel):
    name: str = "cargo-modern"
