import asyncio
import re
from fastapi import Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List
from datetime import datetime
from ..models.subscriber import  Manufacturer, Category, Orders, OrderItem, OrderStatus, StoreDetails, MedicinePrescribed, productMaster, Subscriber, productMaster
from ..schemas.subscriber import SubscriberMessage, SubscriberStoreSearch, CreateOrder, SubscriberCartProduct
from ..utils import check_data_exist_utils, entity_data_return_utils , get_data_by_id_utils, id_incrementer, get_data_by_mobile, hyperlocal_search_store
from ..crud.subscriber_store import ( get_medicine_products_dal, create_order_dal, create_order_item_dal, create_order_status_dal, store_stock_check_dal, get_healthcare_products_dal, orders_list_dal, view_prescribed_products_dal, subscriber_hubbystore_dal, store_mobile, get_batch_pricing_dal)
from sqlalchemy.ext.asyncio import AsyncSession

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def get_medicine_products_bl(subscriber_mysql_session: AsyncSession) -> list:
    """
    Fetches the list of medicine products.

    This function interacts with the Data Access Layer to retrieve medicine product information
    from the database. It maps product details into a list of dictionaries for easy access.

    Args:
        subscriber_mysql_session (AsyncSession): An async database session used to execute queries.

    Returns:
        list: A list of dictionaries, each containing details of a medicine product, such as:
              - Product ID
              - Product Name
              - Product Type
              - HSN Code
              - Product Form
              - Unit of Measure
              - Product Composition
              - Manufacturer Details
              - Category Details
              - Remarks

    Raises:
        HTTPException: If no medicine products are found or for validation-related errors.
        SQLAlchemyError: If there is a database-related error during retrieval.
        Exception: If an unexpected error occurs.
    """
    try:
        product_medicine_data = await get_medicine_products_dal(subscriber_mysql_session=subscriber_mysql_session)
        if not product_medicine_data:
            raise HTTPException(status_code=404, detail="No medicine products found")
        medicine_list = [
            {
                "product_id": medicine.product_id,
                "product_name": medicine.product_name,
                "product_type": medicine.product_type,
                "product_hsn_code": medicine.hsn_code,
                "product_form": medicine.product_form,
                "unit_of_measure": medicine.unit_of_measure,
                "product_composition": medicine.composition,
                "product_manufacturer_id": medicine.manufacturer_id,
                "product_manufacturer_name": (
                    await get_data_by_id_utils(
                        table=Manufacturer,
                        field="manufacturer_id",
                        subscriber_mysql_session=subscriber_mysql_session,
                        data=medicine.manufacturer_id
                    )
                ).manufacturer_name,
                "product_category_id": medicine.category_id,
                "product_category_name": (
                    await get_data_by_id_utils(
                        table=Category,
                        field="category_id",
                        subscriber_mysql_session=subscriber_mysql_session,
                        data=medicine.category_id
                    )
                ).category_name,
                "product_remarks": medicine.remarks,
            }
            for medicine in product_medicine_data
        ]
        return medicine_list
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"get_medicine_products BL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting medicine products BL")
    except Exception as e:
        logger.error(f"Unexpected error BL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred BL")


