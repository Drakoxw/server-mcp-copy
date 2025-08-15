from fastapi import Request
from fastapi.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Depends, HTTPException, status
from fastapi.requests import Request
from typing import List

from src.infrastructure.session.session_manager import get_session_manager

session_manager = get_session_manager()

class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        is_valid, session = session_manager.validate_session(token)
        request.state.user_session = session if is_valid else None
        response = await call_next(request)
        return response
    
    def get_current_user(self, required_permissions: List[str] = []):
        def dependency(request: Request):
            session = request.state.user_session
            if not session:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
            
            if required_permissions and not set(required_permissions).issubset(set(session.permissions)):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
            
            return session
        return Depends(dependency)



# @app.get("/admin/dashboard")
# async def admin_dashboard(user= get_current_user(["admin"])):
#     return {"message": f"Bienvenido, {user.username}"}