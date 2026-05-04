from fastapi import APIRouter, Depends, HTTPException

from auth import (
    LoginRequest,
    TokenResponse,
    User,
    authenticate_user,
    create_token,
    get_current_user,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    user = authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user.username, user.role)
    return TokenResponse(access_token=token, role=user.role)


@router.get("/me", response_model=User)
def me(user: User = Depends(get_current_user)):
    return user