async def get_healthcare_products_bl(subscriber_mysql_session: AsyncSession) -> list:
    """
    Fetches the list of healthcare products.

    This function interacts with the Data Access Layer to retrieve healthcare product information
    from the database. It maps product details into a list of dictionaries for easy access.

    Args:
        subscriber_mysql_session (AsyncSession): An async database session used to execute queries.

    Returns:
        list: A list of dictionaries, each containing details of a healthcare product, such as:
              - Product ID
              - Product Name
              - Product Type
              - HSN Code
              - Product Form
              - Unit of Measure
              - Product Composition
              - Manufacturer Details
              - Category Details
              - Remarks

    Raises:
        HTTPException: If no healthcare products are found or for validation-related errors.
        SQLAlchemyError: If there is a database-related error during retrieval.
        Exception: If an unexpected error occurs.
    """
    try:
        product_healthcare_data = await get_healthcare_products_dal(subscriber_mysql_session=subscriber_mysql_session)
        if not product_healthcare_data:
            raise HTTPException(status_code=404, detail="No healthcare products found")
        healthcare_list = [
            {
                "product_id": healthcare.product_id,
                "product_name": healthcare.product_name,
                "product_type": healthcare.product_type,
                "product_hsn_code": healthcare.hsn_code,
                "product_form": healthcare.product_form,
                "unit_of_measure": healthcare.unit_of_measure,
                "product_composition": healthcare.composition,
                "product_manufacturer_id": healthcare.manufacturer_id,
                "product_manufacturer_name": (
                    await get_data_by_id_utils(
                        table=Manufacturer,
                        field="manufacturer_id",
                        subscriber_mysql_session=subscriber_mysql_session,
                        data=healthcare.manufacturer_id
                    )
                ).manufacturer_name,
                "product_category_id": healthcare.category_id,
                "product_category_name": (
                    await get_data_by_id_utils(
                        table=Category,
                        field="category_id",
                        subscriber_mysql_session=subscriber_mysql_session,
                        data=healthcare.category_id
                    )
                ).category_name,
                "product_remarks": healthcare.remarks,
            }
            for healthcare in product_healthcare_data
        ]
        return healthcare_list
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"get_healthcare_products BL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting healthcare products BL")
    except Exception as e:
        logger.error(f"Unexpected error BL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred BL")

async def store_search_bl(
    search_data: SubscriberStoreSearch,
    subscriber_mysql_session: AsyncSession,
    subscriber_mongodb_session
):
    """
    Performs a store search for the subscriber based on their cart items.

    This function retrieves hyper-local stores, categorizes them based on delivery options,
    and checks if the items in the subscriber's cart are available in these stores.

    Args:
        search_data (SubscriberStoreSearch): The search criteria, including the subscriber's cart items.
        subscriber_mysql_session (AsyncSession): An async database session for MySQL queries.
        subscriber_mongodb_session: A database session for MongoDB queries.

    Returns:
        dict: A dictionary containing two lists:
              - "home_delivery_stores": Stores offering home delivery.
              - "In_stores": Stores requiring in-store purchases.

    Raises:
        HTTPException: If there is a validation or known error.
        SQLAlchemyError: For database-related errors during execution.
        Exception: For any unexpected errors.
    """
    try:
        #hyper_local_search = await store_mobile(subscriber_mysql_session=subscriber_mysql_session)
        hyper_local_search = await hyperlocal_search_store(user_lat=search_data.subscriber_latitude, user_lon=search_data.subscriber_longitude, radius_km=search_data.radius_km, subscriber_mysql_session=subscriber_mysql_session)
        
        home_delivery_stores_list = []
        non_home_delivery_stores_list = []

        for store in hyper_local_search:
            store = (await get_data_by_id_utils(
                table=StoreDetails,
                field="mobile",
                subscriber_mysql_session=subscriber_mysql_session,
                data=store
            )).store_id

            if await subscriber_cart_bl(
                store_id=store,
                cart_data=search_data.cart_products,
                subscriber_mongodb_session=subscriber_mongodb_session
            ):
                store_data = await get_data_by_id_utils(
                    table=StoreDetails,
                    field="store_id",
                    subscriber_mysql_session=subscriber_mysql_session,
                    data=store
                )
                
                product_price = await store_stock_helper(store_id=store, cart_data=search_data.cart_products, subscriber_mongodb_session=subscriber_mongodb_session, subscriber_mysql_session=subscriber_mysql_session)
                
                store_info = {
                    "store_id": store,
                    "store_name": store_data.store_name,
                    "store_image": store_data.store_image,
                    "store_address": store_data.address,
                    "store_latitude": store_data.latitude,
                    "store_longitude": store_data.longitude,
                    "store_mobile": store_data.mobile,
                    "store_delivery_options": store_data.delivery_options,
                    "store_product_price": product_price
                }
                if store_data.delivery_options == "Home Delivery":
                    home_delivery_stores_list.append(store_info)
                else:
                    non_home_delivery_stores_list.append(store_info)
        
        return {"home_delivery_stores": home_delivery_stores_list, "In_stores": non_home_delivery_stores_list}
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"store_search BL: {e}")
        raise HTTPException(status_code=500, detail="Error in store search BL")
    except Exception as e:
        logger.error(f"Unexpected error BL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred BL")

