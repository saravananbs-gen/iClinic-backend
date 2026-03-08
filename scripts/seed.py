"""
Seed script – populates the database with realistic test data.

Tables seeded (in order):
  1. roles               (4 roles: patient, provider, admin, frontdesk)
  2. frontdesk users     (2 users with the frontdesk role, password: frontdesk123)
  3. appointment_types   (3 types)
  4. providers           (6 doctors, walk-in – no user account)
  5. availability_slots  (5 slots per provider per day for the next 7 days)
  6. patients            (12 walk-in patients)
  7. appointments        (8 pre-booked appointments across patients/providers)

Run:
    python -m scripts.seed
"""

import asyncio
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.constants.auth import ROLE_ADMIN, ROLE_FRONTDESK, ROLE_PATIENT, ROLE_PROVIDER
from src.data.clients.postgres import AsyncSessionLocal
from src.data.models.postgres.AppointmentType import AppointmentType
from src.data.models.postgres.Appointment import Appointment
from src.data.models.postgres.AvailabilitySlot import AvailabilitySlot
from src.data.models.postgres.Patient import Patient
from src.data.models.postgres.Provider import Provider
from src.data.models.postgres.Role import Role
from src.data.models.postgres.User import User
from src.utils.auth import _hash_password
from src.utils.generate_uuidv7 import uuid7_str


# ── Roles ────────────────────────────────────────────────────────────────────

ROLES = [ROLE_PATIENT, ROLE_PROVIDER, ROLE_ADMIN, ROLE_FRONTDESK]


# ── Appointment Types ────────────────────────────────────────────────────────

APPOINTMENT_TYPES = [
    {
        "name": "General Consultation",
        "description": "Routine check-up or general health concern evaluation with a physician.",
        "duration_minutes": 30,
    },
    {
        "name": "Follow-Up Visit",
        "description": "Review of previous treatment, lab results, or ongoing care plan.",
        "duration_minutes": 30,
    },
    {
        "name": "Specialist Referral",
        "description": "First-time or referred visit to a specialist for focused diagnosis.",
        "duration_minutes": 30,
    },
]


# ── Providers ────────────────────────────────────────────────────────────────

PROVIDERS = [
    {
        "first_name": "Ananya",
        "last_name": "Sharma",
        "phone": "+919876543210",
        "email": "ananya.sharma@iclinic.in",
        "specialization": "General Medicine",
        "notable_work": "Published research on tropical fevers in The Lancet Regional Health",
        "experience_years": 14,
        "qualification": "MBBS, MD (Internal Medicine) – AIIMS Delhi",
        "consultation_fee": Decimal("700.00"),
        "bio": "Dr. Ananya Sharma is a seasoned internist with over 14 years of clinical experience. She focuses on preventive healthcare, chronic disease management, and infectious diseases.",
    },
    {
        "first_name": "Rajesh",
        "last_name": "Patel",
        "phone": "+919876543211",
        "email": "rajesh.patel@iclinic.in",
        "specialization": "Dermatology",
        "notable_work": "Pioneer of laser-assisted vitiligo treatment protocols in Gujarat",
        "experience_years": 10,
        "qualification": "MBBS, DVD – BJ Medical College, Ahmedabad",
        "consultation_fee": Decimal("900.00"),
        "bio": "Dr. Rajesh Patel specialises in medical and cosmetic dermatology, with a keen interest in autoimmune skin conditions and paediatric dermatology.",
    },
    {
        "first_name": "Meera",
        "last_name": "Iyer",
        "phone": "+919876543212",
        "email": "meera.iyer@iclinic.in",
        "specialization": "Pediatrics",
        "notable_work": "Led the neonatal ICU expansion at Apollo Children's Hospital, Chennai",
        "experience_years": 18,
        "qualification": "MBBS, DCH, DNB (Pediatrics) – CMC Vellore",
        "consultation_fee": Decimal("800.00"),
        "bio": "Dr. Meera Iyer is a compassionate paediatrician with nearly two decades of experience in newborn care, childhood nutrition, and developmental milestones.",
    },
    {
        "first_name": "Arjun",
        "last_name": "Deshmukh",
        "phone": "+919876543213",
        "email": "arjun.deshmukh@iclinic.in",
        "specialization": "Orthopedics",
        "notable_work": "Performed 500+ arthroscopic knee surgeries with 98% success rate",
        "experience_years": 12,
        "qualification": "MBBS, MS (Orthopedics) – KEM Hospital, Mumbai",
        "consultation_fee": Decimal("1000.00"),
        "bio": "Dr. Arjun Deshmukh is an orthopaedic surgeon specialising in sports injuries, joint replacements, and minimally invasive arthroscopic procedures.",
    },
    {
        "first_name": "Priya",
        "last_name": "Nair",
        "phone": "+919876543214",
        "email": "priya.nair@iclinic.in",
        "specialization": "Cardiology",
        "notable_work": "Co-authored Indian Heart Association guidelines on preventive cardiology",
        "experience_years": 20,
        "qualification": "MBBS, MD (Medicine), DM (Cardiology) – SCTIMST Trivandrum",
        "consultation_fee": Decimal("1200.00"),
        "bio": "Dr. Priya Nair is a senior cardiologist with expertise in interventional cardiology, heart failure management, and cardiac rehabilitation.",
    },
    {
        "first_name": "Vikram",
        "last_name": "Singh",
        "phone": "+919876543215",
        "email": "vikram.singh@iclinic.in",
        "specialization": "ENT",
        "notable_work": "Introduced endoscopic sinus surgery technique at Safdarjung Hospital",
        "experience_years": 9,
        "qualification": "MBBS, MS (ENT) – Maulana Azad Medical College, Delhi",
        "consultation_fee": Decimal("650.00"),
        "bio": "Dr. Vikram Singh is an ENT specialist experienced in managing hearing disorders, chronic sinusitis, and paediatric airway problems.",
    },
]


