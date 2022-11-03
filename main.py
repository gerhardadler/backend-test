from fastapi import FastAPI
from influxdb import InfluxDBClient
from home_assistant_price_cap.other.power import PowerCalculation
from home_assistant_price_cap.homeassistant.connect import Base
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import requests
from pydantic import BaseModel
from home_assistant_price_cap.homeassistant.entity_controll import PowerEntity

client = InfluxDBClient('10.0.19.14', 8086, 'frontend', 'Hemmelig', 'home_assistant')

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

base = Base()
power = PowerCalculation()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get('/index')
async def index():
    watt_result = str(client.query(
        'SELECT mean("value") AS "mean_value" FROM "home_assistant"."autogen"."W" WHERE time > now()-24h AND time < now() GROUP BY time(5m) FILL(null)'))
    watt_parsed = find_between(watt_result, '[', ']')
    watt_json = eval(watt_parsed)
    watt_index = sum(d['mean_value'] for d in watt_json) / len(watt_json)

    nordPricesMeanOslo = power.year()['Oslo']['mean']
    return JSONResponse(content={'avg_watt': watt_index, 'avg_krkwh': nordPricesMeanOslo})


class Schedule(BaseModel):
    entity_name: str
    start_time: str
    end_time: str


@app.post('/schedule')
async def schedule(schedule_data: Schedule):
    res = requests.post("http://10.0.11.97:8001/schedule",
                        json={"entity_name": schedule_data.entity_name, "start_time": schedule_data.start_time,
                              "end_time": schedule_data.end_time})
    return res.json()


@app.get('/nord')
async def nord():
    return power.year()


class Power(BaseModel):
    state: str


@app.get('/entities')
async def entities():
    res = requests.get("http://10.0.19.14:12345/api/states",
                       headers={
                           "Authorization":
                               'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJmNjNiNTNmM2NlN2E0YmI0ODA2NGI5Y2FhYWE3NmZiNCIsImlhdCI6MTY1NzIwMzI4OCwiZXhwIjoxOTcyNTYzMjg4fQ.FERv1n7T7GC_OGOS0FCjVqCqlBbWDNk9RBybjwPA_r8',
                           'Content-Type': 'application/json',
                       })
    return res.json()


@app.post('/user_power')
async def user_power(power: Power):
    res = requests.post("http://10.0.19.14:12345/api/states/input_number.user_power", json={'state': power.state},
                        headers={
                            "Authorization":
                                'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJmNjNiNTNmM2NlN2E0YmI0ODA2NGI5Y2FhYWE3NmZiNCIsImlhdCI6MTY1NzIwMzI4OCwiZXhwIjoxOTcyNTYzMjg4fQ.FERv1n7T7GC_OGOS0FCjVqCqlBbWDNk9RBybjwPA_r8',
                            'Content-Type': 'application/json',
                        })
    return res.json()


@app.get('/voltage/')
async def voltage(time: str = "1h", interval: str = "5m"):
    result = str(client.query(
        'SELECT mean("value") AS "mean_value" FROM "home_assistant"."autogen"."V" WHERE time > now()-{} AND time < now() GROUP BY time({}) FILL(null)'.format(
            time, interval)))
    parsed = find_between(result, '[', ']')
    json = eval(parsed)
    return JSONResponse(content=json)


@app.get('/watt/')
async def voltage(time: str = "1h", interval: str = "5m"):
    result = str(client.query(
        'SELECT mean("value") AS "mean_value" FROM "home_assistant"."autogen"."W" WHERE time > now()-{} AND time < now() GROUP BY time({}) FILL(null)'.format(
            time, interval)))
    parsed = find_between(result, '[', ']')
    json = eval(parsed)
    return JSONResponse(content=json)


def find_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""