async def subscriber_cart_bl(
    store_id: str,
    cart_data: List[SubscriberCartProduct],
    subscriber_mongodb_session
) -> bool:
    """
    Checks if all cart items are available in the specified store.

    Args:
        store_id (str): The ID of the store to check for item availability.
        cart_data (List[SubscriberCartProduct]): The list of products in the subscriber's cart.
        subscriber_mongodb_session: A database session for MongoDB queries.

    Returns:
        bool: True if all cart items are available in the store, otherwise False.

    Raises:
        HTTPException: If there is a validation or known error.
        SQLAlchemyError: For database-related errors during execution.
        Exception: For any unexpected errors.
    """
    try:
        store_stocks_available = True
        for item in cart_data:
            stocks_in_store = await store_stock_check_dal(
                store_id=store_id,
                product_id=item.product_id,
                quantity=item.quantity,
                subscriber_mongodb_session=subscriber_mongodb_session
            )
            if stocks_in_store is None:
                store_stocks_available = False
                break
                
        return store_stocks_available
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"subscriber_cart BL: {e}")
        raise HTTPException(status_code=500, detail="Error in adding products to cart BL")
    except Exception as e:
        logger.error(f"Unexpected error BL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred BL")

async def store_stock_helper(store_id: str,
    cart_data: List[SubscriberCartProduct],
    subscriber_mongodb_session, subscriber_mysql_session:AsyncSession):
    try:
        total_amount = 0
        product_list=[]
        for item in cart_data:
            stocks_in_store = await store_stock_check_dal(
                store_id=store_id,
                product_id=item.product_id,
                quantity=item.quantity,
                subscriber_mongodb_session=subscriber_mongodb_session
            )
            
            for batch in stocks_in_store["batch_details"]:
                expiry_date = datetime.strptime(batch["expiry_date"], "%m/%Y")
                if batch["is_active"] == 1 and (expiry_date < datetime.now() or (expiry_date - datetime.now()).days <= 30):
                    pass
                else:
                    if batch["batch_quantity"] >= item.quantity:
                        price = await get_batch_pricing_dal(store_id, item.product_id, batch["batch_number"], subscriber_mongodb_session)
                        total_amount += price["net_rate"] * item.quantity
                        product_list.append({
                            "product_id": item.product_id,
                            "product_name": (await get_data_by_id_utils(table=productMaster, field="product_id", subscriber_mysql_session=subscriber_mysql_session, data=item.product_id)).product_name,
                            "quantity": item.quantity,
                            "batch_number": batch["batch_number"],
                            "price": price["net_rate"]
                        })
                        break
                    else:
                        item.quantity -= batch["batch_quantity"]
                        price = await get_batch_pricing_dal(store_id, item["product_id"], batch["batch_number"], subscriber_mongodb_session)
                        total_amount += price["net_rate"] * batch["batch_quantity"]
                        product_list.append({
                            "product_id": item.product_id,
                            "product_name": (await get_data_by_id_utils(table=productMaster, field="product_id", subscriber_mysql_session=subscriber_mysql_session, data=item.product_id)).product_name,
                            "quantity": batch["batch_quantity"],
                            "batch_number": batch["batch_number"],
                            "price": price["net_rate"]
                        })
        return {
            "total_amount": total_amount,
            "product_list": product_list
        }
    except Exception as e:
        logger.error(f"Unexpected error BL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred in search store medicine price BL")

