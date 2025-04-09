import calendar
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime, timedelta
from ..models.subscriber import Subscriber, FamilyMember, Qualification, Specialization, DoctorAppointment, Doctor, DoctorQualification
from ..schemas.subscriber import SubscriberMessage, CreateAppointment, UpdateAppointment, CancelAppointment
from ..utils import check_data_exist_utils, entity_data_return_utils , get_data_by_id_utils, get_data_by_mobile, id_incrementer 
from ..crud.subscriber_appointment import (create_appointment_dal, update_appointment_dal, cancel_appointment_dal, 
                                             clinic_data_active_helper, doctors_availability_active_helper, doctor_data_active_helper, doctor_avblty_log_helper, 
                                             get_doctor_list_dal, get_prescription_helper, get_doctor_upcoming_list_dal, past_appointment_dal, 
                                             health_hub_stacks_dal, get_doctor_by_specialization)
from sqlalchemy.ext.asyncio import AsyncSession

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def create_appointment_bl(appointment: CreateAppointment, subscriber_mysql_session: AsyncSession):
    """
    Handles the business logic for creating a new appointment.

    This function validates the subscriber's existence, generates a new appointment ID,     
    and creates a new appointment record in the database. The function ensures data consistency 
    and handles errors gracefully.

    Args:
        appointment (CreateAppointment): The data required to create the appointment, including subscriber mobile, doctor ID, clinic name, etc.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        SubscriberMessage: A message confirming the successful creation of the appointment.

    Raises:
        HTTPException: If the subscriber does not exist or if validation errors occur.
        SQLAlchemyError: If a database error occurs during the appointment creation process.
        Exception: If an unexpected error occurs.
    """
    async with subscriber_mysql_session.begin(): # Outer transaction here
        try:
            # Check if the subscriber exists
            subscriber_data = await get_data_by_mobile(
            table=Subscriber, 
            field="mobile", 
            subscriber_mysql_session=subscriber_mysql_session, 
            mobile=appointment.subscriber_mobile
            )
            subscriber_id = subscriber_data.subscriber_id
            # Convert date and time
            date = datetime.strptime(appointment.date, "%Y-%m-%d").date()
            time = datetime.strptime(appointment.time, "%H:%M:%S").time()

            # Generate new appointment ID
            new_appointment_id = await id_incrementer(entity_name="DOCTORAPPOINTMENT", subscriber_mysql_session=subscriber_mysql_session)

            # Create appointment object
            appointment_data = DoctorAppointment(
            appointment_id=new_appointment_id,
            doctor_id=appointment.doctor_id,
            subscriber_id=subscriber_id,
            appointment_date=date,
            appointment_time=time,
            book_for_id= None if appointment.book_for_id is None else appointment.book_for_id,
            status="Scheduled",
            clinic_name=appointment.clinic_name,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            active_flag=1
            )
            print("Appointment data", appointment_data)

            # Insert into database
            await create_appointment_dal(appointment_data=appointment_data, subscriber_mysql_session=subscriber_mysql_session)
            return SubscriberMessage(message="Appointment Created Successfully")

        except HTTPException as http_exc:
            raise http_exc    

        except SQLAlchemyError as e:
            logger.error(f"Error creating appointment BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error in creating appointment BL")

        except Exception as e:
            logger.error(f"Unexpected error BL: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred BL")
            
async def update_appointment_bl(appointment:UpdateAppointment, subscriber_mysql_session:AsyncSession):
    """
    Handles the business logic for updating an existing appointment.

    This function updates the appointment details, such as date, time, or other fields, 
    and ensures that the appointment is updated in the database. The function validates the subscriber's existence 
    and raises errors when necessary.

    Args:
        appointment (UpdateAppointment): The updated appointment data, including appointment ID, date, time, and subscriber details.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        SubscriberMessage: A message confirming the successful update of the appointment.

    Raises:
        HTTPException: If the subscriber or appointment is not found, or if validation errors occur.
        SQLAlchemyError: If a database error occurs during the update process.
        Exception: If an unexpected error occurs.
    """
    async with subscriber_mysql_session.begin(): # Outer transaction here
        try:
            existing_subscriber =await check_data_exist_utils(table=Subscriber, field="mobile", subscriber_mysql_session=subscriber_mysql_session, data=appointment.subscriber_mobile)
            #if existing_subscriber == "unique":
            #    raise HTTPException(status_code=400, detail="No Subscriber Found With This Mobile Number")
            #else:
            subscriber_id = existing_subscriber.subscriber_id
            date = datetime.strptime(appointment.date, "%Y-%m-%d").date()
            time = datetime.strptime(appointment.time, "%H:%M:%S").time()
            await update_appointment_dal(appointment=appointment, subscriber_id=subscriber_id, date=date, time=time, subscriber_mysql_session=subscriber_mysql_session)
            return SubscriberMessage(message="Appointment Updated Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error updating appointment BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error in updating appointment BL")
        except Exception as e:
            logger.error(f"Unexpected error BL: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred BL")
    
