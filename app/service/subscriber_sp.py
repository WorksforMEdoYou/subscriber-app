from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List
from datetime import datetime
from ..models.subscriber import ServiceProvider, ServiceProviderCategory, ServiceSubType, ServiceType, ServiceProviderAppointment, Subscriber
from ..schemas.subscriber import SubscriberMessage, CreateServiceProviderAppointment, UpdateServiceProviderAppointment, CancelServiceProviderAppointment
from ..utils import check_data_exist_utils, id_incrementer, entity_data_return_utils, get_data_by_id_utils, get_data_by_mobile
from ..crud.subscriber_sp import get_hubby_sp_dal, get_sp_provider_helper, create_sp_booking_dal, update_service_provider_booking_dal, cancel_service_provider_booking_dal

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

                                                                    
            
           