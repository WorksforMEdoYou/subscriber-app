from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from ..models.subscriber import Address, FamilyMember, FamilyMemberAddress
from ..schemas.family_member import CreateFamilyMember, UpdateFamilyMember, SuspendFamilyMember, FamilyMemberMessage
from ..utils import get_data_by_id_utils, id_incrementer
from ..crud.family_member import create_family_member_dal, update_family_member_dal, family_member_suspend_dal, family_member_list_dal
from datetime import datetime

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def create_family_member_bl(familymember: CreateFamilyMember, subscriber_mysql_session: AsyncSession):
    """
    Handles the business logic for creating a family member.

    This function creates a new family member along with their address and a family member-to-address mapping.
    It assigns unique IDs to each record, saves them to the database, and ensures transactional consistency.

    Args:
        familymember (CreateFamilyMember): The details of the new family member, including name, mobile, gender, age, address, etc.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        FamilyMemberMessage: A response message confirming the successful creation of the family member.

    Raises:
        HTTPException: If a validation error or HTTP-related error occurs.
        SQLAlchemyError: If there is an error interacting with the database.
        Exception: If an unexpected error occurs.
    """
    async with subscriber_mysql_session.begin(): # Outer transaction here
        try:
            new_family_member_id = await id_incrementer(entity_name="FAMILYMEMBER", subscriber_mysql_session=subscriber_mysql_session)
            new_family_address_id = await id_incrementer(entity_name="ADDRESS", subscriber_mysql_session=subscriber_mysql_session)
            new_family_member_address_id = await id_incrementer(entity_name="FAMILYMEMBERADDRESS", subscriber_mysql_session=subscriber_mysql_session)
            # Create a new family member
            create_family_member_data = FamilyMember(
            familymember_id=new_family_member_id,
            name=familymember.family_member_name,
            mobile_number=familymember.family_member_mobile if familymember.family_member_mobile!=None else 0,
            gender=familymember.family_member_gender,
            dob=datetime.strptime(familymember.family_member_dob, "%Y-%m-%d").date(),
            age=familymember.family_member_age,
            blood_group=familymember.family_member_blood_group,
            relation=familymember.family_member_relation,
            subscriber_id=familymember.family_member_subscriber_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            active_flag=1,
            remarks=""
            )
        
            # address
            create_address_data = Address(
            address_id=new_family_address_id,
            address=familymember.family_member_address,
            landmark=familymember.family_member_landmark,
            pincode=familymember.family_member_pincode,
            city=familymember.family_member_city,
            state=familymember.family_member_state,
            geolocation=familymember.family_member_geolocation,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            active_flag=1
            )
        
            create_family_member_address = FamilyMemberAddress(
            familymember_address_id = new_family_member_address_id,
            address_type="core",
            address_id=create_address_data.address_id,
            familymember_id=create_family_member_data.familymember_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            active_flag=1
            )
        
            created_family_member = await create_family_member_dal(create_family_member_data_dal=create_family_member_data, create_address_data_dal=create_address_data, create_family_member_address_dal=create_family_member_address, subscriber_mysql_session=subscriber_mysql_session)
            return FamilyMemberMessage(message="Family Member onboarded Successfully") #created_family_member
    
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error in creating family member BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error BL")
        except Exception as e:
            logger.error(f"Unexpected error BL: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred BL")
    
async def update_family_member_bl(familymember: UpdateFamilyMember, subscriber_mysql_session: AsyncSession):
    """
    Handles the business logic for updating a family member's details.

    This function updates an existing family member's personal and address information in the database.

    Args:
        familymember (UpdateFamilyMember): The updated data for the family member, including ID, name, address, and other fields.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        FamilyMemberMessage: A response message confirming the successful update of the family member.

    Raises:
        HTTPException: If the family member is not found or if any validation error occurs.
        SQLAlchemyError: If there is an error interacting with the database.
        Exception: If an unexpected error occurs.
"""
    async with subscriber_mysql_session.begin(): # Outer transaction here
        try:
            updated_family_member = await update_family_member_dal(familymember=familymember, subscriber_mysql_session=subscriber_mysql_session)
            return FamilyMemberMessage(message="Family Member Updated Successfully") #updated_family_member
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error updating family member BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error BL")
        except Exception as e:
            logger.error(f"Unexpected error BL: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred BL")
    
