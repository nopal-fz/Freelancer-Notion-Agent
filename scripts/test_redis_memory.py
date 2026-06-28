import asyncio

from app.memory.redis_memory import RedisMemory

async def main() -> None:
    memory = RedisMemory()

    is_alive = await memory.ping()
    print("Redis alive:", is_alive)

    await memory.save_chat_id(123456789)

    await memory.save_recent_message(
        chat_id=123456789,
        user_id=123456789,
        text="halo dari redis test",
    )

    chat_ids = await memory.get_chat_ids()
    messages = await memory.get_recent_messages(123456789)

    print("Chat IDs:", chat_ids)
    print("Recent messages:", messages)

    await memory.close()


if __name__ == "__main__":
    asyncio.run(main())