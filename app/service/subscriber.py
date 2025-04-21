import os
from fastapi import Depends, HTTPException, UploadFile
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List
from datetime import datetime
from ..models.subscriber import Address, Subscriber, SubscriberAddress, Specialization, UserDevice, UserAuth
from ..schemas.subscriber import SubscriberSetProfile, UpdateSubscriber, SubscriberMessage, CreateSpecialization, CreateSubscriberAddress, UpdateSubscriberAddress, SubscriberSignup, SubscriberLogin, SubscriberSetMpin, SubscriberUpdateMpin
from ..utils import check_data_exist_utils, id_incrementer, entity_data_return_utils, get_data_by_id_utils, get_data_by_mobile
from ..crud.subscriber import check_device_existing_data_helper, subscriber_setprofile_dal, get_subscriber_profile_dal, update_subscriber_dal, create_subscriber_address_dal, update_subscriber_address_dal, view_subscriber_address_dal, list_subscriber_address_dal, create_user_device_dal, create_subscriber_signup_dal, subscriber_login_dal, subscriber_setmpin_dal, subscriber_updatempin_dal, get_device_data_active, device_data_update_helper

from ..service.subscriber_dc import get_hubby_dc_bl
from ..service.subscriber_sp import get_hubby_sp_bl
from ..service.subscriber_appointments import health_hub_stacks_bl

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

""" async def subscriber_signup_bl(subscriber_signup: SubscriberSignup, subscriber_mysql_session: AsyncSession):
    async with subscriber_mysql_session.begin():
        try:
            # Check if the subscriber already exists by mobile number
            subscriber_data = await check_data_exist_utils(
                table=Subscriber, field="mobile", subscriber_mysql_session=subscriber_mysql_session, data=subscriber_signup.mobile
            )

            # Check if the device already exists for the given mobile number
            device_data = await check_device_existing_data_helper(
                subscriber_mysql_session=subscriber_mysql_session, mobile_number=subscriber_signup.mobile
            )

            # Check if the device_id and token exist in the database (regardless of mobile number)
            existing_device = await subscriber_mysql_session.execute(
                select(UserDevice).where(
                    UserDevice.device_id == subscriber_signup.device_id,
                    UserDevice.token == subscriber_signup.token,
                    UserDevice.app_name == "SUBSCRIBER"
                )
            )
            existing_device_data = existing_device.scalars().first()

            # Generate a new subscriber ID
            new_subscriber_id = await id_incrementer(entity_name="SUBSCRIBER", subscriber_mysql_session=subscriber_mysql_session)

            # Create new subscriber data
            new_subscriber_data = Subscriber(
                subscriber_id=new_subscriber_id,
                first_name=subscriber_signup.name,
                mobile=subscriber_signup.mobile,
                email_id=subscriber_signup.email_id if subscriber_signup.email_id else None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                active_flag=1
            )

            # Create new user device data
            new_user_device = UserDevice(
                mobile_number=int(subscriber_signup.mobile),
                device_id=subscriber_signup.device_id,
                token=subscriber_signup.token,
                app_name="SUBSCRIBER",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                active_flag=1
            )

            if existing_device_data:
                # Case: Device ID and token already exist in the database
                # Deactivate all other records for the same device_id and token
                await subscriber_mysql_session.execute(
                    update(UserDevice)
                    .where(
                        UserDevice.device_id == subscriber_signup.device_id,
                        UserDevice.token == subscriber_signup.token,
                        UserDevice.app_name == "SUBSCRIBER"
                    )
                    .values(active_flag=0)
                )
                # Activate the current record
                existing_device_data.active_flag = 1
                await subscriber_mysql_session.flush()
                return SubscriberMessage(message="Device reactivated successfully for existing user.")
            elif subscriber_data == "unique":
                # Case 1: New subscriber with new device_id and token
                if device_data == "unique":
                    await create_subscriber_signup_dal(subscriber_data=new_subscriber_data, subscriber_mysql_session=subscriber_mysql_session)
                    await create_user_device_dal(user_device=new_user_device, subscriber_mysql_session=subscriber_mysql_session)
                    return SubscriberMessage(message="Subscriber Signup Successfully")
                # Case 2: New subscriber with old device_id and token
                else:
                    for device in device_data:
                        if device.device_id == subscriber_signup.device_id and device.token == subscriber_signup.token:
                            raise HTTPException(status_code=400, detail="Device already exists for this subscriber.")
                    # Deactivate all old device records
                    for old_device in device_data:
                        old_device.active_flag = 0
                        await device_data_update_helper(
                            device_id=old_device.device_id, token=old_device.token, active_flag=0, subscriber_mysql_session=subscriber_mysql_session
                        )
                    # Create new subscriber and activate current device
                    await create_subscriber_signup_dal(subscriber_data=new_subscriber_data, subscriber_mysql_session=subscriber_mysql_session)
                    await create_user_device_dal(user_device=new_user_device, subscriber_mysql_session=subscriber_mysql_session)
                    return SubscriberMessage(message="Subscriber Signup Successfully")
            else:
                # Case 3: Old subscriber with old device_id and token
                for device in device_data:
                    if device.device_id == subscriber_signup.device_id and device.token == subscriber_signup.token:
                        raise HTTPException(status_code=400, detail="Subscriber already exists. Please login.")
                # Case 4: Old subscriber with new device_id and token
                for old_device in device_data:
                    old_device.active_flag = 0
                    await device_data_update_helper(
                        device_id=old_device.device_id, token=old_device.token, active_flag=0, subscriber_mysql_session=subscriber_mysql_session
                    )
                await create_user_device_dal(user_device=new_user_device, subscriber_mysql_session=subscriber_mysql_session)
                return SubscriberMessage(message="Device updated successfully for existing subscriber. Please login.")

        except SQLAlchemyError as e:
            logger.error(f"Error occurred while signing up subscriber BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error BL")
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Error occurred while signing up subscriber BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error BL")
 """
