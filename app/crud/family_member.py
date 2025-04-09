from fastapi import Depends, HTTPException
from typing import List
from datetime import datetime
from ..models.subscriber import Address, Subscriber, FamilyMember, FamilyMemberAddress
from ..schemas.family_member import UpdateFamilyMember, SuspendFamilyMember
import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import asyncio

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def create_family_member_dal(
    create_family_member_data_dal,
    create_address_data_dal,
    create_family_member_address_dal,
    subscriber_mysql_session: AsyncSession
):
    """
    Creates a new family member along with their address and address mapping in the database.

    This function performs transactional operations to add a family member, their address, and the family member-to-address mapping.
    The transaction is rolled back if any operation fails, ensuring data integrity.

    Args:
        create_family_member_data_dal (FamilyMember): The family member data to be added to the database.
        create_address_data_dal (Address): The address data of the family member to be added.
        create_family_member_address_dal (FamilyMemberAddress): The mapping between the family member and their address.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        dict: A dictionary containing the created family member, their address, and address mapping.

    Raises:
        HTTPException: If there are validation or HTTP-related issues.
        SQLAlchemyError: If a database-related error occurs.
        Exception: If an unexpected error occurs.
    """

    try:
        subscriber_mysql_session.add(create_family_member_data_dal)
        subscriber_mysql_session.add(create_address_data_dal)     
        subscriber_mysql_session.add(create_family_member_address_dal)
        #await subscriber_mysql_session.commit()
        await subscriber_mysql_session.flush()
        await asyncio.gather(
            subscriber_mysql_session.refresh(create_family_member_data_dal),
            subscriber_mysql_session.refresh(create_address_data_dal),
            subscriber_mysql_session.refresh(create_family_member_address_dal)
        )
        return {
            "familymember": create_family_member_data_dal,
            "address": create_address_data_dal,
            "family_member_address": create_family_member_address_dal
        }

    except HTTPException as http_exc:
            await subscriber_mysql_session.rollback()
            raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error creating family member DAL: {e}")
        await subscriber_mysql_session.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error while creating family member DAL")
    except Exception as e:
        logger.error(f"Unexpected error DAL: {e}")
        await subscriber_mysql_session.rollback()
        raise HTTPException(status_code=500, detail="An unexpected error occurred DAL")
    
async def update_family_member_dal(familymember: UpdateFamilyMember, subscriber_mysql_session: AsyncSession):
    """
    Updates the details of an existing family member in the database.

    This function modifies the personal details of the family member, along with their address and mapping, 
    while ensuring consistency across all related records.

    Args:
        familymember (UpdateFamilyMember): The updated family member data, including fields like name, address, etc.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        UpdateFamilyMember: The updated family member data.

    Raises:
        HTTPException: If the family member is not found or if validation errors occur.
        SQLAlchemyError: If a database-related error occurs.
        Exception: If an unexpected error occurs.
    """

    try:
        familymember_db = await subscriber_mysql_session.execute(select(FamilyMember).filter(FamilyMember.familymember_id == familymember.family_member_id))
        familymember_db = familymember_db.scalars().first()
            
        if not familymember_db:
            raise HTTPException(status_code=404, detail="Family member not found")
            
            # Getting family member id
        family_member_id = familymember_db.familymember_id
            
        familymember_db.name = familymember.family_member_name
        familymember_db.mobile_number = familymember.family_member_mobile if familymember.family_member_mobile else None
        familymember_db.gender = familymember.family_member_gender
        familymember_db.dob = datetime.strptime(familymember.family_member_dob, "%Y-%m-%d").date()
        familymember_db.age = familymember.family_member_age
        familymember_db.blood_group = familymember.family_member_blood_group
        familymember_db.relation = familymember.family_member_relation
        familymember_db.updated_at = datetime.now()
            
        familymember_address_data = await subscriber_mysql_session.execute(select(FamilyMemberAddress).filter(FamilyMemberAddress.familymember_id == family_member_id))
        familymember_address_data = familymember_address_data.scalars().first()
            
        familymember_address_data.updated_at = datetime.now()
            
            # Getting the Family member address id
        familymember_address_id = familymember_address_data.address_id
            
        familymember_address = await subscriber_mysql_session.execute(select(Address).filter(Address.address_id == familymember_address_id))
        familymember_address = familymember_address.scalars().first()
            
        familymember_address.updated_at = datetime.now()
        familymember_address.address = familymember.family_member_address
        familymember_address.landmark = familymember.family_member_landmark
        familymember_address.pincode = familymember.family_member_pincode
        familymember_address.city = familymember.family_member_city
        familymember_address.state = familymember.family_member_state
        familymember_address.geolocation = familymember.family_member_geolocation
        familymember_address.updated_at = datetime.now()
        
        #await subscriber_mysql_session.commit()
        await subscriber_mysql_session.flush()
        await asyncio.gather(
            subscriber_mysql_session.refresh(familymember_db),
            subscriber_mysql_session.refresh(familymember_address),
            subscriber_mysql_session.refresh(familymember_address_data)
        )
        return familymember
    
    except HTTPException as http_exc:
        await subscriber_mysql_session.rollback()
        raise http_exc
    except SQLAlchemyError as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error updating family member DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while updating family member DAL")
    except Exception as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Unexpected error DAL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred DAL")

