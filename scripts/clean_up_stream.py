# cleanup_stream.py
import asyncio
import nats

async def cleanup():
    nc = await nats.connect("nats://localhost:4222")
    js = nc.jetstream()

    try:
        # Delete old stream
        await js.delete_stream("GLAM_EVENTS")
        print("Deleted old stream")
    except:
        pass

    # Create with correct subjects
    await js.add_stream(
        name="GLAM_EVENTS",
        subjects=["evt.>", "cmd.>"]
    )
    print("Created stream with correct subjects")

    info = await js.stream_info("GLAM_EVENTS")
    print(f"Stream ready with subjects: {info.config.subjects}")

    await nc.close()

asyncio.run(cleanup())
