from repositories.bond import MoexORM
from services.moex import ContextStrategy
from services.task_manager import task_schedule
import asyncio


# Найминг функции
async def update_task():
    context = ContextStrategy()
    update_data = MoexORM.update_data
    await context.execute_strategy(update_data=update_data)


@task_schedule(hour=9, minute=4)
def main():
    asyncio.run(update_task())


if __name__ == '__main__':
    main()
