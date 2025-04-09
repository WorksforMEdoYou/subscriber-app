from pydantic import BaseModel, constr
from typing import Optional, List
from sqlalchemy import Date, Time
   
class SubscriberBase(BaseModel):
    """
    Base Model For the Subscriber
    """
    subscriber_firstname: constr(max_length=255)
    subscriber_lastname: constr(max_length=255)
    subscriber_mobile: constr(max_length=15)
    subscriber_email: constr(max_length=255)
    subscriber_gender: constr(max_length=255)
    subscriber_dob: constr(max_length=255)
    subscriber_age: constr(max_length=255) 
    subscriber_blood_group: constr(max_length=255)
    """ subscriber_address: str
    subscriber_landmark: constr(max_length=255)
    subscriber_pincode: constr(max_length=255)
    subscriber_city: constr(max_length=255)
    subscriber_state: constr(max_length=255)
    subscriber_geolocation: constr(max_length=255) """

class CreateSubscriber(SubscriberBase):
    """
    Pydantic Model for the Create Subscriber
    """
    pass

class UpdateSubscriber(SubscriberBase):
    """
    Pydantic Model for the Update Subscriber
    """
    pass

class Subscriber(SubscriberBase):
    """
    Detailed Subscriber model
    """
    subscriber_id: Optional[str]
    address_id: Optional[str]
    subscriber_address_id: Optional[str]
    
    class Config:
        from_attributes = True
        
class Mpin(BaseModel):
    """
    Subscriber Login Model
    """
    subscriber_mobile:int
    mpin:int
    
class SubscriberLogin(Mpin):
    """
    Pydantic Model for the Subscriber Login
    """
    pass

class SubscriberSetMpin(Mpin):
    """
    Pydantic Model for the Subscriber Set Mpin
    """
    pass

class SubscriberUpdateMpin(Mpin):
    """
    Pydantic Model for the Subscriber Update Mpin
    """
    pass
        
class SubscriberSetProfile(BaseModel):
    """
    Pydantic Model for the Subscriber Set Profile
    """
    
    first_name: constr(max_length=45)
    last_name: constr(max_length=45)
    email_id: constr(max_length=255)
    age: constr(max_length=255)
    gender: constr(max_length=45)
    mobile: constr(max_length=15)
    dob: constr(max_length=255)
    blood_group: constr(max_length=255)
    address_type: constr(max_length=255)
    address: str
    landmark: constr(max_length=255)
    pincode: constr(max_length=255)
    city: constr(max_length=255)
    state: constr(max_length=255)
    geolocation: constr(max_length=255)
        
class SubscriberAddress(BaseModel):
    """
    Base Model For the Subscriber Address
    """
    subscriber_mobile: constr(max_length=15)
    address_type: constr(max_length=255)
    address: constr(max_length=255)
    landmark: constr(max_length=255)
    pincode: constr(max_length=255)
    city: constr(max_length=255)
    state: constr(max_length=255)
    geolocation: constr(max_length=255)
    
class CreateSubscriberAddress(SubscriberAddress):
    """
    Pydantic Model for the Create Subscriber Address
    """
    pass

class UpdateSubscriberAddress(BaseModel):
    """
    Pydantic Model for the Update Subscriber Address
    """
    subscriber_address_id: str
    address_type: constr(max_length=255)
    address: constr(max_length=255)
    landmark: constr(max_length=255)
    pincode: constr(max_length=255)
    city: constr(max_length=255)
    state: constr(max_length=255)
    geolocation: constr(max_length=255)
    
class SubscriberSignup(BaseModel):
    """
    Pydantic Model for the Subscriber Signup
    """
    name: constr(max_length=45)
    mobile: constr(max_length=15)
    email_id: Optional[constr(max_length=255)]
    device_id: constr(max_length=255)
    token: constr(max_length=255)
        
class SubscriberMessage(BaseModel):
    """
    Message for Subscriber
    """
    message: str
    
    class Config:
        from_attributes = True

class AppointmentBase(BaseModel):
    """
    Basemodel for the apoointment 
    """
    date: str 
    time: str
    subscriber_mobile: constr(max_length=15)
    doctor_id: str
    clinic_name: str
    book_for_id: Optional[str] = None
    
    class Config:
        #arbitrary_types_allowed=True # to support sqlalchemy data DATE and TIME
        from_attributes = True

class CreateAppointment(AppointmentBase):
    """
    Pydantic Model for the Appointment
    """
    pass 

