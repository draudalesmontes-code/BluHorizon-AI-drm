from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field
from services.postgres.auth_store import register_user, get_user_by_email, pwd_context
from services.jwt import create_token, verify_token

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str =  Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str =  Field(min_length=8)


@router.post("/register")
async def register(request: RegisterRequest):
    ##check account doesnt exist
    user =  get_user_by_email(request.email)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")  
    
    ##make insertion to db
    user_id = register_user(request.email, request.password)
    return {"id":user_id, "email": request.email}



@router.post("/login")
async def login(request: LoginRequest):
    user =  get_user_by_email(request.email)
    if user == None:
        raise HTTPException(status_code=400, detail="Account does not exist")  
    
    if not pwd_context.verify(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(user["id"])
    return {"access_token": token, "token_type": "bearer"}