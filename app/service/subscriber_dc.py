from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List, Dict
from datetime import datetime
from ..models.subscriber import ServiceProvider, ServiceProviderCategory, ServiceSubType, ServiceType, Subscriber, Address, DCAppointments, DCAppointmentPackage, FamilyMember, DCPackage, TestPanel, TestProvided, SubscriberAddress
from ..schemas.subscriber import SubscriberMessage, CreateSpecialization, CreateDCAppointment, UpdateDCAppointment, CancelDCAppointment
from ..utils import check_data_exist_utils, id_incrementer, entity_data_return_utils, get_data_by_id_utils, get_data_by_mobile
from ..crud.subscriber_dc import get_hubby_dc_dal, get_dc_provider, create_dc_booking_dal, update_dc_booking_dal, cancel_dc_booking_dal, dc_booking_package_dal, get_upcoming_dc_booking_dal, get_past_dc_booking_dal

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def get_hubby_dc_bl(subscriber_mysql_session: AsyncSession) -> list:
    """
    Fetches a list of diagnostics specializations along with the count of service providers.

    This function queries the database through the Data Access Layer to retrieve diagnostics
    service types. It calculates the count of service providers for each service type and
    compiles the results into a list of dictionaries.

    Args:
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        list: A list of dictionaries, each containing:
              - "service_type_name": Name of the diagnostic service type.
              - "service_type_id": ID of the diagnostic service type.
              - "dc_count": Count of service providers offering this service type.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related issues during processing.
        Exception: Raised for unexpected errors.
    """
    try:
        dc_list = []
        list_dc_spl = await get_hubby_dc_dal(subscriber_mysql_session)

        for spl in list_dc_spl:
            dc_list.append(
                {
                    "service_type_name": spl.service_type_name,
                    "service_type_id": spl.service_type_id,
                    "dc_count": len(await get_dc_provider(
                        service_type_id=spl.service_type_id,
                        subscriber_mysql_session=subscriber_mysql_session
                    ))
                }
            )
        return dc_list
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in listing the diagnostics by specialization: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error in listing the diagnostics by specialization"
        )
    except Exception as e:
        logger.error(f"Error in listing the diagnostics by specialization: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error in listing the diagnostics by specialization"
        )
    
async def create_dc_booking_bl(appointment: CreateDCAppointment, subscriber_mysql_session: AsyncSession):
    """
    Business logic to create a new DC booking.
    
    Args:
        appointment (CreateDCAppointment): The details of the appointment to be created.
        subscriber_mysql_session (AsyncSession): Database session dependency.
    
    Returns:
        SubscriberMessage: Confirmation message upon successful booking creation.
    """
    async with subscriber_mysql_session.begin():
        try:
            subscriber_data = await check_data_exist_utils(
                table=Subscriber, field="mobile", subscriber_mysql_session=subscriber_mysql_session, data=appointment.subscriber_mobile
            )
            if subscriber_data == "unique":
                raise HTTPException(status_code=400, detail="Subscriber with this mobile number does not exist")
            
            sp_data = await get_data_by_id_utils(
                table=ServiceProvider, field="sp_mobilenumber", subscriber_mysql_session=subscriber_mysql_session, data=appointment.sp_mobile
            )
            
            dc_booking_id = await id_incrementer("DCAPPOINTMENT", subscriber_mysql_session)
            dc_package_id = await id_incrementer("DCAPPOINTMENTPACKAGE", subscriber_mysql_session)
            date = datetime.strptime(appointment.appointment_date, "%Y-%m-%d %I:%M:%S %p").strftime("%d-%m-%Y %I:%M:%S %p")
            
            dc_booking_data = DCAppointments(
                dc_appointment_id=dc_booking_id,
                appointment_date=date,
                reference_id=appointment.reference_id,
                prescription_image=appointment.prescription_image,
                status="Scheduled",
                homecollection=appointment.homecollection,
                address_id=appointment.address_id,
                book_for_id=appointment.book_for_id if appointment.book_for_id is not None else None,
                subscriber_id=subscriber_data.subscriber_id,
                sp_id=sp_data.sp_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                active_flag=1
            )
            
            dc_booking_package = DCAppointmentPackage(
                dc_appointment_package_id = dc_package_id,
                package_id = appointment.package_id,
                report_image = appointment.report_image if appointment.report_image is not None else None,
                dc_appointment_id = dc_booking_id,
                created_at = datetime.now(),
                updated_at = datetime.now(),
                active_flag = 1
            )
            
            await create_dc_booking_dal(appointment=dc_booking_data, subscriber_mysql_session=subscriber_mysql_session)
            await dc_booking_package_dal(appointment=dc_booking_package, subscriber_mysql_session=subscriber_mysql_session)
            return SubscriberMessage(message="DC booking created successfully")
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error in creating the DC booking: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error in creating the DC booking")
        except Exception as e:
            logger.error(f"Error in creating the DC booking: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error in creating the DC booking")

