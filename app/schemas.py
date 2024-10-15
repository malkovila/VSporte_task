from pydantic import BaseModel

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str



class Token(BaseModel):
    access_token: str
    token_type: str

class LoginForm(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    id: int
    username: str
    email: str

class RoleRead(BaseModel):
    id: int
    name: str

class RoleCreate(BaseModel):
    name: str

class ServiceCreate(BaseModel):
    name: str

class UserRoleCreate(BaseModel):
    who_gives_role: str
    username: str
    role: str
    service: str

class UserRoleRead(BaseModel):
    user_id: int
    role_id: int
    service_id: int


class DeleteUserServer(BaseModel):
    who_delete_username: str
    username_to_delete: str
    service: str


class ServiceRead(BaseModel):
    id: int
    name: str


class DeleteUser(BaseModel):
    who_delete_username: str
    username_to_delete: str

class TokenData(BaseModel):
    username: str | None = None