async def suspend_family_member_bl(familymember: SuspendFamilyMember, subscriber_mysql_session: AsyncSession):
    """
    Handles the business logic for suspending a family member.

    This function updates the family member's status to indicate that they are suspended. Suspension may
    temporarily disable their participation in the subscriber's account or system.

    Args:
        familymember (SuspendFamilyMember): The details required to suspend the family member, including their ID.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        FamilyMemberMessage: A response message confirming the successful suspension of the family member.

    Raises:
        HTTPException: If the family member is not found or if any validation error occurs.
        SQLAlchemyError: If there is an error interacting with the database.
        Exception: If an unexpected error occurs.
"""
    async with subscriber_mysql_session.begin(): # Outer transaction here
        try:
            suspended_family_memner = await family_member_suspend_dal(familymember=familymember, subscriber_mysql_session=subscriber_mysql_session)
            return FamilyMemberMessage(message="Family Member Suspended Successfully") #suspended_family_memner
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error suspending family member BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error BL")
        except Exception as e:
            logger.error(f"Unexpected error BL: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred BL")
    
async def get_family_members_bl(subscriber_mobile:str, subscriber_mysql_session:AsyncSession):
    """
    Handles the business logic for retrieving a list of family members associated with a subscriber.

    This function fetches the list of family members based on the subscriber's mobile number and gathers
    their personal and address details. It returns a comprehensive list of family members and their associated data.

    Args:
        subscriber_mobile (str): The mobile number of the subscriber whose family members are to be retrieved.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        list: A list of dictionaries containing detailed information about each family member, 
          including personal details and address.

    Raises:
        HTTPException: If the subscriber or their family members are not found, or if any validation error occurs.
        SQLAlchemyError: If there is an error interacting with the database.
        Exception: If an unexpected error occurs.
    """

    try:
        family_member_list_data = []
        #if check_data_exist_utils(data=subscriber_mobile, table=Subscriber, field="mobile", mysql_session=mysql_session)=="unique":
        #    raise HTTPException(status_code=404, detail="Family member with this mobile number not available")
        family_member_list = await family_member_list_dal(subscriber_mobile=subscriber_mobile, subscriber_mysql_session=subscriber_mysql_session)
        for person in family_member_list:
            familymember_id = person.familymember_id
            familymember_address_data = await get_data_by_id_utils(table=FamilyMemberAddress, field="familymember_id", subscriber_mysql_session=subscriber_mysql_session, data=familymember_id)
            address_id = familymember_address_data.address_id
            address_data = await get_data_by_id_utils(table=Address, field="address_id", subscriber_mysql_session=subscriber_mysql_session, data=address_id)
            family_member_list_data.append(
                {
                    "family_member_id": person.familymember_id,
                    "family_member_name": person.name,
                    "family_member_mobile": person.mobile_number if person.mobile_number else None,
                    "family_member_gender": person.gender,
                    "family_member_dob": person.dob,
                    "family_member_age": person.age,
                    "family_member_blood_group": person.blood_group,
                    "family_member_relation": person.relation,
                    "family_member_created_at": person.created_at,
                    "family_member_updated_at": person.updated_at,
                    "family_member_active_flag": person.active_flag,
                    "family_member_remarks": person.remarks,
                    "family_member_address_id": address_data.address_id,
                    "family_member_address": address_data.address,
                    "family_member_landmark": address_data.landmark,
                    "family_member_pincode": address_data.pincode,
                    "family_member_city": address_data.city,
                    "family_member_state": address_data.state,
                    "family_member_geolocation": address_data.geolocation,
                    "family_member_address_address_id": familymember_address_data.familymember_address_id,
                    "family_member_address_type": familymember_address_data.address_type,
                }
            )
        return family_member_list_data
    
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error getting family members BL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error BL")
    except Exception as e:
        logger.error(f"Unexpected error BL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred BL")
            