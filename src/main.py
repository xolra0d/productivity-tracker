from datetime import datetime, timedelta

from fastapi import FastAPI

from database import Database, ProgrammerState, WorkingCounter
from middleware import HeaderSecretChecker

app = FastAPI()
app.add_middleware(HeaderSecretChecker)


@app.get("/health")
async def health():
    return True


@app.get("/start")
async def start():
    match WorkingCounter.state:
        case ProgrammerState.AWAIT:
            WorkingCounter.start()
        case ProgrammerState.WORK:
            if (datetime.now() - WorkingCounter.started_at) > timedelta(hours=14):
                # probably fell asleep, add 2 hours and call it a day
                WorkingCounter.started_at += timedelta(hours=2)
                ended_at = WorkingCounter.started_at
                minutes = WorkingCounter.end()
                Database.query(f"INSERT INTO performance(timestamp, minutes) VALUES ({ended_at.isoformat(sep=' ')}, {minutes})")


@app.get("/end")
async def end():
    match WorkingCounter.state:
        case ProgrammerState.AWAIT:
            pass
        case ProgrammerState.WORK:
            minutes = WorkingCounter.end()
            Database.query(f"INSERT INTO performance(minutes) VALUES ({minutes})")


@app.post("/query")
def query(sql: str):
    result = Database.query(sql=sql)
    if isinstance(result, str):
        return {"ok": False, "error": result}
    return {"ok": True, "rows": result}

@app.post("/working")
async def working():
    if WorkingCounter.state == ProgrammerState.WORK:
        return True
    return False
