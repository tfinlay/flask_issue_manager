import os

class Config:
    SQLITE_DATABASE_PATH = "database.sqlite"

    # This could be kept constant in production so sessions can remain across server reboots.
    SECRET_KEY = os.urandom(16)


class Constants:
    TICKET_SUMMARY_MAX_LENGTH = 127
    TICKET_DESC_MAX_LENGTH = 65535
    USERNAME_MAX_LENGTH = 89