async def cancel_appointment_bl(appointment:CancelAppointment, subscriber_mysql_session:AsyncSession):
    """
    Handles the business logic for canceling an existing appointment.

    This function validates the subscriber's existence, cancels the appointment by updating its status 
    in the database, and ensures that all changes are committed.

    Args:
        appointment (CancelAppointment): The appointment data required to cancel, including appointment ID and subscriber details.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        SubscriberMessage: A message confirming the successful cancellation of the appointment.

    Raises:
        HTTPException: If the subscriber or appointment is not found, or if validation errors occur.
        SQLAlchemyError: If a database error occurs during the cancellation process.
        Exception: If an unexpected error occurs.
    """
    async with subscriber_mysql_session.begin(): # Outer transaction here
        try:
            existing_subscriber = await check_data_exist_utils(table=Subscriber, field="mobile", subscriber_mysql_session=subscriber_mysql_session, data=appointment.subscriber_mobile)
            #if existing_subscriber == "unique":
            #    raise HTTPException(status_code=400, detail="No Subscriber Found With This Mobile Number")
            #else:
            subscriber_id = existing_subscriber.subscriber_id
            await cancel_appointment_dal(appointment=appointment, subscriber_id=subscriber_id, subscriber_mysql_session=subscriber_mysql_session)
            return SubscriberMessage(message="Appointment Cancelled Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error cancelling appointment BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error in cancelling appointment BL")
        except Exception as e:
            logger.error(f"Unexpected error BL: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred BL")