async def subscriber_order_by_prescription_bl(
    prescription_id: str,
    subscriber_mysql_session: AsyncSession,
    subscriber_mongodb_session
) -> dict:
    """
    Retrieves stores where the subscriber can order prescribed medicines.

    This function checks which stores have the prescribed medicines available
    for purchase and categorizes them based on delivery options.

    Args:
        prescription_id (str): The unique identifier of the prescription.
        subscriber_mysql_session (AsyncSession): An async database session for MySQL queries.
        subscriber_mongodb_session: A database session for MongoDB queries.

    Returns:
        dict: A dictionary containing two lists:
              - "home_delivery_stores": Stores offering home delivery.
              - "In_stores": Stores requiring in-store purchases.

    Raises:
        HTTPException: If there is a validation or known error.
        SQLAlchemyError: For database-related errors during execution.
        Exception: For any unexpected errors.
    """
    try:
        product_prescribed = await entity_data_return_utils(
            table=MedicinePrescribed,
            field="prescription_id",
            subscriber_mysql_session=subscriber_mysql_session,
            data=prescription_id
        )
        medicine_list = [
            {
                "product_id": (
                    await get_data_by_id_utils(
                        table=productMaster,
                        field="product_name",
                        subscriber_mysql_session=subscriber_mysql_session,
                        data=item.medicine_name
                    )
                ).product_id,
                "product_name": item.medicine_name,
                "quantity": (
                    await calculate_quantity_by_medicication_and_days(
                        dosage_timing=item.medication_timing,
                        days=item.treatment_duration
                    )
                )
            }
            for item in product_prescribed
        ]
        return medicine_list
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"subscriber_order_by_prescription BL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting orders by prescription BL")
    except Exception as e:
        logger.error(f"Unexpected error BL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred BL")
    
async def calculate_quantity_by_medicication_and_days(dosage_timing: str, days: str) -> int:
    """
    Calculates the total quantity of medication based on dosage timing and treatment duration.

    Args:
        dosage_timing (str): A string where '1' indicates a dosage instance (e.g., "101" for morning and night).
        days (str): A string representation of the number of days of treatment.

    Returns:
        int: The total quantity of medication required.

    Raises:
        ValueError: If the input format for days or dosage_timing is invalid.
    """
    dosage = dosage_timing.count('1')  # Count occurrences of '1'
    days = int(re.search(r'\d+', str(days)).group()) if re.search(r'\d+', str(days)) else 0
    return dosage * days


async def create_order_bl(order: CreateOrder, subscriber_mysql_session: AsyncSession) -> SubscriberMessage:
    """
    Creates a new order for a subscriber.

    This function generates a new order, adds order items, and creates an entry
    in the database. It also validates the input and ensures data integrity.

    Args:
        order (CreateOrder): The order data to be created, including order items and metadata.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        SubscriberMessage: A success message indicating the order creation status.

    Raises:
        HTTPException: For validation-related or known errors.
        SQLAlchemyError: For database-related issues during query execution.
        Exception: For any unexpected errors.
    """
    async with subscriber_mysql_session.begin():
        try:
            if not isinstance(order.order_items, list):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid data type for order_items. Expected a list."
                )
            
            # Generate a new order ID
            new_order_id = await id_incrementer(entity_name="ORDER", subscriber_mysql_session=subscriber_mysql_session)

            # Create order status
            order_status_data = OrderStatus(
                order_id=new_order_id,
                order_status="Listed",
                store_id=order.store_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                active_flag=1
            )
            await create_order_status_dal(order_status=order_status_data, subscriber_mysql_session=subscriber_mysql_session)

            # Create the order
            new_order_data = Orders(
                order_id=new_order_id,
                store_id=order.store_id,
                subscriber_id=order.subscriber_id,
                order_total_amount=order.order_total_amount,
                payment_type=order.payment_type,
                prescription_reference=order.prescription or None,
                delivery_type=order.delivery_type,
                payment_status="Pending",
                doctor=order.doctor or None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                active_flag=1
            )
            await create_order_dal(order_data=new_order_data, subscriber_mysql_session=subscriber_mysql_session)

            # Add order items
            for item in order.order_items:
                new_order_item_id = await id_incrementer(entity_name="ORDERITEM", subscriber_mysql_session=subscriber_mysql_session)
                item_data = OrderItem(
                    order_item_id=new_order_item_id,
                    order_id=new_order_id,
                    product_id=item.product_id,
                    product_quantity=item.product_quantity,
                    product_amount=item.product_amount,
                    product_type=item.product_type,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    active_flag=1
                )
                await create_order_item_dal(order_item=item_data, subscriber_mysql_session=subscriber_mysql_session)

            return SubscriberMessage(message="Order Created Successfully")

        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"create_order BL: {e}")
            raise HTTPException(status_code=500, detail="Error in creating order BL")
        except Exception as e:
            logger.error(f"Error in creating order BL: {e}")
            raise HTTPException(status_code=500, detail="An error occurred while creating order")

