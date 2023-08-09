import uvicorn
from beebot.initiator.api import create_app


if __name__ == "__main__":
    uvicorn.run(create_app())