async def doctor_upcomming_schedules_bl(subscriber_mobile: str, subscriber_mysql_session: AsyncSession):
    """
    Handles the business logic for retrieving a doctor's upcoming appointments.

    This function fetches and returns a list of upcoming appointments for a doctor, 
    including appointment details, subscriber information, and doctor qualifications.

    Args:
        subscriber_mobile (str): The mobile number of the subscriber whose doctor's appointments are to be retrieved.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        list: A list of dictionaries containing detailed information about each upcoming appointment, 
          including date, time, doctor details, and subscriber details.

    Raises:
        HTTPException: If the subscriber or appointments are not found, or if validation errors occur.
        SQLAlchemyError: If a database error occurs while retrieving the appointments.
        Exception: If an unexpected error occurs.
    """

    try:
        existing_subscriber = await check_data_exist_utils(table=Subscriber, field="mobile", subscriber_mysql_session=subscriber_mysql_session, data=subscriber_mobile)
        if existing_subscriber == "unique":
            raise HTTPException(status_code=400, detail="No Subscriber Found With This Mobile Number")
        else:
            subscriber_data = existing_subscriber
        subscriber_id = subscriber_data.subscriber_id
        upcoming_appointments = await get_doctor_upcoming_list_dal(subscriber_id=subscriber_id, subscriber_mysql_session=subscriber_mysql_session)
        appointment_list = []
        if not upcoming_appointments:
            return SubscriberMessage(message="No Upcomming appointments found")
        for appointment in upcoming_appointments:
            appointment_id = appointment.appointment_id
            date = appointment.appointment_date
            time = appointment.appointment_time
            status = appointment.status
            
            # Doctor data
            doctor_data = await get_data_by_id_utils(
                table=Doctor,
                field="doctor_id",
                subscriber_mysql_session=subscriber_mysql_session,
                data=appointment.doctor_id
            )
            
            doctor_id = appointment.doctor_id
            doctor_first_name = doctor_data.first_name
            doctor_last_name = doctor_data.last_name
            
            # Doctor qualifications
            qualification_list = []
            specialization_list = []
            doctor_qualification_data = await entity_data_return_utils(table=DoctorQualification, field="doctor_id", subscriber_mysql_session=subscriber_mysql_session, data=appointment.doctor_id)
            for doc_qualification in doctor_qualification_data:
                qualification_data = await get_data_by_id_utils(
                    table=Qualification,
                    field="qualification_id",
                    subscriber_mysql_session=subscriber_mysql_session,
                    data=doc_qualification.qualification_id
                )
                qualification_name = qualification_data.qualification_name if qualification_data else ""
                
                specialization_name = ""
                if doc_qualification.specialization_id:
                    specialization_data = await get_data_by_id_utils(
                        table=Specialization,
                        field="specialization_id",
                        subscriber_mysql_session=subscriber_mysql_session,
                        data=doc_qualification.specialization_id
                    )
                    specialization_name = specialization_data.specialization_name if specialization_data else ""
                
                qualification_list.append(qualification_name)
                specialization_list.append(specialization_name)
            
            # Subscriber data
            subscriber_first_name = subscriber_data.first_name
            subscriber_last_name = subscriber_data.last_name
            
            # Book for data
            book_for_name = ""
            book_for_mobile = ""
            if appointment.book_for_id:
                book_for_data = await get_data_by_id_utils(
                    table=FamilyMember,
                    field="familymember_id",
                    subscriber_mysql_session=subscriber_mysql_session,
                    data=appointment.book_for_id
                )
                if book_for_data:
                    book_for_name = book_for_data.name
                    book_for_mobile = book_for_data.mobile_number
            
            appointment_list.append({
                "appointment_id": appointment_id,
                "date": date,
                "time": time,
                "status": status,
                "subscriber_first_name": subscriber_first_name,
                "subscriber_last_name": subscriber_last_name,
                "book_for_name": book_for_name,
                "book_for_mobile": book_for_mobile,
                "doctor_id": doctor_id,
                "doctor_firstname": doctor_first_name,
                "doctor_lastname": doctor_last_name,
                "qualification": qualification_list,
                "specialization": specialization_list
            })
        
        return appointment_list
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error while fetching the appointment upcoming list BL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while fetching the appointment upcoming list BL") 
    except Exception as e:
        logger.error(f"Unexpected error BL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred BL")
    
