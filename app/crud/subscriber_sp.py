from fastapi import Depends, HTTPException
from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List
from datetime import datetime
from ..models.subscriber import ServiceProvider, ServiceProviderCategory, ServiceSubType, ServiceType, ServiceProviderAppointment, Subscriber, ServicePackage, VitalsRequest, VitalsLog, VitalFrequency, ServicePackage, VitalsTime, Vitals, Address
from ..schemas.subscriber import SubscriberMessage, CreateServiceProviderAppointment, UpdateServiceProviderAppointment, CancelServiceProviderAppointment
from ..utils import check_data_exist_utils, id_incrementer, entity_data_return_utils, get_data_by_id_utils, get_data_by_mobile
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def get_hubby_sp_dal(subscriber_mysql_session: AsyncSession) -> list:
    """
    Retrieves a list of service types from the database.

    Args:
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        list: A list of ServiceType objects.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        service_type = await subscriber_mysql_session.execute(
            select(ServiceType)
            .join(ServiceProviderCategory, ServiceType.service_category_id == ServiceProviderCategory.service_category_id)
            .where(ServiceProviderCategory.service_category_name != "Diagnostics")
        )
        return service_type.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Error in fetching the list of service type: {e}")
        raise HTTPException(status_code=500, detail="Error in fetching the list of service type")
    except Exception as e:
        logger.error(f"Error in fetching the list of service type: {e}")
        raise HTTPException(status_code=500, detail="Error in fetching the list of service type")
    
async def get_sp_provider_helper(service_type_id: str, subscriber_mysql_session: AsyncSession) -> list:
    """
    Retrieves a list of service providers for a given service type.

    Args:
        service_type_id (str): The ID of the service type.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        list: A list of ServiceProvider objects.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        service_provider = await subscriber_mysql_session.execute(
            select(ServiceProvider).where(ServiceProvider.service_type_id == service_type_id)
        )
        return service_provider.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Error in fetching the list of service provider: {e}")
        raise HTTPException(status_code=500, detail="Error in fetching the list of service provider")
    except Exception as e:
        logger.error(f"Error in fetching the list of service provider: {e}")
        raise HTTPException(status_code=500, detail="Error in fetching the list of service provider")

async def create_sp_booking_dal(
    new_sp_appointment: ServiceProviderAppointment,
    subscriber_mysql_session: AsyncSession
) -> ServiceProviderAppointment:
    """
    Creates a new service provider booking.

    Args:
        new_sp_appointment (ServiceProviderAppointment): The service provider appointment details.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        ServiceProviderAppointment: The created service provider appointment object.

    Raises:
        HTTPException: Raised for validation errors or known issues during booking creation.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        subscriber_mysql_session.add(new_sp_appointment)
        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(new_sp_appointment)
        return new_sp_appointment
    except SQLAlchemyError as e:
        logger.error(f"Error in creating the service provider booking: {e}")
        raise HTTPException(status_code=500, detail="Error in creating the service provider booking")
    except Exception as e:
        logger.error(f"Error in creating the service provider booking: {e}")
        raise HTTPException(status_code=500, detail="Error in creating the service provider booking")

async def update_service_provider_booking_dal(
    sp_appointment: UpdateServiceProviderAppointment,
    subscriber_mysql_session: AsyncSession
) -> ServiceProviderAppointment:
    """
    Updates an existing service provider booking.

    Args:
        sp_appointment (UpdateServiceProviderAppointment): The updated appointment details.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        ServiceProviderAppointment: The updated service provider booking object.

    Raises:
        HTTPException: Raised for validation errors or known issues during booking updates.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        subscriber_data = await get_data_by_id_utils(
            table=Subscriber,
            field="mobile",
            subscriber_mysql_session=subscriber_mysql_session,
            data=sp_appointment.subscriber_mobile
        )
        service_provider_booking = await subscriber_mysql_session.execute(
            select(ServiceProviderAppointment).where(
                ServiceProviderAppointment.sp_appointment_id == sp_appointment.sp_appointment_id
            )
        )
        service_provider_booking = service_provider_booking.scalars().first()

        # Update booking fields
        service_provider_booking.session_time = sp_appointment.session_time
        service_provider_booking.start_time = sp_appointment.start_time
        service_provider_booking.end_time = sp_appointment.end_time
        service_provider_booking.session_frequency = sp_appointment.session_frequency
        service_provider_booking.start_date = sp_appointment.start_date
        service_provider_booking.end_date = sp_appointment.end_date
        service_provider_booking.prescription_id = sp_appointment.prescription_id or None
        service_provider_booking.status = "Rescheduled"
        service_provider_booking.visittype = sp_appointment.visittype
        service_provider_booking.address_id = sp_appointment.address_id or None
        service_provider_booking.book_for_id = sp_appointment.book_for_id or None
        service_provider_booking.subscriber_id = subscriber_data.subscriber_id
        service_provider_booking.sp_id = sp_appointment.sp_id
        service_provider_booking.service_package_id = sp_appointment.service_package_id
        service_provider_booking.service_subtype_id = sp_appointment.service_subtype_id
        service_provider_booking.updated_at = datetime.now()

        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(service_provider_booking)
        return service_provider_booking
    except SQLAlchemyError as e:
        logger.error(f"Error in updating the service provider booking: {e}")
        raise HTTPException(status_code=500, detail="Error in updating the service provider booking")
    except Exception as e:
        logger.error(f"Error in updating the service provider booking: {e}")
        raise HTTPException(status_code=500, detail="Error in updating the service provider booking")
    
