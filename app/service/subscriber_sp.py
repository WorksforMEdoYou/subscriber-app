import json
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List
from datetime import date, datetime, time, timedelta
from ..models.subscriber import ServiceProvider, ServiceProviderCategory, ServiceSubType, ServiceType, ServiceProviderAppointment, Subscriber, ServicePackage, FamilyMember, Address, VitalsRequest, VitalsTime, VitalFrequency, MedicinePrescribed, Medications, Vitals, Address
from ..schemas.subscriber import SubscriberMessage, CreateServiceProviderAppointment, UpdateServiceProviderAppointment, CancelServiceProviderAppointment, CreateMedicineIntake, CreateNursingParameter, FoodIntake
from ..utils import check_data_exist_utils, id_incrementer, entity_data_return_utils, get_data_by_id_utils, get_data_by_mobile
from ..crud.subscriber_sp import get_hubby_sp_dal, get_sp_provider_helper, create_sp_booking_dal, update_service_provider_booking_dal, cancel_service_provider_booking_dal, upcoming_service_provider_booking_dal, past_service_provider_booking_dal, service_provider_list_for_service_dal, create_vitals_dal, create_vital_time_dal, create_medication_dal, get_nursing_vitals_today_dal, get_nursing_vitals_log_dal

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def get_hubby_sp_bl(subscriber_mysql_session: AsyncSession) -> list:
    """
    Fetches a list of service providers along with their details.

    This function retrieves service provider categories and adds information
    about the count of service providers for each service type.

    Args:
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        list: A list of dictionaries containing details of service types and service provider counts.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related issues during processing.
        Exception: Raised for unexpected errors.
    """
    try:
        hubby_sp_bl = await get_hubby_sp_dal(subscriber_mysql_session=subscriber_mysql_session)
        sp_spl_list = [
            {
                "service_type_id": spl.service_type_id,
                "service_type_name": spl.service_type_name,
                "sp_count": len(await get_sp_provider_helper(
                    service_type_id=spl.service_type_id,
                    subscriber_mysql_session=subscriber_mysql_session
                )),
            } for spl in hubby_sp_bl
        ]
        return sp_spl_list
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while fetching hubby sp: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while fetching hubby sp")
    except Exception as e:
        logger.error(f"Error occurred while fetching hubby sp: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while fetching hubby sp")
   
