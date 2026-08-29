from peewee import *
from moodle_bot.config import DB_PATH

db = SqliteDatabase(DB_PATH)


class UserSession(Model):
    """Stores the active user session, token, and LMS endpoint."""

    id = IntegerField(primary_key=True)  # Kept as 1 for single-user desktop setup
    userid = IntegerField(null=True)
    username = CharField(null=True)
    fullname = CharField(null=True)
    lastname = CharField(null=True)
    sitename = CharField(null=True)
    lang = CharField(null=True)
    token = CharField(null=True)
    google_id = CharField(null=True)
    base_url = CharField(null=True)
    phone_number = CharField(null=True)

    class Meta:
        database = db


class EnrolledCourse(Model):
    """Tracks enrolled courses, full names, and latest stable content hashes."""

    course_id = IntegerField(primary_key=True)
    shortname = CharField()
    fullname = CharField()
    hash_ = CharField(null=True)

    class Meta:
        database = db


def init_db() -> None:
    """Ensure database tables exist and schema migrations are applied."""
    db.connect(reuse_if_open=True)
    db.create_tables([UserSession, EnrolledCourse], safe=True)
    try:
        cursor = db.execute_sql("PRAGMA table_info(usersession);")
        columns = [row[1] for row in cursor.fetchall()]
        if "phone_number" not in columns:
            db.execute_sql(
                "ALTER TABLE usersession ADD COLUMN phone_number VARCHAR(255) NULL;"
            )
    except Exception as e:
        print(f"Schema migration warning: {e}")


# Initialize tables safely
init_db()
# db.drop_tables([UserSession, EnrolledCourse])
# Bulk update all records to set hash_ to None
# EnrolledCourse.update(hash_=None).execute()
