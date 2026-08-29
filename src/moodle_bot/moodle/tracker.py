import json
from moodle_bot.config import CACHE_DIR
from moodle_bot.models import UserSession, EnrolledCourse
from moodle_bot.moodle.courses import course_content, normalize_course
from moodle_bot.moodle.services.save_data import save_contents
from moodle_bot.ai.summarizer import generate_notification
from moodle_bot.chat.sender import send_message


def extract_course_delta(old_norm: dict, new_norm: dict) -> dict:
    """
    Compares two normalized course dictionaries by module ID.
    Returns added, updated, and removed items.
    """
    added = []
    updated = []
    removed = []

    for mod_id, new_item in new_norm.items():
        if mod_id not in old_norm:
            added.append(new_item)
        else:
            old_item = old_norm[mod_id]
            if old_item != new_item:
                updated.append({"before": old_item, "after": new_item})

    for mod_id, old_item in old_norm.items():
        if mod_id not in new_norm:
            removed.append(old_item)

    return {"added": added, "updated": updated, "removed": removed}


def check_course_changes(client=None) -> None:
    """
    Checks all enrolled courses for content changes, generates AI summaries
    for any detected deltas, and dispatches WhatsApp notifications.
    """
    print("------ Course change check started ------")
    new_cont = course_content()
    if not new_cont:
        print("No courses available to check.")
        return

    for course_id, value in new_cont.items():
        # value is [raw_data, normalized_data, stable_hash]
        raw_data, new_norm, new_hash = value

        course_record = EnrolledCourse.get_or_none(
            EnrolledCourse.course_id == course_id
        )
        old_hash = course_record.hash_ if course_record else None

        cache_file = CACHE_DIR / f"{course_id}.json"

        if old_hash != new_hash:
            old_norm = {}
            if cache_file.exists():
                try:
                    with open(cache_file, "r", encoding="utf-8") as file:
                        cached_raw = json.load(file)
                        old_norm = normalize_course(cached_raw)
                except Exception as e:
                    print(f"Error reading cache for course {course_id}: {e}")
            elif old_hash is None:
                # First time tracking this course without existing cache: establish baseline
                print(
                    f"Course {course_id} ({course_record.shortname if course_record else course_id}): "
                    f"Initial baseline saved ({len(new_norm)} modules)."
                )
                save_contents(course_id, raw_data)
                EnrolledCourse.update(hash_=new_hash).where(
                    EnrolledCourse.course_id == course_id
                ).execute()
                continue

            delta = extract_course_delta(old_norm, new_norm)

            if delta["added"] or delta["updated"] or delta["removed"]:
                course_title = (
                    course_record.fullname if course_record else f"Course {course_id}"
                )
                print(
                    f"Course {course_id} changed! Delta: {len(delta['added'])} added, "
                    f"{len(delta['updated'])} updated, {len(delta['removed'])} removed."
                )
                msg = generate_notification(delta, course_name=course_title)
                if client:
                    session = UserSession.get_or_none(UserSession.id == 1)
                    target_phone = (
                        getattr(session, "phone_number", None) if session else None
                    )
                    send_message(client=client, message=msg, phone_number=target_phone)
                else:
                    print(f"Generated notification:\n{msg}")
            else:
                print(f"No meaningful student-facing changes in course {course_id}.")

            save_contents(course_id, raw_data)
            EnrolledCourse.update(hash_=new_hash).where(
                EnrolledCourse.course_id == course_id
            ).execute()
        else:
            print(f"Course {course_id}: No hash change.")

    print(f"------ Course change check finished ({len(new_cont)} courses checked) ------")


if __name__ == "__main__":
    check_course_changes()