async def create_sp_booking_bl(
    subscriber_mysql_session: AsyncSession,
    sp_appointment: CreateServiceProviderAppointment
) -> SubscriberMessage:
    """
    Creates a new service provider appointment booking.

    This function validates subscriber data and creates a service provider booking
    with the provided appointment details.

    Args:
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.
        sp_appointment (CreateServiceProviderAppointment): The appointment details for booking creation.

    Returns:
        SubscriberMessage: A message indicating the booking creation status.

    Raises:
        HTTPException: Raised for validation errors or known issues during booking creation.
        SQLAlchemyError: Raised for database-related issues during processing.
        Exception: Raised for unexpected errors.
    """
    async with subscriber_mysql_session.begin():
        try:
            subscriber_data = check_data_exist_utils(
                table=Subscriber,
                field="mobile",
                subscriber_mysql_session=subscriber_mysql_session,
                data=sp_appointment.subscriber_mobile
            )
            if subscriber_data == "unique":
                raise HTTPException(status_code=400, detail="Subscriber mobile number is not unique")

            new_sp_appointment_id = await id_incrementer(
                entity_name="SERVICEPROVIDERAPPOINMENT",
                subscriber_mysql_session=subscriber_mysql_session
            )

            start_date = datetime.strptime(sp_appointment.start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(sp_appointment.end_date, "%Y-%m-%d").date()
            # Validate the time format for start_time and end_time
            start_time = datetime.strptime(sp_appointment.start_time, "%H:%m:%S").time()
            end_time = datetime.strptime(sp_appointment.end_time, "%H:%m:%S").time()
            
            new_sp_appointment = ServiceProviderAppointment(
                sp_appointment_id=new_sp_appointment_id,
                session_time=sp_appointment.session_time,
                start_time=start_time,
                end_time=end_time,
                session_frequency=sp_appointment.session_frequency,
                start_date=start_date,
                end_date=end_date,
                prescription_id=sp_appointment.prescription_id or None,
                status="Listed",
                visittype=sp_appointment.visittype,
                address_id=sp_appointment.address_id or None,
                book_for_id=sp_appointment.book_for_id or None,
                subscriber_id=subscriber_data.subscriber_id,
                sp_id=sp_appointment.sp_id,
                service_package_id=sp_appointment.service_package_id,
                service_subtype_id=sp_appointment.service_subtype_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                active_flag=1
            )

            await create_sp_booking_dal(new_sp_appointment=new_sp_appointment, subscriber_mysql_session=subscriber_mysql_session)
            return SubscriberMessage(message="Service Provider Booking Created Successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error occurred while creating sp booking: {e}")
            raise HTTPException(status_code=500, detail="Error occurred while creating sp booking")
        except Exception as e:
            logger.error(f"Error occurred while creating sp booking: {e}")
            raise HTTPException(status_code=500, detail="Error occurred while creating sp booking")

async def update_service_provider_booking_bl(
    sp_appointment: UpdateServiceProviderAppointment,
    subscriber_mysql_session: AsyncSession
) -> SubscriberMessage:
    """
    Updates an existing service provider booking.

    This function interacts with the Data Access Layer to update the booking
    details for the specified appointment.

    Args:
        sp_appointment (UpdateServiceProviderAppointment): Appointment details for updating the booking.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        SubscriberMessage: A message indicating the booking update status.

    Raises:
        HTTPException: Raised for validation errors or known issues during booking updates.
        SQLAlchemyError: Raised for database-related issues during processing.
        Exception: Raised for unexpected errors.
    """
    async with subscriber_mysql_session.begin():
        try:
            updated_sp_booking = await update_service_provider_booking_dal(
                sp_appointment=sp_appointment,
                subscriber_mysql_session=subscriber_mysql_session
            )
            return SubscriberMessage(message="Service Provider Booking Updated Successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error occurred while updating sp booking: {e}")
            raise HTTPException(status_code=500, detail="Error occurred while updating sp booking")
        except Exception as e:
            logger.error(f"Error occurred while updating sp booking: {e}")
            raise HTTPException(status_code=500, detail="Error occurred while updating sp booking")

async def cancel_service_provider_booking_bl(
    sp_appointment: CancelServiceProviderAppointment,
    subscriber_mysql_session: AsyncSession
) -> SubscriberMessage:
    """
    Cancels an existing service provider booking.

    This function interacts with the Data Access Layer to cancel the booking
    for the specified appointment.

    Args:
        sp_appointment (CancelServiceProviderAppointment): Appointment details for canceling the booking.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        SubscriberMessage: A message indicating the booking cancellation status.

    Raises:
        HTTPException: Raised for validation errors or known issues during booking cancellations.
        SQLAlchemyError: Raised for database-related issues during processing.
        Exception: Raised for unexpected errors.
    """
    async with subscriber_mysql_session.begin():
        try:
            cancel_sp_booking = await cancel_service_provider_booking_dal(
                sp_appointment=sp_appointment,
                subscriber_mysql_session=subscriber_mysql_session
            )
            return SubscriberMessage(message="Service Provider Booking Cancelled Successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error occurred while cancelling sp booking: {e}")
            raise HTTPException(status_code=500, detail="Error occurred while cancelling sp booking")
        except Exception as e:
            logger.error(f"Error occurred while cancelling sp booking: {e}")
            raise HTTPException(status_code=500, detail="Error occurred while cancelling sp booking")

async def upcoming_service_provider_booking_bl(subscriber_mobile:str, subscriber_mysql_session:AsyncSession):
    """
    Fetches the upcoming service provider bookings for a subscriber based on their mobile number.

    This function queries the database using the provided mobile number to retrieve subscriber details
    and fetch their upcoming service provider bookings. It processes the data to generate a detailed
    list of bookings, including information about the service provider, appointment, service subtype,
    and service package.

    Args:
        subscriber_mobile (str): The mobile number of the subscriber.
        subscriber_mysql_session (AsyncSession): The async SQLAlchemy session for database interactions.

    Returns:
        List[dict]: A list of dictionaries containing details of the upcoming service provider bookings.

    Raises:
        HTTPException: If the subscriber is not found, or in case of any errors during the database operation.
        HTTPException: If an unexpected error occurs.

    Note:
        Uses helper functions `get_data_by_mobile`, `upcoming_service_provider_booking_dal`, 
        and `sp_bookings_helper` to retrieve and process booking data.
    """
    async with subscriber_mysql_session.begin():
        try:
            subscriber_data = await get_data_by_mobile(mobile=subscriber_mobile, field="mobile", table=Subscriber, subscriber_mysql_session=subscriber_mysql_session)
            if not subscriber_data:
                raise HTTPException(status_code=404, detail="Subscriber not found")
            upcoming_sp_booking = await upcoming_service_provider_booking_dal(subscriber_id=subscriber_data.subscriber_id, subscriber_mysql_session=subscriber_mysql_session)
        
            upcoming_booking_list = []
            for booking in upcoming_sp_booking:
                service_provider = booking["service_provider"]
                appointment = booking["appointment"]
                service_subtype = booking["service_subtype"]
                service_package = booking["service_package"]
                upcoming_booking_list.append(
                    await sp_bookings_helper(subscriber_data=subscriber_data, service_provider=service_provider, appointment=appointment, service_subtype=service_subtype, service_package=service_package, subscriber_mysql_session=subscriber_mysql_session)
                )
            
            return upcoming_booking_list
        except SQLAlchemyError as e:
            logger.error(f"Error occurred while getting upcoming sp booking: {e}")
            raise HTTPException(status_code=500, detail="Error occurred while getting upcoming sp booking")
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Error occurred while getting upcoming sp booking: {e}")
            raise HTTPException(status_code=500, detail="Error occurred while getting upcoming sp booking")

async def past_service_provider_booking_bl(subscriber_mobile:str, subscriber_mysql_session:AsyncSession):
    """
    Fetches the past service provider bookings for a subscriber based on their mobile number.

    This function queries the database using the provided mobile number to retrieve subscriber details
    and fetch their past service provider bookings. It processes the data to generate a detailed list 
    of bookings, including information about the service provider, appointment, service subtype, and 
    service package.

    Args:
        subscriber_mobile (str): The mobile number of the subscriber.
        subscriber_mysql_session (AsyncSession): The async SQLAlchemy session for database interactions.

    Returns:
        List[dict]: A list of dictionaries containing details of the past service provider bookings.

    Raises:
        HTTPException: If the subscriber is not found, or in case of any errors during the database operation.
        HTTPException: If an unexpected error occurs.

    Note:
        Utilizes helper functions `get_data_by_mobile`, `past_service_provider_booking_dal`, 
        and `sp_bookings_helper` to retrieve and process booking data.
    """

    async with subscriber_mysql_session.begin():
        try:
            subscriber_data = await get_data_by_mobile(mobile=subscriber_mobile, field="mobile", table=Subscriber, subscriber_mysql_session=subscriber_mysql_session)
            if not subscriber_data:
                raise HTTPException(status_code=404, detail="Subscriber not found")
            past_sp_booking = await past_service_provider_booking_dal(subscriber_id=subscriber_data.subscriber_id, subscriber_mysql_session=subscriber_mysql_session)
        
            past_booking_list = []
            for booking in past_sp_booking:
                service_provider = booking["service_provider"]
                appointment = booking["appointment"]
                service_subtype = booking["service_subtype"]
                service_package = booking["service_package"]
                past_booking_list.append(
                    await sp_bookings_helper(subscriber_data=subscriber_data, service_provider=service_provider, appointment=appointment, service_subtype=service_subtype, service_package=service_package, subscriber_mysql_session=subscriber_mysql_session)
                )
            
            return past_booking_list
        except SQLAlchemyError as e:
            logger.error(f"Error occurred while getting past sp booking: {e}")
            raise HTTPException(status_code=500, detail="Error occurred while getting past sp booking")
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Error occurred while getting past sp booking: {e}")
            raise HTTPException(status_code=500, detail="Error occurred while getting past sp booking")
                                                              
async def sp_bookings_helper(subscriber_data, service_provider, appointment, service_subtype, service_package, subscriber_mysql_session:AsyncSession):
    """
    Generates a detailed dictionary containing service provider booking information for a subscriber.

    This function processes the provided subscriber, service provider, appointment, service subtype, 
    and service package data to create a comprehensive booking object. It includes details such as 
    the subscriber's and service provider's information, service package details, appointment subtype 
    data, and address details for home visits.

    Args:
        subscriber_data: The data of the subscriber requesting the booking details.
        service_provider: The service provider's details involved in the booking.
        appointment: The appointment details for the booking.
        service_subtype: The subtype of the service related to the booking.
        service_package: The service package details included in the booking.
        subscriber_mysql_session (AsyncSession): The async SQLAlchemy session for database operations.

    Returns:
        dict: A dictionary containing detailed information about the service provider booking, including
          subscriber details, service provider details, service package information, appointment 
          subtype data, and address (if applicable).

    Raises:
        HTTPException: If any errors occur during database operations or other unexpected issues arise.

    Note:
        Utilizes helper functions such as `get_data_by_id_utils` and `subtype_helper` for fetching related 
        data from the database. Handles SQLAlchemy and general exceptions to log errors and raise appropriate HTTP exceptions.
    """
    try:
        book_for_id = appointment.get("book_for_id") if appointment.get("book_for_id")!=None else None
        #book_for_data
        if book_for_id!=None:
            book_for_data = await get_data_by_id_utils(table=FamilyMember, field="familymember_id", subscriber_mysql_session=subscriber_mysql_session, data=book_for_id)
        
        #package
        package_data = await get_data_by_id_utils(table=ServicePackage, field="service_package_id", subscriber_mysql_session=subscriber_mysql_session, data=appointment.get("service_package_id"))
        service_package_data = {
            "service_package_id": package_data.service_package_id,
            "session_time": package_data.session_time,
            "session_frequency": package_data.session_frequency,
            "rate": package_data.rate,
            "discount": package_data.discount,
            "service_provided": await subtype_helper(service_subtype_id=package_data.service_subtype_id, subscriber_mysql_session=subscriber_mysql_session)
        }
        
        #appointment subtype
        appointment_subtype_data = {
            "appointment_subtype_data": await subtype_helper(service_subtype_id=appointment.get("service_subtype_id"), subscriber_mysql_session=subscriber_mysql_session)
        }
        
        subscriber_address = None
        if appointment.get("visittype")=="Home Visit":
            subscriber_address_data = await get_data_by_id_utils(table=Address, field="address_id", subscriber_mysql_session=subscriber_mysql_session, data=appointment.get("address_id"))
            subscriber_address = {
                "address_id": subscriber_address_data.address_id,
                "address": subscriber_address_data.address,
                "city": subscriber_address_data.city,
                "state": subscriber_address_data.state,
                "pincode": subscriber_address_data.pincode,
                "landmark": subscriber_address_data.landmark,
                "state": subscriber_address_data.state,
                "geolocation": subscriber_address_data.geolocation
            }
        
        sp_bookings = {
            "sp_appointment_id": appointment.get("sp_appointment_id"),
            "session_time": appointment.get("session_time"),
            "start_time": appointment.get("start_time"),
            "end_time": appointment.get("end_time"),
            "session_frequency": appointment.get("session_frequency"),
            "start_date": datetime.strptime(appointment.get("start_date"), "%Y-%m-%d").strftime("%d-%m-%Y") if appointment.get("start_date") else None,
            "end_date": datetime.strptime(appointment.get("end_date"), "%Y-%m-%d").strftime("%d-%m-%Y") if appointment.get("end_date") else None,
            "prescription_id": appointment.get("prescription_id"),
            "status": appointment.get("status"),
            "visittype": appointment.get("visittype"),
            "book_for_id": book_for_data.familymember_id if book_for_id != None else None,
            "book_for_name": book_for_data.name if book_for_data != None else None,
            "book_for_mobile": book_for_data.mobile_number if book_for_data != None else None,
            "subscriber_id": subscriber_data.subscriber_id,
            "subscriber_first_name": subscriber_data.first_name,
            "subscriber_last_name": subscriber_data.last_name,
            "subscriber_mobile": subscriber_data.mobile,
            "subscriber_address": subscriber_address,
            "sp_id": service_provider.get("sp_id"),
            "sp_first_name": service_provider.get("sp_firstname"),
            "sp_last_name": service_provider.get("sp_lastname"),
            "sp_mobilenumber": service_provider.get("sp_mobilenumber"),
            "sp_address": service_provider.get("sp_address") if appointment.get("visittype") != "Home Visit" else None,
            "service_package": service_package_data,
            "service_subtype": appointment_subtype_data
        }
        return sp_bookings
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while getting sp booking: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while getting sp booking")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error occurred while getting sp booking: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while getting sp booking")