async def update_dc_booking_bl(appointment: UpdateDCAppointment, subscriber_mysql_session: AsyncSession):
    """
    Business logic to update an existing DC booking.
    
    Args:
        appointment (UpdateDCAppointment): The updated details of the appointment.
        subscriber_mysql_session (AsyncSession): Database session dependency.
    
    Returns:
        SubscriberMessage: Confirmation message upon successful booking update.
    """
    async with subscriber_mysql_session.begin():
        try:
            subscriber_data = await check_data_exist_utils(
                table=Subscriber, field="mobile", subscriber_mysql_session=subscriber_mysql_session, data=appointment.subscriber_mobile
            )
            sp_data = await get_data_by_id_utils(
                table=ServiceProvider, field="sp_mobilenumber", subscriber_mysql_session=subscriber_mysql_session, data=appointment.sp_mobile
            )
            
            await update_dc_booking_dal(appointment=appointment, subscriber_data=subscriber_data, sp_data=sp_data, subscriber_mysql_session=subscriber_mysql_session)
            return SubscriberMessage(message="DC booking updated successfully")
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error in updating the DC booking: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error in updating the DC booking")
        except Exception as e:
            logger.error(f"Error in updating the DC booking: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error in updating the DC booking")

async def cancel_dc_booking_bl(appointment: CancelDCAppointment, subscriber_mysql_session: AsyncSession):
    """
    Business logic to cancel an existing DC booking.
    
    Args:
        appointment (CancelDCAppointment): The details of the appointment to be canceled.
        subscriber_mysql_session (AsyncSession): Database session dependency.
    
    Returns:
        SubscriberMessage: Confirmation message upon successful booking cancellation.
    """
    async with subscriber_mysql_session.begin():
        try:
            await cancel_dc_booking_dal(appointment=appointment, subscriber_mysql_session=subscriber_mysql_session)
            return SubscriberMessage(message="DC booking cancelled successfully")
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error in cancelling the DC booking: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error in cancelling the DC booking")
        except Exception as e:
            logger.error(f"Error in cancelling the DC booking: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error in cancelling the DC booking")
  
async def upcoming_dc_booking_bl(subscriber_mysql_session: AsyncSession, subscriber_mobile: str) -> List[dict]:
    """
    Business logic to fetch DC booking details for a subscriber.
    
    Args:
        subscriber_mysql_session (AsyncSession): Database session dependency.
        subscriber_mobile (str): Mobile number of the subscriber.
    
    Returns:
        List[dict]: A list of dictionaries containing DC booking details.
    """
    async with subscriber_mysql_session.begin():
        try:
            subscriber_data = await get_data_by_mobile(mobile=subscriber_mobile, field="mobile", table=Subscriber, subscriber_mysql_session=subscriber_mysql_session)
            if not subscriber_data:
                raise HTTPException(status_code=404, detail="Subscriber not found")
            upcoming_dc_booking = await get_upcoming_dc_booking_dal(subscriber_id=subscriber_data.subscriber_id, subscriber_mysql_session=subscriber_mysql_session)
            if not upcoming_dc_booking:
                return SubscriberMessage(message="No upcoming DC bookings found")

            upcomming_appointments = []

            for booking in upcoming_dc_booking:
                dc_appointment = booking["dc_appointment"]
                service_provider = booking["service_provider"]
                dc_appointment_package = booking["dc_appointment_package"]
                address = booking["address"]

                book_for_id = dc_appointment.get("book_for_id") if dc_appointment.get("book_for_id") else None
                book_for_data = None
                if book_for_id:
                    book_for_data = await get_data_by_id_utils(table=FamilyMember, field="fmailymember_id", subscriber_mysql_session=subscriber_mysql_session, data=book_for_id)

                subscriber_address = None
                if dc_appointment.get("homecollection") == "Yes":
                    address_type_data = await get_data_by_id_utils(table=SubscriberAddress, field="address_id", subscriber_mysql_session=subscriber_mysql_session, data=dc_appointment.get("address_id"))
                    subscriber_address = {
                        "city": address.get("city"),
                        "address": address.get("address"),
                        "landmark": address.get("landmark"),
                        "geolocation": address.get("geolocation"),
                        "updated_at": address.get("updated_at"),
                        "pincode": address.get("pincode"),
                        "state": address.get("state"),
                        "address_type": address_type_data.address_type,
                        "address_id": address.get("address_id")
                    }

                appointment_datetime = datetime.strptime(dc_appointment.get("appointment_date"), "%d-%m-%Y %I:%M:%S %p")
                appointment_date = appointment_datetime.strftime("%Y-%m-%d")
                appointment_time = appointment_datetime.strftime("%I:%M %p")

                upcomming_appointments.append({
                    "dc_appointment_id": dc_appointment.get("dc_appointment_id"),
                    "appointment_date": appointment_date,
                    "appointment_time": appointment_time,
                    "reference_id": dc_appointment.get("reference_id"),
                    "homecollection": dc_appointment.get("homecollection"),
                    "prescription_image": dc_appointment.get("prescription_image"),
                    "status": dc_appointment.get("status"),
                    "subscriber_address": subscriber_address,
                    "book_for_id": book_for_data.familymember_id if book_for_data!=None else None,
                    "book_for_name": book_for_data.name if book_for_data!=None else None,
                    "book_for_mobile": book_for_data.mobile if book_for_data!=None else None,
                    "service_provider_address": service_provider.get("sp_address") if dc_appointment.get("homecollection") == "No" else None,
                    "service_provider_name": (service_provider.get("sp_firstname") + " " + service_provider.get("sp_lastname")),
                    "service_provider_mobile": service_provider.get("sp_mobilenumber"),
                    "package_details": await get_package_details_helper(
                        package_id=dc_appointment_package.get("package_id"), subscriber_mysql_session=subscriber_mysql_session
                    ),
                })
            return upcomming_appointments
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error in fetching the DC booking details: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error in fetching the DC booking details")
        except Exception as e:
            logger.error(f"Error in fetching the DC booking details: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error in fetching the DC booking details")