async def past_appointment_list_bl(subscriber_mobile: str, subscriber_mysql_session: AsyncSession):
    """
    Handles the business logic for retrieving a subscriber's past appointments.

    This function fetches and processes a list of all past appointments for a subscriber based on their mobile number.
    It also retrieves detailed information about each appointment, such as doctor details, qualifications, subscriber information, 
    family member information (if applicable), and prescriptions (if the appointment was completed).

    Args:
        subscriber_mobile (str): The mobile number of the subscriber whose past appointments are to be retrieved.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        list | dict: A list of dictionaries containing detailed information about each past appointment, 
                 or a message if no past appointments are found.

    Raises:
        HTTPException: If the subscriber, doctor, specialization, or qualification is not found, 
                   or if any validation error occurs.
        SQLAlchemyError: If a database error occurs while retrieving the appointments.
        Exception: If an unexpected error occurs.
    """

    try:
        subscriber_exist = await check_data_exist_utils(table=Subscriber, field="mobile", subscriber_mysql_session=subscriber_mysql_session, data=subscriber_mobile)
        if subscriber_exist == "unique":
            raise HTTPException(status_code=404, detail="Subscriber not found with this mobile number")
        else:
            subscriber_id = subscriber_exist.subscriber_id
        
        past_appointment_list = await past_appointment_dal(subscriber_id=subscriber_id, subscriber_mysql_session=subscriber_mysql_session)
        if len(past_appointment_list) == 0:
            return {"message": "No Past Booking Appointments Found"}
        previous_appointments = []
        
        for booked_appointment in past_appointment_list:
            appointment_date = booked_appointment.appointment_date
            appointment_time = booked_appointment.appointment_time
            appointment_id = booked_appointment.appointment_id
            appointment_status = booked_appointment.status
            
            doctor_data = await check_data_exist_utils(table=Doctor, field="doctor_id", subscriber_mysql_session=subscriber_mysql_session, data=booked_appointment.doctor_id)
            if doctor_data == "unique":
                raise HTTPException(status_code=404, detail="Doctor not found")
            else:
                doctor_name = doctor_data.first_name
                doctor_last_name = doctor_data.last_name
            
            # Qualification
            doctor_qualification_data = await entity_data_return_utils(table=DoctorQualification, field="doctor_id", subscriber_mysql_session=subscriber_mysql_session, data=booked_appointment.doctor_id)
            qualification_list = []
            specialization_list = []
            if doctor_qualification_data:
                for qual in doctor_qualification_data:
                    specialization_name = ""
                    if qual.specialization_id is not None:
                        specialization_data = await check_data_exist_utils(table=Specialization, field="specialization_id", subscriber_mysql_session=subscriber_mysql_session, data=qual.specialization_id)
                        if specialization_data == "unique":
                            raise HTTPException(status_code=404, detail="Specialization not found")
                        else:
                            specialization_name = specialization_data.specialization_name
                    
                    qualification_data = await check_data_exist_utils(table=Qualification, field="qualification_id", subscriber_mysql_session=subscriber_mysql_session, data=qual.qualification_id)
                    if qualification_data == "unique":
                        raise HTTPException(status_code=404, detail="Qualification not found")
                    else:
                        qualification_name = qualification_data.qualification_name
                    
                    qualification_list.append( qualification_name)
                    specialization_list.append(specialization_name)
            
            # Subscriber data
            subscriber_data = await get_data_by_id_utils(table=Subscriber, field="subscriber_id", subscriber_mysql_session=subscriber_mysql_session, data=booked_appointment.subscriber_id)
            subscriber_first_name = subscriber_data.first_name
            subscriber_last_name = subscriber_data.last_name
            
            # Book for
            book_for_name = ""
            book_for_mobile = ""
            if booked_appointment.book_for_id is not None:
                book_for_data = await get_data_by_id_utils(table=FamilyMember, field="familymember_id", subscriber_mysql_session=subscriber_mysql_session, data=booked_appointment.book_for_id)
                book_for_name = book_for_data.name
                book_for_mobile = book_for_data.mobile_number
            
            # Prescription
            if booked_appointment.status == "Completed":
                prescription = await get_prescription_helper(appointment_id=booked_appointment.appointment_id, subscriber_mysql_session=subscriber_mysql_session)
                prescription_values = {
                        "blood_pressure": prescription["prescription"].blood_pressure,
                        "body_temperature": prescription["prescription"].temperature,
                        "pulse": prescription["prescription"].pulse,
                        "weight": prescription["prescription"].weight,
                        "drug_allergy": prescription["prescription"].drug_allergy,
                        "history": prescription["prescription"].history,
                        "complaints": prescription["prescription"].complaints,
                        "diagnosis": prescription["prescription"].diagnosis,
                        "specialist_type": prescription["prescription"].specialist_type,
                        "consulting_doctor": prescription["prescription"].consulting_doctor,
                        "next_visit_date": prescription["prescription"].next_visit_date,
                        "procedure_name": prescription["prescription"].procedure_name,
                        "home_care_service": prescription["prescription"].home_care_service,
                    }
                
                medicine_list = []
                for pres in prescription["medicine"]:
                    medicine_list.append(
                        {
                        "medicine_name": pres.medicine_name,  # Use dot notation
                        "dosage_timing": pres.dosage_timing,
                        "medication_timing": pres.medication_timing,
                        "treatment_duration": pres.treatment_duration
                        }
                    )
            else:
                medicine_list = []
                prescription_values = ""
            
            previous_appointments.append(
                {
                    "appointment_id": appointment_id,
                    "appointment_date": appointment_date,
                    "appointment_time": appointment_time,
                    "appointment_status": appointment_status,
                    "doctor_firstname": doctor_name,
                    "doctor_lastname": doctor_last_name,
                    "qualification": qualification_list,
                    "specialization": specialization_list,
                    "subscriber_firstname": subscriber_first_name,
                    "subscriber_lastname": subscriber_last_name,
                    "book_for_name": book_for_name,
                    "book_for_mobile": book_for_mobile,
                    "prescription": prescription_values,
                    "medicine_prescribed": medicine_list
                }
            )
        return previous_appointments
    except HTTPException as http_exc:
        raise http_exc    
    except SQLAlchemyError as e:
        logger.error(f"Error in fetching the past booking appointments BL: {e}")
        raise HTTPException(status_code=500, detail="Error in fetching the past booking appointments BL")
    except Exception as e:
        logger.error(f"Unexpected error BL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred BL")