async def subtype_helper(service_subtype_id:str, subscriber_mysql_session:AsyncSession):
    """
    Fetches and organizes service subtype details based on the given service subtype ID.

    This function retrieves service subtype data, along with related service type and service 
    category details, from the database. It returns the data in a structured dictionary format, 
    which includes subtype ID, subtype name, type ID, type name, category ID, and category name.

    Args:
        service_subtype_id (str): The ID of the service subtype to be fetched.
        subscriber_mysql_session (AsyncSession): The async SQLAlchemy session for database operations.

    Returns:
        dict: A dictionary containing the service subtype data, including its name, associated service type, 
          and category details.

    Raises:
        HTTPException: If any errors occur during the database operations or other unexpected issues arise.

    Note:
        This function uses the `get_data_by_id_utils` helper function to fetch details for the service 
        subtype, service type, and service category from the database. Handles SQLAlchemy and general 
        exceptions, logging any errors and raising appropriate HTTP exceptions.
    """

    try:
        subtype_data = await get_data_by_id_utils(table=ServiceSubType, field="service_subtype_id", subscriber_mysql_session=subscriber_mysql_session, data=service_subtype_id)
        service_type_data = await get_data_by_id_utils(table=ServiceType, field="service_type_id", subscriber_mysql_session=subscriber_mysql_session, data=subtype_data.service_type_id)
        service_category = await get_data_by_id_utils(table=ServiceProviderCategory, field="service_category_id", subscriber_mysql_session=subscriber_mysql_session, data=service_type_data.service_category_id)
        
        return {
            "subtype_id": subtype_data.service_subtype_id,
            "service_subtype_name": subtype_data.service_subtype_name,
            "service_type_id": service_type_data.service_type_id,
            "service_type_name": service_type_data.service_type_name,
            "service_category_id": service_category.service_category_id,
            "service_category_name": service_category.service_category_name
        }
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while getting service subtype data: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while getting service subtype data")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error occurred while getting service subtype data: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while getting service subtype data")
        
