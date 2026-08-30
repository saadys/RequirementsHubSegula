"""
Unit and Concurrency Tests for QueueManager Service
Verifies 5-slot GPU concurrency control, FIFO queue ordering, position broadcasting, and cleanup.
"""

import asyncio
import pytest
from backend.services.queue_manager import QueueManager


@pytest.mark.asyncio
async def test_queue_manager_immediate_acquisition():
    """Requests under max_active (5) are granted immediately without waiting."""
    qm = QueueManager(max_active=5, max_queue=10, estimated_seconds=30)
    
    events = []
    async for event in qm.acquire_slot("req-1"):
        events.append(event)
        if event["status"] == "PROCESSING":
            break
            
    assert len(events) == 1
    assert events[0]["status"] == "PROCESSING"
    assert events[0]["position"] == 0
    assert qm.active_count == 1
    assert qm.queued_count == 0
    
    await qm.release_slot("req-1")
    assert qm.active_count == 0


@pytest.mark.asyncio
async def test_queue_manager_fifo_ordering():
    """Requests exceeding max_active are queued in FIFO order and advanced as slots free up."""
    qm = QueueManager(max_active=2, max_queue=5, estimated_seconds=20)
    
    # Fill the 2 active slots
    slot1_events = []
    slot2_events = []
    async for e in qm.acquire_slot("active-1"):
        slot1_events.append(e)
        break
    async for e in qm.acquire_slot("active-2"):
        slot2_events.append(e)
        break
        
    assert qm.active_count == 2
    assert qm.queued_count == 0
    
    # 3rd request should be queued at position 1
    queued_events_req3 = []
    queued_events_req4 = []
    
    async def run_waiter_3():
        async for e in qm.acquire_slot("waiting-3"):
            queued_events_req3.append(e)
            if e["status"] == "PROCESSING":
                break
                
    async def run_waiter_4():
        async for e in qm.acquire_slot("waiting-4"):
            queued_events_req4.append(e)
            if e["status"] == "PROCESSING":
                break

    task3 = asyncio.create_task(run_waiter_3())
    task4 = asyncio.create_task(run_waiter_4())
    
    # Give tasks a moment to register in the queue
    await asyncio.sleep(0.05)
    
    assert qm.queued_count == 2
    assert queued_events_req3[0]["status"] == "QUEUED"
    assert queued_events_req3[0]["position"] == 1
    assert queued_events_req3[0]["estimated_wait_seconds"] == 20
    
    assert queued_events_req4[0]["status"] == "QUEUED"
    assert queued_events_req4[0]["position"] == 2
    assert queued_events_req4[0]["estimated_wait_seconds"] == 40
    
    # Release active-1 -> waiting-3 should be promoted to PROCESSING
    await qm.release_slot("active-1")
    await asyncio.sleep(0.05)
    
    assert queued_events_req3[-1]["status"] == "PROCESSING"
    assert queued_events_req3[-1]["position"] == 0
    
    # waiting-4 should have received an update advancing to position 1
    assert queued_events_req4[-1]["status"] == "QUEUED"
    assert queued_events_req4[-1]["position"] == 1
    assert queued_events_req4[-1]["estimated_wait_seconds"] == 20
    
    # Release active-2 -> waiting-4 should be promoted to PROCESSING
    await qm.release_slot("active-2")
    await asyncio.sleep(0.05)
    
    assert queued_events_req4[-1]["status"] == "PROCESSING"
    
    await task3
    await task4
    
    # Clean up remaining
    await qm.release_slot("waiting-3")
    await qm.release_slot("waiting-4")
    assert qm.active_count == 0
    assert qm.queued_count == 0


@pytest.mark.asyncio
async def test_queue_manager_queue_full():
    """Requests exceeding max_queue buffer are rejected with QUEUE_FULL."""
    qm = QueueManager(max_active=1, max_queue=1, estimated_seconds=10)
    
    # 1 active
    async for _ in qm.acquire_slot("active-1"):
        break
        
    # 1 queued
    queued_events = []
    async def run_waiter():
        async for e in qm.acquire_slot("waiting-1"):
            queued_events.append(e)
            if e["status"] == "PROCESSING":
                break
    t = asyncio.create_task(run_waiter())
    await asyncio.sleep(0.05)
    
    # 3rd request -> queue is full (max_queue=1 reached)
    rejected_events = []
    async for e in qm.acquire_slot("overflow-1"):
        rejected_events.append(e)
        
    assert len(rejected_events) == 1
    assert rejected_events[0]["status"] == "QUEUE_FULL"
    assert rejected_events[0]["position"] == -1
    
    # Cleanup
    await qm.release_slot("active-1")
    await t
    await qm.release_slot("waiting-1")
    assert qm.active_count == 0


@pytest.mark.asyncio
async def test_queue_manager_abandoned_waiter_cleanup():
    """If a client disconnects while waiting in queue, release_slot cleans them up cleanly."""
    qm = QueueManager(max_active=1, max_queue=5, estimated_seconds=15)
    
    # 1 active
    async for _ in qm.acquire_slot("active-1"):
        break
        
    # User 2 queues
    async def run_abandoned():
        try:
            async for _ in qm.acquire_slot("abandoned-2"):
                pass
        except asyncio.CancelledError:
            await qm.release_slot("abandoned-2")
            raise

    task = asyncio.create_task(run_abandoned())
    await asyncio.sleep(0.05)
    assert qm.queued_count == 1
    
    # User 3 queues behind User 2
    user3_events = []
    async def run_user3():
        async for e in qm.acquire_slot("user-3"):
            user3_events.append(e)
            if e["status"] == "PROCESSING":
                break
                
    task3 = asyncio.create_task(run_user3())
    await asyncio.sleep(0.05)
    assert qm.queued_count == 2
    assert user3_events[0]["position"] == 2
    
    # Simulate User 2 disconnecting (cancel task)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
        
    await asyncio.sleep(0.05)
    assert qm.queued_count == 1
    # User 3 should now be at position 1
    assert user3_events[-1]["position"] == 1
    
    # Release active slot -> User 3 is promoted
    await qm.release_slot("active-1")
    await asyncio.sleep(0.05)
    assert user3_events[-1]["status"] == "PROCESSING"
    
    await task3
    await qm.release_slot("user-3")
    assert qm.active_count == 0
    assert qm.queued_count == 0


@pytest.mark.asyncio
async def test_queue_manager_high_concurrency_stress():
    """Simulates 25 concurrent callers with random hold times, verifying active_slots never exceeds max_active."""
    max_slots = 5
    qm = QueueManager(max_active=max_slots, max_queue=50, estimated_seconds=10)
    
    max_observed_active = 0
    completed_count = 0
    
    async def worker(idx: int):
        nonlocal max_observed_active, completed_count
        req_id = f"worker-{idx}"
        
        async for event in qm.acquire_slot(req_id):
            if event["status"] == "PROCESSING":
                break
                
        # Critical section: slot acquired
        current_active = qm.active_count
        if current_active > max_observed_active:
            max_observed_active = current_active
            
        assert current_active <= max_slots, f"Violation: active count {current_active} > max {max_slots}"
        
        # Simulate processing time
        await asyncio.sleep(0.05)
        
        completed_count += 1
        await qm.release_slot(req_id)
        
    tasks = [asyncio.create_task(worker(i)) for i in range(25)]
    await asyncio.gather(*tasks)
    
    assert completed_count == 25
    assert max_observed_active <= max_slots
    assert qm.active_count == 0
    assert qm.queued_count == 0