# ── Patients (walk-in) ───────────────────────────────────────────────────────

# ── Frontdesk Users ──────────────────────────────────────────────────────────
# Password for all seeded frontdesk users: "frontdesk123"

FRONTDESK_USERS = [
    {
        "email": "priya.frontdesk@iclinic.in",
        "phone": "+919800200101",
        "first_name": "Priya",
        "last_name": "Kapoor",
    },
    {
        "email": "arun.frontdesk@iclinic.in",
        "phone": "+919800200102",
        "first_name": "Arun",
        "last_name": "Bhatia",
    },
]

FRONTDESK_DEFAULT_PASSWORD = "frontdesk123"


# ── Patients (walk-in) ───────────────────────────────────────────────────────

PATIENTS = [
    {
        "first_name": "Rohan",
        "last_name": "Mehta",
        "phone": "+919800100001",
        "email": "rohan.mehta@gmail.com",
        "dob": date(1992, 4, 15),
        "gender": "Male",
        "blood_group": "B+",
        "emergency_contact": "+919800200001",
        "medical_notes": "Mild seasonal allergies; no chronic conditions.",
    },
    {
        "first_name": "Sneha",
        "last_name": "Kulkarni",
        "phone": "+919800100002",
        "email": "sneha.kulkarni@yahoo.com",
        "dob": date(1988, 11, 2),
        "gender": "Female",
        "blood_group": "A+",
        "emergency_contact": "+919800200002",
        "medical_notes": "History of hypothyroidism; on levothyroxine 50 mcg daily.",
    },
    {
        "first_name": "Amit",
        "last_name": "Verma",
        "phone": "+919800100003",
        "email": "amit.verma@outlook.com",
        "dob": date(1975, 7, 28),
        "gender": "Male",
        "blood_group": "O+",
        "emergency_contact": "+919800200003",
        "medical_notes": "Type 2 diabetes managed with metformin 500 mg BD.",
    },
    {
        "first_name": "Kavitha",
        "last_name": "Reddy",
        "phone": "+919800100004",
        "email": "kavitha.reddy@gmail.com",
        "dob": date(1995, 1, 10),
        "gender": "Female",
        "blood_group": "AB+",
        "emergency_contact": "+919800200004",
        "medical_notes": "No known medical conditions or allergies.",
    },
    {
        "first_name": "Suresh",
        "last_name": "Nambiar",
        "phone": "+919800100005",
        "email": "suresh.nambiar@gmail.com",
        "dob": date(1968, 3, 22),
        "gender": "Male",
        "blood_group": "A-",
        "emergency_contact": "+919800200005",
        "medical_notes": "Hypertension; on amlodipine 5 mg OD. Mild osteoarthritis in right knee.",
    },
    {
        "first_name": "Divya",
        "last_name": "Joshi",
        "phone": "+919800100006",
        "email": "divya.joshi@hotmail.com",
        "dob": date(2001, 9, 5),
        "gender": "Female",
        "blood_group": "B-",
        "emergency_contact": "+919800200006",
        "medical_notes": "Occasional migraine episodes; takes sumatriptan as needed.",
    },
    {
        "first_name": "Farhan",
        "last_name": "Sheikh",
        "phone": "+919800100007",
        "email": "farhan.sheikh@gmail.com",
        "dob": date(1983, 12, 18),
        "gender": "Male",
        "blood_group": "O-",
        "emergency_contact": "+919800200007",
        "medical_notes": "Asthma since childhood; uses salbutamol inhaler on demand.",
    },
    {
        "first_name": "Lakshmi",
        "last_name": "Venkatesh",
        "phone": "+919800100008",
        "email": "lakshmi.v@gmail.com",
        "dob": date(1990, 6, 30),
        "gender": "Female",
        "blood_group": "A+",
        "emergency_contact": "+919800200008",
        "medical_notes": "Iron-deficiency anaemia; on ferrous sulphate supplements.",
    },
    {
        "first_name": "Karthik",
        "last_name": "Subramanian",
        "phone": "+919800100009",
        "email": "karthik.sub@yahoo.com",
        "dob": date(1997, 2, 14),
        "gender": "Male",
        "blood_group": "AB-",
        "emergency_contact": "+919800200009",
        "medical_notes": "ACL reconstruction (left knee) in 2023; physiotherapy completed.",
    },
    {
        "first_name": "Neha",
        "last_name": "Gupta",
        "phone": "+919800100010",
        "email": "neha.gupta@gmail.com",
        "dob": date(1985, 8, 9),
        "gender": "Female",
        "blood_group": "B+",
        "emergency_contact": "+919800200010",
        "medical_notes": "PCOD; on oral contraceptives for cycle regulation.",
    },
    {
        "first_name": "Ravi",
        "last_name": "Krishnan",
        "phone": "+919800100011",
        "email": "ravi.krishnan@outlook.com",
        "dob": date(1970, 5, 25),
        "gender": "Male",
        "blood_group": "O+",
        "emergency_contact": "+919800200011",
        "medical_notes": "Post coronary angioplasty (2022); on dual antiplatelet therapy.",
    },
    {
        "first_name": "Isha",
        "last_name": "Chatterjee",
        "phone": "+919800100012",
        "email": "isha.chatterjee@gmail.com",
        "dob": date(1999, 10, 17),
        "gender": "Female",
        "blood_group": "A+",
        "emergency_contact": "+919800200012",
        "medical_notes": "No known conditions. Routine check-up for employment medical.",
    },
]