async def service_provider_list_for_service_bl(service_subtype_id: str, subscriber_mysql_session: AsyncSession):
    """
    Fetches a list of service providers offering services of a specific subtype.

    This function retrieves service package data for a given service subtype ID from the database and 
    constructs a detailed list of service providers. The data includes service provider details, service 
    category, service type, service subtype, and service package information, all organized into 
    structured dictionaries.

    Args:
        service_subtype_id (str): The ID of the service subtype for which service providers are to be fetched.
        subscriber_mysql_session (AsyncSession): The async SQLAlchemy session for database operations.

    Returns:
        List[dict]: A list of dictionaries containing comprehensive details about service providers, their services, 
                packages, and related data.

    Raises:
        HTTPException: If any errors occur during the database operations or in case of unexpected issues.

    Note:
        Utilizes the `service_provider_list_for_service_dal` function to fetch raw service package data and 
        processes it to generate a structured list. Handles SQLAlchemy and generic exceptions, logging errors 
        and raising appropriate HTTP exceptions.
    """
    try:
        # Fetch service package data
        service_package_data = await service_provider_list_for_service_dal(
            service_subtype_id=service_subtype_id, subscriber_mysql_session=subscriber_mysql_session
        )
        service_provider_list = []
        for sp in service_package_data:
            service_provider = sp["service_provider"]
            service_provider_category = sp["service_provider_category"]
            service_type = sp["service_type"]
            service_subtype = sp["service_subtype"]
            service_package = sp["service_package"]
            service_provider_list.append({
                "sp_id": service_provider.get("sp_id"),
                "sp_firstname": service_provider.get("sp_firstname"),
                "sp_lastname": service_provider.get("sp_lastname"),
                "sp_mobilenumber": service_provider.get("sp_mobilenumber"),
                "sp_email": service_provider.get("sp_email"),
                "sp_geolocation": service_provider.get("sp_geolocation"),
                "agency": service_provider.get("agency"),
                "sp_address": service_provider.get("sp_address"),
                "geolocation": service_provider.get("geolocation"),
                "service_category_id": service_provider_category.get("service_category_id"),
                "service_category_name": service_provider_category.get("service_category_name"),
                "service_type_id": service_type.get("service_type_id"),
                "service_type_name": service_type.get("service_type_name"),
                "service_subtype_name": service_subtype.get("service_subtype_name"),
                "service_subtype_id": service_subtype.get("service_subtype_id"),
                "service_package_id": service_package.get("service_package_id"),
                "session_time": service_package.get("session_time"),
                "session_frequency": service_package.get("session_frequency"),
                "discount": service_package.get("discount"),
                "visittype": service_package.get("visittype"),
                "rate": service_package.get("rate")
            })
        return service_provider_list
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while getting service provider list for service: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while getting service provider list for service")
    except Exception as e:
        logger.error(f"Error occurred while getting service provider list for service: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while getting service provider list for service")

async def create_nursing_vitals_bl(nursing_vitals:CreateNursingParameter,subscriber_mysql_session:AsyncSession):
    """
    Creates nursing vitals based on the provided parameters.

    This function processes nursing vitals data by retrieving the relevant service provider appointment details, 
    determining frequency times, and generating vitals data with timestamps. It ensures that all nursing 
    vitals are accurately recorded with their corresponding frequency times.

    Args:
        nursing_vitals (CreateNursingParameter): An object containing details about the nursing vitals, 
            including appointment ID, frequency ID, and vitals ID.
        subscriber_mysql_session (AsyncSession): The async SQLAlchemy session for database operations.

    Returns:
        SubscriberMessage: A message confirming the successful creation of nursing vitals.

    Raises:
        HTTPException: If any errors occur during the database operations or other unexpected issues.

    Note:
        Uses helper functions such as `get_data_by_id_utils`, `frequency_time_helper`, `vitals_request_helper`, 
        `create_vitals_dal`, `vitals_time_helper`, and `create_vital_time_dal` to fetch and create vitals data. 
        Handles SQLAlchemy and general exceptions to log errors and raise appropriate HTTP exceptions.
    """

    async with subscriber_mysql_session.begin():
        try:
            # service provider appointment data
            sp_appointment_data = await get_data_by_id_utils(
                table=ServiceProviderAppointment,
                field="sp_appointment_id",
                subscriber_mysql_session=subscriber_mysql_session,
                data=nursing_vitals.sp_appointment_id
            )
            
            frequency_time = await frequency_time_helper(
                service_start_time=sp_appointment_data.start_time,
                service_end_time=sp_appointment_data.end_time,
                session_frequency_id=nursing_vitals.vitals_frequency_id,
                subscriber_mysql_session=subscriber_mysql_session
            )
            
            #for vital in nursing_vitals.vitals_id:
            vitals_requested = await vitals_request_helper(nursing_vitals=nursing_vitals, vital=nursing_vitals.vitals_id)
            vitals_created = await create_vitals_dal(vitals_request=vitals_requested, subscriber_mysql_session=subscriber_mysql_session)
            for time in frequency_time:
                # create nursing parameter data
                #vitals_requested = await vitals_request_helper(nursing_vitals=nursing_vitals, vital=nursing_vitals.vitals_id)
                #vitals_created = await create_vitals_dal(vitals_request=vitals_requested, subscriber_mysql_session=subscriber_mysql_session)
                vitals_time = await vitals_time_helper(vitals_request_id=vitals_created.vitals_request_id, vital_time=time)
                await create_vital_time_dal(vital_time=vitals_time, subscriber_mysql_session=subscriber_mysql_session)
                
            return SubscriberMessage(message="Nursing vitals created successfully")
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error occurred while getting service provider appointment data: {e}")
            raise HTTPException(status_code=500, detail="Error occurred while getting service provider appointment data")
        except Exception as e:
            logger.error(f"Error occurred while getting service provider appointment data: {e}")
            raise HTTPException(status_code=500, detail="Error occurred while getting service provider appointment data")

async def vitals_request_helper(nursing_vitals:CreateNursingParameter, vital):
    """
    Creates a VitalsRequest object based on the provided nursing vitals and vital data.

    This function initializes and returns a VitalsRequest object using the provided appointment ID, 
    vitals data, and timestamps. It also marks the active flag as true (1).

    Args:
        nursing_vitals (CreateNursingParameter): An object containing nursing vitals data, including 
            the service provider appointment ID.
        vital: The specific vital data to be included in the request.

    Returns:
        VitalsRequest: The created VitalsRequest object containing the appointment ID, vital data, 
                   timestamps, and active flag.

    Raises:
        HTTPException: If any unexpected errors occur during the creation of the VitalsRequest object.
    """

    try:
        vital_value = ",".join(str(item) for item in vital)
        vitals = VitalsRequest(
            appointment_id = nursing_vitals.sp_appointment_id,
            vitals_requested = vital_value,
            vital_frequency_id = nursing_vitals.vitals_frequency_id,
            created_at = datetime.now(),
            updated_at = datetime.now(),
            active_flag = 1
        )
        return vitals
    except Exception as e:
        logger.error(f"Error occurred while getting vitals request: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while getting vitals request")

