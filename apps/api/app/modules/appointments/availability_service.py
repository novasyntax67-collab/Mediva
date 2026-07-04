from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any
from zoneinfo import ZoneInfo
import sys
import os
import uuid

# Ensure backend-core is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "packages", "backend-core")))

from app.core.unit_of_work import APIUnitOfWork
from database.models import Doctor

class AvailabilityService:
    def __init__(self, uow: APIUnitOfWork):
        self.uow = uow

    async def get_available_slots(
        self, doctor_id: uuid.UUID, target_date: date, slot_duration_minutes: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Computes available time slots for a doctor on a target date, 
        evaluating weekly recurring templates, exception windows, and existing bookings.
        """
        # 1. Fetch Doctor details
        # We query the doctor record using raw session via uow.appointments repository context
        query_doc = await self.uow.appointments.db.get(Doctor, doctor_id)
        if not query_doc or not query_doc.accepting_patients or query_doc.deleted_at:
            return []

        template = query_doc.availability_template or {}
        weekly = template.get("weekly", {})
        exceptions = template.get("exceptions", [])

        # 2. Get slots defined in the weekly template for this weekday (Monday = 1, Sunday = 7)
        weekday_str = str(target_date.isoweekday())
        daily_rules = weekly.get(weekday_str, [])
        if not daily_rules:
            return []

        # 3. Generate raw template slots for the day
        raw_slots = []
        tz = ZoneInfo(query_doc.timezone or "UTC")
        
        for rule in daily_rules:
            # Parse start and end hours (e.g. "09:00", "13:00")
            try:
                start_h, start_m = map(int, rule["start"].split(":"))
                end_h, end_m = map(int, rule["end"].split(":"))
            except (ValueError, KeyError, AttributeError):
                continue
                
            start_dt = datetime.combine(target_date, time(start_h, start_m), tzinfo=tz)
            end_dt = datetime.combine(target_date, time(end_h, end_m), tzinfo=tz)
            
            curr = start_dt
            while curr + timedelta(minutes=slot_duration_minutes) <= end_dt:
                slot_end = curr + timedelta(minutes=slot_duration_minutes)
                raw_slots.append({
                    "start_time": curr,
                    "end_time": slot_end
                })
                curr = slot_end

        # 4. Filter out slots overlapping with doctor exception windows (leaves, holidays)
        available_slots = []
        for slot in raw_slots:
            slot_start = slot["start_time"]
            slot_end = slot["end_time"]
            is_exceptional = False
            
            for exc in exceptions:
                try:
                    exc_start = datetime.fromisoformat(exc["start_time"].replace("Z", "+00:00"))
                    exc_end = datetime.fromisoformat(exc["end_time"].replace("Z", "+00:00"))
                    
                    # Check overlap
                    if slot_start < exc_end and slot_end > exc_start:
                        is_exceptional = True
                        break
                except (ValueError, KeyError, AttributeError):
                    continue
                    
            if not is_exceptional:
                available_slots.append(slot)

        # 5. Filter out slots overlapping with existing active appointments
        # Query doctor's schedule on this day using our composite index (doctor_id, scheduled_time)
        day_start = datetime.combine(target_date, time.min, tzinfo=tz)
        day_end = datetime.combine(target_date, time.max, tzinfo=tz)
        
        appointments = await self.uow.appointments.get_doctor_schedule(doctor_id, day_start, day_end)
        
        final_slots = []
        for slot in available_slots:
            slot_start = slot["start_time"]
            slot_end = slot["end_time"]
            is_booked = False
            
            for appt in appointments:
                if appt.status == "cancelled" or appt.deleted_at:
                    continue
                appt_start = appt.scheduled_time
                appt_end = appt_start + timedelta(minutes=appt.duration)
                
                # Check overlap
                if slot_start < appt_end and slot_end > appt_start:
                    is_booked = True
                    break
                    
            if not is_booked:
                final_slots.append({
                    "start_time": slot_start.isoformat(),
                    "end_time": slot_end.isoformat(),
                    "available": True
                })

        return final_slots
