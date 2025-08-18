# services/catalog-analysis/src/main.py
import asyncio
import signal

from .config import config
from .lifecycle import ServiceLifecycle

lifecycle = ServiceLifecycle(config)


async def main():
    """Main application entry point"""
    shutdown_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    # Signal handlers just trigger the event (no background task -> no RUF006)
    def _on_signal() -> None:
        loop.call_soon_threadsafe(shutdown_event.set)

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _on_signal)

    try:
        await lifecycle.startup()
        # Keep running until a signal arrives
        await shutdown_event.wait()
    except Exception as e:
        lifecycle.logger.error(f"Fatal error: {e}", exc_info=True)
        raise
    finally:
        # Always shutdown gracefully
        await lifecycle.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