async def vitals_time_helper(vitals_request_id, vital_time):
    """
    Creates a VitalsTime object based on the provided request ID and time.

    This function initializes and returns a VitalsTime object, setting the vitals request ID, 
    vital time, creation timestamp, update timestamp, and marking the active flag as true (1).

    Args:
        vitals_request_id: The ID of the vitals request for which the time entry is being created.
        vital_time: The specific time associated with the vitals entry.

    Returns:
        VitalsTime: The created VitalsTime object containing the request ID, vital time, timestamps, 
                and active flag.

    Raises:
        HTTPException: If an unexpected error occurs during the creation of the VitalsTime object.
    """

    try:
        vital_time = VitalsTime(
            vitals_request_id = vitals_request_id,
            vital_time = vital_time,
            created_at = datetime.now(),
            updated_at = datetime.now(),
            active_flag = 1
        )
        return vital_time
    except Exception as e:
        logger.error(f"Error occurred while getting vitals time: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while getting vitals time")

async def frequency_time_helper(service_start_time, service_end_time, session_frequency_id, subscriber_mysql_session:AsyncSession):
    """
    Generates a list of frequency times for a session based on the session frequency.

    This function calculates specific times for a session based on its start and end times, as well as the 
    session frequency ID. It supports multiple frequency types, including "Twice in a session," 
    "Every two hours," "Every one hour," and "Twice a day." The frequency times are returned as a 
    list of strings formatted in "HH:MM:SS."

    Args:
        service_start_time (str): The start time of the service session, formatted as "HH:MM:SS."
        service_end_time (str): The end time of the service session, formatted as "HH:MM:SS."
        session_frequency_id: The ID of the session frequency to determine the frequency of time intervals.
        subscriber_mysql_session (AsyncSession): The async SQLAlchemy session for database operations.

    Returns:
        List[str]: A list of frequency times formatted as "HH:MM:SS."

    Raises:
        HTTPException: If an error occurs during the retrieval of session frequency data or any other unexpected issue.

    Note:
        - Utilizes `get_data_by_id_utils` to fetch session frequency data from the database.
        - Handles different session frequency options and computes the corresponding times.
        - Logs errors and raises HTTP exceptions for unhandled issues.
    """

    try:
        # get data from the vitalFrequency
        frequency = await get_data_by_id_utils(table=VitalFrequency, field="vital_frequency_id", subscriber_mysql_session=subscriber_mysql_session, data=session_frequency_id)
        session_frequency = frequency.session_frequency
        # Convert string times to datetime objects
        service_start_time = datetime.strptime(service_start_time, "%H:%M:%S")
        service_end_time = datetime.strptime(service_end_time, "%H:%M:%S")
    
        # Calculate the time difference between service start time and service end time
        total_time_hours = (service_end_time - service_start_time).total_seconds() / 3600
    
        # The frequency session logic
        frequency_time = []
        if session_frequency == "Twice in a session":
            frequency_time.append(service_start_time)
            frequency_time.append(service_end_time)
        elif session_frequency == "Every two hours":
            for i in range(0, int(total_time_hours) + 1, 2):
                current_time = service_start_time + timedelta(hours=i)
                if current_time <= service_end_time:
                    frequency_time.append(current_time)
        elif session_frequency == "Every one hour":
            for i in range(0, int(total_time_hours) + 1, 1):
                current_time = service_start_time + timedelta(hours=i)
                if current_time <= service_end_time:
                    frequency_time.append(current_time)
        elif session_frequency == "Twice a day":
            if (service_end_time - service_start_time).total_seconds() == 0:
                frequency_time.append(service_start_time)
                mid_time = service_start_time + timedelta(hours=12)
                frequency_time.append(mid_time)
                frequency_time.append(service_end_time)
            else:
                frequency_time.append(service_start_time)
                frequency_time.append(service_end_time)
        return [time.strftime("%H:%M:%S") for time in frequency_time]
    except Exception as e:
        logger.error(f"Error occurred while getting frequency time: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while getting frequency time")

async def create_nursing_medication_bl(nursing_medication:CreateMedicineIntake, subscriber_mysql_session: AsyncSession):
    """
    Create a nursing medication Business Logic (BL) entry based on provided attributes.

    Args:
        nursing_medication (CreateMedicineIntake): Object containing medication details including prescription ID, medicines list, and food intake timings.
        subscriber_mysql_session (AsyncSession): Database session used for executing queries.

    Returns:
        SubscriberMessage: A message confirming successful creation of nursing medication.

    Raises:
        HTTPException: If required fields are missing, a database error occurs, or any other error arises during execution.
    """
    async with subscriber_mysql_session.begin():
        try:
            # validate wether the medicine list is present or the prescription id is present 
            if nursing_medication.medicines_list==None and nursing_medication.prescription_id==None:
                raise HTTPException(status_code=400, detail="Either medicines list or prescription id must be present")
            # get the spappointment_data
            sp_appointment_data = await get_data_by_id_utils(table=ServiceProviderAppointment, field="sp_appointment_id", subscriber_mysql_session=subscriber_mysql_session, data=nursing_medication.sp_appointment_id)
            # medicine prescibed
            if nursing_medication.prescription_id!=None:
                medicine_prescibed = await entity_data_return_utils(table=MedicinePrescribed, field="prescription_id", subscriber_mysql_session=subscriber_mysql_session, data=nursing_medication.prescription_id)
                for item in medicine_prescibed:
                    medicines = await get_medication_schedule(medicine_name=item.medicine_name, dosage_timing=item.dosage_timing, medication_timing=item.medication_timing, food_timing=nursing_medication.food_intake_timing)
                    for med in medicines:
                        medications = await medications_helper(appointment_id=sp_appointment_data.sp_appointment_id, medicine_name=med.get("medicine_name"), quantity=med.get("quantity"), dosage_timing=med.get("dosage_timing"), prescription_id=nursing_medication.prescription_id, medication_timing=med.get("medication_timing"), intake_timing=med.get("intake_timing"))
                        await create_medication_dal(medication=medications, subscriber_mysql_session=subscriber_mysql_session)
            # medicine list
            if nursing_medication.medicines_list!=None:
                prescription_id = nursing_medication.prescription_id if nursing_medication.prescription_id!=None else None
                for item in nursing_medication.medicines_list:
                    medicines = await get_medication_schedule(medicine_name=item.medicine_name, dosage_timing=item.dosage_timing, medication_timing=item.medication_timing, food_timing=nursing_medication.food_intake_timing)
                    for med in medicines:
                        medications = await medications_helper(appointment_id=sp_appointment_data.sp_appointment_id, medicine_name=med.get("medicine_name"), quantity=med.get("quantity"), dosage_timing=med.get("dosage_timing"), prescription_id=prescription_id, medication_timing=med.get("medication_timing"), intake_timing=med.get("intake_timing"))
                        await create_medication_dal(medication=medications, subscriber_mysql_session=subscriber_mysql_session)
            return SubscriberMessage(message="Nursing medication created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error occurred while creating nursing medication BL: {e}")
            raise HTTPException(status_code=500, detail="Error occurred while creating nursing medication BL")
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Error occurred while creating nursing medication BL: {e}")
            raise HTTPException(status_code=500, detail="Error occurred while creating nursing medication BL")