async def subscriber_signup_bl(subscriber_signup:SubscriberSignup, subscriber_mysql_session:AsyncSession):
    async with subscriber_mysql_session.begin():
        try:
            # Check if the subscriber already exists by mobile number
            subscriber_data = await check_data_exist_utils(
                table=Subscriber, field="mobile", subscriber_mysql_session=subscriber_mysql_session, data=subscriber_signup.mobile
            )
            #check the subscriber device allready exist
            token_exist = await check_device_existing_data_helper(mobile_number=subscriber_signup.mobile, subscriber_mysql_session=subscriber_mysql_session, token=subscriber_signup.token, device_id=subscriber_signup.device_id)
            
            if subscriber_data=="unique" and token_exist=="unique":
                new_subscriber_data = await subscriber_profile_helper(subscriber_signup=subscriber_signup, subscriber_mysql_session=subscriber_mysql_session)
                new_device_data = await subscriber_device_helper(subscriber_signup=subscriber_signup)
                await create_subscriber_signup_dal(subscriber_data=new_subscriber_data, subscriber_mysql_session=subscriber_mysql_session)
                await create_user_device_dal(user_device=new_device_data, subscriber_mysql_session=subscriber_mysql_session)
                await subscriber_mysql_session.commit()
            else:
                existing_device = await get_device_data_active(mobile=subscriber_signup.mobile, subscriber_mysql_session=subscriber_mysql_session)
                await device_data_update_helper(mobile=existing_device.mobile_number, token=existing_device.token, device_id=existing_device.device_id, active_flag=0, subscriber_mysql_session=subscriber_mysql_session)
                
                if(subscriber_data!="unique" and token_exist!="unique"):
                    if(token_exist.token==subscriber_signup.token and token_exist.device_id==subscriber_signup.device_id):
                        await device_data_update_helper(
                            mobile=subscriber_signup.mobile,
                            token=subscriber_signup.token,
                            device_id=subscriber_signup.device_id,
                            active_flag=1,
                            subscriber_mysql_session=subscriber_mysql_session
                        )
                        await subscriber_mysql_session.commit()
                        raise HTTPException(status_code=400, detail="Subscriber Allready Exist Please login")
                elif subscriber_data != "unique" and token_exist == "unique":
                    new_device_data = await subscriber_device_helper(subscriber_signup=subscriber_signup)
                    await create_user_device_dal(user_device=new_device_data, subscriber_mysql_session=subscriber_mysql_session)
                    await subscriber_mysql_session.commit()
                elif subscriber_data != "unique" and token_exist != "unique" and token_exist.device_id == subscriber_signup.device_id and token_exist.token != subscriber_signup.token:
                    new_device_data = await subscriber_device_helper(subscriber_signup=subscriber_signup)
                    await create_user_device_dal(user_device=new_device_data, subscriber_mysql_session=subscriber_mysql_session)
                    await subscriber_mysql_session.commit()
            return SubscriberMessage(message="Subscriber Signup Successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error occurred while signing up subscriber BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error BL")
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Error occurred while signing up subscriber BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error BL")
        
