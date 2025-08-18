# src/main.py
import asyncio

from shared.utils.logger import create_logger

from .config import config
from .lifecycle import ConnectorServiceLifecycle

# Create lifecycle manager
lifecycle = ConnectorServiceLifecycle(config)


async def main():
    """Main application entry point"""
    logger = create_logger("platform-connector-main")

    try:
        logger.info("Starting Platform Connector Service")

        # Start the service
        await lifecycle.startup()

        # Keep the service running
        logger.info("Platform Connector Service is running. Press Ctrl+C to stop.")

        # Wait forever (until interrupted)
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutdown signal received")

    except Exception as e:
        logger.error(f"Service failed: {e}")
    finally:
        # Clean shutdown
        await lifecycle.shutdown()
        logger.info("Platform Connector Service stopped")


if __name__ == "__main__":
    asyncio.run(main())
