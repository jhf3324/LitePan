"""全局缓存管理器：LRU + TTL + 持久化 + 内存压力感知。"""

import asyncio
import time
import psutil
import contextvars
import json
import os
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
from core.base import FileItem

from core.log_manager import get_writer, LogModule

from .cache_types import (
    CacheItem, CacheConfig, CacheStats, CacheType, CacheStatus,
    CacheConstants, AccountId, FileId, ParentId
)
from .cache_keys import CacheKeyGenerator, CacheKeyValidator


def get_cache_logger():
    # 延迟初始化避免与 log_manager 循环依赖
    try:
        return get_writer(LogModule.CACHE)
    except RuntimeError:
        return None

def log_cache(level: str, message: str):
    logger = get_cache_logger()
    if logger:
        getattr(logger, level)(message)


session_id_context: contextvars.ContextVar[str] = contextvars.ContextVar('session_id', default='default')

def set_session_context(session_id: str):
    session_id_context.set(session_id)

def get_session_context() -> str:
    return session_id_context.get()


def _serialize_file_item(file_item: FileItem) -> Dict[str, Any]:
    return {
        "__type__": "FileItem",
        "id": file_item.id,
        "name": file_item.name,
        "path": file_item.path,
        "size": file_item.size,
        "is_dir": file_item.is_dir,
        "modified": file_item.modified.isoformat() if file_item.modified else None,
        "created": file_item.created.isoformat() if file_item.created else None,
        "download_url": file_item.download_url,
        "thumbnail_url": file_item.thumbnail_url,
        "mime_type": file_item.mime_type,
        "extra": file_item.extra or {}
    }


def _deserialize_file_item(data: Dict[str, Any]) -> FileItem:
    modified = datetime.fromisoformat(data["modified"]) if data.get("modified") else None
    created = datetime.fromisoformat(data["created"]) if data.get("created") else None
    return FileItem(
        id=data.get("id", ""),
        name=data.get("name", ""),
        path=data.get("path", ""),
        size=data.get("size", 0),
        is_dir=data.get("is_dir", False),
        modified=modified,
        created=created,
        download_url=data.get("download_url"),
        thumbnail_url=data.get("thumbnail_url"),
        mime_type=data.get("mime_type"),
        extra=data.get("extra") or {}
    )


def _serialize_cache_value(value: Any) -> Any:
    if isinstance(value, FileItem):
        return _serialize_file_item(value)
    if isinstance(value, list):
        return [_serialize_cache_value(item) for item in value]
    if isinstance(value, dict):
        return {k: _serialize_cache_value(v) for k, v in value.items()}
    return value


def _deserialize_cache_value(value: Any) -> Any:
    if isinstance(value, dict):
        if value.get("__type__") == "FileItem":
            return _deserialize_file_item(value)
        return {k: _deserialize_cache_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_deserialize_cache_value(item) for item in value]
    return value


