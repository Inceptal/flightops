# FlightOps AI Demo Data

This folder contains the first demo dataset for the aviation hackathon:

- `flightops-ai-typhoon-sgn-2026-07-12.json`

It is a realistic synthetic operations-control snapshot for Vietjet during a typhoon disruption at Ho Chi Minh City / SGN.

## What Is Included

- Airport model for SGN, HAN, DAD, CXR, PQC and BKK
- Simulated METAR/TAF-style weather feed
- NOTAM-style operational constraints
- Aircraft availability and maintenance status
- Crew rosters and duty constraints
- Flight schedule for the affected morning wave
- Passenger connection exposure
- Gate and stand status
- Specialist agent findings
- Supervisor recommendation
- "Why?" explanation payload for the demo UI

## Demo Recommendation

The supervisor recommends:

> Swap VJ152 onto VN-A237, delay VJ237 by 42 minutes, move VJ152 to Gate 18, and keep VN-A678 on ground until storm risk drops.

Headline metrics:

- Confidence: 94%
- Estimated savings: USD 18,200
- Misconnections prevented: 38
- Turnaround time saved by Gate 18: 11 minutes

## Realism Notes

The dataset is synthetic, but it is grounded in public aviation facts where useful:

- Vietjet uses IATA `VJ`, ICAO `VJC`, callsign `VIETJET`.
- SGN/Tan Son Nhat uses ICAO `VVTS`.
- SGN has parallel runways `07L/25R` and `07R/25L`.
- Vietjet narrow-body aircraft are represented with Airbus A320/A321 family capacities.

Flight numbers, tail numbers, crew names, maintenance events, NOTAM text, weather forecast, costs and recommendations are simulated for demo purposes.

## Suggested UI Panels

- Live disruption timeline
- Agent findings by domain: weather, aircraft, crew, maintenance, cost
- Supervisor recommendation card
- Alternative options rejected
- "Why?" explanation chain
- Ops-impact metrics

## Public References Used

- Tan Son Nhat International Airport facts: https://en.wikipedia.org/wiki/Tan_Son_Nhat_International_Airport
- Vietjet fleet page: https://www.vietjetair.com/en/pages/our-fleet-1601131595327
- VietJetAir fleet reference: https://www.planespotters.net/airline/VietJetAir
