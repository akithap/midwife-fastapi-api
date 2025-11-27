from pydantic import BaseModel
from datetime import datetime, date
from typing import List, Optional

# --- HealthRecord Schemas ---
class HealthRecordBase(BaseModel):
    visit_date: datetime
    weight_kg: Optional[float] = None
    blood_pressure: Optional[str] = None
    notes: Optional[str] = None

class HealthRecordCreate(HealthRecordBase):
    pass

class HealthRecord(HealthRecordBase):
    id: int
    mother_id: int
    class Config:
        from_attributes = True

# --- Pregnancy Record Schemas ---
class PregnancyRecordBase(BaseModel):
    blood_group: Optional[str] = None
    bmi: Optional[float] = None
    height_cm: Optional[float] = None
    allergies: Optional[str] = None
    consanguinity: bool = False
    rubella_immunization: bool = False
    pre_pregnancy_screening: bool = False
    folic_acid: bool = False
    subfertility_history: bool = False
    identified_risks: Optional[str] = None
    gravidity: Optional[int] = None
    parity: Optional[int] = None
    living_children: Optional[int] = None
    youngest_child_age: Optional[str] = None
    lrmp: Optional[datetime] = None
    edd: Optional[datetime] = None
    us_corrected_edd: Optional[datetime] = None
    poa_at_registration: Optional[str] = None

class PregnancyRecordCreate(PregnancyRecordBase):
    pass

class PregnancyRecord(PregnancyRecordBase):
    id: int
    mother_id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# --- Delivery Record Schemas ---
class DeliveryRecordBase(BaseModel):
    delivery_date: Optional[datetime] = None
    delivery_mode: Optional[str] = None
    episiotomy: bool = False
    temp_normal: bool = False
    vaginal_exam_done: bool = False
    maternal_complications: Optional[str] = None
    wound_infection: bool = False
    family_planning_discussed: bool = False
    danger_signals_explained: bool = False
    breast_feeding_established: bool = False
    birth_weight: Optional[float] = None
    poa_at_birth: Optional[int] = None
    apgar_score: Optional[int] = None
    abnormalities: Optional[str] = None
    vitamin_a_given: bool = False
    rubella_given: bool = False
    anti_d_given: bool = False
    diagnosis_card_given: bool = False
    chdr_completed: bool = False
    prescription_given: bool = False
    referred_to_phm: bool = False
    special_notes: Optional[str] = None
    discharge_date: Optional[datetime] = None

class DeliveryRecordCreate(DeliveryRecordBase):
    pass

class DeliveryRecord(DeliveryRecordBase):
    id: int
    mother_id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# --- Antenatal Plan Schemas ---
class AntenatalPlanBase(BaseModel):
    next_clinic_date: Optional[datetime] = None
    class_1st_date: Optional[datetime] = None
    class_1st_husband: bool = False
    class_1st_wife: bool = False
    class_1st_other: Optional[str] = None
    class_2nd_date: Optional[datetime] = None
    class_2nd_husband: bool = False
    class_2nd_wife: bool = False
    class_2nd_other: Optional[str] = None
    class_3rd_date: Optional[datetime] = None
    class_3rd_husband: bool = False
    class_3rd_wife: bool = False
    class_3rd_other: Optional[str] = None
    book_antenatal_issued: Optional[datetime] = None
    book_antenatal_returned: Optional[datetime] = None
    book_breastfeeding_issued: Optional[datetime] = None
    book_breastfeeding_returned: Optional[datetime] = None
    book_eccd_issued: Optional[datetime] = None
    book_eccd_returned: Optional[datetime] = None
    leaflet_fp_issued: Optional[datetime] = None
    leaflet_fp_returned: Optional[datetime] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_address: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    moh_office_phone: Optional[str] = None
    phm_phone: Optional[str] = None
    grama_niladari_div: Optional[str] = None

class AntenatalPlanCreate(AntenatalPlanBase):
    pass

class AntenatalPlan(AntenatalPlanBase):
    id: int
    mother_id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# --- Mother Schemas ---
class MotherBase(BaseModel):
    full_name: str
    nic: Optional[str] = None
    address: Optional[str] = None
    contact_number: Optional[str] = None

class MotherCreate(MotherBase):
    password: str 

class MotherUpdate(BaseModel):
    full_name: Optional[str] = None
    address: Optional[str] = None
    contact_number: Optional[str] = None

class Mother(MotherBase):
    id: int
    midwife_id: int
    health_records: List[HealthRecord] = []
    pregnancy_records: List[PregnancyRecord] = []
    delivery_records: List[DeliveryRecord] = []
    antenatal_plans: List[AntenatalPlan] = []
    class Config:
        from_attributes = True

# ------------------------------
# MOH & MIDWIFE MANAGEMENT SCHEMAS
# ------------------------------

# 1. MOH Officer
class MOHOfficerBase(BaseModel):
    username: str
    full_name: str
    moh_area: Optional[str] = None
    email: Optional[str] = None

class MOHOfficerCreate(MOHOfficerBase):
    password: str
    
class MOHOfficer(MOHOfficerBase):
    id: int
    class Config:
        from_attributes = True

# 2. Comprehensive Midwife Registration (Web Portal)
class MidwifeRegistration(BaseModel):
    username: str
    password: str
    full_name: str
    nic: str
    date_of_birth: date 
    phone_number: str
    email: Optional[str] = None
    residential_address: str
    slmc_reg_no: str
    service_grade: Optional[str] = None
    assigned_moh_area: str
    user_must_change_password: bool = True
    is_active: bool = True

# 3. Legacy Midwife Create (Mobile/Old) - Restored to prevent crash
class MidwifeCreate(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None

# 4. Midwife Response Model
class MidwifeBase(BaseModel):
    username: str
    full_name: Optional[str] = None
    nic: Optional[str] = None
    date_of_birth: Optional[date] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    residential_address: Optional[str] = None
    slmc_reg_no: Optional[str] = None
    service_grade: Optional[str] = None
    assigned_moh_area: Optional[str] = None
    is_active: bool = True

class Midwife(MidwifeBase):
    id: int
    mothers: List[Mother] = []
    class Config:
        from_attributes = True

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    sub_id: Optional[str] = None

class PasswordChange(BaseModel):
    old_password: str
    new_password: str