async def past_dc_booking_bl(subscriber_mysql_session: AsyncSession, subscriber_mobile: str) -> List[dict]:
    """
    Business logic to fetch DC booking details for a subscriber.
    
    Args:
        subscriber_mysql_session (AsyncSession): Database session dependency.
        subscriber_mobile (str): Mobile number of the subscriber.
    
    Returns:
        List[dict]: A list of dictionaries containing DC booking details.
    """
    async with subscriber_mysql_session.begin():
        try:
            subscriber_data = await get_data_by_mobile(mobile=subscriber_mobile, field="mobile", table=Subscriber, subscriber_mysql_session=subscriber_mysql_session)
            if not subscriber_data:
                raise HTTPException(status_code=404, detail="Subscriber not found")
            past_dc_booking = await get_past_dc_booking_dal(subscriber_id=subscriber_data.subscriber_id, subscriber_mysql_session=subscriber_mysql_session)
            if not past_dc_booking:
                return SubscriberMessage(message="No past DC bookings found")

            past_appointments = []

            for booking in past_dc_booking:
                dc_appointment = booking["dc_appointment"]
                service_provider = booking["service_provider"]
                dc_appointment_package = booking["dc_appointment_package"]
                address = booking["address"]

                book_for_id = dc_appointment.get("book_for_id") if dc_appointment.get("book_for_id") else None
                book_for_data = None
                if book_for_id:
                    book_for_data = await get_data_by_id_utils(table=FamilyMember, field="fmailymember_id", subscriber_mysql_session=subscriber_mysql_session, data=book_for_id)

                subscriber_address = None
                if dc_appointment.get("homecollection") == "Yes":
                    address_type_data = await get_data_by_id_utils(table=SubscriberAddress, field="address_id", subscriber_mysql_session=subscriber_mysql_session, data=dc_appointment.get("address_id"))
                    subscriber_address = {
                        "city": address.get("city"),
                        "address": address.get("address"),
                        "landmark": address.get("landmark"),
                        "geolocation": address.get("geolocation"),
                        "updated_at": address.get("updated_at"),
                        "pincode": address.get("pincode"),
                        "state": address.get("state"),
                        "address_type": address_type_data.address_type,
                        "address_id": address.get("address_id")
                    }

                appointment_datetime = datetime.strptime(dc_appointment.get("appointment_date"), "%d-%m-%Y %I:%M:%S %p")
                appointment_date = appointment_datetime.strftime("%Y-%m-%d")
                appointment_time = appointment_datetime.strftime("%I:%M %p")

                past_appointments.append({
                    "dc_appointment_id": dc_appointment.get("dc_appointment_id"),
                    "appointment_date": appointment_date,
                    "appointment_time": appointment_time,
                    "reference_id": dc_appointment.get("reference_id"),
                    "homecollection": dc_appointment.get("homecollection"),
                    "prescription_image": dc_appointment.get("prescription_image"),
                    "status": dc_appointment.get("status"),
                    "subscriber_address": subscriber_address,
                    "raport_image": dc_appointment_package.get("report_image"),
                    "book_for_id": book_for_data.familymember_id if book_for_data!=None else None,
                    "book_for_name": book_for_data.name if book_for_data!=None else None,
                    "book_for_mobile": book_for_data.mobile if book_for_data!=None else None,
                    "service_provider_address": service_provider.get("sp_address") if dc_appointment.get("homecollection") == "No" else None,
                    "service_provider_name": (service_provider.get("sp_firstname") + " " + service_provider.get("sp_lastname")),
                    "service_provider_mobile": service_provider.get("sp_mobilenumber"),
                    "package_details": await get_package_details_helper(
                        package_id=dc_appointment_package.get("package_id"), subscriber_mysql_session=subscriber_mysql_session
                    ),
                })
            return past_appointments
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error in fetching the DC booking details: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error in fetching the DC booking details")
        except Exception as e:
            logger.error(f"Error in fetching the DC booking details: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error in fetching the DC booking details")

