from datetime import datetime, timedelta
import typing as tp
from fastapi import FastAPI
from src.database import Database, ProgrammerState, WorkingCounter
from src.middleware import HeaderSecretChecker

app = FastAPI()
app.add_middleware(HeaderSecretChecker)


@app.get("/health")
async def health() -> dict[str, bool]:
    return {"Status": True}


@app.get("/start")
async def start() -> None:
    match WorkingCounter.state:
        case ProgrammerState.AWAIT:
            WorkingCounter.start()
        case ProgrammerState.WORK:
            if (datetime.now() - WorkingCounter.started_at) > timedelta(hours=14):
                # probably fell asleep, add 2 hours and call it a day
                WorkingCounter.started_at += timedelta(hours=2)
                ended_at = WorkingCounter.started_at
                minutes = WorkingCounter.end()
                Database.query(
                    f"INSERT INTO performance(timestamp, minutes) VALUES ({ended_at.isoformat(sep=' ')}, {minutes})"
                )


@app.get("/end")
async def end() -> None:
    match WorkingCounter.state:
        case ProgrammerState.AWAIT:
            pass
        case ProgrammerState.WORK:
            minutes = WorkingCounter.end()
            Database.query(f"INSERT INTO performance(minutes) VALUES ({minutes})")


@app.get("/query")
def query(sql: str) -> dict[str, bool | str | list[tp.Any]]:
    try:
        return {"ok": True, "rows": Database.query(sql=sql)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/working")
async def working():
    if WorkingCounter.state == ProgrammerState.WORK:
        return True
    return False
