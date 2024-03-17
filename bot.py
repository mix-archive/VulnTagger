import hashlib
import subprocess
import time
from logging import getLogger
from secrets import token_urlsafe

from httpx import Client
from rich.logging import RichHandler

logger = getLogger(__name__)
logger.addHandler(RichHandler())
logger.setLevel("DEBUG")

client = Client(base_url="http://localhost:8080")


def validate(difficulty: int = 4, token: str | None = None):
    resp = client.post(
        "/",
        headers={
            "x-pow-token": (token := token or token_urlsafe()),
            "x-pow-difficulty": str(difficulty),
        },
    )

    # abnormal status code indicates server error
    if resp.status_code >= 500:
        resp.raise_for_status()

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
        time.sleep(10)
        if validate(difficulty):  # noqa: SIM102
            if all(validate(difficulty) for _ in range(difficulty)):
                break
        logger.info("Failed to validate with difficulty %d", difficulty)

    logger.info("Successfully validated with difficulty %d", difficulty)

    flag = subprocess.check_output(["/readflag"], text=True).strip()
    result = validate(difficulty, flag)
    logger.info("Flag validation result: %s", result)

    logger.warning("Flag has been submitted, the container will be restarted shortly.")
    time.sleep(5)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("An error occurred: %s", e)
    finally:
        subprocess.run(["/restart"], check=False)