class Appointment(AppointmentBase):
    """
    Detailed model for appointment
    """
    appointment_id: Optional[str]
    
    class Config:
        #arbitrary_types_allowed=True
        from_attributes = True

class UpdateAppointment(BaseModel):
    """
    Pydantic Model for the Appointment
    """
    date: str
    time: str
    subscriber_mobile: constr(max_length=15)
    doctor_id: str
    appointment_id: str
    class Config:
        from_attributes = True
        
class CancelAppointment(BaseModel):
    """
    Pydantic Model for the Appointment
    """
    appointment_id: str
    doctor_id: str
    subscriber_mobile: constr(max_length=15)
    active_flag: int
    class Config:
        from_attributes = True
        
class CreateSpecialization(BaseModel):
    specialization_name:str
    class Config:
        from_attributes = True

# ================ subscriber store locate ================== 

class SubscriberCartProduct(BaseModel):
    """
    Base Model For the Subscriber Purchased Product
    """
    product_id: str
    quantity: int
    
    class Config:
        from_attributes = True
     
class SubscriberStoreSearch(BaseModel):
    """
    Base Model For the Store Location
    """
    subscriber_id: str
    subscriber_latitude: float
    subscriber_longitude: float 
    cart_products: List[SubscriberCartProduct]
    
    class Config:
        from_attributes = True
 
class OrderItems(BaseModel):
    """
    Base Model For the Order Items
    """
    product_id: str
    product_quantity: int
    product_amount: float
    product_type: str
    
    class Config:
        from_attributes = True 
        
class CreateOrder(BaseModel):
    """
    Base Model For the Create Order
    """
    store_id:str
    subscriber_id: str
    order_total_amount: float
    delivery_type: str
    payment_type: str
    prescription: Optional[str]=None
    doctor: Optional[str]=None
    order_items: List[OrderItems]
    
    class Config:
        from_attributes = True

class CreateServiceProviderAppointment(BaseModel):
    """
    Base Model For the Create Service Provider Appointment
    """
    session_time: constr(max_length=45)
    start_time: constr(max_length=45)
    end_time: constr(max_length=45)
    session_frequency: constr(max_length=45)
    start_date: constr(max_length=45)
    end_date: constr(max_length=45)
    prescription_id: Optional[str]=None
    visittype: constr(max_length=45)
    address_id: Optional[str]=None
    book_for_id: Optional[str]=None
    subscriber_mobile: constr(max_length=15)
    sp_id: constr(max_length=255)
    service_package_id: constr(max_length=255)
    service_subtype_id: constr(max_length=255)
    
class UpdateServiceProviderAppointment(BaseModel):
    """
    Base Model For the Update Service Provider Appointment
    """
    sp_appointment_id: constr(max_length=255)
    session_time: constr(max_length=45)
    start_time: constr(max_length=45)
    end_time: constr(max_length=45)
    session_frequency: constr(max_length=45)
    start_date: constr(max_length=45)
    end_date: constr(max_length=45)
    prescription_id: Optional[str]=None
    visittype: constr(max_length=45)
    address_id: Optional[str]=None
    book_for_id: Optional[str]=None
    subscriber_mobile: constr(max_length=15)
    sp_id: constr(max_length=255)
    service_package_id: constr(max_length=255)
    service_subtype_id: constr(max_length=255)
    
class CancelServiceProviderAppointment(BaseModel):
    """
    Base Model For the Cancel Service Provider Appointment
    """
    sp_appointment_id: constr(max_length=255)
    active_flag: int

class CreateDCAppointment(BaseModel):
    """
    Base Model For the Create DC Appointment
    """
    appointment_date: constr(max_length=45)
    reference_id: str
    prescription_image: str
    homecollection: str
    address_id: str
    book_for_id: Optional[str]
    subscriber_mobile: constr(max_length=15)
    sp_mobile: constr(max_length=15)
    package_id: str
    report_image: Optional[str]
    

class UpdateDCAppointment(BaseModel):
    """
    Base Model For the Update DC Appointment
    """
    dc_appointment_id: constr(max_length=255)
    appointment_date: constr(max_length=45)
    reference_id: str
    prescription_image: str
    homecollection: str
    address_id: str
    book_for_id: Optional[str]
    subscriber_mobile: constr(max_length=15)
    sp_mobile: constr(max_length=15)
    package_id: str
    report_image: Optional[str]
    
class CancelDCAppointment(BaseModel):
    """
    Base Model For the Cancel DC Appointment
    """
    dc_appointment_id: constr(max_length=255)
    active_flag: int
    

