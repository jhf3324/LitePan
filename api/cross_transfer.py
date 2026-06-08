"""跨盘秒传管理接口。"""

import json
from typing import List, Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.deps import require_admin_auth
from api.responses import error_response as _error_response, success_response as _success_response
from cross_transfer import build_routes, execute_transfer, probe_stream, scan_source
from core.log_manager import LogModule, get_writer

router = APIRouter(prefix="/api/cross-transfer", tags=["跨盘秒传"])


def _log():
    return get_writer(LogModule.API)


class ScanRequest(BaseModel):
    source_account_id: int
    source_parent_id: str
    method: str


class ProbeFile(BaseModel):
    rel_path: Optional[str] = ""
    name: str
    size: int = 0
    hash: str = ""


class ProbeRequest(BaseModel):
    target_account_id: int
    target_parent_id: str
    method: str
    files: List[ProbeFile]


class TransferFile(BaseModel):
    rel_path: Optional[str] = ""
    rel_dir: Optional[str] = ""
    name: str
    size: int = 0
    hash: str


class ExecuteRequest(BaseModel):
    target_account_id: int
    target_parent_id: str
    method: str
    files: List[TransferFile]
    conflict: str = "rename"


@router.get("/routes")
async def get_routes(session_data: dict = Depends(require_admin_auth)):
    try:
        routes = build_routes()
        return _success_response(data=routes, message=f"可用线路 {len(routes)} 条")
    except Exception as exc:
        _log().error(f"获取跨盘秒传线路失败: {exc}")
        return _error_response(message=f"获取线路失败: {exc}", data=[])


@router.post("/scan")
async def scan(req: ScanRequest, session_data: dict = Depends(require_admin_auth)):
    try:
        result = await scan_source(
            source_account_id=req.source_account_id,
            source_parent_id=req.source_parent_id,
            method_id=req.method,
        )
        return _success_response(data=result, message=f"已扫描 {result['total']} 个文件")
    except Exception as exc:
        _log().error(f"跨盘秒传扫描失败: {exc}")
        return _error_response(message=f"扫描失败: {exc}")


@router.post("/probe")
async def probe(req: ProbeRequest, session_data: dict = Depends(require_admin_auth)):
    async def generate():
        try:
            async for msg in probe_stream(
                target_account_id=req.target_account_id,
                target_parent_id=req.target_parent_id,
                method_id=req.method,
                files=[f.model_dump() for f in req.files],
            ):
                yield json.dumps(msg, ensure_ascii=False) + "\n"
        except Exception as exc:
            _log().error(f"跨盘秒传试探失败: {exc}")
            yield json.dumps({"event": "error", "message": str(exc)}, ensure_ascii=False) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson; charset=utf-8")


@router.post("/execute")
async def execute(req: ExecuteRequest, session_data: dict = Depends(require_admin_auth)):
    try:
        result = await execute_transfer(
            target_account_id=req.target_account_id,
            target_parent_id=req.target_parent_id,
            method_id=req.method,
            files=[f.model_dump() for f in req.files],
            conflict=req.conflict,
        )
        return _success_response(data=result, message=f"秒传完成 {result['done']}/{result['total']}")
    except Exception as exc:
        _log().error(f"跨盘秒传执行失败: {exc}")
        return _error_response(message=f"执行失败: {exc}")