async def orders_list_bl(subscriber_mobile: str, subscriber_mysql_session: AsyncSession) -> dict:
    """
    Retrieves the ongoing and delivered orders for a subscriber.

    This function fetches the subscriber's orders from the database and categorizes
    them into ongoing and delivered orders based on their status. It includes detailed
    information about the orders and the associated store and products.

    Args:
        subscriber_mobile (str): The mobile number of the subscriber.
        subscriber_mysql_session (AsyncSession): An async database session for query execution.

    Returns:
        dict: A dictionary containing two keys:
              - "on_going_orders": A list of ongoing orders.
              - "delivered_orders": A list of delivered orders.

    Raises:
        HTTPException: Raised when an error occurs during order retrieval or processing.
        SQLAlchemyError: For any database-related issues.
        Exception: For unexpected errors.
    """
    try:
        on_going_orders = []
        delivered_orders = []

        subscriber_data = await get_data_by_mobile(
            mobile=subscriber_mobile,
            subscriber_mysql_session=subscriber_mysql_session,
            table=Subscriber,
            field="mobile"
        )
        orders_list = await orders_list_dal(
            subscriber_id=subscriber_data.subscriber_id,
            subscriber_mysql_session=subscriber_mysql_session
        )

        for order in orders_list:
            store_data = await get_data_by_id_utils(
                table=StoreDetails,
                field="store_id",
                subscriber_mysql_session=subscriber_mysql_session,
                data=order.store_id
            )
            orders = {
                "store_id": order.store_id,
                "store_name": store_data.store_name,
                "store_address": store_data.address,
                "store_mobile": store_data.mobile,
                "store_latitude": store_data.latitude,
                "store_longitude": store_data.longitude,
                "store_image": store_data.store_image,
                "order_id": order.order_id,
                "order_total_amount": order.order_total_amount,
                "prescription_reference": order.prescription_reference,
                "payment_status": order.payment_status,
                "payment_type": order.payment_type,
                "delivery_type": order.delivery_type,
                "order_date": order.created_at.strftime("%d-%m-%Y"),
                "order_status": order.order_status[0].order_status,
                "order_status_id": order.order_status[0].orderstatus_id,
                "order_status_updated": order.order_status[0].updated_at.strftime("%d-%m-%Y"),
                "order_items": [
                    {
                        "order_id": item.order_id,
                        "product_id": item.product_id,
                        "product_name": (await get_data_by_id_utils(
                            table=productMaster,
                            field="product_id",
                            subscriber_mysql_session=subscriber_mysql_session,
                            data=item.product_id
                        )).product_name,
                        "product_amount": item.product_amount,
                        "product_quantity": item.product_quantity,
                        "order_item_id": item.order_item_id,
                        "product_type": item.product_type
                    } for item in order.order_items
                ]
            }
            if orders["order_status"] != "Delivered":
                on_going_orders.append(orders)
            else:
                delivered_orders.append(orders)

        return {"on_going_orders": on_going_orders, "delivered_orders": delivered_orders}

    except SQLAlchemyError as e:
        logger.error(f"orders_list BL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting orders list BL")
    except Exception as e:
        logger.error(f"Error in getting orders list BL: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while getting orders list")
        
