"""跨盘秒传服务：扫描源指纹、试探可秒传（流式）、执行秒传。"""

import time
from typing import Any, AsyncGenerator, Dict, List

from core.base import FileItem
from core.driver_service import get_account_driver_instance
from core.log_manager import LogModule, get_writer

from .methods import get_method

MAX_FILES = 3000
MAX_DEPTH = 40


def _log():
    return get_writer(LogModule.API)


def _file_hash(item: FileItem, method: str) -> str:
    extra = item.extra or {}
    hashes = extra.get("hashes") or {}
    value = hashes.get(method)
    if not value and method == "sha1":
        value = extra.get("hash_info")
    return str(value or "").strip().lower()


async def _walk_source(driver, parent_id: str, method: str, rel_prefix: str, depth: int, acc: Dict) -> List[Dict]:
    if depth > MAX_DEPTH or acc["count"] >= MAX_FILES:
        return []

    items = await driver.list_files(parent_id)
    dirs = [it for it in items if it.is_dir]
    files = [it for it in items if not it.is_dir]

    nodes: List[Dict] = []
    for it in dirs:
        child_prefix = f"{rel_prefix}{it.name}/"
        children = await _walk_source(driver, it.id, method, child_prefix, depth + 1, acc)
        nodes.append({"type": "dir", "id": it.id, "name": it.name, "children": children})

    for it in files:
        if acc["count"] >= MAX_FILES:
            break
        file_hash = _file_hash(it, method)
        node = {
            "type": "file",
            "id": it.id,
            "name": it.name,
            "size": int(it.size or 0),
            "hash": file_hash,
            "rel_path": f"{rel_prefix}{it.name}",
            "rel_dir": rel_prefix.rstrip("/"),
            "eligible": bool(file_hash),
            "reuse": None,
        }
        nodes.append(node)
        acc["files"].append(node)
        acc["count"] += 1

    return nodes


async def scan_source(
    *,
    source_account_id: int,
    source_parent_id: str,
    method_id: str,
) -> Dict[str, Any]:
    method = get_method(method_id)
    src = await get_account_driver_instance(source_account_id)

    acc: Dict[str, Any] = {"count": 0, "files": []}
    tree = await _walk_source(src, source_parent_id, method.id, "", 0, acc)
    files: List[Dict] = acc["files"]

    return {
        "tree": tree,
        "total": len(files),
        "truncated": acc["count"] >= MAX_FILES,
        "files": [
            {
                "rel_path": f["rel_path"],
                "rel_dir": f["rel_dir"],
                "name": f["name"],
                "size": f["size"],
                "hash": f["hash"],
                "eligible": f["eligible"],
            }
            for f in files
        ],
    }


async def probe_stream(
    *,
    target_account_id: int,
    target_parent_id: str,
    method_id: str,
    files: List[Dict],
) -> AsyncGenerator[Dict[str, Any], None]:
    method = get_method(method_id)
    tgt = await get_account_driver_instance(target_account_id)

    yield {"event": "start", "total": len(files)}

    probe_folder_id = ""
    ok = 0
    no = 0
    try:
        probe_name = f"_litepan_probe_{int(time.time())}"
        created = await tgt.create_folder(target_parent_id, probe_name)
        if not created.success:
            yield {"event": "error", "message": f"创建临时探测目录失败: {created.message}"}
            return
        probe_folder_id = str((created.data or {}).get("folder_id") or "")
        if not probe_folder_id:
            yield {"event": "error", "message": "创建临时探测目录失败: 未返回目录ID"}
            return

        for f in files:
            rel_path = f.get("rel_path")
            file_hash = str(f.get("hash") or "").strip().lower()
            reuse = False
            if file_hash:
                try:
                    result = await tgt.rapid_upload_by_hash(
                        probe_folder_id, f.get("name"), method.id, file_hash, int(f.get("size") or 0), duplicate=2,
                    )
                    reuse = bool(result.data and result.data.get("reuse"))
                except Exception as exc:
                    _log().warning(f"跨盘秒传试探失败 {f.get('name')}: {exc}")
                    reuse = False
            if reuse:
                ok += 1
            else:
                no += 1
            yield {"event": "item", "rel_path": rel_path, "reuse": reuse}

        yield {"event": "end", "ok": ok, "no": no}
    finally:
        if probe_folder_id:
            try:
                await tgt.delete_file(probe_folder_id)
            except Exception as exc:
                _log().warning(f"清理临时探测目录失败 {probe_folder_id}: {exc}")


async def _ensure_target_dir(driver, root_id: str, rel_dir: str, cache: Dict[str, str]) -> str:
    if rel_dir in cache:
        return cache[rel_dir]

    parts = [p for p in rel_dir.split("/") if p]
    cur = root_id
    cur_rel = ""
    for part in parts:
        cur_rel = f"{cur_rel}/{part}" if cur_rel else part
        if cur_rel in cache:
            cur = cache[cur_rel]
            continue
        children = await driver.list_files(cur)
        found = next((c for c in children if c.is_dir and c.name == part), None)
        if found:
            cur = found.id
        else:
            created = await driver.create_folder(cur, part)
            if not created.success:
                raise RuntimeError(created.message or f"创建目录失败: {part}")
            cur = str((created.data or {}).get("folder_id") or "")
            if not cur:
                raise RuntimeError(f"创建目录失败: {part}")
        cache[cur_rel] = cur
    cache[rel_dir] = cur
    return cur


async def execute_transfer(
    *,
    target_account_id: int,
    target_parent_id: str,
    method_id: str,
    files: List[Dict],
    conflict: str = "rename",
) -> Dict[str, Any]:
    method = get_method(method_id)
    tgt = await get_account_driver_instance(target_account_id)

    duplicate = 2 if str(conflict).lower() == "overwrite" else 1
    dir_cache: Dict[str, str] = {"": target_parent_id}
    results: List[Dict] = []

    for f in files:
        name = f.get("name")
        file_hash = str(f.get("hash") or "").strip().lower()
        rel_dir = f.get("rel_dir") or ""
        if not file_hash:
            results.append({"rel_path": f.get("rel_path"), "name": name, "success": False, "error": "缺少指纹"})
            continue
        try:
            folder_id = await _ensure_target_dir(tgt, target_parent_id, rel_dir, dir_cache)
            result = await tgt.rapid_upload_by_hash(
                folder_id, name, method.id, file_hash, int(f.get("size") or 0), duplicate=duplicate,
            )
            reuse = bool(result.data and result.data.get("reuse"))
            results.append({
                "rel_path": f.get("rel_path"),
                "name": name,
                "success": reuse,
                "file_id": (result.data or {}).get("file_id", ""),
                "error": "" if reuse else "未命中秒传",
            })
        except Exception as exc:
            _log().warning(f"跨盘秒传执行失败 {name}: {exc}")
            results.append({"rel_path": f.get("rel_path"), "name": name, "success": False, "error": str(exc)})

    done = sum(1 for r in results if r["success"])
    return {"done": done, "total": len(files), "results": results}
