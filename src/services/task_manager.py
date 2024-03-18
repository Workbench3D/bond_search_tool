import sched
import time
import logging
from datetime import datetime, timedelta


def task_schedule(hour=0, minute=0):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    log = logging.getLogger(__name__)
    log.info("Запуск планировщика задач")

    def decorator(func):
        scheduler = sched.scheduler(time.time, time.sleep)

        def wrapper():
            now = datetime.now()
            next_day = now + timedelta(days=1)
            date = datetime(next_day.year, next_day.month, next_day.day, hour, minute)
            backup_time = date.timestamp()

            scheduler.enterabs(time=backup_time, priority=1, action=wrapper)
            if now.weekday() < 5:
                log.info("Запуск задачи")
                func()
            next_date_task = datetime.fromtimestamp(scheduler.queue[0].time)
            log.info(f"Следующая задача запланирована на {next_date_task}")
            scheduler.run()

        return wrapper

    return decorator
