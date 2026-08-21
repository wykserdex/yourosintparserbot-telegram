"""AccountPool with health-check, dynamic flood-wait handling, and session rotation."""

import asyncio
import contextlib
import logging
import random
import time
from datetime import UTC, datetime, timedelta
from typing import Any

from .client import SmartTelegramClient

logger = logging.getLogger(__name__)


class AccountPool:
    """Manages Telegram worker accounts with intelligent load balancing and auto-recovery."""

    def __init__(self, accounts_config: dict[str, dict[str, Any]] | None = None):
        self.accounts_config = accounts_config or {}
        self.accounts: list[dict[str, Any]] = []
        self.chat_assignments: dict[str, int] = {}
        self._lock = asyncio.Lock()
        self._request_times: dict[str, list[float]] = {}
        self._health_check_task: asyncio.Task | None = None
        self.stats = {
            "total_requests": 0,
            "flood_events": 0,
            "bans": 0,
            "recoveries": 0,
            "health_checks": 0,
            "rotations": 0,
        }

    async def initialize(
        self, account_names: list[str] | None = None, max_retries: int = 3
    ) -> list[dict[str, Any]]:
        names = account_names or list(self.accounts_config.keys())
        logger.info(f"Initializing {len(names)} accounts in AccountPool...")

        for name in names:
            cfg = self.accounts_config.get(name, {})
            for attempt in range(max_retries):
                try:
                    client = SmartTelegramClient(
                        session_name=name,
                        api_id=cfg.get("api_id", 0),
                        api_hash=cfg.get("api_hash", ""),
                        phone=cfg.get("phone"),
                        pool=self,
                    )
                    if cfg.get("api_id") and cfg.get("api_hash"):
                        await client.start()
                        me = await client.get_me()
                        phone = me.get("phone") if me else "unknown"
                        username = me.get("username") if me else None
                    else:
                        phone = cfg.get("phone", "mock-phone")
                        username = f"{name}_bot"

                    self.accounts.append(
                        {
                            "name": name,
                            "client": client,
                            "phone": phone,
                            "username": username,
                            "status": "active",
                            "ban_until": None,
                            "chats_assigned": [],
                            "total_requests": 0,
                            "last_used": None,
                            "errors": 0,
                            "health_check_failures": 0,
                        }
                    )
                    self._request_times[name] = []
                    logger.info(f"  OK {name}: @{username} ({phone})")
                    break
                except Exception as e:
                    logger.warning(f"  WARN {name} attempt {attempt + 1}/{max_retries}: {e}")
                    if attempt == max_retries - 1:
                        logger.error(f"  FAIL {name}")
                    await asyncio.sleep(random.uniform(1.0, 3.0))

        logger.info(f"Loaded {len(self.accounts)} active accounts")
        if not self._health_check_task and self.accounts:
            self._health_check_task = asyncio.create_task(self._health_check_loop())

        return self.accounts

    async def register_account(
        self, name: str, client: Any, phone: str | None = None, username: str | None = None
    ) -> None:
        async with self._lock:
            self.accounts.append(
                {
                    "name": name,
                    "client": client,
                    "phone": phone or "mock",
                    "username": username or name,
                    "status": "active",
                    "ban_until": None,
                    "chats_assigned": [],
                    "total_requests": 0,
                    "last_used": None,
                    "errors": 0,
                    "health_check_failures": 0,
                }
            )
            self._request_times[name] = []

    async def temporary_disable(self, session_name: str, seconds: int) -> None:
        async with self._lock:
            self._temporary_disable_locked(session_name, seconds)

    def _temporary_disable_locked(self, session_name: str, seconds: int) -> None:
        acc = self._get_account_by_name(session_name)
        if not acc:
            return
        until = datetime.now(UTC) + timedelta(seconds=seconds)
        acc["ban_until"] = until

        if seconds > 300:
            acc["status"] = "banned"
            self.stats["bans"] += 1
            logger.warning(f"BAN {session_name} for {seconds // 60}m")
        elif seconds > 60:
            acc["status"] = "flood_wait"
            self.stats["flood_events"] += 1
            logger.info(f"FLOOD {session_name} wait {seconds}s")
        else:
            acc["status"] = "cooling"
            logger.debug(f"COOLING {session_name} for {seconds}s")

    async def enable_account(self, session_name: str) -> None:
        async with self._lock:
            acc = self._get_account_by_name(session_name)
            if acc:
                acc["status"] = "active"
                acc["ban_until"] = None
                acc["errors"] = 0
                self.stats["recoveries"] += 1

    def _is_unbanned(self, account: dict[str, Any]) -> bool:
        if account["ban_until"] and datetime.now(UTC) > account["ban_until"]:
            account["status"] = "active"
            account["ban_until"] = None
            self.stats["recoveries"] += 1
            return True
        return account["status"] == "active"

    async def get_next_available(
        self, chat_username: str | None = None, prefer_same: bool = True
    ) -> Any | None:
        """Selects the optimal account using chat affinity and least RPM load balancing."""
        async with self._lock:
            if chat_username and prefer_same and chat_username in self.chat_assignments:
                idx = self.chat_assignments[chat_username]
                if idx < len(self.accounts):
                    acc = self.accounts[idx]
                    if acc["status"] == "active" or self._is_unbanned(acc):
                        acc["status"] = "active"
                        acc["ban_until"] = None
                        acc["last_used"] = datetime.now(UTC)
                        acc["total_requests"] += 1
                        self._track_request(acc["name"])
                        return acc["client"]

            available = [
                a for a in self.accounts if a["status"] == "active" or self._is_unbanned(a)
            ]

            if not available:
                banned = [a for a in self.accounts if a["ban_until"]]
                if banned:
                    banned.sort(key=lambda a: a["ban_until"])
                    wait_time = (banned[0]["ban_until"] - datetime.now(UTC)).total_seconds()
                    if wait_time > 0:
                        logger.warning(
                            f"All accounts rate-limited. Next available: {banned[0]['name']} in {wait_time:.0f}s"
                        )
                return None

            available.sort(
                key=lambda a: (
                    self._get_rpm(a["name"]),
                    len(a.get("chats_assigned", [])),
                    a.get("health_check_failures", 0),
                )
            )

            chosen = available[0]
            chosen["status"] = "active"
            chosen["ban_until"] = None
            chosen["last_used"] = datetime.now(UTC)
            chosen["total_requests"] += 1

            if chat_username and chat_username not in self.chat_assignments:
                idx = self.accounts.index(chosen)
                self.chat_assignments[chat_username] = idx
                if "chats_assigned" not in chosen:
                    chosen["chats_assigned"] = []
                chosen["chats_assigned"].append(chat_username)

            self._track_request(chosen["name"])
            return chosen["client"]

    def _track_request(self, account_name: str) -> None:
        if account_name not in self._request_times:
            self._request_times[account_name] = []
        now_ts = time.time()
        self._request_times[account_name].append(now_ts)
        cutoff = now_ts - 60
        self._request_times[account_name] = [
            t for t in self._request_times[account_name] if t > cutoff
        ]
        self.stats["total_requests"] += 1

    def _get_rpm(self, account_name: str) -> int:
        if account_name not in self._request_times:
            return 0
        cutoff = time.time() - 60
        return len([t for t in self._request_times[account_name] if t > cutoff])

    def _get_account_by_name(self, name: str) -> dict[str, Any] | None:
        for acc in self.accounts:
            if acc["name"] == name:
                return acc
        return None

    async def report_flood(self, client: Any, wait_seconds: int) -> None:
        async with self._lock:
            for acc in self.accounts:
                if acc["client"] == client:
                    self._temporary_disable_locked(acc["name"], wait_seconds)
                    break

    async def report_error(self, client: Any) -> None:
        async with self._lock:
            for acc in self.accounts:
                if acc["client"] == client:
                    acc["errors"] = acc.get("errors", 0) + 1
                    if acc["errors"] > 5:
                        self._temporary_disable_locked(acc["name"], 300)
                    break

    async def rotate_session(self, session_name: str) -> None:
        acc = self._get_account_by_name(session_name)
        if not acc:
            return
        self.stats["rotations"] += 1
        try:
            if acc.get("client") and hasattr(acc["client"], "stop"):
                with contextlib.suppress(Exception):
                    await acc["client"].stop()

            cfg = self.accounts_config.get(session_name, {})
            client = SmartTelegramClient(
                session_name=session_name,
                api_id=cfg.get("api_id", 0),
                api_hash=cfg.get("api_hash", ""),
                phone=cfg.get("phone"),
                pool=self,
            )
            if cfg.get("api_id") and cfg.get("api_hash"):
                await client.start()
            acc["client"] = client
            acc["status"] = "active"
            acc["ban_until"] = None
            acc["errors"] = 0
            acc["health_check_failures"] = 0
            logger.info(f"Rotated session successfully: {session_name}")
        except Exception as e:
            logger.error(f"Rotation failed for {session_name}: {e}")
            await self.temporary_disable(session_name, 600)

    async def _health_check_loop(self) -> None:
        while True:
            try:
                await asyncio.sleep(300)
                self.stats["health_checks"] += 1
                for acc in self.accounts:
                    if acc["status"] != "active":
                        continue
                    try:
                        client = acc.get("client")
                        if client:
                            me = await client.get_me()
                            if not me:
                                acc["health_check_failures"] += 1
                            else:
                                acc["health_check_failures"] = 0
                        else:
                            acc["health_check_failures"] += 1

                        if acc["health_check_failures"] >= 3:
                            await self.rotate_session(acc["name"])
                    except Exception:
                        acc["health_check_failures"] += 1
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"Health check error: {e}")
                break

    async def get_stats(self) -> dict[str, Any]:
        stats: dict[str, Any] = {
            "total": len(self.accounts),
            "active": 0,
            "banned": 0,
            "flood_wait": 0,
            "cooling": 0,
            "total_requests": self.stats["total_requests"],
            "flood_events": self.stats["flood_events"],
            "bans": self.stats["bans"],
            "recoveries": self.stats["recoveries"],
            "health_checks": self.stats["health_checks"],
            "rotations": self.stats["rotations"],
            "accounts": [],
        }
        for acc in self.accounts:
            status = acc["status"]
            if status == "active":
                stats["active"] += 1
            elif status == "banned":
                stats["banned"] += 1
            elif status == "flood_wait":
                stats["flood_wait"] += 1
            elif status == "cooling":
                stats["cooling"] += 1

            stats["accounts"].append(
                {
                    "name": acc["name"],
                    "username": acc.get("username"),
                    "status": status,
                    "rpm": self._get_rpm(acc["name"]),
                    "chats": len(acc.get("chats_assigned", [])),
                    "ban_until": acc["ban_until"].isoformat() if acc["ban_until"] else None,
                    "errors": acc.get("errors", 0),
                    "total_requests": acc.get("total_requests", 0),
                    "health_failures": acc.get("health_check_failures", 0),
                }
            )
        return stats

    async def close_all(self) -> None:
        if self._health_check_task:
            self._health_check_task.cancel()
            with contextlib.suppress(Exception):
                await self._health_check_task
        for acc in self.accounts:
            try:
                if acc.get("client") and hasattr(acc["client"], "stop"):
                    await acc["client"].stop()
            except Exception:
                pass
        logger.info("AccountPool: All client connections closed")
