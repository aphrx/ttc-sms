from pydantic import BaseModel

class UserCreds(BaseModel):
    username: str
    password: str

class User(UserCreds):
    first_name: str
    last_name: str
    avatar_url: str
    bio: str

class BasicUser(BaseModel):
    first_name: str
    last_name: str
    avatar_url: str
    bio: str

class Profile(BaseModel):
    id: int
    username: str
    section: str
    title: str
    body: str
    image_url: str
    priority: int

class About(BaseModel):
    about: str

class Link(BaseModel):
    image_url: str
    title: str
    body: str
    destination_url: str

class DeleteLink(BaseModel):
    id: int