async def view_prescribed_product_bl(subscriber_mobile: str, subscriber_mysql_session: AsyncSession) -> list:
    """
    Retrieves the list of prescribed products for a subscriber.

    This function fetches the prescribed products for a subscriber, including details
    such as medicine names, dosage timings, and treatment durations.

    Args:
        subscriber_mobile (str): The mobile number of the subscriber.
        subscriber_mysql_session (AsyncSession): An async database session for query execution.

    Returns:
        list: A list of prescribed product details including medicine and prescription data.

    Raises:
        HTTPException: If no prescriptions are found or for validation-related errors.
        SQLAlchemyError: For any database-related issues.
        Exception: For unexpected errors.
    """
    try:
        subscriber_data = await get_data_by_mobile(
            mobile=subscriber_mobile,
            subscriber_mysql_session=subscriber_mysql_session,
            field="mobile",
            table=Subscriber
        )

        prescribed_products = await view_prescribed_products_dal(
            subscriber_id=subscriber_data.subscriber_id,
            subscriber_mysql_session=subscriber_mysql_session
        )

        if not prescribed_products:
            raise HTTPException(status_code=404, detail="No Prescription found for this Subscriber")

        prescribed_products_list = [
            {
                "pulse": prescription_data.pulse,
                "next_visit_date": prescription_data.next_visit_date,
                "weight": prescription_data.weight,
                "procedure_name": prescription_data.procedure_name,
                "drug_allergy": prescription_data.drug_allergy,
                "home_care_service": prescription_data.home_care_service,
                "history": prescription_data.history,
                "appointment_id": prescription_data.appointment_id,
                "complaints": prescription_data.complaints,
                "created_at": prescription_data.created_at.strftime("%d-%m-%Y"),
                "blood_pressure": prescription_data.blood_pressure,
                "diagnosis": prescription_data.diagnosis,
                "updated_at": prescription_data.updated_at.strftime("%d-%m-%Y"),
                "prescription_id": prescription_data.prescription_id,
                "specialist_type": prescription_data.specialist_type,
                "temperature": prescription_data.temperature,
                "consulting_doctor": prescription_data.consulting_doctor,
                "medicine_prescribed": [
                    {
                        "dosage_timing": medicine.dosage_timing,
                        "treatment_duration": medicine.treatment_duration,
                        "medicine_name": medicine.medicine_name,
                        "medication_timing": medicine.medication_timing
                    } for medicine in prescription_data.medicine_prescribed
                ]
            } for prescription_data in prescribed_products
        ]

        return prescribed_products_list

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"view_prescribed_product_bl BL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting prescribed products BL")
    except Exception as e:
        logger.error(f"Error in getting prescribed products BL: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while getting prescribed products")
    
async def subscriber_hubbystore_bl(subscriber_mysql_session: AsyncSession) -> dict:
    """
    Fetches the list of hub stores.

    This function retrieves details of all hub stores available for a subscriber.

    Args:
        subscriber_mysql_session (AsyncSession): An async database session for query execution.

    Returns:
        dict: A dictionary containing the list of stores under the key "stores".

    Raises:
        HTTPException: For validation or known errors.
        SQLAlchemyError: For any database-related issues.
        Exception: For unexpected errors.
    """
    try:
        stores = await subscriber_hubbystore_dal(subscriber_mysql_session=subscriber_mysql_session)
        return {"stores": stores}

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"subscriber hubbystore_bl BL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting subscriber hubbystore BL")
    except Exception as e:
        logger.error(f"Error in getting subscriber hubbystore BL: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while getting subscriber hubbystore")
