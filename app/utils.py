import os
import shutil
from .models.subscriber import IdGenerator
from fastapi import File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime
import re
from sqlalchemy.future import select

#configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def id_incrementer(entity_name: str, subscriber_mysql_session: AsyncSession) -> str:
    """
    Increments the ID for a specific entity.

    This function retrieves the last generated ID for a given entity, increments the numeric part, 
    preserves leading zeros, and updates the record in the database.

    Args:
        entity_name (str): The name of the entity for which the ID is being generated.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        str: The newly generated and incremented ID (e.g., ICDOC0001).

    Raises:
        HTTPException: If the entity is not found.
        SQLAlchemyError: If a database error occurs during the operation.
    """
    try:
        print("entered to the id incrementor logic to get the ids (utils)")
        id_data = await subscriber_mysql_session.execute(select(IdGenerator).where(IdGenerator.entity_name == entity_name, IdGenerator.active_flag == 1).order_by(IdGenerator.generator_id.desc()))
        id_data = id_data.scalar()
        if id_data:
            last_code = id_data.last_code
            match = re.match(r"([A-Za-z]+)(\d+)", str(last_code))
            prefix, number = match.groups()
            incremented_number = str(int(number) + 1).zfill(len(number))  # Preserve leading zeros
            new_code = f"{prefix}{incremented_number}"
            id_data.last_code = new_code
            id_data.updated_at = datetime.now()
            #await subscriber_mysql_session.commit()
            await subscriber_mysql_session.flush()
            print("-------------- the returned id", new_code)
            return new_code
        else:  
            raise HTTPException(status_code=404, detail="Entity not found")
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

async def check_data_exist_utils(table, field: str, subscriber_mysql_session: AsyncSession, data: str):
    """
    Checks whether a specific value exists in a given table.

    This function checks if the provided value exists for the specified field in the given table. 
    If the value exists, the corresponding entity data is returned; otherwise, "unique" is returned.

    Args:
        table: The SQLAlchemy table model to query.
        field (str): The name of the field to check.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.
        data (str): The value to check for existence.

    Returns:
        object | str: The entity data if it exists, otherwise "unique".

    Raises:
        SQLAlchemyError: If a database error occurs during the operation.
    """
    try:
        result = await subscriber_mysql_session.execute(select(table).filter(getattr(table, field) == data))
        entity_data = result.scalars().first()
        return entity_data if entity_data else "unique"
    except SQLAlchemyError as e:
        logger.error(f"Database error while checking data existence in utils: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while checking data existence in utils: " + str(e))

async def get_data_by_id_utils(table, field: str, subscriber_mysql_session: AsyncSession, data):
    """
    Fetches data by a specific ID from a given table.

    This function retrieves a record from the specified table based on the provided field and value.

    Args:
        table: The SQLAlchemy table model to query.
        field (str): The name of the field to filter by.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.
        data: The value of the field to filter by.

    Returns:
        object: The entity data retrieved from the database.

    Raises:
        SQLAlchemyError: If a database error occurs during the operation.
    """
    try:
        result = await subscriber_mysql_session.execute(select(table).filter(getattr(table, field) == data))
        entity_data = result.scalars().first()
        return entity_data
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching data by ID in utils: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching data by ID in utils: " + str(e))

async def entity_data_return_utils(table, field: str, subscriber_mysql_session: AsyncSession, data: str):
    """
    Fetches all data for a specific value from a given table.

    This function retrieves all records from the specified table that match the provided field and value.

    Args:
        table: The SQLAlchemy table model to query.
        field (str): The name of the field to filter by.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.
        data (str): The value of the field to filter by.

    Returns:
        list: A list of entity data matching the provided criteria.

    Raises:
        SQLAlchemyError: If a database error occurs during the operation.
    """

    try:
        result = await subscriber_mysql_session.execute(select(table).filter(getattr(table, field) == data))
        entity_data = result.scalars().all()
        return entity_data
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching entity data in utils: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching entity data in utils: " + str(e))

async def get_data_by_mobile(mobile, field: str, table, subscriber_mysql_session: AsyncSession):
    """
    Fetches an entity's data by mobile number.

    This function retrieves a record from the specified table based on the provided mobile number.

    Args:
        mobile (str): The mobile number to filter by.
        field (str): The name of the field to filter by (e.g., "mobile").
        table: The SQLAlchemy table model to query.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        object: The entity data retrieved from the database.

    Raises:
        SQLAlchemyError: If a database error occurs during the operation.
    """
    try:
        result = await subscriber_mysql_session.execute(select(table).filter(getattr(table, field) == mobile))
        entity_data = result.scalars().first()
        return entity_data
    except SQLAlchemyError as e:
        logger.error(f"Database error while getting data by mobile in utils: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while getting data by mobile in utils")