async def cancel_service_provider_booking_dal(
    sp_appointment: CancelServiceProviderAppointment,
    subscriber_mysql_session: AsyncSession
) -> ServiceProviderAppointment:
    """
    Cancels an existing service provider booking.

    Args:
        sp_appointment (CancelServiceProviderAppointment): The appointment details for cancellation.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        ServiceProviderAppointment: The cancelled service provider booking object.

    Raises:
        HTTPException: Raised for validation errors or known issues during booking cancellations.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        service_provider_booking = await subscriber_mysql_session.execute(
            select(ServiceProviderAppointment).where(
                ServiceProviderAppointment.sp_appointment_id == sp_appointment.sp_appointment_id
            )
        )
        service_provider_booking = service_provider_booking.scalars().first()

        # Update booking status and flag
        service_provider_booking.status = "Cancelled"
        service_provider_booking.active_flag = sp_appointment.active_flag
        service_provider_booking.updated_at = datetime.now()

        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(service_provider_booking)
        return service_provider_booking
    except SQLAlchemyError as e:
        logger.error(f"Error in cancelling the service provider booking: {e}")
        raise HTTPException(status_code=500, detail="Error in cancelling the service provider booking")
    except Exception as e:
        logger.error(f"Error in cancelling the service provider booking: {e}")
        raise HTTPException(status_code=500, detail="Error in cancelling the service provider booking")

async def upcoming_service_provider_booking_dal(subscriber_id: str, subscriber_mysql_session: AsyncSession):
    """
    Retrieves upcoming service provider bookings for a subscriber within the start_date and end_date range.

    Args:
        subscriber_id (str): The ID of the subscriber.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        list: A list of upcoming service provider bookings.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        upcoming_sp_booking = await subscriber_mysql_session.execute(
            select(ServiceProvider, ServiceProviderAppointment, ServiceSubType, ServicePackage)
            .join(ServiceProviderAppointment, ServiceProviderAppointment.sp_id == ServiceProvider.sp_id)
            .join(ServiceSubType, ServiceSubType.service_subtype_id == ServiceProviderAppointment.service_subtype_id)
            .join(ServicePackage, ServicePackage.service_package_id == ServiceProviderAppointment.service_package_id)
            .where(
                ServiceProviderAppointment.subscriber_id == subscriber_id,
                or_(
                    # Ongoing bookings
                    ServiceProviderAppointment.start_date <= datetime.now(),
                    # Upcoming bookings
                    ServiceProviderAppointment.start_date > datetime.now()
                ),
                ServiceProviderAppointment.active_flag == 1
            )
        )
        upcoming_sp_bookings = [
            {
                "service_provider": vars(sp),
                "appointment": vars(appointment),
                "service_subtype": vars(subtype),
                "service_package": vars(package)
            }
            for sp, appointment, subtype, package in upcoming_sp_booking.all()
        ]
        return upcoming_sp_bookings
    except SQLAlchemyError as e:
        logger.error(f"Error in getting upcoming service provider booking: {e}")
        raise HTTPException(status_code=500, detail="Error in getting upcoming service provider booking")
    except Exception as e:
        logger.error(f"Error in getting upcoming service provider booking: {e}")
        raise HTTPException(status_code=500, detail="Error in getting upcoming service provider booking")

