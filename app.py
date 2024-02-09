"""MIT License

Copyright (c) 2024 Peter Munk

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE. """

from flask import Flask, Response, request
import requests
import os
import json
import base64
import icalendar
import datetime
import pytz
import uuid
import urllib
import dateutil.relativedelta
import logging

# Define a function that converts a datetime string to UTC format
def to_utc_format(dt_str):
    dt_obj = datetime.datetime.fromisoformat(dt_str)
    dt_utc = dt_obj.astimezone(pytz.utc)
    dt_utc_format = dt_utc.strftime("%Y%m%dT%H%M%SZ")
    return dt_utc_format


def to_url_format(timestamp):
    dt_utc = timestamp.astimezone(pytz.utc)
    dt_utc_format = dt_utc.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    as_str = urllib.parse.quote(dt_utc_format)
    return as_str


def authorize(user: str, password: str, api_key: str) -> str:
    url = "https://de1.cantamen.de/casirest/v3/tokens?expand=customerId"
    headers = {
        "Accept": "application/json",
        "X-API-Key": api_key,
        "Idempotency-Key": str(uuid.uuid4()),
    }
    body = {
        "login": user,
        "credential": password,
        "provId": "79",
        "storeLogin": True
    }
    try:
        response = requests.post(url, headers=headers, json=body, timeout=60)
        logging.debug(url)
        logging.debug(response.status_code)
        logging.debug(response.content)
    except Exception as e:
        logging.error(e)
        return 0
        
    r = json.loads(response.content)
    id_base64 = base64.b64encode((r["id"]+":").encode()).decode()
    return id_base64

def get_bookings(otp: str, api_key: str, months_in_future:int = 6):
    start = datetime.datetime.now()
    end = (start + dateutil.relativedelta.relativedelta(months=months_in_future))
    url = "https://de1.cantamen.de/casirest/v3/bookings?expand=bookeeId&start="+to_url_format(start)+"&end="+to_url_format(end)+"&sort=timeRange.start%2CtimeRange.end%2Cid"
    headers = {
            "Accept": "application/json",
            "X-API-Key": api_key,
            "Idempotency-Key": str(uuid.uuid4()),
            "Content-Type": "application/json",
            "Authorization": f"Basic {otp}"
        }
    try:
        response = requests.get(url, headers=headers, timeout=60)
        logging.debug(url)
        logging.debug(response.status_code)
        logging.debug(response.content)
    except Exception as e:
        logging.error(e)
        return 
    bookings = json.loads(response.content)
    for booking in bookings:
        if booking["cancelled"] != True:
            url = "https://de1.cantamen.de/casirest/v3/bookeeproducts/"+booking["bookeeId"]+"?expand=bookeeTypeId"
            headers = {
                    "Accept": "application/json",
                    "X-API-Key": api_key,
                    "Idempotency-Key": str(uuid.uuid4()),
                    "Content-Type": "application/json",
                    "Authorization": f"Basic {otp}"
                }
            try:
                response = requests.get(url, headers=headers, timeout=60)
                logging.debug(url)
                logging.debug(response.status_code)
                logging.debug(response.content)
            except Exception as e:
                logging.error(e)
                return
            bookee = json.loads(response.content)
            booking.update({"vehicle": bookee["name"]})
            
            url = "https://de1.cantamen.de/casirest/v3/bookees/"+booking["bookeeId"]+"?expand=placeId"
            headers = {
                    "Accept": "application/json",
                    "X-API-Key": api_key,
                    "Idempotency-Key": str(uuid.uuid4()),
                    "Content-Type": "application/json",
                    "Authorization": f"Basic {otp}"
                }
            try:
                response = requests.get(url, headers=headers, timeout=60)
                logging.debug(url)
                logging.debug(response.status_code)
                logging.debug(response.content)
            except Exception as e:
                logging.error(e)
                return
            bookee = json.loads(response.content)
            booking.update({"location": bookee["name"]})    
    return bookings


def generate_calendar(bookings):
    cal = icalendar.Calendar()
    cal.add("prodid", "-//Copilot//icalendar 4.0.3//EN")
    cal.add("version", "2.0")
    for booking in bookings:
        if booking["cancelled"] != True:
            event = icalendar.Event()
            event.add("uid", booking["id"])
            event.add("summary", booking["vehicle"])
            event.add("location", booking["location"])
            event.add("dtstart", icalendar.vDatetime.from_ical(to_utc_format(booking["timeRange"]["start"])))
            event.add("dtend", icalendar.vDatetime.from_ical(to_utc_format(booking["timeRange"]["end"])))
            cal.add_component(event)
    return cal
    

# Create a Flask app
app = Flask(__name__)

@app.route("/cantamen_to_ical")
def cantamen_to_ical():
    # We want a base64 encoded username not just to be safe with URL parameters but also to be safe it is an allowed environment variable name
    user_base64 = request.args.get('user')
    if not user_base64:
        logging.warn("No user parameter provided")
        return Response(status = 401)
    pwd = os.environ.get("CANTAMEN_PWD_"+user_base64, None)
    if not pwd:
        logging.warn("Password for user %s not found in environment variables", user_base64)
        return Response(status = 401)
    user = base64.urlsafe_b64decode(user_base64).decode()
    api_key = os.environ.get("CANTAMEN_API_KEY")
    otp = authorize(user, pwd, api_key)
    boookings = get_bookings(otp, api_key)
    cal = generate_calendar(boookings)
    ical_str = cal.to_ical()
    logging.debug(ical_str)
    return Response(ical_str, mimetype="text/calendar")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app.run()
