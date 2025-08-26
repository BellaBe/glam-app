# services/selfie-service/src/tasks.py
import asyncio
from datetime import UTC, datetime, timedelta

from shared.utils.logger import ServiceLogger


async def cleanup_stale_analyses(lifecycle, logger: ServiceLogger):
    """Mark stale PROCESSING analyses as FAILED"""
    while True:
        try:
            # Get stale analyses (>45s in PROCESSING)
            cutoff = datetime.now(UTC) - timedelta(seconds=lifecycle.config.sweeper_interval_seconds)

            count = await lifecycle.analysis_repo.mark_stale_as_failed(cutoff)

            if count > 0:
                logger.info(f"Marked {count} stale analyses as FAILED")

        except Exception as e:
            logger.error(f"Cleanup sweeper error: {e}")

        # Sleep before next sweep
        await asyncio.sleep(lifecycle.config.sweeper_interval_seconds)


async def start_cleanup_sweeper(lifecycle, logger: ServiceLogger):
    """Start background cleanup task"""
    return asyncio.create_task(cleanup_stale_analyses(lifecycle, logger), name="cleanup-sweeper")