async def doctor_list_appointment(subscriber_mobile:str, subscriber_mysql_session:AsyncSession):
    """
    Fetches the list of past and upcoming appointments for a given subscriber.

    This asynchronous function retrieves both past and upcoming appointments for a subscriber
    using their mobile number and an asynchronous MySQL session. It handles specific exceptions
    to ensure proper error logging and response.

    Parameters:
        subscriber_mobile (str): The mobile number of the subscriber whose appointments are to be fetched.
        subscriber_mysql_session (AsyncSession): An asynchronous session object for interacting with the MySQL database.

    Returns:
        dict: A dictionary containing two keys:
            - "past_appointment": List of past appointments for the subscriber.
            - "upcomming_appointmert": List of upcoming appointments for the subscriber.

    Raises:
        HTTPException: Raised in case of an HTTP-related error.
        SQLAlchemyError: Raised in case of an SQLAlchemy database error.
        Exception: Raised for unexpected errors with appropriate logging.
    """
    try:
        past_appointment = await past_appointment_list_bl(subscriber_mobile=subscriber_mobile, subscriber_mysql_session=subscriber_mysql_session)
        upcomming_appointmert = await doctor_upcomming_schedules_bl(subscriber_mobile=subscriber_mobile, subscriber_mysql_session=subscriber_mysql_session)
        return {"past_appointment":past_appointment, "upcomming_appointmert":upcomming_appointmert}
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in fetching the past booking appointments BL: {e}")
        raise HTTPException(status_code=500, detail="Error in fetching the past booking appointments BL")
    except Exception as e:
        logger.error(f"Unexpected error BL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred BL")
   
