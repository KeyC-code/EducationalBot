from datetime import datetime, timedelta, timezone

from dateutil import relativedelta

import config
from db import Database

db = Database("database.db")


async def new_day(db):
    for item in db.get_users():
        id = item[0]
        sub = item[6]
        if sub:
            year, month, day = sub.split(",")
            if datetime.now(timezone.utc) + timedelta(hours=config.UTC_STEP) > datetime(
                year=int(year), month=int(month), day=int(day), tzinfo=timezone.utc
            ):
                db.set_subed(0, id)
            if datetime.now(timezone.utc) + timedelta(hours=config.UTC_STEP) - datetime(
                year=int(year), month=int(month), day=int(day), tzinfo=timezone.utc
            ) == relativedelta.relativedelta(months=1):
                date = (
                    datetime.now(timezone.utc)
                    + timedelta(hours=config.UTC_STEP)
                    + relativedelta.relativedelta(days=3)
                )
                db.set_sub(f"{date.year},{date.month},{date.day}", id)