async def get_dc_appointments_bl(subscriber_mobile: str, subscriber_mysql_session: AsyncSession):
    try:
        dc_appointments=[
            {
                "past_appointment": await past_dc_booking_bl(
                    subscriber_mysql_session=subscriber_mysql_session, subscriber_mobile=subscriber_mobile
                )
            },
            {
                "upcoming_appointment": await upcoming_dc_booking_bl(
                    subscriber_mysql_session=subscriber_mysql_session, subscriber_mobile=subscriber_mobile
                )
            }
        ]
        return dc_appointments
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in fetching the DC booking details: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching the DC booking details")
    except Exception as e:
        logger.error(f"Error in fetching the DC booking details: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching the DC booking details")  

async def get_package_details_helper(
    package_id: str, 
    subscriber_mysql_session: AsyncSession
):
    """
    Helper function to fetch package details for a given package ID.
    
    Args:
        package_id (str): The ID of the package.
        subscriber_mysql_session (AsyncSession): Database session dependency.
    
    Returns:
        List[dict]: A list of dictionaries containing package details.
    """
    try:
        package_list = []
        package_data = await get_data_by_id_utils(
            table=DCPackage, field="package_id", subscriber_mysql_session=subscriber_mysql_session, data=package_id
        )
        
        #package_test
        test_id = package_data.test_ids if package_data.test_ids is not None else None
        if test_id is not None:
            package_list.append({
                "rate": package_data.rate,
                "test_id": test_id,           
                "package_test": await get_test_helper(
                    test_id=test_id, subscriber_mysql_session=subscriber_mysql_session
                )
            })
        
        #package_test_panel
        panel_id = package_data.panel_ids if package_data.panel_ids!=None else None
        if panel_id is not None:
            pannel_data = await get_data_by_id_utils(
                table=TestPanel, field="panel_id", subscriber_mysql_session=subscriber_mysql_session, data=panel_id
            )
            package_list.append({
                "rate": package_data.rate,
                "pannel_id": pannel_data.panel_id,
                "pannel_name": pannel_data.panel_name,
                "pannel_test": await get_test_helper(
                    test_id=pannel_data.test_ids, subscriber_mysql_session=subscriber_mysql_session
                )if pannel_data.test_ids!=None else None
            })
        return package_list
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in fetching the package details: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching the package details")
    except Exception as e:
        logger.error(f"Error in fetching the package details: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching the package details")

async def get_test_helper(
    test_id: str,
    subscriber_mysql_session: AsyncSession
    ):
    """
    Helper function to fetch test panel details for a given test ID.
    
    Args:
        test_id (str): The ID of the test.
        subscriber_mysql_session (AsyncSession): Database session dependency.
    
    Returns:
        List[dict]: A list of dictionaries containing test panel details.
    """
    try:
        test_data = await get_data_by_id_utils(table=TestProvided, field="test_id", subscriber_mysql_session=subscriber_mysql_session, data=test_id)
        test_details = {
                "test_id": test_data.test_id,
                "test_name": test_data.test_name,
                "sample": test_data.sample,
                "home_collection": test_data.home_collection,
                "prerequisites": test_data.prerequisites,
                "description": test_data.description
            }
        return test_details
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in fetching the test panel details: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching the test panel details")
    except Exception as e:
        logger.error(f"Error in fetching the test panel details: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching the test panel details")

