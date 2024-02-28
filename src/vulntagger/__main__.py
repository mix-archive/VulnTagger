import logging
import secrets
from os import environ

import dotenv
from nicegui import ui
from rich.logging import RichHandler

from . import pages as pages

logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)

logger = logging.getLogger(__name__)

dotenv.load_dotenv()


def main():
    from nicegui import ui_run

    ui_run.APP_IMPORT_STRING = "vulntagger:app"

    ui.run(
        host=environ.get("HOST"),
        port=int(environ.get("PORT", 8080)),
        title="VulnTagger",
        storage_secret=secrets.token_urlsafe(16),
        show=False,
        access_log=True,
    )


if __name__ == "__main__":
    main()
