"""
⚡ Segula Real-Time Queue Manager Service
Manages concurrency limit (e.g., 5 parallel GPU inference slots) and maintains
a FIFO waiting queue with real-time SSE position broadcasting.
"""

import asyncio
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional, Set, Tuple

from backend import config

logger = logging.getLogger(__name__)


class QueueManager:
    """Thread-safe asynchronous FIFO Queue Manager for GPU inference slots."""

    def __init__(
        self,
        max_active: Optional[int] = None,
        max_queue: Optional[int] = None,
        estimated_seconds: Optional[int] = None,
    ):
        self.max_active: int = max_active or config.MAX_CONCURRENT_SUBMISSIONS
        self.max_queue: int = max_queue or config.MAX_QUEUE_CAPACITY
        self.estimated_seconds: int = estimated_seconds or config.ESTIMATED_ANALYSIS_SECONDS

        self._lock: asyncio.Lock = asyncio.Lock()
        self._active_requests: Set[str] = set()
        # List of (request_id, notify_event) in FIFO order
        self._waiting_queue: List[Tuple[str, asyncio.Event]] = []

    @property
    def active_count(self) -> int:
        return len(self._active_requests)

    @property
    def queued_count(self) -> int:
        return len(self._waiting_queue)

    def get_status_dict(self) -> Dict[str, Any]:
        """Returns instantaneous snapshot of the queue state."""
        return {
            "active_slots": len(self._active_requests),
            "max_slots": self.max_active,
            "queued_requests": len(self._waiting_queue),
            "max_queue": self.max_queue,
            "estimated_seconds_per_slot": self.estimated_seconds,
        }

    async def get_request_status(self, request_id: str) -> Dict[str, Any]:
        """Returns the real-time queue status of a specific request."""
        async with self._lock:
            if request_id in self._active_requests:
                return {
                    "status": "PROCESSING",
                    "position": 0,
                    "active_slots": len(self._active_requests),
                    "max_slots": self.max_active,
                    "total_queued": len(self._waiting_queue),
                    "estimated_wait_seconds": 0,
                    "message": "Slot allocated. AI analysis is active.",
                }
            pos = self._get_position_locked(request_id)
            if pos > 0:
                est_wait = pos * self.estimated_seconds
                return {
                    "status": "QUEUED",
                    "position": pos,
                    "active_slots": len(self._active_requests),
                    "max_slots": self.max_active,
                    "total_queued": len(self._waiting_queue),
                    "estimated_wait_seconds": est_wait,
                    "message": f"Server at capacity ({len(self._active_requests)}/{self.max_active}). You are #{pos} in queue.",
                }
            return {
                "status": "NOT_QUEUED",
                "position": -1,
                "active_slots": len(self._active_requests),
                "max_slots": self.max_active,
                "total_queued": len(self._waiting_queue),
                "estimated_wait_seconds": 0,
            }

    async def register_submission(self, request_id: str) -> Dict[str, Any]:
        """
        Quickly registers a submission in the queue manager without holding long-lived connections.
        Returns immediate status: 'PROCESSING' if slot is free, or 'QUEUED' with position.
        """
        async with self._lock:
            # 1. If buffer full
            if len(self._waiting_queue) >= self.max_queue:
                return {
                    "status": "QUEUE_FULL",
                    "position": -1,
                    "active_slots": len(self._active_requests),
                    "max_slots": self.max_active,
                    "total_queued": len(self._waiting_queue),
                    "estimated_wait_seconds": 0,
                    "message": "Server queue is currently full. Please retry shortly.",
                }

            # 2. If slot is immediately available
            if len(self._active_requests) < self.max_active:
                self._active_requests.add(request_id)
                logger.info(
                    "Fast-registered active slot | req=%s active=%d/%d queued=%d",
                    request_id,
                    len(self._active_requests),
                    self.max_active,
                    len(self._waiting_queue),
                )
                return {
                    "status": "PROCESSING",
                    "position": 0,
                    "active_slots": len(self._active_requests),
                    "max_slots": self.max_active,
                    "total_queued": len(self._waiting_queue),
                    "estimated_wait_seconds": 0,
                    "message": "Slot allocated. Starting AI analysis.",
                }

            # 3. Otherwise enqueue
            for r_id, _ in self._waiting_queue:
                if r_id == request_id:
                    pos = self._get_position_locked(request_id)
                    return {
                        "status": "QUEUED",
                        "position": pos,
                        "active_slots": len(self._active_requests),
                        "max_slots": self.max_active,
                        "total_queued": len(self._waiting_queue),
                        "estimated_wait_seconds": pos * self.estimated_seconds,
                        "message": f"Server at capacity ({len(self._active_requests)}/{self.max_active}). You are #{pos} in queue.",
                    }

            notify_event = asyncio.Event()
            self._waiting_queue.append((request_id, notify_event))
            pos = len(self._waiting_queue)
            est_wait = pos * self.estimated_seconds

            logger.info(
                "Fast-registered queued request | req=%s position=%d active=%d/%d total_queued=%d est_wait=%ds",
                request_id,
                pos,
                len(self._active_requests),
                self.max_active,
                len(self._waiting_queue),
                est_wait,
            )

            return {
                "status": "QUEUED",
                "position": pos,
                "active_slots": len(self._active_requests),
                "max_slots": self.max_active,
                "total_queued": len(self._waiting_queue),
                "estimated_wait_seconds": est_wait,
                "message": f"Server at capacity ({len(self._active_requests)}/{self.max_active}). You are #{pos} in queue.",
            }

    async def acquire_slot(self, request_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Asynchronously acquires a processing slot.
        Yields status dictionaries as SSE queue updates until the slot is acquired (status='PROCESSING').
        """
        notify_event = asyncio.Event()
        is_queued = False

        async with self._lock:
            # Check if already active (e.g. via fast register)
            if request_id in self._active_requests:
                yield {
                    "status": "PROCESSING",
                    "position": 0,
                    "active_slots": len(self._active_requests),
                    "max_slots": self.max_active,
                    "total_queued": len(self._waiting_queue),
                    "estimated_wait_seconds": 0,
                    "message": "Slot allocated. Starting AI analysis.",
                }
                return

            # 1. Reject if waiting buffer is full
            if len(self._waiting_queue) >= self.max_queue:
                yield {
                    "status": "QUEUE_FULL",
                    "position": -1,
                    "active_slots": len(self._active_requests),
                    "max_slots": self.max_active,
                    "total_queued": len(self._waiting_queue),
                    "estimated_wait_seconds": 0,
                    "message": "Server queue is currently full. Please retry shortly.",
                }
                return

            # 2. If slot is immediately available
            if len(self._active_requests) < self.max_active:
                self._active_requests.add(request_id)
                logger.info(
                    "Slot immediately granted | req=%s active=%d/%d queued=%d",
                    request_id,
                    len(self._active_requests),
                    self.max_active,
                    len(self._waiting_queue),
                )
                yield {
                    "status": "PROCESSING",
                    "position": 0,
                    "active_slots": len(self._active_requests),
                    "max_slots": self.max_active,
                    "total_queued": len(self._waiting_queue),
                    "estimated_wait_seconds": 0,
                    "message": "Slot allocated. Starting AI analysis.",
                }
                return

            # 3. Otherwise, enqueue in FIFO waiting list
            # Check if already in queue
            already_in = False
            for r_id, evt in self._waiting_queue:
                if r_id == request_id:
                    notify_event = evt
                    already_in = True
                    break

            if not already_in:
                self._waiting_queue.append((request_id, notify_event))

            is_queued = True
            pos = self._get_position_locked(request_id)
            est_wait = pos * self.estimated_seconds

            logger.info(
                "Request queued | req=%s position=%d active=%d/%d total_queued=%d est_wait=%ds",
                request_id,
                pos,
                len(self._active_requests),
                self.max_active,
                len(self._waiting_queue),
                est_wait,
            )

            yield {
                "status": "QUEUED",
                "position": pos,
                "active_slots": len(self._active_requests),
                "max_slots": self.max_active,
                "total_queued": len(self._waiting_queue),
                "estimated_wait_seconds": est_wait,
                "message": f"Server at capacity ({len(self._active_requests)}/{self.max_active}). You are #{pos} in queue.",
            }

        # 4. Wait loop while queued
        try:
            while is_queued:
                try:
                    await asyncio.wait_for(notify_event.wait(), timeout=15.0)
                    notify_event.clear()
                except asyncio.TimeoutError:
                    pass

                async with self._lock:
                    # Check if slot was granted
                    if request_id in self._active_requests:
                        break

                    pos = self._get_position_locked(request_id)
                    if pos > 0:
                        est_wait = pos * self.estimated_seconds
                        yield {
                            "status": "QUEUED",
                            "position": pos,
                            "active_slots": len(self._active_requests),
                            "max_slots": self.max_active,
                            "total_queued": len(self._waiting_queue),
                            "estimated_wait_seconds": est_wait,
                            "message": f"Queue advanced! You are now #{pos} in queue (~{est_wait}s).",
                        }

            # 5. Slot is now granted
            async with self._lock:
                yield {
                    "status": "PROCESSING",
                    "position": 0,
                    "active_slots": len(self._active_requests),
                    "max_slots": self.max_active,
                    "total_queued": len(self._waiting_queue),
                    "estimated_wait_seconds": 0,
                    "message": "Slot allocated! Starting AI analysis.",
                }

        except Exception as e:
            logger.warning("Exception while waiting in queue | req=%s err=%s", request_id, e)
            await self.release_slot(request_id)
            raise

    async def release_slot(self, request_id: str):
        """
        Releases an active processing slot or removes an abandoned request from the queue.
        Wakes up the next waiting request in FIFO order.
        """
        async with self._lock:
            # 1. Remove from active requests if present
            was_active = request_id in self._active_requests
            self._active_requests.discard(request_id)

            # 2. Remove from waiting queue if client disconnected while waiting
            self._waiting_queue = [item for item in self._waiting_queue if item[0] != request_id]

            # 3. Promote next in line if slot is available
            if len(self._active_requests) < self.max_active and self._waiting_queue:
                next_req_id, next_event = self._waiting_queue.pop(0)
                self._active_requests.add(next_req_id)
                next_event.set()
                logger.info(
                    "Promoted next queued request | req=%s active=%d/%d remaining_queued=%d",
                    next_req_id,
                    len(self._active_requests),
                    self.max_active,
                    len(self._waiting_queue),
                )

            # 4. Notify all remaining waiting requests that positions changed
            for _, event in self._waiting_queue:
                event.set()

            if was_active:
                logger.info(
                    "Released slot | req=%s active=%d/%d queued=%d",
                    request_id,
                    len(self._active_requests),
                    self.max_active,
                    len(self._waiting_queue),
                )

    def _get_position_locked(self, request_id: str) -> int:
        """Returns 1-based position in waiting queue, or 0 if not in queue."""
        for idx, (r_id, _) in enumerate(self._waiting_queue, 1):
            if r_id == request_id:
                return idx
        return 0


# Global singleton instance
queue_manager = QueueManager()
