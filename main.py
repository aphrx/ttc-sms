import src.schemas as schemas
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request, Response, APIRouter, FastAPI, Form

from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from twilio.twiml.messaging_response import MessagingResponse
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv() 

APIKEY = os.environ.get('TRANSIT_API_KEY')
SID = os.environ.get("TWILIO_SID")
AUTH = os.environ.get("TWILIO_AUTH")

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:30000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# router = APIRouter(prefix='/api/fit')

# @app.get("/find")
directory = {}

def yellow_pages(From: str):
    date_index = datetime.now().strftime(r"%b%d%y")
    if From in directory:
        if date_index in directory[From]:
            directory[From][date_index] = directory[From][date_index] + 1
        else:
            directory[From][date_index] = 1
    else:
        directory[From] = {date_index: 1}

    if directory[From][date_index] <= 10:
        return True
    return False

def find_stop(stop_number: str):
    api_url = f"https://external.transitapp.com/v3/public/search_stops?query={stop_number}&max_num_results=10&lat=43.690730&lon=-79.418124"
    headers = {'apiKey': APIKEY}
    response = requests.get(api_url, headers=headers)
    stops = json.loads(response.text)['results']
    # print(stops)
    for stop in stops:
        if 'TTC' in stop['global_stop_id']:
            return stop
    return None

def get_stop(stop_number: str):
    schedule = {}

    stop = find_stop(stop_number)
    if stop:
        api_url = f"https://external.transitapp.com/v3/public/stop_departures?global_stop_id={stop['global_stop_id']}"
        headers = {'apiKey': APIKEY}
        response = requests.get(api_url, headers=headers)
        routes = json.loads(response.text)['route_departures']
        for route in routes:
            line = route['route_short_name']
            for itinerary in route['itineraries']:
                branched_line = f"{line}{itinerary['branch_code']}"
                for depart in itinerary['schedule_items']:
                    delta = (datetime.fromtimestamp(depart['departure_time']) - datetime.now())
                    diff = relativedelta(datetime.fromtimestamp(depart['departure_time']), datetime.now())
                    if diff.hours < 1:
                        if branched_line in schedule:
                            schedule[branched_line].append(diff.minutes)
                        else:
                            schedule[branched_line] = [diff.minutes]
        return stop, schedule
    return None, None

@app.get("/")
async def status():    
    return {"status": "Online"}

def get_stop_message(stop_number: str):    
    stop, schedule = get_stop(stop_number)
    if stop:
        sms_body = ""
        for k, v in schedule.items():
            sms_body = f"{sms_body}\n{k}: {''.join((str(x) + 'm ') for x in v)}"

        response = f"""{stop['stop_name']}\n{sms_body}\n\nPowered by Transit and Aphrx.\nhttps://linktr.ee/aphrx"""
        print(response)
        return response
    return "Stop could not be found. Please try again."

@app.post("/sms-reply")
async def sms_reply(From: str = Form(...), Body: str = Form(...)): 
    resp = MessagingResponse()
    print(directory)
    if yellow_pages(From):

        # body = request.get('Body', None)
        

        sms_body = get_stop_message(Body)

    else:
        sms_body = """You have reached your maximum daily request allowance. Please try again tomorrow. """

    resp.message(sms_body)

    return Response(content=str(resp), media_type="application/xml")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)