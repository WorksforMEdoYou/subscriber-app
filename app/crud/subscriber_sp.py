from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List
from datetime import datetime
from ..models.subscriber import ServiceProvider, ServiceProviderCategory, ServiceSubType, ServiceType, ServiceProviderAppointment, Subscriber
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
        service_type = await subscriber_mysql_session.execute(select(ServiceType))
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

    