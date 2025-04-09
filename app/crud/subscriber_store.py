from fastapi import Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import logging
from typing import List, Optional
from datetime import datetime
from ..models.subscriber import DoctorAppointment, Doctor, DoctorQualification, OrderItem, Prescription, MedicinePrescribed, Doctoravbltylog, DoctorsAvailability, Specialization, productMaster, Orders, OrderStatus, StoreDetails
from ..schemas.subscriber import UpdateAppointment, CancelAppointment

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def get_medicine_products_dal(subscriber_mysql_session:AsyncSession):
    """
    Data Access Layer function to fetch medicine products.

    This function queries the database to retrieve all medicine products.

    Args:
        subscriber_mysql_session (AsyncSession): An asynchronous database session for querying the MySQL database.

    Returns:
        list: A list of `MedicineProduct` objects containing medicine product details.

    Raises:
        HTTPException: Raised if an HTTP-related error occurs during the query process.
        SQLAlchemyError: Raised when a database-related error occurs.
        Exception: Raised for any unexpected errors during the execution.
"""

    try:
        result = await subscriber_mysql_session.execute(select(productMaster).filter(productMaster.active_flag==1, productMaster.product_type=="medicine"))
        medicine_products = result.scalars().all()
        return medicine_products
    except SQLAlchemyError as e:
        logger.error(f"Error fetching medicine products DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching medicine products DAL")
    except Exception as e:
        logger.error(f"Error fetching medicine products DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching medicine products DAL")
    
async def create_order_dal(order_data, subscriber_mysql_session:AsyncSession):
    """
    Data Access Layer function to create an order.

    This function inserts the order details into the database.

    Args:
        order_data (dict): The order details to be inserted.
        subscriber_mysql_session (AsyncSession): An asynchronous database session for querying the MySQL database.

    Returns:
        dict: The order details that were inserted.

    Raises:
        HTTPException: Raised if an HTTP-related error occurs during the query process.
        SQLAlchemyError: Raised when a database-related error occurs.
        Exception: Raised for any unexpected errors during the execution.
"""

    try:
        subscriber_mysql_session.add(order_data)
        await subscriber_mysql_session.flush()
        #await subscriber_mysql_session.refresh(order_data)
        return order_data
    except SQLAlchemyError as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error creating order DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in creating order DAL")
    except Exception as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error creating order DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in creating order DAL")
    
async def create_order_item_dal(order_item: OrderItem, subscriber_mysql_session: AsyncSession) -> OrderItem:
    """
    Inserts a new order item into the database.

    Args:
        order_item (OrderItem): The order item object to be added to the database.
        subscriber_mysql_session (AsyncSession): An async database session for query execution.

    Returns:
        OrderItem: The inserted order item object.

    Raises:
        HTTPException: For validation or known errors.
        SQLAlchemyError: For database-related errors during execution.
        Exception: For any unexpected errors.
    """
    try:
        subscriber_mysql_session.add(order_item)
        await subscriber_mysql_session.flush()
        return order_item
    except SQLAlchemyError as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error creating order item DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in creating order item DAL")
    except Exception as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error creating order item DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in creating order item DAL")
    
async def create_order_status_dal(order_status: OrderStatus, subscriber_mysql_session: AsyncSession) -> OrderStatus:
    """
    Inserts a new order status into the database.

    Args:
        order_status (OrderStatus): The order status object to be added to the database.
        subscriber_mysql_session (AsyncSession): An async database session for query execution.

    Returns:
        OrderStatus: The inserted order status object.

    Raises:
        HTTPException: For validation or known errors.
        SQLAlchemyError: For database-related errors during execution.
        Exception: For any unexpected errors.
    """
    try:
        subscriber_mysql_session.add(order_status)
        await subscriber_mysql_session.flush()
        return order_status
    except SQLAlchemyError as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error creating order status DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in creating order status DAL")
    except Exception as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error creating order status DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in creating order status DAL")

async def store_mobile(subscriber_mysql_session: AsyncSession) -> list:
    """
    Fetches the mobile numbers of all stores.

    Args:
        subscriber_mysql_session (AsyncSession): An async database session for query execution.

    Returns:
        list: A list of mobile numbers associated with the stores.

    Raises:
        HTTPException: For validation or known errors.
        SQLAlchemyError: For database-related errors during execution.
        Exception: For any unexpected errors.
    """
    try:
        mobile = await subscriber_mysql_session.execute(select(StoreDetails.mobile))
        return mobile.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Error in store mobile DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in store mobile DAL")
    except Exception as e:
        logger.error(f"Error in store mobile DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in store mobile DAL")

async def get_batch_pricing_dal(store_id, item, batch, subscriber_mongodb_session):
    try:
        pricing = await subscriber_mongodb_session["pricing"].find_one({"store_id": store_id, "product_id": item, "batch_number": batch})
        if pricing:
            pricing["_id"] = str(pricing["_id"]) 
            return pricing
    except Exception as e:
        logger.error(f"Database error in fetching pricing by batch DAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching pricing by batch DAL: " + str(e))