async def subscriber_profile_helper(subscriber_signup: SubscriberSignup, subscriber_mysql_session: AsyncSession):
    """
    Helper function to create a new subscriber profile.

    Args:
        subscriber_signup (SubscriberSignup): The subscriber signup data.
        subscriber_mysql_session (AsyncSession): The database session.

    Returns:
        Subscriber: The newly created subscriber data.
    """
    try:
        # Generate a new subscriber ID
        new_subscriber_id = await id_incrementer(entity_name="SUBSCRIBER", subscriber_mysql_session=subscriber_mysql_session)

        # Create new subscriber data
        new_subscriber_data = Subscriber(
            subscriber_id=new_subscriber_id,
            first_name=subscriber_signup.name,
            mobile=subscriber_signup.mobile,
            email_id=subscriber_signup.email_id if subscriber_signup.email_id else None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            active_flag=1
        )
        return new_subscriber_data
    except Exception as e:
        logger.error(f"Error occurred while creating subscriber profile helper BL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error helper BL")

async def subscriber_device_helper(subscriber_signup: SubscriberSignup):
    try:
        # Create new user device data
        new_user_device = UserDevice(
            mobile_number=int(subscriber_signup.mobile),
            device_id=subscriber_signup.device_id,
            token=subscriber_signup.token,
            app_name="SUBSCRIBER",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            active_flag=1
            )
        return new_user_device
    except Exception as e:
        logger.error(f"Error occurred while creating subscriber device helper BL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error helper BL")

async def subscriber_setprofile_bl(subscriber: SubscriberSetProfile, subscriber_mysql_session: AsyncSession):
    async with subscriber_mysql_session.begin(): # Outer transaction here
        try:
            # Check if the subscriber already exists
            subscriber_data =  await check_data_exist_utils(table=Subscriber, field="mobile", subscriber_mysql_session=subscriber_mysql_session, data=subscriber.mobile)
                
            if subscriber_data == "unique":
                raise HTTPException(status_code=400, detail="Subscriber Not Exists")

            # Use id_incrementer to generate IDs (operate within the same transaction)
            #new_subscriber_id = await id_incrementer(entity_name="SUBSCRIBER", subscriber_mysql_session=subscriber_mysql_session)
            new_address_id = await id_incrementer(entity_name="ADDRESS", subscriber_mysql_session=subscriber_mysql_session)
            new_subscriber_address_id = await id_incrementer(entity_name="SUBSCRIBERADDRESS", subscriber_mysql_session=subscriber_mysql_session)

            # Get current time
            current_time = datetime.now()

            # Construct models
            """ subscribers = Subscriber(
            subscriber_id=new_subscriber_id,
            first_name=subscriber.subscriber_firstname,
            last_name=subscriber.subscriber_lastname,
            mobile=subscriber.subscriber_mobile,
            email_id=subscriber.subscriber_email,
            gender=subscriber.subscriber_gender,
            dob=datetime.strptime(subscriber.subscriber_dob, "%Y-%m-%d").date(),
            age=subscriber.subscriber_age,
            blood_group=subscriber.subscriber_blood_group,
            created_at=current_time,
            updated_at=current_time,
            active_flag=1
            ) """

            address = Address(
            address_id=new_address_id,
            address=subscriber.address,
            landmark=subscriber.landmark,
            pincode=subscriber.pincode,
            city=subscriber.city,
            state=subscriber.state,
            geolocation=subscriber.geolocation,
            created_at=current_time,
            updated_at=current_time,
            active_flag=1
            )

            subscriber_address = SubscriberAddress(
            subscriber_address_id=new_subscriber_address_id,
            address_type=subscriber.address_type,
            address_id=new_address_id,
            subscriber_id=subscriber_data.subscriber_id,
            created_at=current_time,
            updated_at=current_time,
            active_flag=1
            )

            # Call the DAL to add the subscriber. No new transaction is started in the DAL.
            await subscriber_setprofile_dal(
            create_subscribers_data=subscriber,
            create_address_data=address,
            create_subscriber_address_data=subscriber_address,
            subscriber_mysql_session=subscriber_mysql_session
            )

            # If this block completes without error, _async with_ will auto-commit.
            return SubscriberMessage(message="Subscriber Created Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error onboarding subscriber BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error BL")
        except Exception as e:
            logger.error(f"Error onboarding subscriber BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error BL")

