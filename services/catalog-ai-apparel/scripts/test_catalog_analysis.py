# ================================================================================================
# scripts/test_catalog_analysis.py
# ================================================================================================
#!/usr/bin/env python3
"""
Manual test script for catalog analysis service.
Publishes a test catalog item analysis request event to NATS.
"""
import asyncio
import json
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from src.events.types import CatalogAnalysisEvents

async def publish_test_event():
    """Publish a test catalog item analysis request"""
    nc = NATS()
    
    try:
        # Connect to NATS
        await nc.connect("nats://localhost:4222")
        js = nc.jetstream()
        
        # Create test event
        event = {
            "event_type": CatalogAnalysisEvents.ITEM_ANALYSIS_REQUESTED,
            "payload": {
                "shop_id": "70931710194",
                "product_id": "8526062977266", 
                "variant_id": "46547096469746"
            },
            "correlation_id": "test-catalog-analysis-123",
            "timestamp": "2024-01-01T12:00:00Z",
            "service": "test-script",
            "version": "1.0.0"
        }
        
        # Publish event
        subject = CatalogAnalysisEvents.ITEM_ANALYSIS_REQUESTED
        await js.publish(subject, json.dumps(event).encode())
        
        print(f"✅ Published test catalog analysis event to {subject}")
        print(f"   Shop: {event['payload']['shop_id']}")
        print(f"   Product: {event['payload']['product_id']}")
        print(f"   Variant: {event['payload']['variant_id']}")
        print(f"   Correlation ID: {event['correlation_id']}")
        
    except Exception as e:
        print(f"❌ Failed to publish test event: {e}")
    finally:
        await nc.close()

async def listen_for_results():
    """Listen for catalog analysis result events"""
    nc = NATS()
    
    try:
        await nc.connect("nats://localhost:4222")
        js = nc.jetstream()
        
        # Subscribe to completion events
        async def completion_handler(msg):
            data = json.loads(msg.data.decode())
            print(f"✅ Catalog analysis completed:")
            print(f"   Status: {data['payload']['status']}")
            print(f"   Colors: {len(data['payload'].get('colours', []))} found")
            print(f"   Latency: {data['payload']['latency_ms']}ms")
            await msg.ack()
        
        # Subscribe to failure events  
        async def failure_handler(msg):
            data = json.loads(msg.data.decode())
            print(f"❌ Catalog analysis failed:")
            print(f"   Error: {data['payload']['error']}")
            await msg.ack()
        
        # Create subscriptions
        await js.subscribe(
            CatalogAnalysisEvents.ITEM_ANALYSIS_COMPLETED,
            cb=completion_handler,
            durable="test-completion-listener"
        )
        
        await js.subscribe(
            CatalogAnalysisEvents.ITEM_ANALYSIS_FAILED,
            cb=failure_handler,
            durable="test-failure-listener"
        )
        
        print("🔄 Listening for catalog analysis results... (Ctrl+C to stop)")
        
        # Keep listening
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n👋 Stopping listener...")
    except Exception as e:
        print(f"❌ Failed to listen for results: {e}")
    finally:
        await nc.close()

async def main():
    """Main test function"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_catalog_analysis.py [publish|listen]")
        return
    
    command = sys.argv[1]
    
    if command == "publish":
        await publish_test_event()
    elif command == "listen":
        await listen_for_results()
    else:
        print("Invalid command. Use 'publish' or 'listen'")

if __name__ == "__main__":
    asyncio.run(main())