async def doctor_list_bl(speciaization_id:str, subscriber_mysql_session:AsyncSession):
    """
    Handles the business logic for retrieving a list of doctors based on a specialization.

    This function fetches a list of doctors associated with a specific specialization, retrieves their qualifications, availability, 
    and booked slots, and formats the data into a structured response. It ensures that all doctors returned are active and have valid 
    availability logs.

    Args:
        speciaization_id (str): The ID of the specialization for which doctors are to be retrieved.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        list: A list of dictionaries, where each dictionary contains details about a doctor, including:
        - Basic information (name, experience, about).
        - Qualifications (degree, specialization).
        - Availability (days, slots, and booked slots).

    Raises:
        HTTPException: If the specialization ID is invalid or not found, or if validation errors occur.
        SQLAlchemyError: If a database error occurs while fetching the doctors list.
        Exception: If an unexpected error occurs.
    """
    try:
        if await check_data_exist_utils(table=Specialization, field="specialization_id", subscriber_mysql_session=subscriber_mysql_session, data=speciaization_id) == "unique":
            raise HTTPException(status_code=404, detail="Specialization now found")
        doctor_qualification = await get_doctor_list_dal(specialization_id=speciaization_id, subscriber_mysql_session=subscriber_mysql_session)
        doctors_data_list=[]
        for doctor in doctor_qualification:
            doctor_availability_log = await doctor_avblty_log_helper(doctor_id=doctor.doctor_id,subscriber_mysql_session=subscriber_mysql_session)
            if doctor_availability_log:
                doctor_data = await doctor_data_active_helper(doctor_id=doctor.doctor_id, subscriber_mysql_session=subscriber_mysql_session)
                if doctor_data:
                    # doctor data
                    doctor_first_name = doctor_data.first_name
                    doctor_last_name = doctor_data.last_name
                    doctor_experience = doctor_data.experience
                    doctor_about = doctor_data.about_me
                    # doctor qualification
                    qualification_list=[]
                    specialization_list=[]
                    doctor_education_list = await entity_data_return_utils(table=DoctorQualification, field="doctor_id", subscriber_mysql_session=subscriber_mysql_session, data=doctor.doctor_id)
                    for qualifiy in doctor_education_list:
                        if qualifiy.specialization_id == None:
                            specialization_name = ""
                        else:
                            specialization_data = await get_data_by_id_utils(table=Specialization, field="specialization_id", subscriber_mysql_session=subscriber_mysql_session, data=qualifiy.specialization_id)
                            specialization_name = specialization_data.specialization_name
                        qualification_data = await get_data_by_id_utils(table=Qualification, field="qualification_id", subscriber_mysql_session=subscriber_mysql_session, data=qualifiy.qualification_id)
                        qualification_list.append(qualification_data.qualification_name)
                        specialization_list.append(specialization_name)
                    # doctor availability
                    doctor_availability_list = []
                    doctor_availability_data = await doctors_availability_active_helper(doctor_id=doctor.doctor_id, subscriber_mysql_session=subscriber_mysql_session)
                    for avbl in doctor_availability_data:
                        booked_list = []
                        clinic_data = await clinic_data_active_helper(doctor_id=doctor.doctor_id, subscriber_mysql_session=subscriber_mysql_session)
                        for clinic in clinic_data:
                            appointment_time = clinic.appointment_time
                            appointment_day = clinic.appointment_date.strftime("%a")  # Get the day from the date
                            if appointment_day in avbl.days:
                                if avbl.morning_slot and appointment_time < datetime.strptime("12:00:00", "%H:%M:%S").time():
                                    booked_list.append({
                                        "appointment_date": clinic.appointment_date,
                                        "appointment_time": appointment_time,
                                        "appointment_clinic_name": clinic.clinic_name
                                    })
                                elif avbl.afternoon_slot and datetime.strptime("12:00:00", "%H:%M:%S").time() <= appointment_time < datetime.strptime("17:00:00", "%H:%M:%S").time():
                                    booked_list.append({
                                        "appointment_date": clinic.appointment_date,
                                        "appointment_time": appointment_time,
                                        "appointment_clinic_name": clinic.clinic_name
                                    })
                                elif avbl.evening_slot and appointment_time >= datetime.strptime("17:00:00", "%H:%M:%S").time():
                                    booked_list.append({
                                        "appointment_date": clinic.appointment_date,
                                        "appointment_time": appointment_time,
                                        "appointment_clinic_name": clinic.clinic_name
                                    })
                        doctor_availability_list.append(
                            {
                                "clinic_name": avbl.clinic_name,
                                "slots": 
                                    {
                                        "days": avbl.days,
                                        "morning": avbl.morning_slot if avbl.morning_slot else "",
                                        "afternoon": avbl.afternoon_slot if avbl.afternoon_slot else "",
                                        "evening": avbl.evening_slot if avbl.evening_slot else ""
                                    },
                                "booked_slots": booked_list
                            }
                        )
                doctors_data_list.append(
                {
                    "doctor_id": doctor.doctor_id,
                    "doctor_first_name": doctor_first_name,
                    "doctor_last_name": doctor_last_name,
                    "doctor_experience": doctor_experience,
                    "doctor_about_me": doctor_about,
                    "qualification": qualification_list,
                    "specialization": specialization_list,
                    "doctor_availability": doctor_availability_list
                }
                )
        return doctors_data_list
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"doctor list BL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting doctors list BL")              
    except Exception as e:
        logger.error(f"Unexpected error BL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred BL")