async def subscriber_login_bl(subscriber_login:SubscriberLogin, subscriber_mysql_session:AsyncSession):
    try:
        # Call the DAL to get the subscriber by mobile number.
        if await check_data_exist_utils(table=Subscriber, field="mobile", subscriber_mysql_session=subscriber_mysql_session, data=subscriber_login.subscriber_mobile) == "unique":
                raise HTTPException(status_code=400, detail="Subscriber Not Exists")
        subscriber_login_data = await subscriber_login_dal(subscriber_login=subscriber_login, subscriber_mysql_session=subscriber_mysql_session)
        return SubscriberMessage(message="Subscriber Login Successful")
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error login subscriber BL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error BL")
    except Exception as e:
        logger.error(f"Error login subscriber BL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error BL")

async def subscriber_setmpin_bl(subscriber:SubscriberSetMpin, subscriber_mysql_session:AsyncSession):
    async with subscriber_mysql_session.begin():
        try:
            if await check_data_exist_utils(table=Subscriber, field="mobile", subscriber_mysql_session=subscriber_mysql_session, data=subscriber.subscriber_mobile) == "unique":
                raise HTTPException(status_code=400, detail="Subscriber Not Exists")
            if await check_data_exist_utils(table=UserAuth, field="mobile_number", subscriber_mysql_session=subscriber_mysql_session, data=subscriber.subscriber_mobile) != "unique":
                raise HTTPException(status_code=400, detail="Subscriber Mpin Already Exists")
            subscriber_mpin = UserAuth(
                mobile_number=subscriber.subscriber_mobile,
                mpin=subscriber.mpin,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                active_flag=1
            )
            subscriber_setmpin_data = await subscriber_setmpin_dal(subscriber_mpin=subscriber_mpin, subscriber_mysql_session=subscriber_mysql_session)
            return SubscriberMessage(message="Subscriber Mpin Created Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error setting mpin BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error BL")
        except Exception as e:
            logger.error(f"Error setting mpin BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error BL")

async def subscriber_update_mpin_bl(subscriber:SubscriberUpdateMpin, subscriber_mysql_session:AsyncSession):
    """
    Updates the MPIN (Mobile Personal Identification Number) for a subscriber in the database.

    This asynchronous function checks if the subscriber's mobile number exists in the database.
    If the mobile number does not exist, it raises an HTTPException. Otherwise, it updates the
    subscriber's MPIN using the provided data access layer (DAL) function.

    Args:
        subscriber (SubscriberUpdateMpin): An object containing the subscriber's mobile number
            and the new MPIN to be updated.
        subscriber_mysql_session (AsyncSession): An asynchronous SQLAlchemy session for interacting
            with the MySQL database.

    Returns:
        SubscriberMessage: A message indicating the success of the MPIN update operation.

    Raises:
        HTTPException: If the subscriber's mobile number does not exist or if an internal server
            error occurs during the update process.
        SQLAlchemyError: If a database-related error occurs.
        Exception: For any other unexpected errors.

    Logs:
        Logs errors related to database operations or unexpected exceptions.
    """
    async with subscriber_mysql_session.begin():
        try:
            if await check_data_exist_utils(table=UserAuth, field="mobile_number", subscriber_mysql_session=subscriber_mysql_session, data=subscriber.subscriber_mobile) == "unique":
                raise HTTPException(status_code=400, detail="Subscriber Mpin Not Exists")
            subscriber_update_mpin_data = await subscriber_updatempin_dal(subscriber_mpin=subscriber, subscriber_mysql_session=subscriber_mysql_session)
            return SubscriberMessage(message="Subscriber Mpin Updated Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error updating mpin BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error BL")
        except Exception as e:
            logger.error(f"Error updating mpin BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error BL")

