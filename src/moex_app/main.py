import os
import sys
dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir_path = os.path.abspath(os.path.join(dir_path, os.pardir))
sys.path.insert(0, parent_dir_path)

from repositories.bond import MoexORM
from services.moex import ContextStrategy
import asyncio


async def main():
    context = ContextStrategy()
    update_data = MoexORM.update_data
    await context.execute_strategy(update_data=update_data)


if __name__ == '__main__':
    asyncio.run(main())
    # MoexORM.create_tables()
