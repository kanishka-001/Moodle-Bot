import os
import json
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from openai import OpenAI

from moodle_bot.config import OPENROUTER_API_KEY
from moodle_bot.models import UserSession


def get_active_token() -> str:
    """Retrieve the active Moodle user token safely from the database."""
    try:
        user = UserSession.get_or_none(UserSession.id == 1)
        return user.token if user and user.token else ""
    except Exception:
        return ""


def get_ai_client() -> OpenAI:
    """Initialize OpenRouter OpenAI client using configuration or environment variables."""
    api_key = OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY", "")
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


def file_url(fileurl: str) -> dict:
    """Convert a Moodle fileurl into a browser-viewable URL using the active token."""
    token = get_active_token()
    parts = urlparse(fileurl)
    query = dict(parse_qsl(parts.query))

    query["forcedownload"] = "0"
    if token:
        query["token"] = token

    view_url = urlunparse(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            parts.params,
            urlencode(query),
            parts.fragment,
        )
    )

    return {"view_url": view_url}


tools = [
    {
        "type": "function",
        "function": {
            "name": "file_url",
            "description": (
                "Convert a Moodle fileurl from a Moodle JSON response into a "
                "browser-viewable URL. Use this when the user wants to open or "
                "view a Moodle file such as a PDF."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "fileurl": {
                        "type": "string",
                        "description": (
                            "The Moodle file URL from the `fileurl` field in the "
                            "Moodle JSON response."
                        ),
                    }
                },
                "required": ["fileurl"],
                "additionalProperties": False,
            },
        },
    }
]

available_functions = {
    "file_url": file_url,
}


def generate_notification(delta_or_prev, course_name: str, current_json=None) -> str:
    """
    Takes detected course changes and uses AI to write a clean, student-friendly WhatsApp digest.
    """
    print(f"-- AI notification generation starting for course: {course_name} --")
    client = get_ai_client()

    if current_json is not None:
        user_content = f"Course - {course_name} PREVIOUS_JSON: {json.dumps(delta_or_prev)}\nCURRENT_JSON: {json.dumps(current_json)}"
    else:
        user_content = (
            f"Course - {course_name} :DELTA_SUMMARY: {json.dumps(delta_or_prev, indent=2)}"
        )

    messages = [
        {
            "role": "system",
            "content": """You are a friendly, helpful Moodle Student Assistant Bot that sends WhatsApp/Telegram notifications to university students.

Your task is to take detected course changes and write a clean, well-spaced, and easy-to-read student digest.

## CRITICAL FORMATTING RULES

1. GROUP BY COURSE (NEVER REPEAT):
   - Mention the Course Name ONLY ONCE at the top.
   - Never repeat the course name for each item. All updates belonging to the same course must sit under that single header.

2. NEVER PRINT EMPTY FIELDS:
   - If an item does not have a URL/link, DO NOT write "Link:" or leave a blank line for it. Completely omit it!
   - If an item does not have a deadline, DO NOT write "Deadline:".

3. NO ROBOTIC LABELS:
   - Do NOT use raw database prefixes like "Section:", "Message:", "Title:".
   - Write like a human student rep posting an update in a class group chat.

4. SPACING & READABILITY:
   - Use double line breaks between items so it does not look cramped.
   - Use WhatsApp bold formatting: *text*
   - Use clean, intuitive emojis:
     • 📢 for Announcements & Notices
     • ⏰ for Deadlines & Submissions
     • 📁 for Study Materials & PDFs
     • 🔗 for Links (only when a valid URL exists and remember to call tools to generate downloadable link using tool file_url)

5. NO SYSTEM NOISE:
   - If duplicate or identical items appear (e.g. "Tutorial Postponement" and "Tutorial Postponement (copy)"), merge them into a single clean note.
   - Do NOT output JSON, code blocks, or system IDs.
   - If there are no updates, respond only with: No new Moodle updates.

---

## OUTPUT TEMPLATE & STRUCTURE

📚 *[Course Code & Course Name]*

Hey everyone! Here are the latest Moodle updates:

📢 *Notices & Announcements*
• *[Title of Notice]* ([Section, if helpful])
  [1-2 friendly sentences explaining the change]

⏰ *Assignments & Deadlines*
• *[Assignment Name]*
  ⏳ *Due Date:* [Date & Time]
  [Brief description or instructions]
  🔗 [URL]

📁 *New Study Materials*
• *[Material / Topic Name]* ([Section])
  [Brief 1-sentence note]
  🔗 [URL]

(Note: Only include categories that actually have updates. Leave plenty of breathing room between items.)
""",
        },
        {
            "role": "user",
            "content": f"Here are the detected course changes:\n\n{user_content}",
        },
    ]

    model_name = os.getenv("AI_MODEL_NAME", "nvidia/nemotron-3-super-120b-a12b:free")

    while True:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=tools,
        )
        msg = response.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            return msg.content or ""

        for tool_call in msg.tool_calls:
            fn_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            if fn_name in available_functions:
                result = available_functions[fn_name](**args)
            else:
                result = {"error": f"Function {fn_name} not found"}

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
            )


# Backward-compatible alias
ai = generate_notification
