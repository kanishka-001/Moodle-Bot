import json
import hashlib
import asyncio
import requests

from moodle_bot.models import UserSession, EnrolledCourse
from moodle_bot.moodle.services.login import get_token


def hash_fnc(data):
    """SHA256 hash of response text."""
    return hashlib.sha256(data.text.encode("utf-8")).hexdigest()


def compute_stable_hash(normalized_data: dict) -> str:
    """Generates a stable SHA256 hash from normalized course content."""
    encoded = json.dumps(normalized_data, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def normalize_course(data) -> dict:
    """
    Extracts student-relevant content and ignores volatile fields like modicon, token, contextid.
    Returns a clean dictionary keyed by module/resource ID.
    """
    normalized = {}

    # Handle root list wrapping
    sections = (
        data[0]
        if isinstance(data, list) and len(data) == 1 and isinstance(data[0], list)
        else data
    )

    if not isinstance(sections, list):
        return normalized

    for sec in sections:
        sec_id = sec.get("id")
        sec_name = sec.get("name", f"Section {sec.get('section')}")

        for mod in sec.get("modules", []):
            mod_id = mod.get("id")

            # Extract content/file metadata
            contents = []
            for item in mod.get("contents", []):
                contents.append(
                    {
                        "filename": item.get("filename"),
                        "filesize": item.get("filesize"),
                        "timemodified": item.get("timemodified"),
                        "fileurl": item.get("fileurl", "").split("?")[
                            0
                        ],  # Strip dynamic tokens
                    }
                )

            normalized[mod_id] = {
                "section_id": sec_id,
                "section_name": sec_name,
                "modname": mod.get(
                    "modname"
                ),  # assign, resource, forum, quiz, page, etc.
                "name": mod.get("name"),
                "description": mod.get("description", ""),
                "visible": mod.get("visible", 1),
                "dates": mod.get("dates", []),  # Due dates / open dates
                "contents": contents,
            }

    return normalized


def fetch_enrolled_courses(user=None) -> list:
    """
    Fetches the user's enrolled courses from Moodle (core_enrol_get_users_courses)
    and saves or updates them in the EnrolledCourse table.
    """
    if not user:
        user = UserSession.get_or_none(UserSession.id == 1)
    if (
        not user
        or not getattr(user, "base_url", None)
        or not getattr(user, "userid", None)
    ):
        print("Moodle setup incomplete: cannot fetch enrolled courses.")
        return []

    base = user.base_url.rstrip("/")
    url = f"{base}/webservice/rest/server.php"
    token = (
        user.token
        if hasattr(user, "token") and user.token
        else asyncio.run(get_token(user.username, getattr(user, "password", ""), base))
    )

    params = {
        "wstoken": token,
        "wsfunction": "core_enrol_get_users_courses",
        "moodlewsrestformat": "json",
        "userid": str(user.userid),
    }

    try:
        r = requests.get(url, params=params, timeout=30)
        data = r.json()
        if not isinstance(data, list):
            print(f"Failed to fetch courses from Moodle API: {data}")
            return []

        synced = []
        for c in data:
            cid = c.get("id")
            sname = c.get("shortname", f"Course {cid}")
            fname = c.get("fullname", f"Course {cid}")
            if not cid:
                continue
            course_rec, created = EnrolledCourse.get_or_create(
                course_id=cid,
                defaults={"shortname": sname, "fullname": fname},
            )
            if not created:
                course_rec.shortname = sname
                course_rec.fullname = fname
                course_rec.save()
            synced.append(course_rec)

        print(
            f"Enrolled courses synced successfully: {len(synced)} courses registered."
        )
        return synced
    except Exception as e:
        print(f"Error fetching enrolled courses from Moodle: {e}")
        return []


def course_content() -> dict:
    print("--getinng content ---")
    """
    Fetches the latest course content from Moodle for all enrolled courses,
    normalizes the contents, and generates stable hashes for change detection.
    """
    print("-- Getting course content from Moodle --")
    content = {}
    user = UserSession.get_or_none(UserSession.id == 1)
    if not user or not getattr(user, "base_url", None):
        raise ValueError(
            "Moodle Base URL is not configured. Please complete setup first."
        )

    base = user.base_url.rstrip("/")
    url = f"{base}/webservice/rest/server.php"
    token = (
        user.token
        if hasattr(user, "token") and user.token
        else asyncio.run(get_token(user.username, getattr(user, "password", ""), base))
    )

    enrolled_courses = list(EnrolledCourse.select())
    if not enrolled_courses:
        print("No enrolled courses found in local DB. Syncing with Moodle...")
        enrolled_courses = fetch_enrolled_courses(user)

    if not enrolled_courses:
        print("No enrolled courses found for this account.")
        return content

    print(f"Checking content for {len(enrolled_courses)} enrolled courses...")
    for course in enrolled_courses:
        params = {
            "wstoken": token,
            "wsfunction": "core_course_get_contents",
            "moodlewsrestformat": "json",
            "courseid": str(course.course_id),
        }
        try:
            r = requests.get(url, params=params, timeout=30)
            data = r.json()
            norm_data = normalize_course(data)
            _hash = compute_stable_hash(norm_data)
            print(
                f"Course {course.course_id} ({course.shortname}) -> Hash: {_hash[:12]}..."
            )
            content[course.course_id] = [data, norm_data, _hash]
        except Exception as e:
            print(f"Error fetching contents for course {course.course_id}: {e}")

    return content