async def store_stock_check_dal(
    product_id: str,
    quantity: int,
    store_id: str,
    subscriber_mongodb_session
) -> Optional[dict]:
    """
    Checks if the specified store has sufficient stock for the given product.

    Args:
        product_id (str): The ID of the product to check.
        quantity (int): The required quantity of the product.
        store_id (str): The ID of the store.
        subscriber_mongodb_session: A MongoDB session for executing queries.

    Returns:
        Optional[dict]: A dictionary representing the store stock if available, otherwise None.

    Raises:
        HTTPException: For validation or known errors.
        Exception: For any unexpected errors.
    """
    try:
        store_stock = await subscriber_mongodb_session.stocks.find_one({
            "store_id": store_id,
            "product_id": product_id,
            "available_stock": {"$gte": quantity},
            "active_flag": 1
        })
        return store_stock if store_stock else None
    except Exception as e:
        logger.error(f"Error checking store stock DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in checking store stock DAL")
    
async def get_healthcare_products_dal(subscriber_mysql_session: AsyncSession) -> list:
    """
    Fetches a list of healthcare products from the database.

    Args:
        subscriber_mysql_session (AsyncSession): An async database session for query execution.

    Returns:
        list: A list of healthcare products excluding medicines.

    Raises:
        HTTPException: For validation or known errors.
        SQLAlchemyError: For database-related errors during execution.
        Exception: For any unexpected errors.
    """
    try:
        result = await subscriber_mysql_session.execute(
            select(productMaster).filter(productMaster.active_flag == 1, productMaster.product_type != "medicine")
        )
        healthcare_products = result.scalars().all()
        return healthcare_products
    except SQLAlchemyError as e:
        logger.error(f"Error fetching healthcare products DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching healthcare products DAL")
    except Exception as e:
        logger.error(f"Error fetching healthcare products DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching healthcare products DAL")
    
async def orders_list_dal(subscriber_id: str, subscriber_mysql_session: AsyncSession) -> list:
    """
    Fetches a list of orders for a given subscriber.

    Args:
        subscriber_id (str): The unique ID of the subscriber.
        subscriber_mysql_session (AsyncSession): An async database session for query execution.

    Returns:
        list: A list of orders associated with the subscriber.

    Raises:
        HTTPException: For validation or known errors.
        SQLAlchemyError: For database-related errors during execution.
        Exception: For any unexpected errors.
    """
    try:
        orders_list = await subscriber_mysql_session.execute(
            select(Orders).join(OrderStatus, Orders.order_id == OrderStatus.order_id)
            .where(Orders.subscriber_id == subscriber_id)
        )
        orders = orders_list.unique().scalars().all()
        return orders
    except SQLAlchemyError as e:
        logger.error(f"Error fetching orders list DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching orders list DAL")
    except Exception as e:
        logger.error(f"Error fetching orders list DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching orders list DAL")

async def view_prescribed_products_dal(subscriber_id: str, subscriber_mysql_session: AsyncSession) -> list:
    """
    Fetches prescribed products for a given subscriber.

    Args:
        subscriber_id (str): The unique ID of the subscriber.
        subscriber_mysql_session (AsyncSession): An async database session for query execution.

    Returns:
        list: A list of prescriptions and their associated prescribed medicines.

    Raises:
        HTTPException: For validation or known errors.
        SQLAlchemyError: For database-related errors during execution.
        Exception: For any unexpected errors.
    """
    try:
        prescribed_products = await subscriber_mysql_session.execute(
            select(Prescription)
            .join(DoctorAppointment, Prescription.appointment_id == DoctorAppointment.appointment_id)
            .where(
                DoctorAppointment.subscriber_id == subscriber_id,
                DoctorAppointment.status == "Completed"
            )
            .options(selectinload(Prescription.medicine_prescribed))
        )
        return prescribed_products.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching prescribed products DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching prescribed products DAL")
    except Exception as e:
        logger.error(f"Error fetching prescribed products DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching prescribed products DAL")

async def subscriber_hubbystore_dal(subscriber_mysql_session: AsyncSession) -> int:
    """
    Fetches the total count of subscriber hub stores.

    Args:
        subscriber_mysql_session (AsyncSession): An async database session for query execution.

    Returns:
        int: The count of subscriber hub stores.

    Raises:
        HTTPException: For validation or known errors.
        SQLAlchemyError: For database-related errors during execution.
        Exception: For any unexpected errors.
    """
    try:
        result = await subscriber_mysql_session.execute(
            select(func.count()).select_from(StoreDetails)
        )
        return result.scalar()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching subscriber hub store DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching subscriber hub store DAL")
    except Exception as e:
        logger.error(f"Error fetching subscriber hub store DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server error in fetching the hub store")                            
    