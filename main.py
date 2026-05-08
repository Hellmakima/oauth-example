from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, text
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
import os

app = FastAPI()

# Session middleware for OAuth state management
app.add_middleware(SessionMiddleware, secret_key="your-secret-key-change-in-production")

DATABASE_URL = "postgresql://app:secret@localhost:5432/tweets"
engine = create_engine(DATABASE_URL)

# OAuth configuration for Authentik
oauth = OAuth()
oauth.register(
    name='authentik',
    client_id='jAFCgEtF0xXupqVOPchedmpoEKDVFtoPU3Rbx7Kn',
    client_secret='TL73LxOFXbka5uJ0NiunnFK4wncnk5mrQaqTzp1gUJ1oxNS8YgquGqpycbPj95FV1ZAZFz1u1hbh6hiU5q3F9zh2OU7M4VapMY9KT6Bjrqpuaau9pPLFwAkrGDSPINnp',
    server_metadata_url='http://localhost:9000/application/o/tweets/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)


def get_current_user(request: Request):
    """Dependency to get the current authenticated user"""
    user_info = request.session.get('user')
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return user_info


@app.get("/login")
async def login(request: Request):
    """Initiate OAuth login flow"""
    redirect_uri = "http://localhost:8000/callback"
    return await oauth.authentik.authorize_redirect(request, redirect_uri)


@app.get("/callback")
async def callback(request: Request):
    """OAuth callback endpoint"""
    try:
        token = await oauth.authentik.authorize_access_token(request)
        user_info = token.get('userinfo')
        
        if user_info:
            # Store user in database
            authentik_sub = user_info.get('sub')
            email = user_info.get('email')
            username = user_info.get('preferred_username') or user_info.get('name')
            
            with engine.connect() as conn:
                # Insert or update user
                conn.execute(
                    text("""
                        INSERT INTO users (authentik_sub, email, username)
                        VALUES (:sub, :email, :username)
                        ON CONFLICT (authentik_sub) 
                        DO UPDATE SET email = :email, username = :username
                    """),
                    {"sub": authentik_sub, "email": email, "username": username}
                )
                conn.commit()
            
            # Store user info in session
            request.session['user'] = {
                'sub': authentik_sub,
                'email': email,
                'username': username
            }
            
            return RedirectResponse(url='/')
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/logout")
async def logout(request: Request):
    """Logout endpoint"""
    request.session.clear()
    return {"message": "Logged out successfully"}


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    return {
        "user": current_user,
        "authenticated": True
    }


@app.get("/")
def home(request: Request):
    """Home endpoint"""
    user = request.session.get('user')
    if user:
        return {"message": "Welcome!", "user": user}
    return {"message": "Please login", "login_url": "/login"}
