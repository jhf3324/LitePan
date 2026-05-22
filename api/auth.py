from fastapi import APIRouter, Request, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from core.session_manager import session_manager
from core.security import check_password_hash, assess_admin_credential_state, is_password_hash
from core.error_handler import raise_unauthorized
from api.deps import is_public_index_enabled

router = APIRouter()

def get_admin_credentials():
    from config import config_manager
    username = config_manager.get('admin_username') or "admin"
    password = config_manager.get('admin_password') or "admin"
    return username, password


def get_admin_credential_state():
    username, password = get_admin_credentials()
    return assess_admin_credential_state(username, password)

class AuthResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: str = ""

@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    remember: str = Form("")
):
    stored_username, stored_password = get_admin_credentials()
    credential_state = assess_admin_credential_state(stored_username, stored_password)

    # 兼容早期明文密码：未哈希的直接等值比较，已哈希的走 check_password_hash
    password_match = False
    if is_password_hash(stored_password):
        password_match = check_password_hash(stored_password, password)
    else:
        password_match = (password == stored_password)
    
    if username == stored_username and password_match:
        response_data = {
            "success": True,
            "data": {
                "username": username,
                "is_admin": True,
                "must_change_password": credential_state["must_change_password"],
                "password_change_reason": credential_state["password_change_reason"],
            },
            "message": "登录成功"
        }
        
        response = JSONResponse(content=response_data)

        session_manager.create_session(
            response=response,
            user_data={
                'is_admin': True,
                'username': username,
            },
            remember=(remember == "1"),
            request=request
        )
        
        return response
    else:
        raise_unauthorized("用户名或密码错误")

@router.post("/logout")
async def logout(request: Request):
    response_data = {"success": True, "message": "登出成功"}
    response = JSONResponse(content=response_data)
    session_manager.clear_session(response)
    return response

@router.get("/status")
async def get_auth_status(request: Request) -> AuthResponse:
    session_data = session_manager.get_session(request)
    is_admin = session_data.get('is_admin', False)
    public_index_enabled = await is_public_index_enabled()
    credential_state = get_admin_credential_state() if is_admin else {
        "must_change_password": False,
        "password_change_reason": "",
    }
    
    return AuthResponse(
        success=True,
        data={
            "is_admin": is_admin,
            "username": session_data.get('username') if is_admin else None,
            "public_index_enabled": public_index_enabled,
            "must_change_password": credential_state["must_change_password"],
            "password_change_reason": credential_state["password_change_reason"],
        },
        message="获取认证状态成功"
    )

@router.post("/reset-password")
async def reset_password(request: Request):
    """生成一个随机明文密码塞进库里，新密码打到容器日志。明文形式保证 login 后会强制改密码。"""
    import secrets
    import string
    from config import config_manager
    from core.log_manager import get_writer, LogModule

    alphabet = string.ascii_letters + string.digits
    new_password = ''.join(secrets.choice(alphabet) for i in range(12))

    system_log = get_writer(LogModule.SYSTEM)

    await config_manager.set_async('admin_password', new_password)

    print(f"\n[重置密码] 您的新管理员密码是: {new_password} (登录后必须修改)\n")
    
    return JSONResponse(content={
        "success": True,
        "message": "重置成功，请查看容器控制台日志获取新密码。"
    })
