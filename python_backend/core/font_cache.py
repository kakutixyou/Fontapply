"""
core/font_cache.py
──────────────────
生成・変換済みフォントをプロセスメモリ上に一時保持するキャッシュ。

役割:
  /fonts/generate や /fonts/subset で作ったフォントを
  font_id (UUID) で参照できるようにする。
  /fonts/preview/{id} や /fonts/convert で使い回す。

設計:
  - シングルトン（FontCache.instance()）
  - TTL 付き（デフォルト 30 分、アクセスで更新）
  - 最大エントリ数制限（メモリ保護）
  - スレッドセーフ（threading.Lock）
"""

from __future__ import annotations
import json
import logging
import sqlite3
import threading
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Callable, Optional


@dataclass
class CachedFont:
    """キャッシュの1エントリ。"""

    font_id: str
    font_bytes: bytes  # TTF or WOFF2
    family_name: str
    style_name: str
    is_woff2: bool
    created_at: float = field(default_factory=time.monotonic)
    accessed_at: float = field(default_factory=time.monotonic)

    def touch(self) -> None:
        """アクセス時刻を更新する（TTL をリセット）。"""
        self.accessed_at = time.monotonic()

    @property
    def age_seconds(self) -> float:
        return time.monotonic() - self.accessed_at


class FontCache:
    """
    生成済みフォントの一時キャッシュ。

    使い方:
        cache = FontCache.instance()

        # 保存
        font_id = cache.put(woff2_bytes, "MyFont", "Regular", is_woff2=True)

        # 取得
        entry = cache.get(font_id)
        if entry:
            return entry.font_bytes

        # 削除
        cache.delete(font_id)
    """

    _instance: Optional["FontCache"] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(
        self,
        ttl_seconds: int = 1800,  # 30 分
        max_entries: int = 100,
        max_bytes: int = 200 * 1024 * 1024,  # 200MB
    ) -> None:
        self._ttl = ttl_seconds
        self._max = max_entries
        self._max_bytes = max_bytes
        self._store: dict[str, CachedFont] = {}
        self._rw_lock = threading.Lock()

    @classmethod
    def instance(cls) -> "FontCache":
        """シングルトンインスタンスを返す。"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ──────────────────────────────
    # 基本操作
    # ──────────────────────────────

    def put(
        self,
        font_bytes: bytes,
        family_name: str,
        style_name: str,
        is_woff2: bool = True,
    ) -> str:
        """
        フォントを保存して font_id を返す。
        容量超過時は古いエントリを自動削除する。
        """
        self._evict_expired()

        with self._rw_lock:
            # 容量チェック
            if len(self._store) >= self._max:
                self._evict_oldest()
            if self._total_bytes() + len(font_bytes) > self._max_bytes:
                self._evict_oldest(n=max(1, len(self._store) // 4))

            font_id = str(uuid.uuid4())
            self._store[font_id] = CachedFont(
                font_id=font_id,
                font_bytes=font_bytes,
                family_name=family_name,
                style_name=style_name,
                is_woff2=is_woff2,
            )
            return font_id

    def get(self, font_id: str) -> Optional[CachedFont]:
        """
        font_id でエントリを取得する。
        見つからない・有効期限切れの場合は None。
        """
        with self._rw_lock:
            entry = self._store.get(font_id)
            if entry is None:
                return None
            if entry.age_seconds > self._ttl:
                del self._store[font_id]
                return None
            entry.touch()
            return entry

    def delete(self, font_id: str) -> bool:
        """エントリを削除する。存在した場合 True。"""
        with self._rw_lock:
            return self._store.pop(font_id, None) is not None

    def exists(self, font_id: str) -> bool:
        return self.get(font_id) is not None

    # ──────────────────────────────
    # 統計・管理
    # ──────────────────────────────

    @property
    def entry_count(self) -> int:
        with self._rw_lock:
            return len(self._store)

    def stats(self) -> dict:
        with self._rw_lock:
            return {
                "entries": len(self._store),
                "total_bytes": self._total_bytes(),
                "max_entries": self._max,
                "ttl_seconds": self._ttl,
            }

    def clear(self) -> None:
        with self._rw_lock:
            self._store.clear()

    # ──────────────────────────────
    # 内部
    # ──────────────────────────────

    def _evict_expired(self) -> None:
        with self._rw_lock:
            expired = [k for k, v in self._store.items() if v.age_seconds > self._ttl]
            for k in expired:
                del self._store[k]

    def _evict_oldest(self, n: int = 1) -> None:
        """最も古いエントリを n 件削除する（Lock 取得済み前提）。"""
        sorted_keys = sorted(
            self._store.keys(), key=lambda k: self._store[k].accessed_at
        )
        for k in sorted_keys[:n]:
            del self._store[k]

    def _total_bytes(self) -> int:
        """保持中の全フォントバイト数合計（Lock 取得済み前提）。"""
        return sum(len(e.font_bytes) for e in self._store.values())


logger = logging.getLogger(__name__)
DEFAULT_ANALYTICS_TTL_SECONDS = 30 * 24 * 60 * 60
DEFAULT_ANALYTICS_DB_PATH = (
    Path(__file__).resolve().parents[2] / "database" / "font_studio.db"
)


class CacheMetrics:
    """Analytics キャッシュパフォーマンス測定。"""

    def __init__(self) -> None:
        self.hits = 0
        self.misses = 0
        self.compute_times: list[float] = []
        self.layer_hits: dict[str, int] = {
            "memory": 0,
            "db": 0,
            "redis": 0,
            "compute": 0,
        }

    def record_hit(self, layer: str) -> None:
        self.hits += 1
        self.layer_hits[layer] = self.layer_hits.get(layer, 0) + 1

    def record_miss(self) -> None:
        self.misses += 1

    def record_compute_time(self, elapsed_ms: float) -> None:
        self.compute_times.append(elapsed_ms)

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    @property
    def avg_compute_time_ms(self) -> float:
        return float(mean(self.compute_times)) if self.compute_times else 0.0

    def to_dict(self, memory_entries: int, db_entries: int) -> dict[str, object]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hit_rate,
            "avg_compute_time_ms": self.avg_compute_time_ms,
            "memory_entries": memory_entries,
            "db_entries": db_entries,
            "layer_hits": self.layer_hits,
            "redis_enabled": False,
        }


class FontCacheManager:
    """Analytics 結果向けの二層キャッシュ（メモリ LRU + SQLite）。"""

    def __init__(
        self,
        db_path: Path = DEFAULT_ANALYTICS_DB_PATH,
        max_memory_entries: int = 100,
        default_ttl_seconds: int = DEFAULT_ANALYTICS_TTL_SECONDS,
    ) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._max_entries = max_memory_entries
        self._default_ttl_seconds = default_ttl_seconds
        self._memory_cache: OrderedDict[str, dict[str, object]] = OrderedDict()
        self._memory_lock = threading.Lock()
        self._db_lock = threading.Lock()
        self._metrics = CacheMetrics()
        self._ensure_tables()

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _to_db_timestamp(dt: datetime) -> str:
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _ensure_tables(self) -> None:
        with self._db_lock:
            conn = self._connect()
            cur = conn.cursor()
            cur.executescript("""
                CREATE TABLE IF NOT EXISTS font_analytics_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    font_id TEXT UNIQUE NOT NULL,
                    font_bytes_hash TEXT NOT NULL,
                    metrics_json TEXT NOT NULL,
                    recommendations_json TEXT NOT NULL,
                    glyph_stats_json TEXT NOT NULL,
                    has_cjk BOOLEAN NOT NULL DEFAULT 0,
                    available_weights TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    hit_count INTEGER DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS idx_font_analytics_cache_font_id
                    ON font_analytics_cache(font_id);
                CREATE INDEX IF NOT EXISTS idx_font_analytics_cache_expires_at
                    ON font_analytics_cache(expires_at);
                CREATE TABLE IF NOT EXISTS analytics_cache_hits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    font_id TEXT NOT NULL,
                    cache_layer TEXT NOT NULL,
                    response_time_ms FLOAT NOT NULL,
                    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (font_id) REFERENCES font_analytics_cache(font_id) ON DELETE CASCADE
                );
                """)
            conn.commit()
            conn.close()

    def _evict_memory_lru(self) -> None:
        while len(self._memory_cache) > self._max_entries:
            self._memory_cache.popitem(last=False)

    def _log_access(
        self, font_id: str, cache_layer: str, response_time_ms: float
    ) -> None:
        with self._db_lock:
            conn = self._connect()
            try:
                conn.execute(
                    """
                    INSERT INTO analytics_cache_hits (font_id, cache_layer, response_time_ms)
                    VALUES (?, ?, ?)
                    """,
                    (font_id, cache_layer, float(response_time_ms)),
                )
            except sqlite3.IntegrityError:
                logger.debug(
                    "Skip analytics_cache_hits insert for missing font_id=%s", font_id
                )
            conn.commit()
            conn.close()

    def _increment_hit_count(self, font_id: str) -> None:
        with self._db_lock:
            conn = self._connect()
            conn.execute(
                "UPDATE font_analytics_cache SET hit_count = hit_count + 1 WHERE font_id = ?",
                (font_id,),
            )
            conn.commit()
            conn.close()

    def get(self, font_id: str) -> tuple[dict[str, object] | None, str]:
        started = time.perf_counter()
        now = self._utc_now()

        with self._memory_lock:
            cached = self._memory_cache.get(font_id)
            if cached and isinstance(cached.get("expires_at"), datetime):
                if cached["expires_at"] > now:
                    self._memory_cache.move_to_end(font_id)
                    self._metrics.record_hit("memory")
                    elapsed_ms = (time.perf_counter() - started) * 1000
                    self._log_access(font_id, "memory", elapsed_ms)
                    self._increment_hit_count(font_id)
                    return cached["data"], "memory"
                self._memory_cache.pop(font_id, None)

        with self._db_lock:
            conn = self._connect()
            row = conn.execute(
                """
                SELECT font_id, metrics_json, recommendations_json, glyph_stats_json, has_cjk,
                       available_weights, expires_at
                FROM font_analytics_cache
                WHERE font_id = ? AND expires_at > CURRENT_TIMESTAMP
                """,
                (font_id,),
            ).fetchone()
            conn.close()

        if not row:
            self._metrics.record_miss()
            return None, "miss"

        try:
            data = {
                "font_id": row["font_id"],
                "metrics": json.loads(row["metrics_json"] or "{}"),
                "recommendations": json.loads(row["recommendations_json"] or "{}"),
                "glyph_stats": json.loads(row["glyph_stats_json"] or "{}"),
                "has_cjk": bool(row["has_cjk"]),
                "available_weights": json.loads(row["available_weights"] or "[]"),
            }
        except json.JSONDecodeError:
            logger.warning("Corrupted analytics cache detected for font_id=%s", font_id)
            self.clear(font_id)
            self._metrics.record_miss()
            return None, "miss"

        expires_at = datetime.strptime(row["expires_at"], "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=timezone.utc
        )
        with self._memory_lock:
            self._memory_cache[font_id] = {"data": data, "expires_at": expires_at}
            self._memory_cache.move_to_end(font_id)
            self._evict_memory_lru()

        self._metrics.record_hit("db")
        elapsed_ms = (time.perf_counter() - started) * 1000
        self._log_access(font_id, "db", elapsed_ms)
        self._increment_hit_count(font_id)
        return data, "db"

    def set(
        self,
        font_id: str,
        data: dict[str, object],
        font_bytes_hash: str | None = None,
        ttl_seconds: int | None = None,
    ) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl_seconds
        expires_at = self._utc_now() + timedelta(seconds=ttl)
        with self._memory_lock:
            self._memory_cache[font_id] = {"data": data, "expires_at": expires_at}
            self._memory_cache.move_to_end(font_id)
            self._evict_memory_lru()

        metrics_json = json.dumps(data.get("metrics", {}), ensure_ascii=False)
        recommendations_json = json.dumps(
            data.get("recommendations", {}), ensure_ascii=False
        )
        glyph_stats_json = json.dumps(data.get("glyph_stats", {}), ensure_ascii=False)
        available_weights_json = json.dumps(
            data.get("available_weights", []), ensure_ascii=False
        )
        font_hash = font_bytes_hash or font_id

        with self._db_lock:
            conn = self._connect()
            conn.execute(
                """
                INSERT INTO font_analytics_cache
                (font_id, font_bytes_hash, metrics_json, recommendations_json, glyph_stats_json,
                 has_cjk, available_weights, expires_at, hit_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                ON CONFLICT(font_id) DO UPDATE SET
                    font_bytes_hash = excluded.font_bytes_hash,
                    metrics_json = excluded.metrics_json,
                    recommendations_json = excluded.recommendations_json,
                    glyph_stats_json = excluded.glyph_stats_json,
                    has_cjk = excluded.has_cjk,
                    available_weights = excluded.available_weights,
                    expires_at = excluded.expires_at
                """,
                (
                    font_id,
                    font_hash,
                    metrics_json,
                    recommendations_json,
                    glyph_stats_json,
                    int(bool(data.get("has_cjk", False))),
                    available_weights_json,
                    self._to_db_timestamp(expires_at),
                ),
            )
            conn.commit()
            conn.close()

    def get_or_compute(
        self, font_id: str, compute_fn: Callable[[], dict[str, object]]
    ) -> tuple[dict[str, object], str]:
        cached, layer = self.get(font_id)
        if cached is not None:
            return cached, layer

        started = time.perf_counter()
        computed = compute_fn()
        elapsed_ms = (time.perf_counter() - started) * 1000
        self.set(font_id, computed)
        self._metrics.record_hit("compute")
        self._metrics.record_compute_time(elapsed_ms)
        self._log_access(font_id, "compute", elapsed_ms)
        return computed, "compute"

    def clear(self, font_id: str) -> bool:
        deleted_memory = False
        with self._memory_lock:
            deleted_memory = self._memory_cache.pop(font_id, None) is not None
        with self._db_lock:
            conn = self._connect()
            conn.execute(
                "DELETE FROM analytics_cache_hits WHERE font_id = ?", (font_id,)
            )
            cur = conn.execute(
                "DELETE FROM font_analytics_cache WHERE font_id = ?", (font_id,)
            )
            conn.commit()
            conn.close()
        return deleted_memory or cur.rowcount > 0

    def clear_all(self) -> None:
        with self._memory_lock:
            self._memory_cache.clear()
        with self._db_lock:
            conn = self._connect()
            conn.execute("DELETE FROM analytics_cache_hits")
            conn.execute("DELETE FROM font_analytics_cache")
            conn.commit()
            conn.close()

    def cleanup_expired(self) -> int:
        with self._memory_lock:
            now = self._utc_now()
            expired_keys = [
                font_id
                for font_id, payload in self._memory_cache.items()
                if isinstance(payload.get("expires_at"), datetime)
                and payload["expires_at"] <= now
            ]
            for key in expired_keys:
                self._memory_cache.pop(key, None)

        with self._db_lock:
            conn = self._connect()
            cur = conn.execute(
                "DELETE FROM font_analytics_cache WHERE expires_at <= CURRENT_TIMESTAMP"
            )
            conn.execute("""
            DELETE FROM analytics_cache_hits
            WHERE NOT EXISTS (
                SELECT 1
                FROM font_analytics_cache
                WHERE font_analytics_cache.font_id = analytics_cache_hits.font_id
            )
            """)
            conn.commit()
            deleted = cur.rowcount
            conn.close()

        if deleted:
            logger.info("Cleaned up %s expired analytics cache entries", deleted)
        return deleted

    def get_statistics(self) -> dict[str, object]:
        with self._memory_lock:
            memory_entries = len(self._memory_cache)
        with self._db_lock:
            conn = self._connect()
            row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM font_analytics_cache"
            ).fetchone()
            conn.close()
        db_entries = int(row["cnt"]) if row else 0
        stats = self._metrics.to_dict(
            memory_entries=memory_entries, db_entries=db_entries
        )
        logger.info(
            "Analytics cache stats - hit_rate=%.1f%% avg_compute=%.2fms",
            stats["hit_rate"] * 100,
            stats["avg_compute_time_ms"],
        )
        return stats


class CacheCleanupScheduler:
    """期限切れキャッシュ削除スケジューラー。"""

    def __init__(self, cache_manager: FontCacheManager) -> None:
        self._cache_manager = cache_manager

    async def cleanup_expired(self) -> int:
        return self._cache_manager.cleanup_expired()
