"""缓存清理：定时清过期 + 写操作触发的目录/路径/WebDAV 缓存失效。"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Optional

from core.log_manager import get_writer, LogModule

from .cache_types import CacheType, CacheConstants, AccountId, FileId, ParentId
from .cache_keys import CacheKeyGenerator
from .cache_manager import GlobalCacheManager


def get_cleaner_logger():
    try:
        return get_writer(LogModule.CACHE)
    except RuntimeError:
        return None

def log_cleaner(level: str, message: str):
    logger = get_cleaner_logger()
    if logger:
        getattr(logger, level)(message)


class CacheCleaner:
    def __init__(self, cache_manager: GlobalCacheManager):
        self.cache_manager = cache_manager
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

        self._cleanup_stats = {
            'total_cleanups': 0,
            'expired_cleaned': 0,
            'operation_cleanups': 0,
            'account_cleanups': 0,
            'last_cleanup': None
        }

    async def start(self):
        if self._running:
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        log_cleaner("info", "缓存清理器已停止")

    async def _cleanup_loop(self):
        while self._running:
            try:
                await self.cleanup_expired()
                await asyncio.sleep(self.cache_manager.config.cleanup_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                log_cleaner("error", f"定时清理任务出错: {str(e)}")
                await asyncio.sleep(60)

    async def cleanup_expired(self) -> int:
        start_time = time.time()
        expired_keys = []

        async with self.cache_manager.lock:
            current_time = datetime.now()
            for key, item in self.cache_manager.cache.items():
                if item.is_expired():
                    expired_keys.append(key)

        cleaned_count = 0
        for key in expired_keys:
            if await self.cache_manager.delete(key):
                cleaned_count += 1

        if cleaned_count > 0:
            self._cleanup_stats['expired_cleaned'] += cleaned_count
            self._cleanup_stats['total_cleanups'] += 1
            self._cleanup_stats['last_cleanup'] = datetime.now()

        return cleaned_count

    async def on_file_created(self, account_id: AccountId, parent_id: ParentId,
                             file_name: str = "", file_id: Optional[FileId] = None):
        log_cleaner("debug", f"文件创建缓存清理: 账号{account_id}, 父目录{parent_id}, 文件{file_name}")

        await self._clear_directory_cache(account_id, parent_id)
        await self._clear_webdav_cache(account_id)

        if file_name:
            await self._clear_path_cache_for_new_folder(account_id, parent_id, file_name)

        self._cleanup_stats['operation_cleanups'] += 1

    async def on_file_deleted(self, account_id: AccountId, file_id: FileId,
                             parent_id: Optional[ParentId] = None):
        try:
            file_info_key = CacheKeyGenerator.file_info_key(account_id, file_id)
            await self.cache_manager.delete(file_info_key)
            log_cleaner("debug", f"已清理文件详情缓存: {file_info_key}")

            if parent_id:
                await self._clear_directory_cache(account_id, parent_id)
                log_cleaner("debug", f"已清理父目录缓存: {parent_id}")

            await self._clear_webdav_cache(account_id)
            log_cleaner("debug", f"已清理WebDAV缓存: 账号{account_id}")
            self._cleanup_stats['operation_cleanups'] += 1

        except Exception as e:
            log_cleaner("error", f"文件删除缓存清理失败: 账号{account_id}, 文件{file_id}, 错误: {str(e)}")
            raise

    async def on_file_moved(self, account_id: AccountId, file_id: FileId,
                           old_parent_id: ParentId, new_parent_id: ParentId):
        log_cleaner("debug", f"文件移动缓存清理: 账号{account_id}, 文件{file_id}, 从{old_parent_id}到{new_parent_id}")

        file_info_key = CacheKeyGenerator.file_info_key(account_id, file_id)
        await self.cache_manager.delete(file_info_key)

        log_cleaner("debug", f"开始清理原目录缓存: {old_parent_id}")
        await self._clear_directory_and_parent_cache(account_id, old_parent_id)

        log_cleaner("debug", f"开始清理目标目录缓存: {new_parent_id}")
        await self._clear_directory_and_parent_cache(account_id, new_parent_id)

        await self._clear_path_cache_for_moved_file(account_id, file_id)

        await self._clear_webdav_cache(account_id)

        self._cleanup_stats['operation_cleanups'] += 1

    async def on_file_renamed(self, account_id: AccountId, parent_id: ParentId,
                             file_id: FileId, old_name: str, new_name: str):
        log_cleaner("debug", f"文件重命名缓存清理: 账号{account_id}, 文件{file_id}, 从{old_name}到{new_name}")

        file_info_key = CacheKeyGenerator.file_info_key(account_id, file_id)
        await self.cache_manager.delete(file_info_key)

        await self._clear_directory_cache(account_id, parent_id)

        await self._clear_path_cache_for_renamed_file(account_id, old_name, new_name)

        await self._clear_webdav_cache(account_id)

        self._cleanup_stats['operation_cleanups'] += 1

    async def on_account_updated(self, account_id: AccountId, config_changed: bool = True):
        log_cleaner("info", f"账号更新缓存清理: 账号{account_id}, 配置变化: {config_changed}")

        if config_changed:
            await self.cache_manager.clear_account_cache(account_id)

        self._cleanup_stats['account_cleanups'] += 1

    async def on_account_deleted(self, account_id: AccountId):
        log_cleaner("info", f"账号删除缓存清理: 账号{account_id}")

        await self.cache_manager.clear_account_cache(account_id)

        self._cleanup_stats['account_cleanups'] += 1

    async def _clear_directory_cache(self, account_id: AccountId, parent_id: ParentId):
        log_cleaner("debug", f"清理目录缓存: account_id={str(account_id)}, dir_id={str(parent_id)}")

        prefix = CacheKeyGenerator.directory_prefix(account_id, parent_id)
        cleared_count = await self.cache_manager.clear_by_prefix(prefix)

        sizes_key = CacheKeyGenerator.dir_folder_sizes_key(account_id, parent_id)
        if await self.cache_manager.delete(sizes_key):
            cleared_count += 1

        if cleared_count <= 0:
            return

        return

    async def _clear_directory_and_parent_cache(self, account_id: AccountId, parent_id: ParentId):
        log_cleaner("debug", f"清理目录及父目录缓存: account_id={str(account_id)}, dir_id={str(parent_id)}")

        await self._clear_directory_cache(account_id, parent_id)
        await self._clear_path_cache_for_directory(account_id, parent_id)

    async def _clear_path_cache_for_directory(self, account_id: AccountId, parent_id: ParentId):
        log_cleaner("debug", f"清理目录路径缓存: account_id={str(account_id)}, dir_id={str(parent_id)}")

        prefix = CacheKeyGenerator.path_mapping_prefix(account_id)
        await self.cache_manager.clear_by_prefix(prefix)

    async def _clear_path_cache_for_moved_file(self, account_id: AccountId, file_id: FileId):
        log_cleaner("debug", f"清理移动文件路径缓存: account_id={str(account_id)}, file_id={str(file_id)}")

        prefix = CacheKeyGenerator.path_mapping_prefix(account_id)
        await self.cache_manager.clear_by_prefix(prefix)

    async def _clear_webdav_cache(self, account_id: AccountId):
        prefix = CacheKeyGenerator.webdav_metadata_prefix(account_id)
        await self.cache_manager.clear_by_prefix(prefix)

    async def _clear_path_cache_for_new_folder(self, account_id: AccountId,
                                             parent_id: ParentId, folder_name: str):
        prefix = CacheKeyGenerator.path_mapping_prefix(account_id)
        await self.cache_manager.clear_by_prefix(prefix)

    async def _clear_path_cache_for_renamed_file(self, account_id: AccountId,
                                               old_name: str, new_name: str):
        prefix = CacheKeyGenerator.path_mapping_prefix(account_id)
        await self.cache_manager.clear_by_prefix(prefix)

    async def force_cleanup(self, cleanup_type: str = "all"):
        """手动触发清理：all / expired / memory。"""
        log_cleaner("info", f"强制执行缓存清理: {cleanup_type}")

        if cleanup_type == "all":
            await self.cache_manager.clear_all()
        elif cleanup_type == "expired":
            await self.cleanup_expired()
        elif cleanup_type == "memory":
            await self.cache_manager._emergency_cleanup()

    async def clear_all_cache(self):
        log_cleaner("info", "开始清空所有缓存")

        cleared_count = await self.cache_manager.clear_all()

        self._cleanup_stats['total_cleanups'] += 1
        self._cleanup_stats['last_cleanup'] = datetime.now()

        log_cleaner("info", f"清空所有缓存完成: 清理了{cleared_count}个项目")
        return cleared_count

    async def clear_download_mode_cache(self, account_id: str) -> None:
        from cache.cache_keys import CacheKeyGenerator
        cache_key = CacheKeyGenerator.download_mode_key(account_id)
        await self.cache_manager.delete(cache_key)
        log_cleaner("debug", f"已清空账号 {account_id} 的下载模式缓存")

    def get_cleanup_stats(self) -> Dict[str, any]:
        return {
            **self._cleanup_stats,
            'is_running': self._running,
            'cleanup_interval': self.cache_manager.config.cleanup_interval
        }


