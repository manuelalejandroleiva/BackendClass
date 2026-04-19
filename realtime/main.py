import uvicorn
from realtime.server import app
from dotenv import load_dotenv
import os

load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("REALTIME_PORT", "8001"))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False
    )