async def past_service_provider_booking_dal(subscriber_id: str, subscriber_mysql_session: AsyncSession):
    """
    Retrieves past service provider bookings for a subscriber within the start_date and end_date range.

    Args:
        subscriber_id (str): The ID of the subscriber.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        list: A list of past service provider bookings.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        past_sp_booking = await subscriber_mysql_session.execute(
            select(ServiceProvider, ServiceProviderAppointment, ServiceSubType, ServicePackage)
            .join(ServiceProviderAppointment, ServiceProviderAppointment.sp_id == ServiceProvider.sp_id)
            .join(ServiceSubType, ServiceSubType.service_subtype_id == ServiceProviderAppointment.service_subtype_id)
            .join(ServicePackage, ServicePackage.service_package_id == ServiceProviderAppointment.service_package_id)
            .where(
                ServiceProviderAppointment.subscriber_id == subscriber_id,
                ServiceProviderAppointment.end_date <= datetime.now(),
                ServiceProviderAppointment.status == "completed",
                ServiceProviderAppointment.active_flag == 0
            )
        )
        past_sp_bookings = [
            {
                "service_provider": vars(sp),
                "appointment": vars(appointment),
                "service_subtype": vars(subtype),
                "service_package": vars(package)
            }
            for sp, appointment, subtype, package in past_sp_booking.all()
        ]
        return past_sp_bookings
    except SQLAlchemyError as e:
        logger.error(f"Error in getting past service provider booking: {e}")
        raise HTTPException(status_code=500, detail="Error in getting past service provider booking")
    except Exception as e:
        logger.error(f"Error in getting past service provider booking: {e}")
        raise HTTPException(status_code=500, detail="Error in getting past service provider booking")

async def service_provider_list_for_service_dal(service_subtype_id: str, subscriber_mysql_session: AsyncSession):
    """
    Retrieves a list of service providers and their service packages for a given service subtype.

    Args:
        service_subtype_id (str): The ID of the service subtype.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        list: A list of dictionaries containing service provider and service package details.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        sp_list = await subscriber_mysql_session.execute(
            select(ServicePackage, ServiceSubType, ServiceType, ServiceProviderCategory, ServiceProvider)
            .join(ServiceProvider, ServiceProvider.sp_id == ServicePackage.sp_id)
            .join(ServiceType, ServiceType.service_type_id == ServicePackage.service_type_id)
            .join(ServiceSubType, ServiceSubType.service_subtype_id == ServicePackage.service_subtype_id)
            .join(ServiceProviderCategory, ServiceProviderCategory.service_category_id == ServiceType.service_category_id)
            .where(ServicePackage.service_subtype_id == service_subtype_id)
        )
        sp_list = [
            {
                "service_package": vars(package),
                "service_subtype": vars(subtype),
                "service_type": vars(service_type),
                "service_provider_category": vars(category),
                "service_provider": vars(provider),
            }
            for package, subtype, service_type, category, provider in sp_list.all()
        ]
        return sp_list
    except SQLAlchemyError as e:
        logger.error(f"Error in getting service provider list for service: {e}")
        raise HTTPException(status_code=500, detail="Error in getting service provider list for service")
    except Exception as e:
        logger.error(f"Error in getting service provider list for service: {e}")
        raise HTTPException(status_code=500, detail="Error in getting service provider list for service")

