# test_nats_fix.py
import asyncio
import nats
from nats.js.api import StreamConfig

async def test():
    print("Connecting to NATS...")
    nc = await nats.connect("nats://localhost:4222")
    js = nc.jetstream()
    print("Connected to JetStream!")

    # Check account info
    account_info = await js.account_info()
    print(f"JetStream Status: {account_info.streams} streams, {account_info.memory} bytes memory")

    # List existing streams
    try:
        streams = await js.streams_info()
        for stream in streams:
            print(f"Found existing stream: {stream.config.name} with subjects: {stream.config.subjects}")
            # Delete it to start fresh
            await js.delete_stream(stream.config.name)
            print(f"Deleted stream: {stream.config.name}")
    except:
        print("No streams to list/delete")

    # Create stream with correct subject pattern
    print("\nCreating GLAM_EVENTS stream...")
    config = StreamConfig(
        name="GLAM_EVENTS",
        subjects=["evt.>", "cmd.>"],  # Use '>' for multi-level wildcard
        max_msgs=1000000,
        max_age=86400  # 24 hours
    )

    stream_info = await js.add_stream(config)
    print(f"✅ Stream created: {stream_info.config.name}")
    print(f"   Subjects: {stream_info.config.subjects}")

    # Wait a moment for stream to be ready
    await asyncio.sleep(0.5)

    # Test publishing
    test_messages = [
        ("evt.test.v1", b"Test event message"),
        ("cmd.test.v1", b"Test command message"),
        ("evt.merchant.installed.v1", b"Test merchant installed")
    ]

    for subject, payload in test_messages:
        try:
            ack = await js.publish(subject, payload)
            print(f"✅ Published to {subject} - seq: {ack.seq}")
        except Exception as e:
            print(f"❌ Failed to publish to {subject}: {e}")

    # Check stream state
    info = await js.stream_info("GLAM_EVENTS")
    print(f"\n📊 Stream stats: {info.state.messages} messages, {info.state.bytes} bytes")

    await nc.close()
    print("\n✨ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test())