# ── Helpers ──────────────────────────────────────────────────────────────────


# Hours at which the 5 daily slots are created (30-min each)
_SLOT_HOURS = [9, 10, 11, 14, 15]


def _generate_slots(provider_id: str, days: int = 7) -> list[dict]:
    """Generate 5 slots per day for the next `days` days (skipping Sundays)."""
    slots = []
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    for day_offset in range(days):
        day = today + timedelta(days=day_offset)
        # skip Sundays
        if day.weekday() == 6:
            continue
        for hour in _SLOT_HOURS:
            start = day.replace(hour=hour, minute=0)
            slots.append(
                {
                    "id": uuid7_str(),
                    "provider_id": provider_id,
                    "start_time": start,
                    "end_time": start + timedelta(minutes=30),
                    "is_booked": False,
                }
            )
    return slots


async def _row_exists(session: AsyncSession, model, **filters) -> bool:
    """Return True if at least one row matches the given filters."""
    stmt = select(model)
    for col, val in filters.items():
        stmt = stmt.where(getattr(model, col) == val)
    result = await session.execute(stmt.limit(1))
    return result.scalar_one_or_none() is not None


# ── Main seed routine ────────────────────────────────────────────────────────


async def seed():
    async with AsyncSessionLocal() as session:
        # 1 ── Roles
        role_count = 0
        for role_name in ROLES:
            if await _row_exists(session, Role, name=role_name):
                print(f"  ✓ role already exists: {role_name}")
                continue
            session.add(Role(id=uuid7_str(), name=role_name))
            role_count += 1
        await session.flush()
        print(f"✔ Roles: {len(ROLES)} ({role_count} new)")

        # 2 ── Frontdesk users
        frontdesk_role = (
            await session.execute(select(Role).where(Role.name == ROLE_FRONTDESK))
        ).scalar_one_or_none()

        fd_count = 0
        if frontdesk_role:
            password_hash = _hash_password(FRONTDESK_DEFAULT_PASSWORD)
            for data in FRONTDESK_USERS:
                if await _row_exists(session, User, email=data["email"]):
                    print(f"  ✓ frontdesk user already exists: {data['email']}")
                    continue
                user = User(
                    id=uuid7_str(),
                    role_id=frontdesk_role.id,
                    email=data["email"],
                    phone=data["phone"],
                    password_hash=password_hash,
                )
                session.add(user)
                fd_count += 1
            await session.flush()
        print(f"✔ Frontdesk users: {len(FRONTDESK_USERS)} ({fd_count} new)")

        # 3 ── Appointment types
        appt_type_ids: dict[str, str] = {}
        for data in APPOINTMENT_TYPES:
            if await _row_exists(session, AppointmentType, name=data["name"]):
                existing = (
                    await session.execute(
                        select(AppointmentType).where(
                            AppointmentType.name == data["name"]
                        )
                    )
                ).scalar_one()
                appt_type_ids[data["name"]] = existing.id
                print(f"  ✓ appointment type already exists: {data['name']}")
                continue

            at = AppointmentType(id=uuid7_str(), **data)
            session.add(at)
            appt_type_ids[data["name"]] = at.id
        await session.flush()
        print(f"✔ Appointment types: {len(appt_type_ids)}")

        # 4 ── Providers
        provider_ids: list[str] = []
        for data in PROVIDERS:
            if await _row_exists(session, Provider, phone=data["phone"]):
                existing = (
                    await session.execute(
                        select(Provider).where(Provider.phone == data["phone"])
                    )
                ).scalar_one()
                provider_ids.append(existing.id)
                print(
                    f"  ✓ provider already exists: {data['first_name']} {data['last_name']}"
                )
                continue

            pid = uuid7_str()
            provider = Provider(id=pid, **data)
            session.add(provider)
            provider_ids.append(pid)
        await session.flush()
        print(f"✔ Providers: {len(provider_ids)}")

        # 5 ── Availability slots (for each provider, next 7 days)
        slot_count = 0
        all_slots: list[dict] = []
        for pid in provider_ids:
            existing_slot = await _row_exists(
                session, AvailabilitySlot, provider_id=pid
            )
            if existing_slot:
                print(f"  ✓ slots already exist for provider {pid[:8]}…")
                # collect existing unbooked slots for appointment seeding
                result = await session.execute(
                    select(AvailabilitySlot).where(
                        AvailabilitySlot.provider_id == pid,
                        AvailabilitySlot.is_booked == False,  # noqa: E712
                    )
                )
                for s in result.scalars().all():
                    all_slots.append(
                        {
                            "id": s.id,
                            "provider_id": s.provider_id,
                            "start_time": s.start_time,
                            "end_time": s.end_time,
                            "is_booked": s.is_booked,
                        }
                    )
                continue

            slots = _generate_slots(pid)
            for s in slots:
                session.add(AvailabilitySlot(**s))
            all_slots.extend(slots)
            slot_count += len(slots)
        await session.flush()
        print(f"✔ Availability slots created: {slot_count}")

        # 6 ── Patients
        patient_ids: list[str] = []
        for data in PATIENTS:
            if await _row_exists(session, Patient, phone=data["phone"]):
                existing = (
                    await session.execute(
                        select(Patient).where(Patient.phone == data["phone"])
                    )
                ).scalar_one()
                patient_ids.append(existing.id)
                print(
                    f"  ✓ patient already exists: {data['first_name']} {data['last_name']}"
                )
                continue

            pid = uuid7_str()
            patient = Patient(id=pid, is_walk_in=True, **data)
            session.add(patient)
            patient_ids.append(pid)
        await session.flush()
        print(f"✔ Patients: {len(patient_ids)}")

        # 7 ── Pre-booked appointments
        #      Book a few realistic appointments so the system has data to display
        BOOKINGS = [
            # (patient_index, provider_index, slot_day_offset, slot_hour, appt_type_name, channel, notes)
            (
                0,
                0,
                1,
                9,
                "General Consultation",
                "walk-in",
                "Patient complains of persistent headache and mild fever for 3 days.",
            ),
            (
                1,
                2,
                1,
                10,
                "General Consultation",
                "walk-in",
                "Child (age 6) has recurring cough and low appetite.",
            ),
            (
                2,
                0,
                1,
                11,
                "Follow-Up Visit",
                "walk-in",
                "Follow-up for blood sugar levels; fasting glucose report attached.",
            ),
            (
                3,
                1,
                2,
                9,
                "Specialist Referral",
                "walk-in",
                "Referred by GP for evaluation of recurring skin rashes on forearms.",
            ),
            (
                4,
                3,
                2,
                14,
                "Specialist Referral",
                "walk-in",
                "Persistent right knee pain worsening over the past month.",
            ),
            (
                5,
                0,
                2,
                15,
                "General Consultation",
                "online",
                "Severe migraine episode; requesting prescription review.",
            ),
            (
                6,
                5,
                3,
                9,
                "General Consultation",
                "walk-in",
                "Chronic nasal congestion and snoring; requesting ENT evaluation.",
            ),
            (
                7,
                4,
                3,
                10,
                "Follow-Up Visit",
                "walk-in",
                "Post-angioplasty check-up; recent echocardiogram report available.",
            ),
        ]

        # build a lookup: (provider_id, date, hour) -> slot dict
        slot_lookup: dict[tuple[str, str, int], dict] = {}
        for s in all_slots:
            key = (
                s["provider_id"],
                s["start_time"].strftime("%Y-%m-%d"),
                s["start_time"].hour,
            )
            if not s["is_booked"]:
                slot_lookup[key] = s

        booked = 0
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        for pat_idx, prov_idx, day_off, hour, type_name, channel, notes in BOOKINGS:
            target_day = today + timedelta(days=day_off)
            # skip Sunday
            if target_day.weekday() == 6:
                target_day += timedelta(days=1)

            key = (
                provider_ids[prov_idx],
                target_day.strftime("%Y-%m-%d"),
                hour,
            )
            slot = slot_lookup.get(key)
            if not slot:
                print(
                    f"  ⚠ no free slot for booking ({pat_idx},{prov_idx},day+{day_off},{hour}h) – skipped"
                )
                continue

            # check if appointment already exists for this slot
            if await _row_exists(session, Appointment, slot_id=slot["id"]):
                print(f"  ✓ appointment already exists for slot {slot['id'][:8]}…")
                continue

            appointment = Appointment(
                id=uuid7_str(),
                patient_id=patient_ids[pat_idx],
                provider_id=provider_ids[prov_idx],
                slot_id=slot["id"],
                appointment_type_id=appt_type_ids[type_name],
                channel=channel,
                notes=notes,
                status="confirmed",
            )
            session.add(appointment)

            # mark slot as booked in DB
            slot_obj = await session.get(AvailabilitySlot, slot["id"])
            if slot_obj:
                slot_obj.is_booked = True

            # remove from lookup so it's not double-booked
            slot["is_booked"] = True
            booked += 1

        await session.commit()
        print(f"✔ Appointments booked: {booked}")
        print("\n🌱 Seed completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
