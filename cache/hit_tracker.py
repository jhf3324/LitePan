"""缓存命中率追踪：给前端仪表盘用，会话级 + 全局两套计数。"""

from datetime import datetime, timedelta
from typing import Dict, Optional
from dataclasses import dataclass
import asyncio


@dataclass
class HitRateStats:
    session_id: str
    start_time: datetime
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

    @property
    def hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits / self.total_requests) * 100

    @property
    def duration_minutes(self) -> float:
        return (datetime.now() - self.start_time).total_seconds() / 60

    def record_hit(self):
        self.total_requests += 1
        self.cache_hits += 1

    def record_miss(self):
        self.total_requests += 1
        self.cache_misses += 1

    def to_dict(self) -> Dict:
        return {
            'session_id': self.session_id,
            'total_requests': self.total_requests,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': round(self.hit_rate, 1),
            'duration_minutes': round(self.duration_minutes, 1)
        }


class HitRateTracker:
    def __init__(self):
        self.sessions: Dict[str, HitRateStats] = {}
        self.global_stats = HitRateStats("global", datetime.now())
        self.cleanup_task: Optional[asyncio.Task] = None
        self.lock = asyncio.Lock()

    async def start(self):
        if not self.cleanup_task:
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

    async def _cleanup_loop(self):
        while True:
            try:
                await asyncio.sleep(600)
                await self._cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception:
                pass

    async def _cleanup_expired_sessions(self):
        async with self.lock:
            now = datetime.now()
            expired_sessions = []

            for session_id, stats in self.sessions.items():
                # 1 小时没写入就当作废弃会话
                if (now - stats.start_time).total_seconds() > 3600:
                    expired_sessions.append(session_id)

            for session_id in expired_sessions:
                del self.sessions[session_id]

    async def record_hit(self, session_id: str = "default") -> Dict:
        async with self.lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = HitRateStats(session_id, datetime.now())

            stats = self.sessions[session_id]
            stats.record_hit()
            self.global_stats.record_hit()

            return stats.to_dict()

    async def record_miss(self, session_id: str = "default") -> Dict:
        async with self.lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = HitRateStats(session_id, datetime.now())

            stats = self.sessions[session_id]
            stats.record_miss()
            self.global_stats.record_miss()

            return stats.to_dict()

    async def get_stats(self, session_id: str = "default") -> Optional[Dict]:
        async with self.lock:
            stats = self.sessions.get(session_id)
            return stats.to_dict() if stats else None

    async def get_global_stats(self) -> Dict:
        async with self.lock:
            return self.global_stats.to_dict()

    async def reset_stats(self):
        async with self.lock:
            self.global_stats = HitRateStats("global", datetime.now())
            self.sessions.clear()


_hit_tracker: Optional[HitRateTracker] = None


def get_hit_tracker() -> HitRateTracker:
    global _hit_tracker
    if _hit_tracker is None:
        _hit_tracker = HitRateTracker()
    return _hit_tracker


async def init_hit_tracker():
    tracker = get_hit_tracker()
    await tracker.start()
    return tracker