async def create_vitals_dal(vitals_request, subscriber_mysql_session:AsyncSession):
    """
    Creates and persists a vitals request record in the database.

    This function adds the provided vitals request to the database, flushes the session to persist 
    the changes, and refreshes the instance to retrieve the updated data. It ensures that the vitals 
    request is successfully created and stored.

    Args:
        vitals_request: The vitals request object to be added to the database.
        subscriber_mysql_session (AsyncSession): The async SQLAlchemy session for performing database operations.

    Returns:
        VitalsRequest: The created and refreshed VitalsRequest object.

    Raises:
        HTTPException: If a SQLAlchemy error occurs during the database operations.
        HTTPException: If any unexpected errors are encountered during the operation.

    Note:
        This function handles SQLAlchemy-specific and general exceptions, logging errors and raising 
        appropriate HTTP exceptions when issues arise.
    """

    try:
        subscriber_mysql_session.add(vitals_request)
        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(vitals_request)
        return vitals_request
    except SQLAlchemyError as e:
        logger.error(f"Error in creating vitals: {e}")
        raise HTTPException(status_code=500, detail="Error in creating vitals")
    except Exception as e:
        logger.error(f"Error in creating vitals: {e}")
        raise HTTPException(status_code=500, detail="Error in creating vitals")

async def create_vital_time_dal(vital_time, subscriber_mysql_session:AsyncSession):
    """
    Creates and persists a vital time record in the database.

    This function adds the provided vital time object to the database, flushes the session to persist 
    the changes, and refreshes the instance to retrieve the updated data. It ensures that the vital 
    time is successfully created and stored.

    Args:
        vital_time: The vital time object to be added to the database.
        subscriber_mysql_session (AsyncSession): The async SQLAlchemy session for performing database operations.

    Returns:
        VitalsTime: The created and refreshed VitalsTime object.

    Raises:
        HTTPException: If a SQLAlchemy error occurs during the database operations.
        HTTPException: If any unexpected errors are encountered during the operation.

    Note:
        This function handles SQLAlchemy-specific and general exceptions, logging errors and raising 
        appropriate HTTP exceptions when issues arise.
    """

    try:
        subscriber_mysql_session.add(vital_time)
        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(vital_time)
        return vital_time
    except SQLAlchemyError as e:
        logger.error(f"Error in creating vitals time: {e}")
        raise HTTPException(status_code=500, detail="Error in creating vitals time")
    except Exception as e:
        logger.error(f"Error in creating vitals time: {e}")
        raise HTTPException(status_code=500, detail="Error in creating vitals time")

async def create_medication_dal(medication, subscriber_mysql_session:AsyncSession):
    """
    Insert a medication object into the database using the provided session.

    Args:
        medication: The medication object to be added to the database.
        subscriber_mysql_session (AsyncSession): Database session used for executing queries.

    Returns:
        The refreshed medication object after successful insertion into the database.

    Raises:
        HTTPException: If an SQLAlchemyError or any other exception occurs during the operation.
    """
    try:
        subscriber_mysql_session.add(medication)
        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(medication)
        return medication
    except SQLAlchemyError as e:
        logger.error(f"Error in creating medication: {e}")
        raise HTTPException(status_code=500, detail="Error in creating medication")
    except Exception as e:
        logger.error(f"Error in creating medication: {e}")
        raise HTTPException(status_code=500, detail="Error in creating medication")

