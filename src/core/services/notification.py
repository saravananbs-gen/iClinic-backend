from src.utils.email_utils import send_email
from src.utils.sms_utils import send_sms


async def send_appointment_notification(
    action,
    patient_email,
    patient_phone,
    provider_name,
    specialization,
    slot_time,
    appointment_type,
):

    if action == "booked":
        subject = "Appointment Confirmation"

        body = f"""
            Dear Patient,

            Your appointment has been successfully confirmed.

            Appointment Details:
            ------------------------------
            Doctor: Dr. {provider_name}
            Specialization: {specialization}
            Appointment Type: {appointment_type}
            Scheduled Time: {slot_time}

            Please ensure that you arrive 10 minutes prior to the appointment.

            If you need to cancel or reschedule, please contact our clinic.

            Best Regards,
            Clinic Support Team
        """

        sms = f"""
            Appointment Confirmed
            Dr. {provider_name}
            {slot_time}
            Type: {appointment_type}
        """

    else:
        subject = "Appointment Cancellation Confirmation"

        body = f"""
            Dear Patient,

            Your appointment has been successfully cancelled.

            Cancelled Appointment Details:
            ------------------------------
            Doctor: Dr. {provider_name}
            Specialization: {specialization}
            Appointment Type: {appointment_type}
            Scheduled Time: {slot_time}

            If this cancellation was a mistake, please schedule another appointment.

            Best Regards,
            Clinic Support Team
        """

        sms = f"""
            Appointment Cancelled
            Dr. {provider_name}
            {slot_time}
        """

    await send_email(patient_email, subject, body)
    await send_sms(patient_phone, sms)
