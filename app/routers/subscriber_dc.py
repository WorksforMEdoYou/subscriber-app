from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from ..db.subscriber_mysqlsession import get_async_subscriberdb
from ..schemas.subscriber import SubscriberMessage, CreateDCAppointment, UpdateDCAppointment, CancelDCAppointment
import logging
from ..service.subscriber_dc import get_hubby_dc_bl, create_dc_booking_bl, update_dc_booking_bl, cancel_dc_booking_bl, upcoming_dc_booking_bl, past_dc_booking_bl, get_dc_appointments_bl
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.get("/subscriber/hubbydc/", status_code=status.HTTP_200_OK)
async def get_hubby_dc_endpoint(
    subscriber_mysql_session: Session = Depends(get_async_subscriberdb)
):
    """
    Retrieves a list of diagnostics specializations.

    This endpoint interacts with the business logic layer to fetch a list of diagnostics
    categorized by specialization.

    Args:
        subscriber_mysql_session (Session): An async database session for executing queries.

    Returns:
        list: A list of diagnostics specialization details.

    Raises:
        HTTPException: Raised if there are validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related issues during query processing.
        Exception: Raised for any unexpected errors.
    """
    try:
        list_hub_dc = await get_hubby_dc_bl(subscriber_mysql_session=subscriber_mysql_session)
        return list_hub_dc
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in listing the diagnostics by specialization {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error in listing the diagnostics by specialization"
        )
    except Exception as e:
        logger.error(f"Error in listing the diagnostics by specialization {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error in listing the diagnostics by specialization"
        )

@router.post("/subscriber/createdcbooking/", response_model=SubscriberMessage, status_code=status.HTTP_201_CREATED)
async def create_dc_booking_endpoint(
    appointment: CreateDCAppointment, 
    subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)
):
    """
    Create a new DC booking.
    
    Args:
        appointment (CreateDCAppointment): The details of the appointment to be created.
        subscriber_mysql_session (AsyncSession): Database session dependency.
    
    Returns:
        SubscriberMessage: Confirmation message with booking details.
    """
    try:
        created_dc_booking = await create_dc_booking_bl(appointment=appointment, subscriber_mysql_session=subscriber_mysql_session)
        return created_dc_booking
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in creating the DC booking {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error in creating the DC booking"
        )
    except Exception as e:
        logger.error(f"Error in creating the DC booking {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error in creating the DC booking"
        )

@router.put("/subscriber/updatedcbooking/", response_model=SubscriberMessage, status_code=status.HTTP_200_OK)
async def update_dc_booking_endpoint(
    appointment: UpdateDCAppointment, 
    subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)
):
    """
    Update an existing DC booking.
    
    Args:
        appointment (UpdateDCAppointment): The updated details of the appointment.
        subscriber_mysql_session (AsyncSession): Database session dependency.
    
    Returns:
        SubscriberMessage: Confirmation message with updated booking details.
    """
    try:
        updated_dc_booking = await update_dc_booking_bl(appointment=appointment, subscriber_mysql_session=subscriber_mysql_session)
        return updated_dc_booking
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in updating the DC booking {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error in updating the DC booking"
        )
    except Exception as e:
        logger.error(f"Error in updating the DC booking {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error in updating the DC booking"
        )

@router.put("/subscriber/canceldcbooking/", response_model=SubscriberMessage, status_code=status.HTTP_200_OK)
async def cancel_dc_booking_endpoint(
    appointment: CancelDCAppointment, 
    subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)
):
    """
    Cancel an existing DC booking.
    
    Args:
        appointment (CancelDCAppointment): The details of the appointment to be canceled.
        subscriber_mysql_session (AsyncSession): Database session dependency.
    
    Returns:
        SubscriberMessage: Confirmation message with cancellation details.
    """
    try:
        cancelled_dc_booking = await cancel_dc_booking_bl(appointment=appointment, subscriber_mysql_session=subscriber_mysql_session)
        return cancelled_dc_booking
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in cancelling the DC booking {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error in cancelling the DC booking"
        )
    except Exception as e:
        logger.error(f"Error in cancelling the DC booking {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error in cancelling the DC booking"
        )

@router.get("/subscriber/upcomingdcbooking/", status_code=status.HTTP_200_OK)
async def upcoming_dc_booking_endpoint(
    subscriber_mobile: str, 
    subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)
):
    """
    Retrieve upcoming DC bookings for a subscriber.
    
    Args:
        subscriber_mobile (str): The mobile number of the subscriber.
        subscriber_mysql_session (AsyncSession): Database session dependency.
    
    Returns:
        list: A list of upcoming DC bookings for the subscriber.
    """
    try:
        upcoming_dc_booking = await upcoming_dc_booking_bl(subscriber_mobile=subscriber_mobile, subscriber_mysql_session=subscriber_mysql_session)
        return upcoming_dc_booking
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in fetching the upcoming DC booking {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error in fetching the upcoming DC booking"
        )
    except Exception as e:
        logger.error(f"Error in fetching the upcoming DC booking {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error in fetching the upcoming DC booking"
        )
        
@router.get("/subscriber/dcbookinglist/", status_code=status.HTTP_200_OK)
async def past_dc_list_endpoint(
    subscriber_mobile: str,
    subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)
    ):
    """
    Retrieve a list of DC bookings for a subscriber.
    
    Args:
        subscriber_mobile (str): The mobile number of the subscriber.
        subscriber_mysql_session (AsyncSession): Database session dependency.
        
    Returns:
        list: A list of DC bookings for the subscriber.
    """
    try:
        dc_booking_list = await past_dc_booking_bl(subscriber_mobile=subscriber_mobile, subscriber_mysql_session=subscriber_mysql_session)
        return dc_booking_list
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in fetching the DC booking list {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error in fetching the DC booking list"
        )
    except Exception as e:
        logger.error(f"Error in fetching the DC booking list {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error in fetching the DC booking list"
        )

@router.get("/subscriber/dcappointments/", status_code=status.HTTP_200_OK)
async def get_dc_appointments_endpoint(
    subscriber_mobile: str,
    subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)
    ):
    """
    Retrieve a list of DC appointments for a subscriber.
    
    Args:
        subscriber_mobile (str): The mobile number of the subscriber.
        subscriber_mysql_session (AsyncSession): Database session dependency.
    
    Returns:
        list: A list of DC appointments for the subscriber.
    """
    try:
        dc_appointments = await get_dc_appointments_bl(subscriber_mobile=subscriber_mobile, subscriber_mysql_session=subscriber_mysql_session)
        return dc_appointments
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in fetching the DC appointments {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error in fetching the DC appointments"
        )
    except Exception as e:
        logger.error(f"Error in fetching the DC appointments {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error in fetching the DC appointments"
        )
       