async def get_nursing_vitals_today_dal(sp_appointment_id: str, subscriber_mysql_session: AsyncSession):
    """
    Retrieves today's nursing vitals for a specific service provider appointment.

    Args:
        sp_appointment_id (str): The ID of the service provider appointment.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        list: A list of nursing vitals records for today.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        today = datetime.now().date()
        nursing_vitals_today = await subscriber_mysql_session.execute(
            select(
                ServiceProviderAppointment,
                ServiceProvider,
                VitalFrequency,
                VitalsRequest,
                ServicePackage,
                Subscriber
            )
            .join(ServiceProvider, ServiceProviderAppointment.sp_id == ServiceProvider.sp_id)
            .join(VitalsRequest, VitalsRequest.appointment_id == ServiceProviderAppointment.sp_appointment_id)
            .join(VitalFrequency, VitalFrequency.vital_frequency_id == VitalsRequest.vital_frequency_id)
            .join(ServicePackage, ServicePackage.service_package_id == ServiceProviderAppointment.service_package_id)
            .join(Subscriber, Subscriber.subscriber_id == ServiceProviderAppointment.subscriber_id)
            .where(
                ServiceProviderAppointment.sp_appointment_id == sp_appointment_id,
                func.date(VitalsRequest.created_at) == today,
                ServiceProviderAppointment.active_flag == 1,
            )
        )

        nursing_vitals_today_data = []
        for appointment, provider, frequency, request, package, subscriber in nursing_vitals_today.all():
            vitals_logs = await subscriber_mysql_session.execute(
                select(VitalsLog).where(VitalsLog.vitals_request_id == request.vitals_request_id)
            )
            vitals_times = await subscriber_mysql_session.execute(
                select(VitalsTime).where(VitalsTime.vitals_request_id == request.vitals_request_id)
            )

            nursing_vitals_today_data.append({
                "appointment": vars(appointment),
                "service_provider": vars(provider),
                "vital_frequency": vars(frequency),
                "vitals_request": vars(request),
                "vitals_logs": [vars(log) for log in vitals_logs.scalars().all()],
                "vitals_times": [vars(time) for time in vitals_times.scalars().all()],
                "service_package": vars(package),
                "subscriber": vars(subscriber)
            })

        return nursing_vitals_today_data
    except SQLAlchemyError as e:
        logger.error(f"Error in getting nursing vitals today DAL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting nursing vitals today")
    except Exception as e:
        logger.error(f"Error in getting nursing vitals today DAL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting nursing vitals today")

async def get_nursing_vitals_log_dal(sp_appointment_id: str, subscriber_mysql_session: AsyncSession):
    """
    Retrieves nursing vitals for a specific service provider appointment.

    Args:
        sp_appointment_id (str): The ID of the service provider appointment.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        list: A list of nursing vitals records for the appointment.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        nursing_vitals_today = await subscriber_mysql_session.execute(
            select(
                ServiceProviderAppointment,
                ServiceProvider,
                VitalFrequency,
                VitalsRequest,
                ServicePackage,
                Subscriber
            )
            .join(ServiceProvider, ServiceProviderAppointment.sp_id == ServiceProvider.sp_id)
            .join(VitalsRequest, VitalsRequest.appointment_id == ServiceProviderAppointment.sp_appointment_id)
            .join(VitalFrequency, VitalFrequency.vital_frequency_id == VitalsRequest.vital_frequency_id)
            .join(ServicePackage, ServicePackage.service_package_id == ServiceProviderAppointment.service_package_id)
            .join(Subscriber, Subscriber.subscriber_id == ServiceProviderAppointment.subscriber_id)
            .where(
                ServiceProviderAppointment.sp_appointment_id == sp_appointment_id,
                ServiceProviderAppointment.active_flag==1
            )
        )

        nursing_vitals_today_data = []
        for appointment, provider, frequency, request, package, subscriber in nursing_vitals_today.all():
            vitals_logs = await subscriber_mysql_session.execute(
                select(VitalsLog).where(VitalsLog.vitals_request_id == request.vitals_request_id)
            )
            vitals_times = await subscriber_mysql_session.execute(
                select(VitalsTime).where(VitalsTime.vitals_request_id == request.vitals_request_id)
            )

            nursing_vitals_today_data.append({
                "appointment": vars(appointment),
                "service_provider": vars(provider),
                "vital_frequency": vars(frequency),
                "vitals_request": vars(request),
                "vitals_logs": [vars(log) for log in vitals_logs.scalars().all()],
                "vitals_times": [vars(time) for time in vitals_times.scalars().all()],
                "service_package": vars(package),
                "subscriber": vars(subscriber)
            })

        return nursing_vitals_today_data
    except SQLAlchemyError as e:
        logger.error(f"Error in getting nursing vitals log DAL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting nursing vitals log")
    except Exception as e:
        logger.error(f"Error in getting nursing vitals log DAL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting nursing vitals log")





    