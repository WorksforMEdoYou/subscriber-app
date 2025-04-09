from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from ..db.subscriber_mysqlsession import get_async_subscriberdb
from ..schemas.subscriber import SubscriberMessage, CreateServiceProviderAppointment, UpdateServiceProviderAppointment, CancelServiceProviderAppointment
import logging
from ..service.subscriber_sp import get_hubby_sp_bl, create_sp_booking_bl, cancel_service_provider_booking_bl, update_service_provider_booking_bl
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.get("/subscriber/hubbysp/", status_code=status.HTTP_200_OK)
async def get_hubby_sp_endpoint(
    subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)
):
    """
    Fetches a list of service provider categories.

    This endpoint retrieves service provider categories by interacting with
    the business logic layer.

    Args:
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        list: A list of service provider categories.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        sp_category_list = await get_hubby_sp_bl(subscriber_mysql_session=subscriber_mysql_session)
        return sp_category_list
    except SQLAlchemyError as e:
        logger.error(f"Error in listing the list of service provider: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in listing the service provider"
        )
    except Exception as e:
        logger.error(f"Error in listing the list of service provider: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in listing the service provider"
        )

@router.post("/subscriber/createspbooking/", response_model=SubscriberMessage, status_code=status.HTTP_201_CREATED)
async def create_service_provider_booking_endpoint(
    sp_appointment: CreateServiceProviderAppointment,
    subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)
) -> SubscriberMessage:
    """
    Creates a service provider booking for a subscriber.

    This endpoint interacts with the business logic layer to create a booking
    for the specified service provider appointment.

    Args:
        sp_appointment (CreateServiceProviderAppointment): Appointment details for service provider booking.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        SubscriberMessage: A message indicating the booking creation status.

    Raises:
        HTTPException: Raised for validation errors or known issues during booking creation.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        create_sp_appointment = await create_sp_booking_bl(
            subscriber_mysql_session=subscriber_mysql_session,
            sp_appointment=sp_appointment
        )
        return create_sp_appointment
    except SQLAlchemyError as e:
        logger.error(f"Error in creating the service provider booking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in creating the service provider booking"
        )
    except Exception as e:
        logger.error(f"Error in creating the service provider booking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in creating the service provider booking"
        )

@router.put("/subscriber/updatespbooking/", response_model=SubscriberMessage, status_code=status.HTTP_200_OK)
async def update_service_provider_booking_endpoint(
    sp_appointment: UpdateServiceProviderAppointment,
    subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)
) -> SubscriberMessage:
    """
    Updates a service provider booking for a subscriber.

    This endpoint interacts with the business logic layer to update a booking
    based on the provided appointment details.

    Args:
        sp_appointment (UpdateServiceProviderAppointment): Appointment details for updating the booking.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        SubscriberMessage: A message indicating the booking update status.

    Raises:
        HTTPException: Raised for validation errors or known issues during booking updates.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        update_sp_appointment = await update_service_provider_booking_bl(
            subscriber_mysql_session=subscriber_mysql_session,
            sp_appointment=sp_appointment
        )
        return update_sp_appointment
    except SQLAlchemyError as e:
        logger.error(f"Error in updating the service provider booking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in updating the service provider booking"
        )
    except Exception as e:
        logger.error(f"Error in updating the service provider booking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in updating the service provider booking"
        )

@router.put("/subscriber/cancelspbooking/", response_model=SubscriberMessage, status_code=status.HTTP_200_OK)
async def cancel_service_provider_booking_endpoint(
    sp_appointment: CancelServiceProviderAppointment,
    subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)
) -> SubscriberMessage:
    """
    Cancels a service provider booking for a subscriber.

    This endpoint interacts with the business logic layer to cancel a booking
    based on the provided appointment details.

    Args:
        sp_appointment (CancelServiceProviderAppointment): Appointment details for canceling the booking.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        SubscriberMessage: A message indicating the booking cancellation status.

    Raises:
        HTTPException: Raised for validation errors or known issues during booking cancellations.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        cancel_sp_appointment = await cancel_service_provider_booking_bl(
            subscriber_mysql_session=subscriber_mysql_session,
            sp_appointment=sp_appointment
        )
        return cancel_sp_appointment
    except SQLAlchemyError as e:
        logger.error(f"Error in cancelling the service provider booking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in cancelling the service provider booking"
        )
    except Exception as e:
        logger.error(f"Error in cancelling the service provider booking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in cancelling the service provider booking"
        )

                                                    
