from sqlalchemy import Column, Integer, String, ForeignKey, TEXT, DECIMAL, DATETIME, Boolean
from sqlalchemy.orm import relationship
from .database import Base

class Midwife(Base):
    __tablename__ = "midwives"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    mothers = relationship("Mother", back_populates="owner")

class Mother(Base):
    __tablename__ = "mothers"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    nic = Column(String(20), unique=True)
    address = Column(TEXT)
    contact_number = Column(String(20))
    hashed_password = Column(String(255), nullable=False)
    midwife_id = Column(Integer, ForeignKey("midwives.id"), nullable=False)
    
    owner = relationship("Midwife", back_populates="mothers")
    health_records = relationship("HealthRecord", back_populates="mother")
    pregnancy_records = relationship("PregnancyRecord", back_populates="mother")
    delivery_records = relationship("DeliveryRecord", back_populates="mother")
    antenatal_plans = relationship("AntenatalPlan", back_populates="mother")

class HealthRecord(Base):
    __tablename__ = "health_records"
    id = Column(Integer, primary_key=True, index=True)
    visit_date = Column(DATETIME, nullable=False)
    weight_kg = Column(DECIMAL(5, 2))
    blood_pressure = Column(String(20))
    notes = Column(TEXT)
    mother_id = Column(Integer, ForeignKey("mothers.id"), nullable=False)
    mother = relationship("Mother", back_populates="health_records")

class PregnancyRecord(Base):
    __tablename__ = "pregnancy_records"
    id = Column(Integer, primary_key=True, index=True)
    mother_id = Column(Integer, ForeignKey("mothers.id"), nullable=False)
    created_at = Column(DATETIME)
    
    # Vitals
    blood_group = Column(String(10))
    bmi = Column(DECIMAL(5, 2))
    height_cm = Column(DECIMAL(5, 2))
    allergies = Column(TEXT)
    
    # Medical Checks
    consanguinity = Column(Boolean, default=False)
    rubella_immunization = Column(Boolean, default=False)
    pre_pregnancy_screening = Column(Boolean, default=False)
    folic_acid = Column(Boolean, default=False)
    subfertility_history = Column(Boolean, default=False)
    
    # Obstetric
    identified_risks = Column(TEXT)
    gravidity = Column(Integer)
    parity = Column(Integer)
    living_children = Column(Integer)
    youngest_child_age = Column(String(50))
    
    # Dates
    lrmp = Column(DATETIME)
    edd = Column(DATETIME)
    us_corrected_edd = Column(DATETIME)
    poa_at_registration = Column(String(50))
    
    # Relationship
    mother = relationship("Mother", back_populates="pregnancy_records")

# NEW MODEL
class DeliveryRecord(Base):
    __tablename__ = "delivery_records"
    id = Column(Integer, primary_key=True, index=True)
    mother_id = Column(Integer, ForeignKey("mothers.id"), nullable=False)
    created_at = Column(DATETIME)
    
    # Delivery
    delivery_date = Column(DATETIME) # Using DATETIME for simplicity
    delivery_mode = Column(String(50))
    episiotomy = Column(Boolean, default=False)
    temp_normal = Column(Boolean, default=False)
    vaginal_exam_done = Column(Boolean, default=False)
    maternal_complications = Column(TEXT)
    wound_infection = Column(Boolean, default=False)
    family_planning_discussed = Column(Boolean, default=False)
    danger_signals_explained = Column(Boolean, default=False)
    breast_feeding_established = Column(Boolean, default=False)
    
    # Baby
    birth_weight = Column(DECIMAL(5, 2))
    poa_at_birth = Column(Integer)
    apgar_score = Column(Integer)
    abnormalities = Column(TEXT)
    
    # Discharge
    vitamin_a_given = Column(Boolean, default=False)
    rubella_given = Column(Boolean, default=False)
    anti_d_given = Column(Boolean, default=False)
    diagnosis_card_given = Column(Boolean, default=False)
    chdr_completed = Column(Boolean, default=False)
    prescription_given = Column(Boolean, default=False)
    referred_to_phm = Column(Boolean, default=False)
    special_notes = Column(TEXT)
    discharge_date = Column(DATETIME)
    
    # Relationship
    mother = relationship("Mother", back_populates="delivery_records")

class AntenatalPlan(Base):
    __tablename__ = "antenatal_plans"
    id = Column(Integer, primary_key=True, index=True)
    mother_id = Column(Integer, ForeignKey("mothers.id"), nullable=False)
    created_at = Column(DATETIME)
    
    # Dates
    next_clinic_date = Column(DATETIME)
    
    # Classes (1st)
    class_1st_date = Column(DATETIME)
    class_1st_husband = Column(Boolean, default=False)
    class_1st_wife = Column(Boolean, default=False)
    class_1st_other = Column(String(100))
    
    # Classes (2nd)
    class_2nd_date = Column(DATETIME)
    class_2nd_husband = Column(Boolean, default=False)
    class_2nd_wife = Column(Boolean, default=False)
    class_2nd_other = Column(String(100))
    
    # Classes (3rd)
    class_3rd_date = Column(DATETIME)
    class_3rd_husband = Column(Boolean, default=False)
    class_3rd_wife = Column(Boolean, default=False)
    class_3rd_other = Column(String(100))
    
    # Materials
    book_antenatal_issued = Column(DATETIME)
    book_antenatal_returned = Column(DATETIME)
    book_breastfeeding_issued = Column(DATETIME)
    book_breastfeeding_returned = Column(DATETIME)
    book_eccd_issued = Column(DATETIME)
    book_eccd_returned = Column(DATETIME)
    leaflet_fp_issued = Column(DATETIME)
    leaflet_fp_returned = Column(DATETIME)
    
    # Emergency
    emergency_contact_name = Column(String(255))
    emergency_contact_address = Column(TEXT)
    emergency_contact_phone = Column(String(20))
    moh_office_phone = Column(String(20))
    phm_phone = Column(String(20))
    grama_niladari_div = Column(String(255))
    
    # Relationship
    mother = relationship("Mother", back_populates="antenatal_plans")
