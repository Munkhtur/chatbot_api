import os           
from dotenv import load_dotenv
load_dotenv(override=True)
from fastapi import FastAPI
from helpers import cors, log,rate_limiter
from routes import router
from helpers.scheduler import setup as scheduler_setup

log.setup()
app = FastAPI()
rate_limiter.setup(app)
cors.setup(app)
router.setup(app)
scheduler_setup(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)