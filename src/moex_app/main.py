from repositories.bond import MoexORM
from services.moex import ContextStrategy
import asyncio


async def main():
    context = ContextStrategy()
    update_data = MoexORM.update_data
    await context.execute_strategy(update_data=update_data)


if __name__ == '__main__':
    asyncio.run(main())
