# routes/dependencies.py
# Shared dependencies used across all protected routes
# This is where authentication checks live

from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse


async def require_login(request: Request) -> dict:
    """
    Verify the user is logged in.
    Used as a FastAPI dependency on every protected route.

    Returns the user dict from the session if logged in.
    Redirects to login page if not.

    Usage:
        @router.get("/dashboard")
        async def dashboard(request: Request, user=Depends(require_login)):
            # user is {"email": ..., "name": ..., "role": ...}
    """
    user = request.session.get("user")
    if not user:
        # Can't raise RedirectResponse as an exception
        # so we raise HTTPException and handle it in main.py
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"},
            detail="Not authenticated"
        )
    return user


async def require_management(request: Request) -> dict:
    """
    Verify the user is logged in AND has management or admin role.
    Used on routes that agents should not access.
    """
    user = request.session.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"},
            detail="Not authenticated"
        )

    if user.get("role") not in ("management", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Management access required"
        )

    return user


async def require_admin(request: Request) -> dict:
    """
    Verify the user is logged in AND has admin role.
    Used only on routes that change system settings.
    """
    user = request.session.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"},
            detail="Not authenticated"
        )

    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return user