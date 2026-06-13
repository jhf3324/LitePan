"""缓存子系统入口：全局缓存管理器 + 清理器 + 命中率追踪器。"""

from __future__ import annotations
from typing import Optional

from .cache_manager import GlobalCacheManager
from .cache_cleaner import CacheCleaner
from .cache_keys import CacheKeyGenerator, CacheKeyValidator
from .cache_types import (
    CacheItem, CacheConfig, CacheStats, CacheType, CacheStatus,
    CacheConstants, AccountId, FileId, ParentId
)
from .hit_tracker import HitRateTracker, get_hit_tracker, init_hit_tracker

_global_cache_manager = None
_cache_cleaner = None
_hit_rate_tracker = None


def init_cache_system(config=None):
    global _global_cache_manager, _cache_cleaner, _hit_rate_tracker

    _global_cache_manager = GlobalCacheManager(config)
    _cache_cleaner = CacheCleaner(_global_cache_manager)
    _hit_rate_tracker = get_hit_tracker()

    return _global_cache_manager


def get_global_cache():
    return _global_cache_manager


def get_cache_cleaner():
    return _cache_cleaner


def get_hit_rate_tracker():
    return _hit_rate_tracker


async def start_cache_system():
    from config import Settings, config_manager

    cache_enabled = await config_manager.get_async('cache_enabled')
    cache_enabled = cache_enabled if cache_enabled is not None else Settings.CACHE_ENABLED
    persistence_enabled = await config_manager.get_async('cache_persistence_enabled')
    persistence_enabled = (
        persistence_enabled
        if persistence_enabled is not None
        else Settings.CACHE_PERSISTENCE_ENABLED
    )
    persistence_interval = await config_manager.get_async('cache_persistence_interval_seconds')
    persistence_interval = (
        persistence_interval
        if persistence_interval is not None
        else Settings.CACHE_PERSISTENCE_INTERVAL_SECONDS
    )
    max_items = await config_manager.get_async('cache_max_items')
    max_items = max_items if max_items is not None else Settings.CACHE_MAX_ITEMS

    if _global_cache_manager:
        _global_cache_manager.config.enable_persistence = bool(cache_enabled and persistence_enabled)
        try:
            _global_cache_manager.config.max_items = max(1000, int(max_items))
        except (TypeError, ValueError):
            _global_cache_manager.config.max_items = Settings.CACHE_MAX_ITEMS
        if _global_cache_manager.config.enable_persistence:
            await _global_cache_manager.load_from_disk()

    if _cache_cleaner:
        await _cache_cleaner.start()

    if _hit_rate_tracker:
        await _hit_rate_tracker.start()

    if _global_cache_manager:
        if _global_cache_manager.config.enable_persistence:
            await _global_cache_manager.start_periodic_save(persistence_interval)


async def stop_cache_system():
    if _cache_cleaner:
        await _cache_cleaner.stop()

    if _hit_rate_tracker:
        await _hit_rate_tracker.stop()

    if _global_cache_manager:
        await _global_cache_manager.stop_periodic_save()
        await _global_cache_manager.save_to_disk()


async def apply_cache_runtime_settings(
    *,
    cache_enabled: bool,
    persistence_enabled: bool,
    persistence_interval_seconds: int,
    max_items: Optional[int] = None,
    memory_limit_mb: Optional[int] = None,
):
    """按最新配置热更新缓存持久化开关/间隔、条目上限、内存上限。"""
    if not _global_cache_manager:
        return

    effective_persistence_enabled = bool(cache_enabled and persistence_enabled)
    await _global_cache_manager.configure_persistence(
        enabled=effective_persistence_enabled,
        interval_seconds=persistence_interval_seconds,
    )

    if max_items is not None:
        try:
            new_limit = max(1000, int(max_items))
        except (TypeError, ValueError):
            new_limit = None
        if new_limit and new_limit != _global_cache_manager.config.max_items:
            _global_cache_manager.config.max_items = new_limit
            await _global_cache_manager.enforce_item_limit()

    if memory_limit_mb is not None:
        try:
            new_limit = max(64, int(memory_limit_mb))
        except (TypeError, ValueError):
            new_limit = None
        if new_limit and new_limit != _global_cache_manager.config.memory_limit_mb:
            _global_cache_manager.config.memory_limit_mb = new_limit

    if effective_persistence_enabled:
        await _global_cache_manager.load_from_disk()


__all__ = [
    'GlobalCacheManager',
    'CacheCleaner',
    'CacheKeyGenerator',
    'CacheKeyValidator',
    'HitRateTracker',
    'get_hit_tracker',
    'CacheItem',
    'CacheConfig',
    'CacheStats',
    'CacheType',
    'CacheStatus',
    'CacheConstants',
    'AccountId',
    'FileId',
    'ParentId',
    'init_cache_system',
    'get_global_cache',
    'get_cache_cleaner',
    'get_hit_rate_tracker',
    'start_cache_system',
    'stop_cache_system',
    'apply_cache_runtime_settings'
]
