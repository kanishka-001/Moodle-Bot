import requests
import os, json

base = "https://lms.mgt.sjp.ac.lk"
def login (username:str,password:str):
    r = requests.post(
        f"{base}/login/token.php",
        data={
            "username": username,
            "password": password,
            "service": "moodle_mobile_app",
        },
    )
    return r.json().get('token')
token =login('125545','27346')
url = f"{base}/webservice/rest/server.php"
cid=115
params = {
    "wstoken": token,
    "wsfunction": "core_enrol_get_users_courses",
    "moodlewsrestformat": "json",
    "userid": 10500,  # your Moodle user id
}

r = requests.get(url, params=params)
data = r.json()
text = json.dumps(data, sort_keys=False, ensure_ascii=False)

with open(f"{params['wsfunction']} :results.json", "w", encoding="utf-8") as f:
    f.write(text)

print("Saved to courses.json")