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
print(token)
file_url = (
    "https://lms.mgt.sjp.ac.lk/webservice/pluginfile.php/"
    "15806/mod_resource/content/2/"
    "ACC1370-Course%20Specification-2026.pdf"
    "?forcedownload=1"
)

# Add the token safely because the URL already has ?forcedownload=1
download_url = f"{file_url}&token={token}"
print(download_url)

response = requests.get(download_url, timeout=60)
response.raise_for_status()


with open("ACC1370-Course-Specification-2026.pdf", "wb") as f:
    f.write(response.content)

print("PDF downloaded successfully.")