async def update_subscriber_bl(subscriber:UpdateSubscriber, subscriber_mysql_session:AsyncSession):
    """
    Handles the business logic for updating a subscriber's details.

    This function updates the details of an existing subscriber using data passed to it and saves the changes in the MySQL database.

    Args:
        subscriber (UpdateSubscriber): The updated details of the subscriber, including the subscriber's ID and new data.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        SubscriberMessage: A message confirming the successful update of the subscriber.

    Raises:
        HTTPException: If any validation or HTTP-related error occurs.
        SQLAlchemyError: If there is an error interacting with the database.
        Exception: If an unexpected error occurs.
    """
    async with subscriber_mysql_session.begin(): # Outer transaction here
        try:
            updated_subscriber = await update_subscriber_dal(subscriber=subscriber, subscriber_mysql_session=subscriber_mysql_session)
            return SubscriberMessage(message="Subscriber Updated Successfully") #updated_subscriber
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error updating subscriber BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error BL")
        except Exception as e:
            logger.error(f"Unexpected error BL: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred BL")
    
async def get_subscriber_profile_bl(mobile: str, subscriber_mysql_session: AsyncSession):
    """
    Handles the business logic for retrieving a subscriber's profile by their mobile number.

    This function fetches a subscriber's profile and associated address details by querying the database.
    The profile includes personal and address information.

    Args:
        mobile (str): The mobile number of the subscriber whose profile is to be retrieved.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        dict: A dictionary containing the subscriber's profile and associated address details.

    Raises:
        HTTPException: If the subscriber is not found or any validation error occurs.
        SQLAlchemyError: If there is an error interacting with the database.
        Exception: If an unexpected error occurs.
    """

    try:
        #if check_data_exist_utils(table=Subscriber, field="mobile", mysql_session=mysql_session, data=mobile) == "unique":
        #    raise HTTPException(status_code=400, detail="No Subscriber Found With This Mobile Number")
        
        individual_subscriber = await get_subscriber_profile_dal(mobile=mobile, subscriber_mysql_session=subscriber_mysql_session)
        
        subscriber_address_list = []
        subscriber_address_data = await entity_data_return_utils(table=SubscriberAddress, field="subscriber_id", subscriber_mysql_session=subscriber_mysql_session, data=individual_subscriber["subscribers_data"].subscriber_id)
        for subscriber_address in subscriber_address_data:
            address = await get_data_by_id_utils(table=Address, field="address_id", subscriber_mysql_session=subscriber_mysql_session, data=subscriber_address.address_id)
            subscriber_address_list.append({
                "subscriber_address_id": subscriber_address.subscriber_address_id,
                "address_id": address.address_id,
                "subscriber_address_type": subscriber_address.address_type,
                "subscriber_address": address.address,
                "subscriber_landmark": address.landmark,
                "subscriber_city": address.city,
                "subscriber_state": address.state,
                "subscriber_pincode": address.pincode,
                "subsciiber_geolocation": address.geolocation,
            })
        
        subscriber_profie = {
            "subscriber_id": individual_subscriber["subscribers_data"].subscriber_id,
            "subscriber_first_name": individual_subscriber["subscribers_data"].first_name,
            "subscriber_last_name": individual_subscriber["subscribers_data"].last_name,
            "subscriber_mobile": individual_subscriber["subscribers_data"].mobile,
            "subscriber_email": individual_subscriber["subscribers_data"].email_id,
            "subscriber_gender": individual_subscriber["subscribers_data"].gender,
            "subscriber_dob": individual_subscriber["subscribers_data"].dob,
            "subscriber_age": individual_subscriber["subscribers_data"].age,
            "subscriber_blood_group": individual_subscriber["subscribers_data"].blood_group,
            "subscriber_created_at": individual_subscriber["subscribers_data"].created_at,
            "subscriber_updated_at": individual_subscriber["subscribers_data"].updated_at,
            "subscriber_address": subscriber_address_list}
        return subscriber_profie
    except HTTPException as http_exc:
        raise http_exc    
    except SQLAlchemyError as e:
        logger.error(f"Error fetching subscriber BL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error BL")
    except Exception as e:
        logger.error(f"Unexpected error BL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred BL")