async def medications_helper(appointment_id, medicine_name, quantity, dosage_timing, prescription_id, medication_timing, intake_timing):
    """
    Create a medication object based on provided attributes.

    Args:
        appointment_id (str): Unique identifier for the appointment associated with the medication.
        medicine_name (str): Name of the medication.
        quantity (int): Quantity of medication to be taken.
        dosage_timing (str): Timing of medication intake relative to food ('Before Food' or 'After Food').
        prescription_id (str): Unique identifier for the prescription associated with the medication.
        medication_timing (str): Timing of medication doses during the day (e.g., morning, afternoon, etc.).
        intake_timing (str): Time of medication intake.

    Returns:
        Medications: A medication object containing all the provided details, including creation and update timestamps.

    Raises:
        HTTPException: If an error occurs during the creation of the medication object.
    """
    try:
        medication = Medications(
            appointment_id=appointment_id,
            medicine_name=medicine_name,
            quantity=quantity,
            dosage_timing=dosage_timing,
            prescription_id=prescription_id,
            medication_timing=medication_timing,
            intake_timing=intake_timing,
            created_at = datetime.now(),
            updated_at = datetime.now(),
            active_flag = 1
        )
        return medication
    except Exception as e:
        logger.error(f"Error occurred while creating medication: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while creating medication")

async def get_medication_schedule(medicine_name, dosage_timing, medication_timing, food_timing):
    """
    Get a medication schedule based on the provided medicine details and timings.

    Args:
        medicine_name (str): Name of the medication.
        dosage_timing (str): Timing of medication intake relative to food ('Before Food' or 'After Food').
        medication_timing (str): String denoting medication quantities in the format 'X-Y-Z-W' 
            where each part corresponds to doses for morning, afternoon, evening, and dinner.
        food_timing (dict): Dictionary where keys are meal times 
            ('morning', 'afternoon', 'evening', 'dinner') and values are meal times in 
            the '%I:%M %p' format.

    Returns:
        list[dict]: A list of dictionaries, each containing:
            - "medicine_name" (str): The name of the medication.
            - "dosage_timing" (str): Timing relative to food.
            - "medication_timing" (str): Time of day ('morning', 'afternoon', etc.).
            - "quantity" (int): Quantity of medication to be taken.
            - "intake_timing" (str): Calculated time of medication intake in '%H:%M:%S' format.

    Raises:
        HTTPException: If an error occurs during the generation of the schedule.
    """
    try:
        times_of_day = ["morning", "afternoon", "evening", "dinner"]
        med_quantities = medication_timing.split('-')
    
        # Convert all food timings to datetime.time objects
        parsed_food_timing = {}
        for key, time_str in food_timing:#.items
            parsed_time = datetime.strptime(time_str, "%I:%M %p")
            parsed_food_timing[key] = parsed_time
    
        # Prepare output
        result = []
        for index, quantity_str in enumerate(med_quantities):
            quantity = int(quantity_str)
            if quantity == 0:
                continue  # Skip if no dose at this time
            
            time_key = times_of_day[index]
            food_time = parsed_food_timing[time_key]
            
            # Apply 15 minutes before/after logic
            if dosage_timing == "Before Food":
                intake_time = food_time - timedelta(minutes=15)
            else:  # After Food
                intake_time = food_time + timedelta(minutes=15)
            
            intake_str = intake_time.strftime("%H:%M:%S")
            
            result.append({
                "medicine_name": medicine_name,
                "dosage_timing": dosage_timing,
                "medication_timing": time_key,
                "quantity": quantity,
                "intake_timing": intake_str
            })
    
        return result
    except Exception as e:
        logger.error(f"Error occurred while getting medication schedule: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while getting medication schedule")

def format_time(value):
    """
    Format a time value into a 12-hour clock string with AM/PM.

    Accepts a string in the format "HH:MM:SS" or a `datetime.time` object and 
    converts it to a string in the format "HH:MM AM/PM".

    Args:
        value (str | time): The time value to format.

    Returns:
        str | None: Formatted time string, or None if input is invalid or unparseable.
    """
    if not value:
        return None
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, "%H:%M:%S").time()
        except ValueError:
            return None
    if isinstance(value, time):
        return value.strftime("%I:%M %p")
    return None

def format_date(value):
    """
    Format a date value into a day-month-year string.

    Accepts a string in the format "YYYY-MM-DD" or a `datetime.date` object and 
    converts it to a string in the format "DD-MM-YYYY".

    Args:
        value (str | date): The date value to format.

    Returns:
        str | None: Formatted date string, or None if input is invalid or unparseable.
    """
    if not value:
        return None
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return None
    if isinstance(value, date):
        return value.strftime("%d-%m-%Y")
    return None