async def health_hub_stacks_bl(subscriber_mysql_session:AsyncSession):
    """
     need to add the hyperlocal search and service provider and doctor
    Business logic to retrieve health hub stacks with doctor specialization details.

    This function interacts with the Data Access Layer (DAL) to fetch specialization data and 
    calculates the number of doctors available for each specialization. It compiles this data 
    into a list of dictionaries containing the specialization ID, name, and doctor count.

    Args:
        subscriber_mysql_session (AsyncSession): An asynchronous database session for interacting 
        with the MySQL database.

    Returns:
        list: A list of dictionaries, where each dictionary includes:
            - specialization_id (str): The ID of the specialization.
            - specialization_name (str): The name of the specialization.
            - no_of_doctor (int): The number of doctors available for this specialization.

    Raises:
        HTTPException: Raised if an HTTP-related error occurs.
        SQLAlchemyError: Raised when a database error occurs while fetching data.
        Exception: Raised for unexpected errors during execution.
    """
    try:
        specialization_data = await health_hub_stacks_dal(subsciber_mysql_session=subscriber_mysql_session)
        doctors=[]
        for specialization in specialization_data:
            no_of_doctor = await get_doctor_by_specialization(subscriber_mysql_session=subscriber_mysql_session, specialization_id=specialization.specialization_id)
            doctors.append({
                "specialization_id": specialization.specialization_id,
                "specialization_name": specialization.specialization_name,
                "doctor_count": len(no_of_doctor) if no_of_doctor else 0
            })
        return doctors
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"health_hub_stacks BL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting health hub stacks BL")
    except Exception as e:
        logger.error(f"Unexpected error BL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred BL")
    
async def specialization_list_bl(specialization_id:str, subscriber_mysql_session:AsyncSession):
    """
    Business logic to retrieve a list of doctors for a specific specialization.

    This function fetches doctors associated with the given specialization ID by interacting with 
    various utility functions and the database. It compiles comprehensive details about each doctor, 
    including their personal information, experience, and qualifications.

    Args:
        specialization_id (str): The ID of the specialization for which to retrieve doctors.
        subscriber_mysql_session (AsyncSession): An asynchronous database session for interacting 
        with the MySQL database.

    Returns:
        list: A list of dictionaries, where each dictionary contains:
            - doctor_id (str): The unique ID of the doctor.
            - doctor_first_name (str): The first name of the doctor.
            - doctor_last_name (str): The last name of the doctor.
            - doctor_experience (int): The years of experience the doctor has.
            - doctor_qualification (list): A list of dictionaries, where each dictionary includes:
                - qualification_id (str): The unique ID of the qualification.
                - qualification_name (str): The name of the qualification.
                - specialization_id (str): The ID of the associated specialization (if any).
                - specialization_name (str): The name of the associated specialization (if any).

    Raises:
        SQLAlchemyError: Raised when a database error occurs while fetching data.
        Exception: Raised for any unexpected errors that may arise during execution.
    """
    try:
        specialization_data = await get_doctor_by_specialization(specialization_id=specialization_id, subscriber_mysql_session=subscriber_mysql_session)
        if not specialization_data:
            raise HTTPException(status_code=404, detail="No doctors found for this specialization")
        doctor_details=[]
        for specialization in specialization_data:
            doctor_id = specialization.doctor_id
            doctor_data = await get_data_by_id_utils(table=Doctor, field="doctor_id", subscriber_mysql_session=subscriber_mysql_session, data=doctor_id)
            doctor_qualification_data = await entity_data_return_utils(table=DoctorQualification, field="doctor_id", subscriber_mysql_session=subscriber_mysql_session, data=doctor_id)
            doctor_qualification=[]
            doctor_specialization=[]
            for qual in doctor_qualification_data:
                doctor_specialization_name = None
                if qual.specialization_id:
                    doctor_specialization_data = await get_data_by_id_utils(table=Specialization, field="specialization_id", subscriber_mysql_session=subscriber_mysql_session, data=qual.specialization_id)
                    doctor_specialization_name = doctor_specialization_data.specialization_name
                qualification_data = await get_data_by_id_utils(table=Qualification, field="qualification_id", subscriber_mysql_session=subscriber_mysql_session, data=qual.qualification_id)
                doctor_qualification_name = qualification_data.qualification_name
                doctor_qualification.append(
                    doctor_qualification_name
                )
                doctor_specialization.append(
                    doctor_specialization_name if doctor_specialization_name!=None else ""
                )
            doctor_details.append({
                "doctor_id": doctor_id,
                "doctor_first_name": doctor_data.first_name,
                "doctor_last_name": doctor_data.last_name,
                "doctor_experience": doctor_data.experience,
                "qualification": doctor_qualification,
                "specialization": doctor_specialization
            })
        return doctor_details
    except SQLAlchemyError as e:
        logger.error(f"specialization_list BL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting specialization list BL")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error BL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred BL")

