from datetime import date, time

from ninja import Schema


class ContactOut(Schema):
    id: int
    whatsapp: str


class SourceOut(Schema):
    id: int
    type: str
    description: str
    link: str | None


class LocationOut(Schema):
    id: int
    name: str
    address: str


class ScheduleOut(Schema):
    id: int
    day: int
    start_time: time
    end_time: time | None
    observation: str
    verified_at: date | None
    location_name: str
    location: LocationOut | None
    source: SourceOut | None


class ParishOut(Schema):
    id: int
    name: str
    city: str
    state: str
    contact: ContactOut
    mass_schedules: list[ScheduleOut]


class ParishPage(Schema):
    items: list[ParishOut]
    next_cursor: str | None