async def get_nursing_vitals_today_bl(sp_appointment_id: str, subscriber_mysql_session):
    """
    Retrieves and processes today's nursing vitals data for a given service provider appointment.

    This function collects detailed information about a subscriber's appointment, the requested vitals,
    family member (if applicable), associated address, service provider details, service package, 
    and vitals monitoring logs. It formats all necessary time and date fields and transforms vitals logs 
    to use human-readable vital names.

    Args:
        sp_appointment_id (str): The ID of the service provider's appointment.
        subscriber_mysql_session (AsyncSession): The async SQLAlchemy session for querying subscriber data.

    Returns:
        List[Dict]: A list of dictionaries where each dictionary contains detailed and structured information 
        about the vitals monitored during the appointment, including:
            - Appointment and session timing details
            - Family member/subscriber info
            - Service provider and service package info
            - Requested vitals and their frequency
            - Address and geolocation details
            - Logged vitals data with readable vital names
            - Timing for scheduled vital checks

    Raises:
        HTTPException: If a known HTTP error occurs during data fetching.
        SQLAlchemyError: If a database-related error is encountered.
        Exception: For any other unexpected errors, with logging and a generic HTTP 500 response.
    """
    try:
        vitals = await get_nursing_vitals_today_dal(
            sp_appointment_id=sp_appointment_id,
            subscriber_mysql_session=subscriber_mysql_session
        )

        vitals_monitored = []

        for vital in vitals:
            sp_appointment = vital.get("appointment", {})
            service_provider = vital.get("service_provider", {})
            vitals_request = vital.get("vitals_request", {})
            vital_frequency = vital.get("vital_frequency", {})
            service_package = vital.get("service_package", {})
            vitals_logs = vital.get("vitals_logs", []) 
            subscriber = vital.get("subscriber", {})
            vital_time = vital.get("vitals_times", [])
            
            family_member_data = None
            if sp_appointment.get("book_for_id") is not None:
                family_member = await get_data_by_id_utils(
                    table=FamilyMember,
                    field="familymember_id",
                    subscriber_mysql_session=subscriber_mysql_session,
                    data=sp_appointment.get("book_for_id")
                )
                family_member_data = {
                    "familymember_id": family_member.familymember_id,
                    "familymember_name": family_member.name,
                    "familymember_mobile": family_member.mobile_number,
                    "familymember_gender": family_member.gender,
                    "familymember_dob": family_member.dob,
                    "familymember_age": family_member.age,
                    "familymember_blood_group": family_member.blood_group,
                    "familymember_relationship": family_member.relation
                }

            address = None
            if sp_appointment.get("address_id") is not None:
                address_obj = await get_data_by_id_utils(
                    table=Address,
                    field="address_id",
                    subscriber_mysql_session=subscriber_mysql_session,
                    data=sp_appointment.get("address_id")
                )
                address = {
                    "address_id": address_obj.address_id,
                    "address": address_obj.address,
                    "landmark": address_obj.landmark,
                    "pincode": address_obj.pincode,
                    "city": address_obj.city,
                    "state": address_obj.state,
                    "geolocation": address_obj.geolocation
                }

            vital_requested = []
            for request in vitals_request.get("vitals_requested", "").split(","):
                if request.strip().isdigit():
                    result = await get_data_by_id_utils(
                        table=Vitals,
                        field="vitals_id",
                        subscriber_mysql_session=subscriber_mysql_session,
                        data=int(request)
                    )
                    vital_requested.append(result.vitals_name)

            vitals_monitored.append(
                await vitals_monitored_helper(
                    sp_appointment, service_provider, vitals_request, vital_frequency, service_package, subscriber, family_member_data, address, vital_requested, vitals_logs, vital_time, subscriber_mysql_session
                )
            )

        return vitals_monitored

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while getting nursing vitals today BL: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while getting nursing vitals today")
    except Exception as e:
        logger.error(f"Unexpected error occurred while getting nursing vitals today BL: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while getting nursing vitals today")

async def get_nursing_vitals_log_bl(sp_appointment_id, subscriber_mysql_session:AsyncSession):
    """
    Business logic to retrieve and format nursing vitals log for a specific service provider appointment.

    This function coordinates the retrieval of vitals monitoring data, including associated appointment, 
    subscriber, family member, address, requested vitals, and service details. It transforms the raw 
    data into a structured format suitable for API responses.

    Args:
        sp_appointment_id (str): Unique identifier for the subscriber's service provider appointment.
        subscriber_mysql_session (AsyncSession): Async SQLAlchemy session for interacting with 
                                                 the subscriber database.

    Returns:
        List[Dict]: A list of structured nursing vitals logs, each entry including:
            - Appointment and provider details
            - Requested and logged vitals data
            - Vitals monitoring frequency and timing
            - Subscriber or family member information
            - Address where service was delivered

    Raises:
        HTTPException: If a business logic or data access issue occurs.
        SQLAlchemyError: If there is an error during database operations.
        Exception: For any other unexpected errors.
    """
    try:
        vitals = await get_nursing_vitals_log_dal(
            sp_appointment_id=sp_appointment_id,
            subscriber_mysql_session=subscriber_mysql_session
        )

        vitals_monitored = []

        for vital in vitals:
            sp_appointment = vital.get("appointment", {})
            service_provider = vital.get("service_provider", {})
            vitals_request = vital.get("vitals_request", {})
            vital_frequency = vital.get("vital_frequency", {})
            service_package = vital.get("service_package", {})
            vitals_logs = vital.get("vitals_logs", []) 
            subscriber = vital.get("subscriber", {})
            vital_time = vital.get("vitals_times", [])
            
            family_member_data = None
            if sp_appointment.get("book_for_id") is not None:
                family_member = await get_data_by_id_utils(
                    table=FamilyMember,
                    field="familymember_id",
                    subscriber_mysql_session=subscriber_mysql_session,
                    data=sp_appointment.get("book_for_id")
                )
                family_member_data = {
                    "familymember_id": family_member.familymember_id,
                    "familymember_name": family_member.name,
                    "familymember_mobile": family_member.mobile_number,
                    "familymember_gender": family_member.gender,
                    "familymember_dob": family_member.dob,
                    "familymember_age": family_member.age,
                    "familymember_blood_group": family_member.blood_group,
                    "familymember_relationship": family_member.relation
                }
            address = None
            if sp_appointment.get("address_id") is not None:
                address_obj = await get_data_by_id_utils(
                    table=Address,
                    field="address_id",
                    subscriber_mysql_session=subscriber_mysql_session,
                    data=sp_appointment.get("address_id")
                )
                address = {
                    "address_id": address_obj.address_id,
                    "address": address_obj.address,
                    "landmark": address_obj.landmark,
                    "pincode": address_obj.pincode,
                    "city": address_obj.city,
                    "state": address_obj.state,
                    "geolocation": address_obj.geolocation
                }
            vital_requested = []
            for request in vitals_request.get("vitals_requested", "").split(","):
                if request.strip().isdigit():
                    result = await get_data_by_id_utils(
                        table=Vitals,
                        field="vitals_id",
                        subscriber_mysql_session=subscriber_mysql_session,
                        data=int(request)
                    )
                    vital_requested.append(result.vitals_name)

            vitals_monitored.append(
                await vitals_monitored_helper(
                    sp_appointment, service_provider, vitals_request, vital_frequency, service_package, subscriber, family_member_data, address, vital_requested, vitals_logs, vital_time, subscriber_mysql_session
                )
            )
        return vitals_monitored
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while getting nursing vitals log BL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while getting nursing vitals log")
    except Exception as e:
        logger.error(f"Error occurred while getting nursing vitals log BL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while getting nursing vitals log")