async def family_member_suspend_dal(familymember: SuspendFamilyMember, subscriber_mysql_session: AsyncSession):
    """
    Suspends a family member or modifies their active status in the database.

    This function updates the `active_flag` field for a family member, their address, and their address mapping.
    The suspension may involve setting the status to active (1), deleted (0), or suspended (2).

    Args:
        familymember (SuspendFamilyMember): The details required to suspend the family member, including their ID, active status, and remarks.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        SuspendFamilyMember: The suspended family member details.

    Raises:
        HTTPException: If the family member or their address is not found.
        SQLAlchemyError: If a database-related error occurs.
        Exception: If an unexpected error occurs.
    """

    try:
        familymember_db = await subscriber_mysql_session.execute(select(FamilyMember).filter(FamilyMember.familymember_id == familymember.family_member_id))
        familymember_db = familymember_db.scalars().first()
            
        if not familymember_db:
            raise HTTPException(status_code=404, detail="Family member not found")
            
        familymember_db.active_flag = familymember.active_flag
        familymember_db.remarks = familymember.remarks
        familymember_db.updated_at = datetime.now()
            
        # Getting the family member id
        family_member_id = familymember_db.familymember_id
            
        familymember_address = await subscriber_mysql_session.execute(select(FamilyMemberAddress).filter(FamilyMemberAddress.familymember_id == family_member_id))
        familymember_address = familymember_address.scalars().first()
        if familymember_address:
            familymember_address.active_flag = familymember.active_flag
            familymember_address.updated_at = datetime.now()
                
            # Getting the address_id 
            address_id = familymember_address.address_id
                
            familymember_address_data = await subscriber_mysql_session.execute(select(Address).filter(Address.address_id == address_id))
            familymember_address_data = familymember_address_data.scalars().first()
            if familymember_address_data:
                familymember_address_data.active_flag = familymember.active_flag
                familymember_address_data.updated_at = datetime.now()
                    
        #await subscriber_mysql_session.commit()
        await subscriber_mysql_session.flush()
        await asyncio.gather(
            subscriber_mysql_session.refresh(familymember_db),
            subscriber_mysql_session.refresh(familymember_address),
            subscriber_mysql_session.refresh(familymember_address_data)
        )
        return familymember
    
    except HTTPException as http_exc:
        await subscriber_mysql_session.rollback()
        raise http_exc
    except SQLAlchemyError as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error suspending family member DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while suspending family member DAL")
    except Exception as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Unexpected error DAL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred DAL")

async def family_member_list_dal(subscriber_mobile, subscriber_mysql_session: AsyncSession):
    """
    Retrieves a list of all family members associated with a subscriber.

    This function fetches all active family members of a subscriber based on their mobile number. 
    It ensures the subscriber exists before returning their associated family members.

    Args:
        subscriber_mobile (str): The mobile number of the subscriber whose family members are to be retrieved.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        list: A list of `FamilyMember` objects containing the details of active family members.

    Raises:
        HTTPException: If the subscriber or their family members are not found.
        SQLAlchemyError: If a database-related error occurs.
        Exception: If an unexpected error occurs.
    """

    try:
        subscriber_data = await subscriber_mysql_session.execute(select(Subscriber).filter(Subscriber.mobile == subscriber_mobile))
        subscriber_data = subscriber_data.scalars().first()
        
        if not subscriber_data:
            raise HTTPException(status_code=404, detail="Subscriber not found")
        
        # subscriber id
        subscriber_id = subscriber_data.subscriber_id
        
        # family member list
        family_member_data = await subscriber_mysql_session.execute(select(FamilyMember).filter(FamilyMember.subscriber_id == subscriber_id, FamilyMember.active_flag == 1))
        family_member_data = family_member_data.scalars().all()
        
        return family_member_data
    
    except HTTPException as http_exc:
        await subscriber_mysql_session.rollback()
        raise http_exc
    except SQLAlchemyError as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error getting family member list DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while getting family member list DAL")
    except Exception as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Unexpected error DAL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred DAL")
    