async def create_subscriber_address_bl(subscriber_address:CreateSubscriberAddress, subscriber_mysql_session:AsyncSession):
    """
    Handles the business logic for creating a new subscriber address.

    This function creates a new address for a subscriber using the provided data and saves it in the MySQL database.

    Args:
        subscriber_address (CreateSubscriberAddress): The details of the new subscriber address to be created.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        SubscriberMessage: A message confirming the successful creation of the subscriber address.

    Raises:
        HTTPException: If any validation or HTTP-related error occurs.
        SQLAlchemyError: If there is an error interacting with the database.
        Exception: If an unexpected error occurs.
    """
    async with subscriber_mysql_session.begin(): # Outer transaction here
        try:
            subscriber_data = await get_data_by_id_utils(table=Subscriber, field="mobile", subscriber_mysql_session=subscriber_mysql_session, data=subscriber_address.subscriber_mobile)
            new_address_id = await id_incrementer(entity_name="ADDRESS", subscriber_mysql_session=subscriber_mysql_session)
            new_subscriber_address_id = await id_incrementer(entity_name="SUBSCRIBERADDRESS", subscriber_mysql_session=subscriber_mysql_session)

            if not subscriber_data:
                raise HTTPException(status_code=400, detail="Subscriber Not Exists")
            
            address_data = Address(
            address_id=new_address_id,
            address=subscriber_address.address,
            landmark=subscriber_address.landmark,
            pincode=subscriber_address.pincode,
            city=subscriber_address.city,
            state=subscriber_address.state,
            geolocation=subscriber_address.geolocation,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            active_flag=1
            )

            subscriber_address_data = SubscriberAddress(
            subscriber_address_id=new_subscriber_address_id,
            address_type=subscriber_address.address_type,
            address_id=new_address_id,
            subscriber_id=subscriber_data.subscriber_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            active_flag=1
            )

            await create_subscriber_address_dal(
                address=address_data, subscriber_address=subscriber_address_data, subscriber_mysql_session=subscriber_mysql_session
            )
            return SubscriberMessage(message="Subscriber Address Created Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error creating subscriber address BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error BL")
        except Exception as e:
            logger.error(f"Error creating subscriber address BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error BL")
        
async def update_subscriber_address_bl(update_subscriber_address:UpdateSubscriberAddress, subscriber_mysql_session:AsyncSession):
    async with subscriber_mysql_session.begin():
        try:
            updated_subscriber_address = await update_subscriber_address_dal(update_subscriber_address=update_subscriber_address, subscriber_mysql_session=subscriber_mysql_session)
            return SubscriberMessage(message="Subscriber Address Updated Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error updating subscriber address BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error BL")
        except Exception as e:
            logger.error(f"Error updating subscriber address BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error BL")

async def view_subscriber_address_bl(subscriber_mobile:str, subscriber_address_label:str, subscriber_mysql_session:AsyncSession):
    try:
        subscriber_data = await get_data_by_mobile(mobile=subscriber_mobile, field="mobile", table=Subscriber, subscriber_mysql_session=subscriber_mysql_session)
        if not subscriber_data:
            raise HTTPException(status_code=400, detail="Subscriber Not Exists")
        subscriber_address_data = await view_subscriber_address_dal(subscriber_id=subscriber_data.subscriber_id, subscriber_address_label=subscriber_address_label, subscriber_mysql_session=subscriber_mysql_session)
        address_data = await get_data_by_id_utils(table=Address, field="address_id", subscriber_mysql_session=subscriber_mysql_session, data=subscriber_address_data.address_id)
        subscriber_address_list = {
            "subscriber_address_id": subscriber_address_data.subscriber_address_id,
            "subscriber_address_type": subscriber_address_data.address_type,
            "subscriber_address": address_data.address,
            "subscriber_landmark": address_data.landmark,
            "subscriber_city": address_data.city,
            "subscriber_state": address_data.state,
            "subscriber_pincode": address_data.pincode,
            "subsciiber_geolocation": address_data.geolocation}
        return subscriber_address_list
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error fetching subscriber address BL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error BL")
    except Exception as e:
        logger.error(f"Error fetching subscriber address BL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error BL")
    