async def process_vitals_logs(vitals_logs, subscriber_mysql_session):
    """
    Processes raw vitals logs by resolving vital IDs to their names and formatting timestamps.

    This function transforms each log's `vital_log` field (stored as a JSON string) by converting
    vital IDs into human-readable vital names using the `Vitals` table. It also formats the 
    timestamp fields (`vitals_on`) into user-friendly date and time formats.

    Args:
        vitals_logs (List[Dict]): List of vitals log entries, each containing a `vital_log` JSON string,
                                  appointment ID, timestamp (`vitals_on`), and vitals log ID.
        subscriber_mysql_session (AsyncSession): Async SQLAlchemy session used to query the `Vitals` table.

    Returns:
        List[Dict]: A list of processed vitals logs, each with:
            - `vital_log`: Dictionary with vital names as keys and their values
            - `appointment_id`: ID of the appointment
            - `vital_reported_date`: Formatted date (e.g., '21-04-2025')
            - `vital_reported_time`: Formatted time (e.g., '03:15 PM')
            - `vitals_log_id`: ID of the vitals log entry

    Raises:
        HTTPException: If any unexpected error occurs during processing.
    """
    try:
        processed_logs = []
        for log in vitals_logs:
            vital_log_dict = json.loads(log["vital_log"])
            updated_vital_log = {}

            for key, value in vital_log_dict.items():
                result = await get_data_by_id_utils(
                    table=Vitals,
                    field="vitals_id",
                    subscriber_mysql_session=subscriber_mysql_session,
                    data=int(key)
                )
                new_key = result.vitals_name if result else key
                updated_vital_log[new_key] = value

            vitals_on = log.get("vitals_on")
            if isinstance(vitals_on, str):
                vitals_on = datetime.strptime(vitals_on, "%Y-%m-%dT%H:%M:%S")

            processed_log = {
                "vital_log": updated_vital_log,
                "appointment_id": log["appointment_id"],
                "vital_reported_date": format_date(vitals_on),
                "vital_reported_time": format_time(vitals_on.time()) if vitals_on else None,
                "vitals_log_id": log["vitals_log_id"]
            }
            processed_logs.append(processed_log)
        return processed_logs
    except Exception as e:
        logger.error(f"Error occurred while processing vitals logs: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while processing vitals logs")

async def process_vital_time(vital_time):
    """
    Process a list of vital time objects and format the time field.

    Each item in the input list is expected to be a dictionary containing 
    'vitals_request_id', 'vital_time', and 'vitals_time_id'. The function formats 
    the 'vital_time' using the `format_time` function and returns a list of 
    processed time dictionaries.

    Args:
        vital_time (list[dict]): A list of dictionaries containing vital time data.

    Returns:
        list[dict] | None: A list of processed vital time dictionaries with 
        formatted 'vital_time', or None if input is empty.

    Raises:
        HTTPException: If an error occurs during processing.
    """
    try:
        if not vital_time:
            return None
        processed_times = []
        for time_obj in vital_time:
            processed_times.append({
                "vitals_request_id": time_obj["vitals_request_id"],
                "vital_time": format_time(time_obj.get("vital_time")),
                "vitals_time_id": time_obj["vitals_time_id"]
            })
        logger.info("Processed vitals times.")
        return processed_times
    except Exception as e:
        logger.error(f"Error occurred while processing vitals time: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while processing vitals time")

async def vitals_monitored_helper(sp_appointment, service_provider, vitals_request, vital_frequency, service_package, subscriber, family_member_data, address, vital_requested, vitals_logs, vital_time, subscriber_mysql_session:AsyncSession):
    """
    Aggregates and processes all necessary data related to vitals monitoring into a structured dictionary.

    This helper function compiles information from multiple data sources related to a subscriber's
    service appointment, service provider, service package, and vital signs. It processes date/time
    fields, formats specific data points, and includes nested calls to format vital times and vital logs.

    Args:
        sp_appointment (dict): Information about the subscriber's appointment.
        service_provider (dict): Details about the assigned service provider.
        vitals_request (dict): Metadata about the requested vitals.
        vital_frequency (dict): Frequency configuration for vital checks.
        service_package (dict): Data about the service package selected.
        subscriber (dict): Basic information about the subscriber.
        family_member_data (dict): Data related to the subscriber's family member (if applicable).
        address (dict): Subscriber's address information.
        vital_requested (list): List of vitals requested for monitoring.
        vitals_logs (list): Logs of vitals already recorded.
        vital_time (list): Time slots for scheduled vital checks.
        subscriber_mysql_session (AsyncSession): SQLAlchemy async session for database operations.

    Returns:
        dict: A structured dictionary containing aggregated and formatted vital monitoring data.

    Raises:
        HTTPException: If any error occurs during data processing.
    """
    try:
        vitals = {
                "sp_appointment_id": sp_appointment.get("sp_appointment_id"),
                "session_time": sp_appointment.get("session_time"),
                "start_time": format_time(sp_appointment.get("start_time")),
                "end_time": format_time(sp_appointment.get("end_time")),
                "session_frequency": sp_appointment.get("session_frequency"),
                "start_date": format_date(sp_appointment.get("start_date")),
                "end_date": format_date(sp_appointment.get("end_date")),
                "prescription_id": sp_appointment.get("prescription_id"),
                "status": sp_appointment.get("status"),
                "visittype": sp_appointment.get("visittype"),
                "service_package_id": service_package.get("service_package_id"),
                "service_package_session_time": service_package.get("session_time"),
                "service_package_session_frequency": service_package.get("session_frequency"),
                "service_package_rate": service_package.get("rate"),
                "service_package_discount": service_package.get("discount"),
                "service_package_visittpe": service_package.get("visittype"),
                "book_for_data": family_member_data,
                "subscriber_id": subscriber.get("subscriber_id"),
                "subscriber_first_name": subscriber.get("first_name"),
                "subscriber_last_name": subscriber.get("last_name"),
                "subscriber_mobile": subscriber.get("mobile_number"),
                "subscriber_email_id": subscriber.get("email_id"),
                "subscriber_gender": subscriber.get("gender"),
                "subscriber_dob": subscriber.get("dob"),
                "subscriber_age": subscriber.get("age"),
                "subscriber_blood_group": subscriber.get("blood_group"),
                "subscriber_address": address,
                "sp_id": service_provider.get("sp_id"),
                "sp_first_name": service_provider.get("sp_firstname"),
                "sp_last_name": service_provider.get("sp_lastname"),
                "sp_mobile_number": service_provider.get("sp_mobilenumber"),
                "sp_email": service_provider.get("sp_email"),
                "sp_address": service_provider.get("sp_address") if sp_appointment.get("visittype") != "Home Visit" else None,
                "sp_verification_status": service_provider.get("verification_status"),
                "sp_remarks": service_provider.get("remarks"),
                "sp_agency": service_provider.get("agency"),
                "sp_geolocation": service_provider.get("geolocation"),
                "vital_request_id": vitals_request.get("vitals_request_id"),
                "vital_frequency_id": vitals_request.get("vital_frequency_id"),
                "vital_requested": vital_requested,
                "vital_frequency_id": vital_frequency.get("vital_frequency_id"),
                "session_frequency": vital_frequency.get("session_frequency"),
                "vital_check_time": await process_vital_time(vital_time=vital_time),
                "vitals_monitored": await process_vitals_logs(
                    vitals_logs=vitals_logs,
                    subscriber_mysql_session=subscriber_mysql_session
                )
            }
        return vitals
    except Exception as e:
        logger.error(f"Error occurred while getting vitals monitored: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while getting vitals monitored")


