================
# services/catalog-analysis/src/main.py
================
import asyncio
import signal
from .config import config
from .lifecycle import ServiceLifecycle

# Create lifecycle manager
lifecycle = ServiceLifecycle(config)

async def main():
    """Main application entry point"""
    try:
        # Setup signal handlers for graceful shutdown
        def signal_handler():
            asyncio.create_task(lifecycle.shutdown())
        
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, signal_handler)
        
        # Start the service
        await lifecycle.startup()
        
        # Keep running
        await asyncio.Event().wait()
        
    except Exception as e:
        lifecycle.logger.error(f"Fatal error: {e}", exc_info=True)
        await lifecycle.shutdown()
        raise

if __name__ == "__main__":
    asyncio.run(main())

    