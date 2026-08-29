import requests
import os, json
from peewee import *
from moodle_bot.models import UserSession, db, EnrolledCourse
import asyncio
import httpx


# from .save_data import save_contents
async def get_token(username: str, password: str, base: str):
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{base}/login/token.php",
            data={
                "username": username,
                "password": password,
                "service": "moodle_mobile_app",
            },
        )
        data = r.json()
        if not data.get("token"):
            return data.get("error")
        return data.get("token")


def login():
    while True:
        username = input("Enter Username (Mc number) : ")
        if username.isdigit() and len(username) == 6:
            password = input("Enter your moodle Password : ")
            api_key = input("Enter your api key in openrouter : ")
            break
        else:
            print("Plz check the username")
    return get_token(username, password), password, api_key


def save_infor(data: str, token: str, base: str):
    UserSession.update(
        userid=data["userid"],
        username=data["username"],
        fullname=data["fullname"],
        lastname=data["lastname"],
        sitename=data["sitename"],
        lang=data["lang"],
        token=token,
        base_url=base,
    ).where(UserSession.id == 1).execute()


def userinfo(base, token):
    url = f"{base}/webservice/rest/server.php"
    # token,pasword,api_key = login()
    params = {
        "wstoken": token,
        "wsfunction": "core_webservice_get_site_info",
        "moodlewsrestformat": "json",
    }
    r = requests.get(url, params=params)
    data = r.json()
    print(data)
    save_infor(data, token, base)


# userinfo()
# print(get_token('125545','27346'))
