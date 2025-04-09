import asyncio
from fastapi import Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List
from datetime import datetime
from ..models.subscriber import Address, Subscriber, SubscriberAddress, UserAuth, UserDevice
from ..schemas.subscriber import UpdateSubscriber, UpdateSubscriberAddress, SubscriberSetProfile, SubscriberLogin, SubscriberSetMpin, SubscriberUpdateMpin
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def check_device_existing_data_helper(mobile_number:str, subscriber_mysql_session:AsyncSession):
    """
    Checks if a device ID already exists for a given mobile number in the database.

    Args:
        mobile_number (str): The mobile number to check.
        device_id (str): The device ID to check.
        subscriber_mysql_session (AsyncSession): The database session for interacting with the MySQL database.

    Returns:
        bool: True if the device ID exists for the mobile number, False otherwise.
    """
    try:
        existing_data = await subscriber_mysql_session.execute(
            select(UserDevice).where(UserDevice.mobile_number == mobile_number, UserDevice.app_name=="SUBSCRIBER")
        )
        result = existing_data.scalars().all()
        return result if result else "unique"
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error checking device data: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as exe:
        logger.error(f"Unexpected error checking device data: {exe}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def device_data_update_helper(token:str, device_id:str, active_flag:int, subscriber_mysql_session:AsyncSession):
    """
    Updates the device ID for a given mobile number in the database.

    Args:
        token (str): The mobile number to update.
        device_id (str): The new device ID to set.
        active_flag (int): The active flag to set for the device.
        subscriber_mysql_session (AsyncSession): The database session for interacting with the MySQL database.

    Returns:
        bool: True if the update was successful, False otherwise.
    """
    try:
        existing_data = await subscriber_mysql_session.execute(
            select(UserDevice).where(UserDevice.token == token, UserDevice.device_id==device_id, UserDevice.app_name=="SUBSCRIBER")
        )
        result = existing_data.scalars().first()
        if result:
            result.active_flag = active_flag
            await subscriber_mysql_session.flush()
            await subscriber_mysql_session.refresh(result)
            return True
        else:
            return False
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error updating device data: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as exe:
        logger.error(f"Unexpected error updating device data: {exe}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def subscriber_setprofile_dal(
    create_subscribers_data: SubscriberSetProfile, 
    create_address_data: Address, 
    create_subscriber_address_data: SubscriberAddress, 
    subscriber_mysql_session: AsyncSession
) -> dict:
    try:
        
        subscriber_data = await subscriber_mysql_session.execute(select(Subscriber).where(Subscriber.mobile==create_subscribers_data.mobile))
        subscriber = subscriber_data.scalars().first()
        
        subscriber.first_name = create_subscribers_data.first_name
        subscriber.last_name = create_subscribers_data.last_name
        subscriber.email_id = create_subscribers_data.email_id
        subscriber.age = create_subscribers_data.age
        subscriber.gender = create_subscribers_data.gender
        subscriber.dob = datetime.strptime(create_subscribers_data.dob, "%Y-%m-%d").date()
        subscriber.blood_group = create_subscribers_data.blood_group
        subscriber.updated_at = datetime.now()
        
        subscriber_mysql_session.add(create_address_data)
        subscriber_mysql_session.add(create_subscriber_address_data)

        # Instead of commit, you can flush to send the changes to the DB if necessary,
        # but the actual commit will be performed by the outer transaction.
        await subscriber_mysql_session.flush()

        # Refresh the objects if needed.
        await asyncio.gather(
            subscriber_mysql_session.refresh(subscriber),
            subscriber_mysql_session.refresh(create_address_data),
            subscriber_mysql_session.refresh(create_subscriber_address_data)
        )

        return {
            "subscriber": create_subscribers_data,
            "address": create_address_data,
            "subscriber_address": create_subscriber_address_data
        }
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error creating subscriber DAL: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred DAL")
    except Exception as exe:
        logger.error(f"Unexpected error creating subscriber DAL: {exe}")
        raise HTTPException(status_code=500, detail="Internal Server Error in DAL")

async def subscriber_login_dal(subscriber_login:SubscriberLogin, subscriber_mysql_session:AsyncSession):
    try:
        subscriber_data = await subscriber_mysql_session.execute(select(UserAuth).where(UserAuth.mobile_number==subscriber_login.subscriber_mobile))
        subscriber = subscriber_data.scalars().first()
        if not subscriber:
            raise HTTPException(status_code=404, detail="Subscriber not found")
        
        if subscriber.mpin != subscriber_login.mpin:
            raise HTTPException(status_code=401, detail="Invalid MPIN")
        
        return subscriber
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error subscriber login DAL: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred DAL")
    except Exception as exe:
        logger.error(f"Unexpected error subscriber login DAL: {exe}")
        raise HTTPException(status_code=500, detail="Internal Server Error in DAL")

async def subscriber_setmpin_dal(subscriber_mpin, subscriber_mysql_session:AsyncSession):
    try:
        subscriber_mysql_session.add(subscriber_mpin)
        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(subscriber_mpin)
        return subscriber_mpin
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error setting MPIN DAL: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred DAL")
    except Exception as exe:
        logger.error(f"Unexpected error setting MPIN DAL: {exe}")
        raise HTTPException(status_code=500, detail="Internal Server Error in DAL")
    
async def subscriber_updatempin_dal(subscriber_mpin:SubscriberUpdateMpin, subscriber_mysql_session:AsyncSession):
    try:
        subscriber_data = await subscriber_mysql_session.execute(select(UserAuth).where(UserAuth.mobile_number==subscriber_mpin.subscriber_mobile))
        subscriber = subscriber_data.scalars().first()
        if not subscriber:
            raise HTTPException(status_code=404, detail="Subscriber not found")
        
        subscriber.mpin = subscriber_mpin.mpin
        subscriber.updated_at = datetime.now()
        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(subscriber)
        return subscriber
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error updating MPIN DAL: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred DAL")
    except Exception as e:
        logger.error(f"Unexpected error updating MPIN DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in DAL")
  
async def create_user_device_dal(user_device, subscriber_mysql_session:AsyncSession):
    try:
        subscriber_mysql_session.add(user_device)
        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(user_device)
        return user_device
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error creating user device DAL: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred DAL")
    except Exception as exe:
        logger.error(f"Unexpected error creating user device DAL: {exe}")
        raise HTTPException(status_code=500, detail="Internal Server Error in DAL")
    
async def create_subscriber_signup_dal(subscriber_data, subscriber_mysql_session:AsyncSession):
    try:
        subscriber_mysql_session.add(subscriber_data)
        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(subscriber_data)
        return subscriber_data
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error creating subscriber signup DAL: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred DAL")
    except Exception as exe:
        logger.error(f"Unexpected error creating subscriber signup DAL: {exe}")
        raise HTTPException(status_code=500, detail="Internal Server Error in DAL")
 
async def update_subscriber_dal(subscriber: UpdateSubscriber, subscriber_mysql_session: AsyncSession):
    """
    Updates a subscriber's details, including their profile, address, and subscriber-to-address mapping.

    This function updates a subscriber's personal information, associated address, 
    and subscriber-to-address mapping in the database. It ensures data integrity by rolling back changes 
    if any step in the process fails.

    Args:
        subscriber (UpdateSubscriber): The updated subscriber data, including personal and address details.
        subscriber_mysql_session (AsyncSession): The database session for interacting with the MySQL database.

    Returns:
        Subscriber: The updated subscriber details.

    Raises:
        HTTPException: If the subscriber is not found or a validation error occurs.
        SQLAlchemyError: If a database error occurs during any of the operations.
            Exception: If an unexpected error occurs.
    """

    try:
            existing_subscriber = await subscriber_mysql_session.execute(
            select(Subscriber).filter(Subscriber.mobile == subscriber.subscriber_mobile)
            )
            existing_subscriber = existing_subscriber.scalars().first()
            if not existing_subscriber:
                raise HTTPException(status_code=404, detail="Subscriber not found")

            # subscriber data
            existing_subscriber.first_name = subscriber.subscriber_firstname
            existing_subscriber.last_name = subscriber.subscriber_lastname
            existing_subscriber.email_id = subscriber.subscriber_email
            existing_subscriber.gender = subscriber.subscriber_gender
            existing_subscriber.dob = datetime.strptime(subscriber.subscriber_dob, "%Y-%m-%d").date()
            existing_subscriber.age = subscriber.subscriber_age
            existing_subscriber.blood_group = subscriber.subscriber_blood_group
            existing_subscriber.updated_at = datetime.now()
            """ #await subscriber_mysql_session.commit()
            
            subscriber_id = existing_subscriber.subscriber_id
            # update subscriber_address
            subscriber_address = await subscriber_mysql_session.execute(select(SubscriberAddress).where(SubscriberAddress.subscriber_id==subscriber_id))
            subscriber_address = subscriber_address.scalars().first()
            subscriber_address.updated_at = datetime.now()
            #await subscriber_mysql_session.commit()
            
            #address id
            address_id = subscriber_address.address_id
            
            address = await subscriber_mysql_session.execute(select(Address).where(Address.address_id==address_id))
            address = address.scalars().first()
            address.address = subscriber.subscriber_address
            address.landmark = subscriber.subscriber_landmark
            address.pincode = subscriber.subscriber_pincode
            address.city = subscriber.subscriber_city
            address.state = subscriber.subscriber_state
            address.geolocation = subscriber.subscriber_geolocation
            address.updated_at = datetime.now() """
            #await subscriber_mysql_session.commit()
            
            await subscriber_mysql_session.flush()
            await asyncio.gather(
                subscriber_mysql_session.refresh(existing_subscriber),
                #subscriber_mysql_session.refresh(subscriber_address),
                #subscriber_mysql_session.refresh(address)
            )
            
            return existing_subscriber
        
    except HTTPException as http_exc:
            await subscriber_mysql_session.rollback()
            raise http_exc
    except SQLAlchemyError as e:
            await subscriber_mysql_session.rollback()
            logger.error(f"Error updating subscriber DAL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error DAL")
    except Exception as e:
            await subscriber_mysql_session.rollback()
            logger.error(f"Error updating subscriber DAL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error DAL")
        
async def get_subscriber_profile_dal(mobile: str, subscriber_mysql_session: AsyncSession) -> dict:
    """
    Retrieves a subscriber's complete profile, including their address and subscriber-to-address mapping.

    This function fetches and returns a subscriber's profile based on their mobile number. 
    It retrieves the subscriber's personal details, their associated address, and the mapping data.

    Args:
        mobile (str): The mobile number of the subscriber whose profile is to be retrieved.
        subscriber_mysql_session (AsyncSession): The database session for interacting with the MySQL database.

    Returns:
        dict: A dictionary containing the subscriber's profile, address details, and subscriber-to-address mapping.

    Raises:
        HTTPException: If the subscriber, their address, or the mapping is not found.
        SQLAlchemyError: If a database error occurs during the retrieval process.
        Exception: If an unexpected error occurs.
    """
    
    try:
            subscriber = await subscriber_mysql_session.execute(
            select(Subscriber).filter(Subscriber.mobile == mobile)
            )
            subscriber = subscriber.scalars().first()
            if not subscriber:
                raise HTTPException(status_code=404, detail="Subscriber with this mobile number not exist")
        
            """ subscriber_address = await subscriber_mysql_session.execute(
                select(SubscriberAddress).filter(SubscriberAddress.subscriber_id == subscriber.subscriber_id)
            )
            subscriber_address = subscriber_address.scalars().first()
            if not subscriber_address:
                raise HTTPException(status_code=404, detail="Subscriber Address not found")
        
            address = await subscriber_mysql_session.execute(
                select(Address).filter(Address.address_id == subscriber_address.address_id)
            )
            address = address.scalars().first()
            if not address:
                raise HTTPException(status_code=404, detail="Address not found")
         """
            subscriber_data = {
            "subscribers_data": subscriber
            }
            return subscriber_data
    except HTTPException as http_exc:
            await subscriber_mysql_session.rollback()
            raise http_exc
    except SQLAlchemyError as e:
            await subscriber_mysql_session.rollback()
            logger.error(f"Error fetching subscriber profile DAL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error while getting subscriber data DAL")
    except Exception as e:
            await subscriber_mysql_session.rollback()
            logger.error(f"Error fetching subscriber profile DAL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error while getting subscriber data DAL")

async def create_subscriber_address_dal(address, subscriber_address, subscriber_mysql_session: AsyncSession) -> dict:
    """
    Creates a new address for a subscriber.

    This function creates a new address associated with a subscriber in the database. 
    It ensures data integrity by rolling back changes if any step in the process fails.

    Args:
        address (Address): The data required to create a new address for the subscriber.
        subscriber_address (SubscriberAddress): The data required to create a new address for the subscriber.
        subscriber_mysql_session (AsyncSession): The database session for interacting with the MySQL database.

    Returns:
        dict: A dictionary containing the newly created subscriber address.

    Raises:
        HTTPException: If a validation error occurs.
        SQLAlchemyError: If a database error occurs during the creation process.
        Exception: If an unexpected error occurs.
    """
    try:
        subscriber_mysql_session.add(address)
        subscriber_mysql_session.add(subscriber_address)
        await subscriber_mysql_session.flush()
        await asyncio.gather(
            subscriber_mysql_session.refresh(subscriber_address),
            subscriber_mysql_session.refresh(address)
        )
        return {"address":address, "subscriber_address": subscriber_address}
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error creating subscriber address DAL: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred DAL")
    except Exception as exe:
        logger.error(f"Unexpected error creating subscriber address DAL: {exe}")
        raise HTTPException(status_code=500, detail="Internal Server Error in DAL")
    
async def update_subscriber_address_dal(update_subscriber_address:UpdateSubscriberAddress, subscriber_mysql_session:AsyncSession):
    try:
        subscriber_address_data = await subscriber_mysql_session.execute(select(SubscriberAddress).filter(SubscriberAddress.subscriber_address_id == update_subscriber_address.subscriber_address_id))
        subscriber_address_data = subscriber_address_data.scalars().first()
        if subscriber_address_data:
            subscriber_address_data.address_type = update_subscriber_address.address_type
            subscriber_address_data.updated_at = datetime.now()
            address_data = await subscriber_mysql_session.execute(select(Address).filter(Address.address_id == subscriber_address_data.address_id))
            address_data = address_data.scalars().first()
            address_data.address = update_subscriber_address.address
            address_data.landmark = update_subscriber_address.landmark
            address_data.pincode = update_subscriber_address.pincode
            address_data.city = update_subscriber_address.city
            address_data.state = update_subscriber_address.state
            address_data.geolocation = update_subscriber_address.geolocation
            address_data.updated_at = datetime.now()
            await subscriber_mysql_session.flush()
            await asyncio.gather(
                subscriber_mysql_session.refresh(subscriber_address_data),
                subscriber_mysql_session.refresh(address_data)
            )
            return {"address":address_data, "subscriber_address": subscriber_address_data}
        else:
            raise HTTPException(status_code=404, detail="Subscriber address not found")
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error updating subscriber address DAL: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred DAL")
    except Exception as exe:
        logger.error(f"Unexpected error updating subscriber address DAL: {exe}")
        raise HTTPException(status_code=500, detail="Internal Server Error in DAL")
    
async def view_subscriber_address_dal(subscriber_id:str, subscriber_address_label:str, subscriber_mysql_session:AsyncSession):
    try:
        subscriber_address_data = await subscriber_mysql_session.execute(select(SubscriberAddress).filter(SubscriberAddress.address_type == subscriber_address_label, SubscriberAddress.subscriber_id == subscriber_id))
        subscriber_address_data = subscriber_address_data.scalars().first()
        if subscriber_address_data:
            return subscriber_address_data
        else:
            raise HTTPException(status_code=404, detail="Subscriber address not found")
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error fetching subscriber address DAL: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred DAL")
    except Exception as exe:
        logger.error(f"Unexpected error fetching subscriber address DAL: {exe}")
        raise HTTPException(status_code=500, detail="Internal Server Error in DAL")


async def list_subscriber_address_dal(subscriber_id:int, subscriber_mysql_session:AsyncSession):
    try:
        subscriber_address_data = await subscriber_mysql_session.execute(select(SubscriberAddress).filter(SubscriberAddress.subscriber_id == subscriber_id))
        subscriber_address_data = subscriber_address_data.scalars().all()
        if subscriber_address_data:
            return subscriber_address_data
        else:
            raise HTTPException(status_code=404, detail="Subscriber address not found")
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error fetching subscriber address DAL: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred DAL")
    except Exception as exe:
        logger.error(f"Unexpected error fetching subscriber address DAL: {exe}")
        raise HTTPException(status_code=500, detail="Internal Server Error in DAL")