async def list_subscriber_address_bl(subscriber_mobile:str, subscriber_mysql_session:AsyncSession):
    """
    Fetches a list of subscriber addresses based on the subscriber's mobile number.

    This function retrieves subscriber data using the provided mobile number, 
    fetches associated address data, and compiles a list of subscriber address details.

    Args:
        subscriber_mobile (str): The mobile number of the subscriber.
        subscriber_mysql_session (AsyncSession): The asynchronous SQLAlchemy session 
            for interacting with the MySQL database.

    Returns:
        list[dict]: A list of dictionaries containing subscriber address details. 
            Each dictionary includes:
            - subscriber_address_id (int): The ID of the subscriber address.
            - subscriber_address_type (str): The type of the subscriber address.
            - address_id (int): The ID of the address.
            - subscriber_address (str): The address details.
            - subscriber_landmark (str): The landmark of the address.
            - subscriber_city (str): The city of the address.
            - subscriber_state (str): The state of the address.
            - subscriber_pincode (str): The pincode of the address.
            - subsciiber_geolocation (str): The geolocation of the address.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        HTTPException: If an internal server error occurs during processing.
        SQLAlchemyError: If a database-related error occurs.
        Exception: For any other unexpected errors.
    """
    try:
        subscriber_data = await get_data_by_mobile(mobile=subscriber_mobile, field="mobile", table=Subscriber, subscriber_mysql_session=subscriber_mysql_session)
        if not subscriber_data:
            raise HTTPException(status_code=400, detail="Subscriber Not Exists")
        subscriber_address_data = await list_subscriber_address_dal(subscriber_id=subscriber_data.subscriber_id, subscriber_mysql_session=subscriber_mysql_session)
        subscriber_address_list_data = []
        for subscriber_address in subscriber_address_data:
            address_data = await get_data_by_id_utils(table=Address, field="address_id", subscriber_mysql_session=subscriber_mysql_session, data=subscriber_address.address_id)
            subscriber_address_list = {
                "subscriber_address_id": subscriber_address.subscriber_address_id,
                "subscriber_address_type": subscriber_address.address_type,
                "address_id": address_data.address_id,
                "subscriber_address": address_data.address,
                "subscriber_landmark": address_data.landmark,
                "subscriber_city": address_data.city,
                "subscriber_state": address_data.state,
                "subscriber_pincode": address_data.pincode,
                "subsciiber_geolocation": address_data.geolocation}
            subscriber_address_list_data.append(subscriber_address_list)
        return subscriber_address_list_data
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error fetching subscriber address BL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error BL")
    except Exception as e:
        logger.error(f"Error fetching subscriber address BL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error BL")

async def healthhub_bl(subscriber_mysql_session: AsyncSession) -> list:
    """
    Fetches health hub data including doctor stacks, diagnostics, and service providers.

    This function interacts with multiple business logic layers to gather information
    about health hub entities. The data is structured into a list of dictionaries.

    Args:
        subscriber_mysql_session (AsyncSession): An async database session used for query execution.

    Returns:
        list: A list containing health hub data structured as dictionaries. Each dictionary includes:
              - Doctor: Data fetched from `health_hub_stacks_bl`.
              - Diagnostics: Data fetched from `get_hubby_dc_bl`.
              - Service_provider: Data fetched from `get_hubby_sp_bl`.

    Raises:
        HTTPException: If a validation or known error occurs during query execution.
        SQLAlchemyError: If a database-related error occurs while fetching data.
        Exception: If an unexpected error occurs.
    """
    try:
        healthhub_data = [
            {
                "Doctor": await health_hub_stacks_bl(subscriber_mysql_session=subscriber_mysql_session),
                "Diagnostics": await get_hubby_dc_bl(subscriber_mysql_session=subscriber_mysql_session),
                "Service_provider": await get_hubby_sp_bl(subscriber_mysql_session=subscriber_mysql_session)
            }
        ]
        return healthhub_data
    except SQLAlchemyError as e:
        logger.error(f"Error fetching healthhub BL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error BL")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error fetching healthhub BL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error BL")