class GlobalCacheManager:
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.cache: OrderedDict[str, CacheItem] = OrderedDict()
        self.stats = CacheStats()
        self.lock = asyncio.Lock()

        self._account_config_cache: Dict[str, Dict] = {}
        self._config_cache_time: Dict[str, datetime] = {}

        self._last_memory_check = time.time()
        self._memory_check_interval = 60

        self._persistence_save_task: Optional[asyncio.Task] = None
        self._last_persistence_save = None
        self._persistence_interval_seconds = 300

        self._init_persistence()

    def _init_persistence(self):
        if self.config.enable_persistence and self.config.persistence_path:
            os.makedirs(self.config.persistence_path, exist_ok=True)
            log_cache("info", f"缓存持久化已启用，路径: {self.config.persistence_path}")

    def _is_cache_globally_enabled(self) -> bool:
        try:
            from config import config_manager
            cache_enabled = config_manager.get('cache_enabled')
            result = cache_enabled if cache_enabled is not None else True
            log_cache("debug", f"全局缓存开关检查: cache_enabled={cache_enabled}, result={result}")
            return result
        except Exception as e:
            log_cache("error", f"检查全局缓存开关失败: {e}")
            return True

    def _extract_account_id_from_key(self, key: str) -> Optional[str]:
        try:
            from .cache_keys import CacheKeyValidator
            return CacheKeyValidator.extract_account_id(key)
        except Exception:
            return None

    async def _get_account_cache_ttl(self, account_id: str) -> Optional[int]:
        """账号级 TTL（秒）：0=该账号禁用缓存；None=落到全局默认。"""
        normalized_account_id = str(account_id or "").strip()
        if not normalized_account_id or normalized_account_id == "temp_test":
            return None
        # 临时探测账号（如 tv_bind_quark_probe）不是 DB 数字 id，跳过账号级 TTL
        if not normalized_account_id.isdigit():
            return None

        try:
            from database.db import db

            account = await db.get_account(int(normalized_account_id))
            if account:
                config = account['config']
                if isinstance(config, str):
                    import json
                    config = json.loads(config)
                cache_ttl_minutes = config.get('cache_ttl')

                if cache_ttl_minutes is not None:
                    # 数据库里存的是分钟，内部统一按秒用
                    cache_ttl_seconds = int(cache_ttl_minutes) * 60
                    return cache_ttl_seconds
                else:
                    return None
            else:
                return None
        except Exception as e:
            log_cache("error", f"获取账号{normalized_account_id}缓存TTL失败: {e}")
            return None

    async def get(self, key: str, default: Any = None) -> Any:
        if not self._is_cache_globally_enabled():
            cache_type = self._get_cache_type_from_key(key)
            self.stats.record_miss(cache_type)
            log_cache("debug", f"全局缓存已禁用，跳过缓存获取: {key}")
            return default
        
        account_id = self._extract_account_id_from_key(key)
        if account_id:
            account_ttl = await self._get_account_cache_ttl(account_id)
            if account_ttl is not None and account_ttl == 0:
                cache_type = self._get_cache_type_from_key(key)
                self.stats.record_miss(cache_type)
                log_cache("debug", f"账号{account_id}缓存已禁用(TTL=0)，跳过缓存获取: {key}")
                return default

        async with self.lock:
            if key not in self.cache:
                cache_type = self._get_cache_type_from_key(key)
                self.stats.record_miss(cache_type)
                return default

            item = self.cache[key]

            if item.is_expired():
                del self.cache[key]
                self.stats.expirations += 1
                self.stats.record_miss(item.cache_type)
                self._update_stats_on_remove(item)
                return default

            item.touch()

            # LRU：命中后挪到尾部
            self.cache.move_to_end(key)

            self.stats.record_hit(item.cache_type)

            return item.value

    async def set(self, key: str, value: Any, ttl: Optional[int] = None,
                  cache_type: CacheType = CacheType.DIRECTORY) -> bool:
        """写入缓存；ttl=None 会按 cache_type + 账号配置推导实际 TTL，ttl=0 跳过写入。"""
        if not self._is_cache_globally_enabled():
            log_cache("debug", f"全局缓存已禁用，跳过缓存存储: {key}")
            return True

        account_id = self._extract_account_id_from_key(key)
        if account_id:
            account_ttl = await self._get_account_cache_ttl(account_id)
            if account_ttl is not None and account_ttl == 0:
                log_cache("debug", f"账号{account_id}缓存已禁用(TTL=0)，跳过缓存存储: {key}")
                return True
        
        try:
            if ttl is None:
                if cache_type in [CacheType.DOWNLOAD_MODE, CacheType.ACCOUNT_CONFIG]:
                    ttl = self.config.get_ttl_for_type(cache_type)
                else:
                    account_id = self._extract_account_id_from_key(key)
                    if account_id:
                        account_ttl = await self._get_account_cache_ttl(account_id)
                        if account_ttl is not None:
                            ttl = account_ttl
                        else:
                            try:
                                from config import config_manager
                                global_ttl = config_manager.get('cache_ttl') or 3600
                                ttl = global_ttl
                            except Exception:
                                ttl = self.config.default_ttl
                    else:
                        try:
                            from config import config_manager
                            global_ttl = config_manager.get('cache_ttl') or 3600
                            ttl = global_ttl
                        except Exception:
                            ttl = self.config.default_ttl

            if ttl == 0:
                log_cache("debug", f"TTL=0，跳过缓存存储: {key}")
                return True

            await self._check_memory_pressure()

            expires_at = datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None

            item = CacheItem(
                key=key,
                value=value,
                cache_type=cache_type,
                created_at=datetime.now(),
                expires_at=expires_at
            )

            async with self.lock:
                if key in self.cache:
                    old_item = self.cache.pop(key)
                    self._update_stats_on_remove(old_item)

                if len(self.cache) >= self.config.max_items:
                    await self._evict_items()

                self.cache[key] = item
                self._update_stats_on_add(item)

            return True

        except Exception as e:
            log_cache("error", f"设置缓存失败: {key}, 错误: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        async with self.lock:
            if key in self.cache:
                item = self.cache.pop(key)
                self._update_stats_on_remove(item)
                log_cache("debug", f"删除缓存项: {key}")
                return True
            return False
    
    async def clear_by_prefix(self, prefix: str) -> int:
        async with self.lock:
            keys_to_delete = [
                key for key in self.cache.keys()
                if CacheKeyValidator.match_prefix(key, prefix)
            ]
            
            count = 0
            for key in keys_to_delete:
                if key in self.cache:
                    item = self.cache.pop(key)
                    self._update_stats_on_remove(item)
                    count += 1
            
            if count > 0:
                log_cache("debug", f"按前缀清理缓存: {prefix}, 清理项目数: {count}")
            
            return count

    def _get_persistence_file_path(self) -> str:
        return os.path.join(self.config.persistence_path, "cache_data.json")

    async def save_to_disk(self) -> bool:
        if not self.config.enable_persistence:
            return False
        
        try:
            async with self.lock:
                cache_data = {}
                for key, item in self.cache.items():
                    if item.expires_at and item.expires_at < datetime.now():
                        continue
                    
                    cache_data[key] = {
                        'value': _serialize_cache_value(item.value),
                        'created_at': item.created_at.isoformat() if item.created_at else None,
                        'expires_at': item.expires_at.isoformat() if item.expires_at else None,
                        'last_access': item.last_access.isoformat() if item.last_access else None,
                        'size_bytes': item.size_bytes,
                        'cache_type': item.cache_type.value if hasattr(item.cache_type, 'value') else str(item.cache_type)
                    }
                
                file_path = self._get_persistence_file_path()
                temp_path = file_path + '.tmp'
                
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'version': 1,
                        'saved_at': datetime.now().isoformat(),
                        'stats': {
                            'total_items': self.stats.total_items,
                            'total_size_bytes': self.stats.total_size_bytes,
                            'hits': self.stats.hits,
                            'misses': self.stats.misses
                        },
                        'cache': cache_data
                    }, f, ensure_ascii=False, indent=2)
                
                os.replace(temp_path, file_path)
                self._last_persistence_save = datetime.now()
                log_cache("debug", f"缓存已持久化: {len(cache_data)} 项")
                return True
                
        except Exception as e:
            log_cache("error", f"缓存持久化失败: {e}")
            return False
    
    async def load_from_disk(self) -> int:
        if not self.config.enable_persistence:
            return 0
        
        file_path = self._get_persistence_file_path()
        if not os.path.exists(file_path):
            return 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            cache_data = data.get('cache', {})
            loaded_count = 0
            
            async with self.lock:
                for key, item_data in cache_data.items():
                    try:
                        created_at = None
                        if item_data.get('created_at'):
                            created_at = datetime.fromisoformat(item_data['created_at'])
                        
                        expires_at = None
                        if item_data.get('expires_at'):
                            expires_at = datetime.fromisoformat(item_data['expires_at'])
                            if expires_at < datetime.now():
                                continue
                        
                        last_access = None
                        if item_data.get('last_access'):
                            last_access = datetime.fromisoformat(item_data['last_access'])
                        
                        cache_type = CacheType.DIRECTORY
                        type_str = item_data.get('cache_type', 'DIRECTORY')
                        try:
                            cache_type = CacheType(type_str)
                        except ValueError:
                            pass
                        
                        item = CacheItem(
                            key=key,
                            value=_deserialize_cache_value(item_data['value']),
                            cache_type=cache_type,
                            created_at=created_at,
                            expires_at=expires_at,
                            last_access=last_access,
                            size_bytes=item_data.get('size_bytes', 0)
                        )
                        self.cache[key] = item
                        self._update_stats_on_add(item)
                        loaded_count += 1

                    except Exception as e:
                        log_cache("warning", f"加载缓存项失败 {key}: {e}")
                        continue

            if loaded_count > 0:
                log_cache("info", f"缓存已从磁盘恢复: {loaded_count} 项，总大小 {self.stats.total_size_bytes / (1024*1024):.2f} MB")
            
            return loaded_count
            
        except Exception as e:
            log_cache("error", f"缓存恢复失败: {e}")
            return 0
    
    async def start_periodic_save(self, interval_seconds: int = 300):
        if not self.config.enable_persistence:
            return

        normalized_interval = max(60, int(interval_seconds or 300))
        if (
            self._persistence_save_task and
            not self._persistence_save_task.done() and
            self._persistence_interval_seconds == normalized_interval
        ):
            return

        if self._persistence_save_task and not self._persistence_save_task.done():
            await self.stop_periodic_save()

        async def save_loop():
            while True:
                try:
                    await asyncio.sleep(normalized_interval)
                    await self.save_to_disk()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    log_cache("error", f"定期保存失败: {e}")
        
        self._persistence_interval_seconds = normalized_interval
        self._persistence_save_task = asyncio.create_task(save_loop())
        log_cache("info", f"缓存定期保存已启动，间隔: {normalized_interval}秒")
    
    async def stop_periodic_save(self):
        if self._persistence_save_task:
            self._persistence_save_task.cancel()
            try:
                await self._persistence_save_task
            except asyncio.CancelledError:
                pass
            self._persistence_save_task = None
            log_cache("info", "缓存定期保存已停止")

    async def configure_persistence(self, enabled: bool, interval_seconds: int = 300) -> None:
        """热更新缓存持久化开关与保存间隔。"""
        normalized_interval = max(60, int(interval_seconds or 300))
        self.config.enable_persistence = bool(enabled)
        self._persistence_interval_seconds = normalized_interval

        if not self.config.enable_persistence:
            await self.stop_periodic_save()
            return

        await self.start_periodic_save(normalized_interval)

    async def enforce_item_limit(self) -> int:
        """按当前 max_items 强制裁剪条目，返回淘汰数量。

        典型用于用户在全局设置中调小 max_items 后立即收缩缓存。
        """
        async with self.lock:
            if not self.cache:
                return 0
            limit = max(0, int(self.config.max_items))
            excess = len(self.cache) - limit
            if excess <= 0:
                return 0
            await self._evict_items(force_count=excess)
            log_cache(
                "info",
                f"已根据新上限收缩缓存：淘汰 {excess} 项，剩余 {len(self.cache)} 项 / 上限 {limit}"
            )
            return excess

    async def clear_all(self) -> int:
        async with self.lock:
            count = len(self.cache)
            self.cache.clear()
            self.stats = CacheStats()
            log_cache("info", f"清理所有缓存, 清理项目数: {count}")
            return count

    async def get_directory_cache(self, account_id: AccountId, parent_id: ParentId,
                                 page: int = 1, search: Optional[str] = None) -> Optional[Dict]:
        key = CacheKeyGenerator.directory_key(account_id, parent_id, page, search)
        return await self.get(key)

    async def set_directory_cache(self, account_id: AccountId, parent_id: ParentId,
                                 data: Dict, page: int = 1, search: Optional[str] = None,
                                 ttl: Optional[int] = None) -> bool:
        key = CacheKeyGenerator.directory_key(account_id, parent_id, page, search)

        if ttl is None:
            ttl = self.config.get_ttl_for_type(CacheType.DIRECTORY)

        return await self.set(key, data, ttl, CacheType.DIRECTORY)

    async def get_dir_folder_sizes_cache(self, account_id: AccountId, parent_id: ParentId) -> Optional[Dict]:
        key = CacheKeyGenerator.dir_folder_sizes_key(account_id, parent_id)
        cached = await self.get(key)
        return cached if isinstance(cached, dict) else None

    async def set_dir_folder_sizes_cache(
        self,
        account_id: AccountId,
        parent_id: ParentId,
        data: Dict,
        ttl: Optional[int] = None,
    ) -> bool:
        key = CacheKeyGenerator.dir_folder_sizes_key(account_id, parent_id)
        if ttl is None:
            ttl = self.config.get_ttl_for_type(CacheType.DIRECTORY)
        return await self.set(key, data, ttl, CacheType.DIRECTORY)

    async def get_file_info_cache(self, account_id: AccountId, file_id: FileId) -> Optional[Dict]:
        key = CacheKeyGenerator.file_info_key(account_id, file_id)
        return await self.get(key)

    async def set_file_info_cache(self, account_id: AccountId, file_id: FileId,
                                 data: Dict, ttl: Optional[int] = None) -> bool:
        key = CacheKeyGenerator.file_info_key(account_id, file_id)
        return await self.set(key, data, ttl, CacheType.FILE_INFO)

    async def get_path_mapping_cache(self, account_id: AccountId, path: str) -> Optional[Any]:
        key = CacheKeyGenerator.path_mapping_key(account_id, path)
        return await self.get(key)

    async def set_path_mapping_cache(self, account_id: AccountId, path: str, value: Any, ttl: Optional[int] = None) -> bool:
        key = CacheKeyGenerator.path_mapping_key(account_id, path)
        return await self.set(key, value, ttl, CacheType.PATH_MAPPING)

    async def get_webdav_metadata_cache(self, account_id: AccountId, path: str) -> Optional[Any]:
        key = CacheKeyGenerator.webdav_metadata_key(account_id, path)
        return await self.get(key)

    async def set_webdav_metadata_cache(self, account_id: AccountId, path: str, value: Any, ttl: Optional[int] = None) -> bool:
        key = CacheKeyGenerator.webdav_metadata_key(account_id, path)
        return await self.set(key, value, ttl, CacheType.WEBDAV_METADATA)

    async def get_download_mode_cache(self, account_id: AccountId) -> Optional[str]:
        key = CacheKeyGenerator.download_mode_key(account_id)
        return await self.get(key)

    async def set_download_mode_cache(self, account_id: AccountId, mode: str,
                                     ttl: Optional[int] = None) -> bool:
        key = CacheKeyGenerator.download_mode_key(account_id)
        return await self.set(key, mode, ttl, CacheType.DOWNLOAD_MODE)

    async def get_download_url_cache(self, account_id: AccountId, file_id: FileId) -> Optional[str]:
        key = CacheKeyGenerator.download_url_key(account_id, file_id)
        return await self.get(key)

    async def set_download_url_cache(self, account_id: AccountId, file_id: FileId,
                                     url: str, ttl: Optional[int] = None) -> bool:
        key = CacheKeyGenerator.download_url_key(account_id, file_id)
        return await self.set(key, url, ttl, CacheType.DOWNLOAD_URL)

    async def clear_download_url_cache(self, account_id: AccountId, file_id: FileId):
        key = CacheKeyGenerator.download_url_key(account_id, file_id)
        await self.delete(key)

    async def clear_account_download_url_cache(self, account_id: AccountId):
        prefix = CacheConstants.KEY_PREFIX_DOWNLOAD_URL + CacheConstants.KEY_SEPARATOR + str(account_id)
        await self.clear_by_prefix(prefix)

    async def clear_download_mode_cache(self, account_id: AccountId):
        cache_key = CacheKeyGenerator.download_mode_key(account_id)
        await self.delete(cache_key)
        log_cache("debug", f"已清除账号{account_id}的下载模式缓存")

    async def clear_account_cache(self, account_id: AccountId):
        prefixes = [
            CacheKeyGenerator.directory_prefix(account_id),
            CacheKeyGenerator.dir_folder_sizes_prefix(account_id),
            CacheKeyGenerator.file_info_prefix(account_id),
            CacheKeyGenerator.path_mapping_prefix(account_id),
            CacheKeyGenerator.webdav_metadata_prefix(account_id),
        ]
        for prefix in prefixes:
            await self.clear_by_prefix(prefix)

        await self.clear_download_mode_cache(account_id)

        config_key = f"account_config_{account_id}"
        if config_key in self._account_config_cache:
            del self._account_config_cache[config_key]
        if config_key in self._config_cache_time:
            del self._config_cache_time[config_key]

        log_cache("debug", f"已清除账号{account_id}的所有缓存")

    async def clear_file_operation_cache(self, account_id: AccountId, parent_id: ParentId,
                                       file_id: Optional[FileId] = None):
        prefixes = CacheKeyGenerator.get_related_keys_for_file_operation(
            account_id, parent_id, file_id
        )

        for prefix in prefixes:
            # 完整 key（≥2 个分隔符）走 delete，前缀走 clear_by_prefix
            if prefix.count(CacheConstants.KEY_SEPARATOR) >= 2:
                await self.delete(prefix)
            else:
                await self.clear_by_prefix(prefix)

        log_cache("debug", f"已清除账号{account_id}文件操作相关缓存")

    async def clear_account_update_cache(self, account_id: AccountId):
        config_key = f"account_config_{account_id}"
        if config_key in self._account_config_cache:
            del self._account_config_cache[config_key]
        if config_key in self._config_cache_time:
            del self._config_cache_time[config_key]

        await self.clear_download_mode_cache(account_id)

        log_cache("info", f"已清除账号{account_id}的更新相关缓存")

    async def _check_memory_pressure(self):
        """周期性内存压力检查：只对「缓存自身体积」做处置，系统内存高只 warn 不动 cache。

        理由：系统内存往往被 Emby、Docker 等其他进程占用，砍掉自家 cache 既救不回系统内存，
        又会拖垮 115 这类风控严的网盘（缓存保持任务白跑）。所以只看自身 memory_limit_mb。
        """
        current_time = time.time()
        if current_time - self._last_memory_check < self._memory_check_interval:
            return

        self._last_memory_check = current_time

        try:
            cache_memory_mb = self.stats.memory_usage_mb
            limit_mb = self.config.memory_limit_mb

            if cache_memory_mb > limit_mb:
                log_cache("warning", f"缓存超限触发紧急清理: {cache_memory_mb:.1f}MB > {limit_mb}MB")
                await self._emergency_cleanup()
            elif cache_memory_mb > limit_mb * 0.8:
                log_cache("info", f"缓存使用接近上限: {cache_memory_mb:.1f}MB / {limit_mb}MB，预防性 LRU 淘汰")
                async with self.lock:
                    await self._evict_items(force_count=min(100, max(1, len(self.cache) // 10)))

            try:
                memory = psutil.virtual_memory()
                memory_usage_percent = memory.percent / 100.0
                if memory_usage_percent > CacheConstants.MEMORY_CRITICAL_THRESHOLD:
                    log_cache(
                        "warning",
                        f"系统内存压力过高: {memory_usage_percent:.1%}"
                        f"（缓存当前 {cache_memory_mb:.1f}MB / {limit_mb}MB，未触发清理）"
                    )
            except Exception:
                pass

        except Exception as e:
            log_cache("error", f"检查内存压力失败: {str(e)}")

    async def _emergency_cleanup(self):
        """缓存超限：按 LRU 顺序弹到 memory_limit_mb * 0.7，比"砍一半"更精准。"""
        target_bytes = int(self.config.memory_limit_mb * 1024 * 1024 * 0.7)
        before_mb = self.stats.memory_usage_mb
        evicted = 0

        async with self.lock:
            while self.stats.total_size_bytes > target_bytes and self.cache:
                _, item = self.cache.popitem(last=False)  # OrderedDict 头部 = 最旧 LRU
                self._update_stats_on_remove(item)
                self.stats.record_eviction(item.cache_type, memory_pressure=True)
                evicted += 1

        after_mb = self.stats.memory_usage_mb
        log_cache(
            "info",
            f"紧急清理完成: 淘汰 {evicted} 项，{before_mb:.1f}MB → {after_mb:.1f}MB"
            f"（目标 {self.config.memory_limit_mb * 0.7:.0f}MB）"
        )

    async def _evict_items(self, force_count: Optional[int] = None):
        """常规 LRU 淘汰；调用方需自行持有 self.lock（避免和 set/紧急清理嵌套加锁死锁）。"""
        if not self.cache:
            return

        if force_count is None:
            if len(self.cache) >= self.config.max_items:
                force_count = max(1, len(self.cache) // 10)
            else:
                return

        evicted_count = 0
        for _ in range(force_count):
            if not self.cache:
                break
            _, item = self.cache.popitem(last=False)  # OrderedDict 头部 = 最旧 LRU
            self._update_stats_on_remove(item)
            self.stats.record_eviction(item.cache_type, memory_pressure=True)
            evicted_count += 1

        if evicted_count > 0:
            log_cache(
                "debug",
                f"LRU 淘汰 {evicted_count} 项（剩余 {len(self.cache)} 项 / {self.stats.memory_usage_mb:.1f}MB）"
            )

    def _update_stats_on_add(self, item: CacheItem):
        self.stats.total_items += 1
        self.stats.total_size_bytes += item.size_bytes

        if item.cache_type in self.stats.type_stats:
            self.stats.type_stats[item.cache_type]['items'] += 1
            self.stats.type_stats[item.cache_type]['size_bytes'] += item.size_bytes

    def _update_stats_on_remove(self, item: CacheItem):
        self.stats.total_items = max(0, self.stats.total_items - 1)
        self.stats.total_size_bytes = max(0, self.stats.total_size_bytes - item.size_bytes)

        if item.cache_type in self.stats.type_stats:
            self.stats.type_stats[item.cache_type]['items'] = max(0,
                self.stats.type_stats[item.cache_type]['items'] - 1)
            self.stats.type_stats[item.cache_type]['size_bytes'] = max(0,
                self.stats.type_stats[item.cache_type]['size_bytes'] - item.size_bytes)

    def _get_cache_type_from_key(self, key: str) -> CacheType:
        cache_type_str = CacheKeyValidator.extract_cache_type(key)

        type_mapping = {
            CacheConstants.KEY_PREFIX_DIRECTORY: CacheType.DIRECTORY,
            CacheConstants.KEY_PREFIX_DIR_FOLDER_SIZES: CacheType.DIRECTORY,
            CacheConstants.KEY_PREFIX_FILE_INFO: CacheType.FILE_INFO,
            CacheConstants.KEY_PREFIX_PATH: CacheType.PATH_MAPPING,
            CacheConstants.KEY_PREFIX_WEBDAV: CacheType.WEBDAV_METADATA,
            CacheConstants.KEY_PREFIX_DOWNLOAD_MODE: CacheType.DOWNLOAD_MODE,
            CacheConstants.KEY_PREFIX_ACCOUNT_CONFIG: CacheType.ACCOUNT_CONFIG,
        }

        return type_mapping.get(cache_type_str, CacheType.DIRECTORY)

    def get_stats(self) -> CacheStats:
        return self.stats

    def get_cache_info(self) -> Dict[str, Any]:
        return {
            'total_items': len(self.cache),
            'memory_usage_mb': self.stats.memory_usage_mb,
            'hit_rate': self.stats.hit_rate,
            'config': {
                'max_items': self.config.max_items,
                'memory_limit_mb': self.config.memory_limit_mb,
                'default_ttl': self.config.default_ttl,
            },
            'type_stats': self.stats.type_stats
        }

    def should_use_cache(self, ttl: Optional[int] = None, cache_type: CacheType = CacheType.DIRECTORY) -> bool:
        """ttl=0 表示不走缓存。"""
        if ttl is None:
            ttl = self.config.get_ttl_for_type(cache_type)

        return ttl > 0

