from fastapi import Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List
from datetime import datetime
from ..models.subscriber import ServiceProvider, ServiceProviderCategory, ServiceSubType, ServiceType, DCAppointments, DCAppointmentPackage, Address, DCPackage
from ..schemas.subscriber import SubscriberMessage, UpdateDCAppointment, CancelDCAppointment
from ..utils import check_data_exist_utils, id_incrementer, entity_data_return_utils, get_data_by_id_utils, get_data_by_mobile
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def get_hubby_dc_dal(subscriber_mysql_session: AsyncSession) -> list:
    """
    Retrieves service types categorized under 'Diagnostics'.

    This function queries the database to fetch the service category named 'Diagnostics'
    and then retrieves the associated service types.

    Args:
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        list: A list of ServiceType objects associated with the 'Diagnostics' category.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        # Get the 'Diagnostics' service category
        service_category = await subscriber_mysql_session.execute(
            select(ServiceProviderCategory).where(ServiceProviderCategory.service_category_name == "Diagnostics")
        )
        service_category = service_category.scalars().first()

        # Get associated service types
        service_type = await subscriber_mysql_session.execute(
            select(ServiceType).where(ServiceType.service_category_id == service_category.service_category_id)
        )
        return service_type.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while fetching data from database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Error occurred while fetching data from database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
async def get_dc_provider(service_type_id: str, subscriber_mysql_session: AsyncSession) -> list:
    """
    Retrieves service providers for the given diagnostic service type.

    This function queries the database to fetch all service providers associated
    with the specified diagnostic service type.

    Args:
        service_type_id (str): The unique ID of the diagnostic service type.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        list: A list of ServiceProvider objects associated with the given service type.

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
        logger.error(f"Error occurred while fetching data from database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Error occurred while fetching data from database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def create_dc_booking_dal(appointment, subscriber_mysql_session: AsyncSession):
    """
    Creates a new DC booking entry in the database.
    
    Args:
        appointment: DCAppointments object containing booking details.
        subscriber_mysql_session (AsyncSession): Database session dependency.
    
    Returns:
        DCAppointments: The created booking entry.
    """
    try:
        subscriber_mysql_session.add(appointment)
        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(appointment)
        return appointment
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while creating data in database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Error occurred while creating data in database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def dc_booking_package_dal(appointment, subscriber_mysql_session: AsyncSession):
    """
    Creates a new DC booking package entry in the database.
    
    Args:
        appointment: DCAppointmentPackage object containing package details.
        subscriber_mysql_session (AsyncSession): Database session dependency.
    
    Returns:
        DCAppointmentPackage: The created package entry.
    """
    try:
        subscriber_mysql_session.add(appointment)
        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(appointment)
        return appointment
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while creating data in database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Error occurred while creating data in database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def update_dc_booking_dal(appointment: UpdateDCAppointment, subscriber_data, sp_data, subscriber_mysql_session: AsyncSession):
    """
    Updates an existing DC booking in the database.
    
    Args:
        appointment (UpdateDCAppointment): The updated appointment details.
        subscriber_data: The subscriber's details.
        sp_data: The service provider's details.
        subscriber_mysql_session (AsyncSession): Database session dependency.
    
    Returns:
        DCAppointments: The updated appointment entry.
    """
    try:
        date = datetime.strptime(appointment.appointment_date, "%Y-%m-%d %I:%M:%S %p").strftime("%d-%m-%Y %I:%M:%S %p")
        dc_appointment_data = await subscriber_mysql_session.execute(
            select(DCAppointments).where(DCAppointments.dc_appointment_id == appointment.dc_appointment_id)
        )
        dc_appointment = dc_appointment_data.scalars().first()
        if not dc_appointment:
            raise HTTPException(status_code=404, detail="DC Appointment not found")
        
        dc_appointment.appointment_date = date
        dc_appointment.reference_id = appointment.reference_id
        dc_appointment.prescription_image = appointment.prescription_image or None
        dc_appointment.status = "Rescheduled"
        dc_appointment.homecollection = appointment.homecollection
        dc_appointment.address_id = appointment.address_id
        dc_appointment.book_for_id = appointment.book_for_id if appointment.book_for_id is not None else None
        dc_appointment.subscriber_id = subscriber_data.subscriber_id
        dc_appointment.sp_id = sp_data.sp_id
        dc_appointment.updated_at = datetime.now()

        dc_appointment_package_data = await subscriber_mysql_session.execute(
            select(DCAppointmentPackage).where(DCAppointmentPackage.dc_appointment_id == appointment.dc_appointment_id)
        )
        dc_appointment_package = dc_appointment_package_data.scalars().first()
        if not dc_appointment_package:
            raise HTTPException(status_code=404, detail="DC Appointment Package not found")
        
        dc_appointment_package.package_id = appointment.package_id
        dc_appointment_package.report_image = appointment.report_image if appointment.report_image is not None else None
        dc_appointment_package.updated_at = datetime.now()
        
        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(dc_appointment)
        await subscriber_mysql_session.refresh(dc_appointment_package)
        return dc_appointment, dc_appointment_package
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while updating data in database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Error occurred while updating data in database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def cancel_dc_booking_dal(appointment: CancelDCAppointment, subscriber_mysql_session: AsyncSession):
    """
    Cancels an existing DC booking in the database.
    
    Args:
        appointment (CancelDCAppointment): The details of the appointment to be canceled.
        subscriber_mysql_session (AsyncSession): Database session dependency.
    
    Returns:
        DCAppointments: The canceled appointment entry.
    """
    try:
        dc_appointment_data = await subscriber_mysql_session.execute(
            select(DCAppointments).where(DCAppointments.dc_appointment_id == appointment.dc_appointment_id)
        )
        dc_appointment = dc_appointment_data.scalars().first()
        if not dc_appointment:
            raise HTTPException(status_code=404, detail="DC Appointment not found")
        
        dc_appointment_package_data = await subscriber_mysql_session.execute(
            select(DCAppointmentPackage).where(DCAppointmentPackage.dc_appointment_id == appointment.dc_appointment_id)
        )
        dc_appointment_package = dc_appointment_package_data.scalars().first()
        if not dc_appointment_package:
            raise HTTPException(status_code=404, detail="DC Appointment Package not found")
        
        dc_appointment_package.active_flag = 0
        dc_appointment_package.updated_at = datetime.now()
        
        dc_appointment.status = "Cancelled"
        dc_appointment.active_flag = appointment.active_flag
        dc_appointment.updated_at = datetime.now()
        dc_appointment.active_flag = 0
        
        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(dc_appointment)
        await subscriber_mysql_session.refresh(dc_appointment_package)
        return dc_appointment
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while updating data in database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error occurred while updating data in database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def get_upcoming_dc_booking_dal(subscriber_id:str, subscriber_mysql_session: AsyncSession) -> List[DCAppointments]:
    """
    Retrieves upcoming DC bookings for a specific subscriber.

    This function queries the database to fetch all upcoming DC bookings for the given subscriber ID.

    Args:
        subscriber_id (str): The unique ID of the subscriber.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        List[DCAppointments]: A list of DCAppointments objects associated with the given subscriber ID.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        dc_appointment_data = await subscriber_mysql_session.execute(
        select(DCAppointments, ServiceProvider, DCAppointmentPackage, Address)
        .join(ServiceProvider, DCAppointments.sp_id == ServiceProvider.sp_id)
        .join(DCAppointmentPackage, DCAppointments.dc_appointment_id == DCAppointmentPackage.dc_appointment_id)
        .join(Address, DCAppointments.address_id == Address.address_id)
        .where(
            DCAppointments.subscriber_id == subscriber_id,
            DCAppointments.status.in_(["Scheduled", "Rescheduled"]),
            DCAppointments.active_flag == 1,
            func.str_to_date(DCAppointments.appointment_date, "%d-%m-%Y %r") >= datetime.now()
        )
        )
        results = dc_appointment_data.all()
        # Convert results to a list of dictionaries for JSON serialization
        serialized_results = []
        for dc_appointment, service_provider, dc_appointment_package, address in results:
            serialized_results.append({
                "dc_appointment": {
                    key: value for key, value in dc_appointment.__dict__.items() if not key.startswith("_")
                },
                "service_provider": {
                    key: value for key, value in service_provider.__dict__.items() if not key.startswith("_")
                },
                "dc_appointment_package": {
                    key: value for key, value in dc_appointment_package.__dict__.items() if not key.startswith("_")
                },
                "address": {
                    key: value for key, value in address.__dict__.items() if not key.startswith("_")
                }
            })
        return serialized_results if serialized_results else None
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while fetching data from database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Error occurred while fetching data from database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def get_past_dc_booking_dal(subscriber_id:str, subscriber_mysql_session: AsyncSession) -> List[DCAppointments]:
    """
    Retrieves past DC bookings for a specific subscriber.

    This function queries the database to fetch all past DC bookings for the given subscriber ID.

    Args:
        subscriber_id (str): The unique ID of the subscriber.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        List[DCAppointments]: A list of DCAppointments objects associated with the given subscriber ID.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        dc_appointment_data = await subscriber_mysql_session.execute(
        select(DCAppointments, ServiceProvider, DCAppointmentPackage, Address)
        .join(ServiceProvider, DCAppointments.sp_id == ServiceProvider.sp_id)
        .join(DCAppointmentPackage, DCAppointments.dc_appointment_id == DCAppointmentPackage.dc_appointment_id)
        .join(Address, DCAppointments.address_id == Address.address_id)
        .where(
            DCAppointments.subscriber_id == subscriber_id,
            DCAppointments.status == "Completed",
            DCAppointments.active_flag == 0,
            func.str_to_date(DCAppointments.appointment_date, "%d-%m-%Y %r") <= datetime.now()
        )
        )
        results = dc_appointment_data.all()
        # Convert results to a list of dictionaries for JSON serialization
        serialized_results = []
        for dc_appointment, service_provider, dc_appointment_package, address in results:
            serialized_results.append({
                "dc_appointment": {
                    key: value for key, value in dc_appointment.__dict__.items() if not key.startswith("_")
                },
                "service_provider": {
                    key: value for key, value in service_provider.__dict__.items() if not key.startswith("_")
                },
                "dc_appointment_package": {
                    key: value for key, value in dc_appointment_package.__dict__.items() if not key.startswith("_")
                },
                "address": {
                    key: value for key, value in address.__dict__.items() if not key.startswith("_")
                }
            })
        return serialized_results if serialized_results else None
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while fetching data from database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Error occurred while fetching data from database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
async def dclistfortest_package_dal(pannel_id: str, subscriber_mysql_session: AsyncSession):
    """
    Retrieves a list of DC packages and their associated service providers for a given panel ID.

    Args:
        pannel_id (str): The unique ID of the panel.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        list: A list of dictionaries containing DC package and service provider details.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        # Query the database for DC packages and their associated service providers
        dc_list_data = await subscriber_mysql_session.execute(
            select(DCPackage, ServiceProvider)
            .join(ServiceProvider, ServiceProvider.sp_id == DCPackage.sp_id)
            .where(DCPackage.panel_ids.contains(pannel_id))
        )
        results = dc_list_data.all()

        # Convert results to a list of dictionaries for JSON serialization
        serialized_results = []
        for dc_package, service_provider in results:
            serialized_results.append({
                "dc_package": {
                    key: value for key, value in dc_package.__dict__.items() if not key.startswith("_")
                },
                "service_provider": {
                    key: value for key, value in service_provider.__dict__.items() if not key.startswith("_")
                }
            })

        return serialized_results if serialized_results else None
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while fetching data from database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def dclistfortest_test_dal(test_id, subscriber_mysql_session: AsyncSession):
    """
    Fetches a list of data center (DC) packages and their associated service providers
    based on the provided test ID. The query retrieves only active service providers
    (those with an active_flag of 1) and DC packages containing the given test ID.

    Args:
        test_id (str): The ID of the test to filter DC packages.
        subscriber_mysql_session (AsyncSession): An active SQLAlchemy asynchronous 
            session for interacting with the database.

    Returns:
        list: A list of dictionaries, where each dictionary contains:
            - 'dc_package': A dictionary representation of the DC package details.
            - 'service_provider': A dictionary representation of the associated 
              service provider details.

    Raises:
        HTTPException: If a database error or an unexpected error occurs, an 
            HTTPException with a 500 status code is raised, along with an error message.

    Logs:
        Logs errors using the logger in case of SQLAlchemy or other exceptions.
    """
    try:
        test_data = await subscriber_mysql_session.execute(
            select(DCPackage, ServiceProvider)
            .join(ServiceProvider, ServiceProvider.sp_id == DCPackage.sp_id)
            .where(DCPackage.test_ids.contains(test_id), ServiceProvider.active_flag == 1)
        )
        results = test_data.all()
        return [
        {
            "dc_package": {key: value for key, value in dc_package.__dict__.items() if not key.startswith("_")},
            "service_provider": {key: value for key, value in service_provider.__dict__.items() if not key.startswith("_")}
        }
        for dc_package, service_provider in results
        ]

    except SQLAlchemyError as e:
        logger.error(f"Error occurred while fetching data from database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


