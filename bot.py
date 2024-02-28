import functools
import hashlib
import time
from ast import TypeVar
from logging import getLogger
from secrets import token_urlsafe
from types import FunctionType

from httpx import Client
from rich.logging import RichHandler

logger = getLogger(__name__)
logger.addHandler(RichHandler())
logger.setLevel("DEBUG")

client = Client(base_url="http://localhost:8080")

_FT = TypeVar("_FT", bound=FunctionType)


def catch_exception(func: _FT) -> _FT:  # type: ignore
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(e)
            return False

    return wrapper


@catch_exception
def validate(difficulty: int = 4, token: str | None = None):
    resp = client.post(
        "/",
        headers={
            "x-pow-token": (token := token or token_urlsafe()),
            "x-pow-difficulty": str(difficulty),
        },
    )
    if resp.status_code != 418:
        logger.debug("Failed to validate with status code %d", resp.status_code)
        return False
    try:
        data: str = resp.json()["bar"]
    except Exception:
        logger.debug("Failed to validate with invalid JSON")
        return False

    return (
        hashlib.sha256(token.encode() + data.encode())
        .hexdigest()
        .startswith("0" * difficulty)
    )


def main():
    difficulty = 4
    while True:
        if validate(difficulty):  # noqa: SIM102
            if all(validate(difficulty) for _ in range(difficulty)):
                break
        logger.info("Failed to validate with difficulty %d", difficulty)
        time.sleep(10)
    logger.info("Successfully validated with difficulty %d", difficulty)

    with open("/flag", encoding="utf-8") as f:
        flag = f.read()

    validate(difficulty, flag)
    logger.info("Flag submitted")


if __name__ == "__main__":
    main()
