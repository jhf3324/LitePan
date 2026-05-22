"""缓存层数据模型：CacheItem / CacheConfig / CacheStats 等。"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import time

CacheKey = str
CacheValue = Any
AccountId = Union[int, str]
FileId = str
ParentId = str


# 估算时每个容器最多抽样的元素数；保证 O(1) 量级
_SIZE_SAMPLE_LIMIT = 5
# 递归深度上限，防止极端嵌套结构带来的递归开销
_SIZE_MAX_DEPTH = 4


def _fast_size_estimate(value: Any, depth: int = 0) -> int:
    if depth >= _SIZE_MAX_DEPTH:
        return 256

    if value is None:
        return 16
    if isinstance(value, bool):
        return 28
    if isinstance(value, int):
        return 28
    if isinstance(value, float):
        return 24
    if isinstance(value, str):
        return 50 + len(value) * 2
    if isinstance(value, (bytes, bytearray)):
        return 33 + len(value)

    if isinstance(value, dict):
        n = len(value)
        if n == 0:
            return 64
        sample_keys = []
        sample_vals = []
        for i, (k, v) in enumerate(value.items()):
            if i >= _SIZE_SAMPLE_LIMIT:
                break
            sample_keys.append(k)
            sample_vals.append(v)
        sample_n = len(sample_keys)
        avg_pair = (
            sum(_fast_size_estimate(k, depth + 1) for k in sample_keys)
            + sum(_fast_size_estimate(v, depth + 1) for v in sample_vals)
        ) / sample_n
        # 64：dict 头；100：每个 entry 哈希槽与指针开销
        return 64 + 100 * n + int(avg_pair * n)

    if isinstance(value, (list, tuple, set, frozenset)):
        n = len(value)
        if n == 0:
            return 64
        sample = []
        for i, item in enumerate(value):
            if i >= _SIZE_SAMPLE_LIMIT:
                break
            sample.append(item)
        avg = sum(_fast_size_estimate(s, depth + 1) for s in sample) / len(sample)
        # 64：容器头；56：每个引用的指针 + 元素对象基础开销
        return 64 + 56 * n + int(avg * n)

    if hasattr(value, '__dict__'):
        # 自定义对象（FileItem / OperationResult 等）
        return _fast_size_estimate(value.__dict__, depth + 1) + 56
    if hasattr(value, '__slots__'):
        slot_size = 0
        for slot in value.__slots__:
            try:
                slot_size += _fast_size_estimate(getattr(value, slot, None), depth + 1)
            except Exception:
                slot_size += 32
        return slot_size + 56

    return 256


class CacheType(Enum):
    DIRECTORY = "directory"
    FILE_INFO = "file_info"
    PATH_MAPPING = "path_mapping"
    WEBDAV_METADATA = "webdav_metadata"
    DOWNLOAD_MODE = "download_mode"
    DOWNLOAD_URL = "download_url"
    ACCOUNT_CONFIG = "account_config"


class CacheStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    EVICTED = "evicted"
    INVALID = "invalid"


@dataclass
class CacheItem:
    key: str
    value: Any
    cache_type: CacheType
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int = 0
    last_access: Optional[datetime] = None
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.last_access is None:
            self.last_access = self.created_at

        if self.size_bytes == 0:
            self.size_bytes = self._estimate_size()

    def _estimate_size(self) -> int:
        try:
            return _fast_size_estimate(self.value) + 50 + len(self.key) * 2
        except Exception:
            return len(str(self.value)) * 2 + len(self.key)

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def touch(self) -> None:
        self.access_count += 1
        self.last_access = datetime.now()

    def get_age_seconds(self) -> float:
        return (datetime.now() - self.created_at).total_seconds()

    def get_ttl_seconds(self) -> Optional[float]:
        if self.expires_at is None:
            return None
        remaining = (self.expires_at - datetime.now()).total_seconds()
        return max(0, remaining)


@dataclass
class CacheConfig:
    max_items: int = 10000
    default_ttl: int = 3600
    cleanup_interval: int = 300
    memory_limit_mb: int = 512
    enable_persistence: bool = True
    persistence_path: str = "data/cache"

    type_ttl_config: Dict[CacheType, int] = field(default_factory=lambda: {
        CacheType.DOWNLOAD_MODE: 86400,
        CacheType.ACCOUNT_CONFIG: 86400,
    })

    def get_ttl_for_type(self, cache_type: CacheType) -> int:
        return self.type_ttl_config.get(cache_type, self.default_ttl)


@dataclass
class CacheStats:
    total_items: int = 0
    total_size_bytes: int = 0
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0
    memory_evictions: int = 0

    type_stats: Dict[CacheType, Dict[str, int]] = field(default_factory=dict)

    def __post_init__(self):
        if not self.type_stats:
            for cache_type in CacheType:
                self.type_stats[cache_type] = {
                    'items': 0,
                    'hits': 0,
                    'misses': 0,
                    'size_bytes': 0
                }

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    @property
    def memory_usage_mb(self) -> float:
        return self.total_size_bytes / (1024 * 1024)

    def get_type_hit_rate(self, cache_type: CacheType) -> float:
        stats = self.type_stats.get(cache_type, {})
        hits = stats.get('hits', 0)
        misses = stats.get('misses', 0)
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0

    def record_hit(self, cache_type: CacheType):
        self.hits += 1
        if cache_type in self.type_stats:
            self.type_stats[cache_type]['hits'] += 1

    def record_miss(self, cache_type: CacheType):
        self.misses += 1
        if cache_type in self.type_stats:
            self.type_stats[cache_type]['misses'] += 1

    def record_eviction(self, cache_type: CacheType, memory_pressure: bool = False):
        self.evictions += 1
        if memory_pressure:
            self.memory_evictions += 1


class CacheConstants:
    DEFAULT_MAX_ITEMS = 10000
    DEFAULT_TTL = 3600
    DEFAULT_CLEANUP_INTERVAL = 300
    DEFAULT_MEMORY_LIMIT_MB = 512

    KEY_PREFIX_DIRECTORY = "dir"
    KEY_PREFIX_DIR_FOLDER_SIZES = "dir_sizes"
    KEY_PREFIX_FILE_INFO = "file"
    KEY_PREFIX_PATH = "path"
    KEY_PREFIX_WEBDAV = "webdav"
    KEY_PREFIX_DOWNLOAD_MODE = "download_mode"
    KEY_PREFIX_DOWNLOAD_URL = "download_url"
    KEY_PREFIX_ACCOUNT_CONFIG = "config"

    KEY_SEPARATOR = ":"

    MEMORY_WARNING_THRESHOLD = 0.8
    MEMORY_CRITICAL_THRESHOLD = 0.9