async def docreq_appointment_bl(doctor_id: str, subscriber_mysql_session: AsyncSession):
    """
    Fetches the availability of a doctor for the next 7 days and returns a structured response
    containing clinic details, available time slots, and booked slots.
    Args:
        doctor_id (str): The unique identifier of the doctor.
        subscriber_mysql_session (AsyncSession): The database session for interacting with the subscriber's MySQL database.
    Returns:
        dict: A dictionary containing the next 7 days as keys, with each day containing clinic details,
              available time slots, and booked slots.
    Raises:
        HTTPException: If no doctor is found with the given ID, or if no availability is found for the doctor.
        HTTPException: If there is an error in fetching data or an unexpected error occurs.
    """
    try:
        # Fetch doctor data
        doctor_data = await get_data_by_id_utils(
            table=Doctor, field="doctor_id", subscriber_mysql_session=subscriber_mysql_session, data=doctor_id
        )
        if not doctor_data:
            raise HTTPException(status_code=404, detail="No doctor found with this ID")

        # Fetch doctor availability
        doctor_availability_data = await doctors_availability_active_helper(
            doctor_id=doctor_id, subscriber_mysql_session=subscriber_mysql_session
        )
        if not doctor_availability_data:
            raise HTTPException(status_code=404, detail="No availability found for this doctor")

        # Generate the next 7 days in "dd-mm-yyyy" format
        today = datetime.today()
        next_7_days = [(today + timedelta(days=i)).strftime("%d-%m-%Y") for i in range(7)]
        date_based_response = {day: {"clinic": []} for day in next_7_days}

        # Time per appointment
        time_per_appointment = doctor_data.avblty

        for avbl in doctor_availability_data:
            # Fetch clinic data
            clinic_data = await clinic_data_active_helper(
                doctor_id=doctor_id, subscriber_mysql_session=subscriber_mysql_session
            )

            for day in next_7_days:
                # Get the day of the week (e.g., "Mon") from the date
                appointment_day = datetime.strptime(day, "%d-%m-%Y").strftime("%a")

                # Check if the appointment day matches the doctor's availability
                if appointment_day not in avbl.days:
                    continue

                # Extract available time slots
                morning_slots = [avbl.morning_slot] if avbl.morning_slot else []
                afternoon_slots = [avbl.afternoon_slot] if avbl.afternoon_slot else []
                evening_slots = [avbl.evening_slot] if avbl.evening_slot else []

                # Merge all slots
                all_slots = morning_slots + afternoon_slots + evening_slots

                # Generate total slots for the clinic based on time_per_appointment
                total_slots = []
                timing = []  # To store the time ranges for the clinic
                for slot in all_slots:
                    if slot and " - " in slot:  # Validate slot format
                        try:
                            start_time, end_time = slot.split(" - ")
                            start_time = datetime.strptime(start_time.strip(), "%I:%M %p")
                            end_time = datetime.strptime(end_time.strip(), "%I:%M %p")
                            timing.append(slot)  # Add the time range to the timing array
                            while start_time < end_time:
                                total_slots.append(start_time.strftime("%I:%M %p"))
                                start_time += timedelta(minutes=time_per_appointment)
                        except ValueError as e:
                            logger.error(f"Invalid slot format: {slot}. Error: {e}")
                            continue

                # Remove booked slots from total slots
                booked_slots = [
                    datetime.strptime(clinic.appointment_time.strftime("%H:%M:%S"), "%H:%M:%S").strftime("%I:%M %p")
                    for clinic in clinic_data
                    if clinic.clinic_name == avbl.clinic_name and clinic.appointment_date.strftime("%d-%m-%Y") == day
                ]
                available_slots = [slot for slot in total_slots if slot not in booked_slots]

                # Handle case where there are no bookings
                if not booked_slots:
                    available_slots = total_slots

                # Append data to the response
                date_based_response[day]["clinic"].append({
                    "name": avbl.clinic_name,
                    "address": avbl.clinic_address,
                    "timing": timing, 
                    "avblslots": available_slots
                })

        return date_based_response

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"docreq_appointment BL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting upcoming appointments BL")
    except Exception as e:
        logger.error(f"Unexpected error BL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred BL")