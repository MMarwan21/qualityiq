# routes/auth.py
# Handles Google OAuth logn flow
# Three routes: /login, /auth/google, /auth/callback

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
import os
import secrets

from sheets.agents import get_role, get_display_name

load_dotenv()

router        = APIRouter()
templates     = Jinja2Templates(directory = "templates")

# Set up the OAuth client 

oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url=("https://accounts.google.com/.well-known/openid-configuration"),
    client_kwargs={"scope": "openid email profile"},
)

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Show the login page.
    If the user is already logged in, redirect to the dashboard.
    """
    if request.session.get("user"):
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/auth/google")
async def auth_google(request: Request):
    """
    Redirect the user to Google's login page.
    Generates a random state string for CSRF protection and saves it in the session.
    """
    # Generate a random state string for CSRF protection
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state

    redirect_uri = os.getenv(
        "REDIRECT_URI",
        "http://localhost:8000/auth/callback"
    )

    return await oauth.google.authorize_redirect(request, redirect_uri, state=state)


@router.get("/auth/callback")
async def auth_callback(request: Request):
    """
    Google redirects here after the user picks their account.

    Steps:
    1. Verify the state parameter matches the one we generated
    2. Exchange the code for user info.
    3. Check the user's role in Agent sheet.
    4. Store user info in the session.
    5. Redirect to the right page based on role.
    """
    # Step 1: Verify state to prevent CSRF attacks
    returned_state = request.query_params.get("state")
    expected_state = request.session.get("oauth_state")

    if not returned_state or returned_state != expected_state:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Security check failed. please try again."
            }
        )
    
    # Step 2: Exchange code for user info
    try:
        token    = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")

        if not user_info:
            raise ValueError("No User info returned from Google.")
        
        email = user_info.get("email", "").lower().strip()

        if not email:
            raise ValueError("No email in user info.")
    except Exception as e:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": f"Login failed: {str(e)}"
            }
        )
    # Step 3: Check the user's role in Agent sheet
    role = get_role(email)

    if role == "unauthorized":
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": (
                    f" Your account ({email}) is not registered."
                )
            }
        )
    
    # Step 4: Store user info in the session
    request.session["user"] = {
        "email": email,
        "name": get_display_name(email),
        "role": role,
    }
    # Step 5: Redirect to the right page based on role
    if role == "agent":
        return RedirectResponse(url="/scorecard")
    
    return RedirectResponse(url="/dashboard")

@router.get("/logout")
async def logout(request: Request):
    """
    Clear the user's session and redirect to the login page.
    """
    request.session.clear()
    return RedirectResponse(url="/login")