from sqlalchemy.orm import Session
from . import models, schemas
from passlib.context import CryptContext
from sqlalchemy import or_ # Needed for "OR" search logic

# Setup password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    return pwd_context.hash(password_bytes)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# --- Midwife CRUD ---
def get_midwife(db: Session, midwife_id: int):
    return db.query(models.Midwife).filter(models.Midwife.id == midwife_id).first()

def get_midwife_by_username(db: Session, username: str):
    return db.query(models.Midwife).filter(models.Midwife.username == username).first()

def create_midwife(db: Session, midwife: schemas.MidwifeCreate):
    hashed_password = get_password_hash(midwife.password)
    db_midwife = models.Midwife(
        username=midwife.username, 
        hashed_password=hashed_password, 
        full_name=midwife.full_name
    )
    db.add(db_midwife)
    db.commit()
    db.refresh(db_midwife)
    return db_midwife

# --- Mother CRUD (UPDATED) ---

def get_mother_by_nic(db: Session, nic: str):
    return db.query(models.Mother).filter(models.Mother.nic == nic).first()

# Helper to get a single mother by ID
def get_mother(db: Session, mother_id: int):
    return db.query(models.Mother).filter(models.Mother.id == mother_id).first()

# UPDATED: Now supports search!
def get_mothers_by_midwife(db: Session, midwife_id: int, skip: int = 0, limit: int = 100, search: str = None):
    query = db.query(models.Mother).filter(models.Mother.midwife_id == midwife_id)
    
    if search:
        # Server-side filtering: Search in Name OR NIC
        search_format = f"%{search}%"
        query = query.filter(
            or_(
                models.Mother.full_name.like(search_format),
                models.Mother.nic.like(search_format)
            )
        )
        
    return query.offset(skip).limit(limit).all()

def create_mother(db: Session, mother: schemas.MotherCreate, midwife_id: int):
    hashed_password = get_password_hash(mother.password)
    db_mother = models.Mother(
        full_name=mother.full_name,
        nic=mother.nic,
        address=mother.address,
        contact_number=mother.contact_number,
        hashed_password=hashed_password,
        midwife_id=midwife_id
    )
    db.add(db_mother)
    db.commit()
    db.refresh(db_mother)
    return db_mother

# NEW: Update function
def update_mother(db: Session, mother_id: int, mother_update: schemas.MotherUpdate):
    db_mother = get_mother(db, mother_id)
    if not db_mother:
        return None
    
    # Only update fields that are sent (exclude_unset=True)
    update_data = mother_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_mother, key, value)

    db.add(db_mother)
    db.commit()
    db.refresh(db_mother)
    return db_mother

# --- HealthRecord CRUD ---
def create_health_record(db: Session, record: schemas.HealthRecordCreate, mother_id: int):
    db_record = models.HealthRecord(**record.dict(), mother_id=mother_id)
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def get_health_records_for_mother(db: Session, mother_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.HealthRecord).filter(models.HealthRecord.mother_id == mother_id).offset(skip).limit(limit).all()
            
# --- Pregnancy Record CRUD ---
def create_pregnancy_record(db: Session, record: schemas.PregnancyRecordCreate, mother_id: int):
    db_record = models.PregnancyRecord(**record.dict(), mother_id=mother_id)
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def get_pregnancy_records_for_mother(db: Session, mother_id: int):
    return db.query(models.PregnancyRecord).filter(models.PregnancyRecord.mother_id == mother_id).all()

# --- Delivery Record CRUD ---
def create_delivery_record(db: Session, record: schemas.DeliveryRecordCreate, mother_id: int):
    db_record = models.DeliveryRecord(**record.dict(), mother_id=mother_id)
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def get_delivery_records_for_mother(db: Session, mother_id: int):
    return db.query(models.DeliveryRecord).filter(models.DeliveryRecord.mother_id == mother_id).all()

# --- Antenatal Plan CRUD ---
def create_antenatal_plan(db: Session, plan: schemas.AntenatalPlanCreate, mother_id: int):
    db_plan = models.AntenatalPlan(**plan.dict(), mother_id=mother_id)
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

def get_antenatal_plans_for_mother(db: Session, mother_id: int):
    return db.query(models.AntenatalPlan).filter(models.AntenatalPlan.mother_id == mother_id).all()
                      
# --- Update Password Logic ---
def update_mother_password(db: Session, mother_id: int, password_data: schemas.PasswordChange):
    # 1. Get the mother
    db_mother = get_mother(db, mother_id)
    if not db_mother:
        return False
        
    # 2. Verify old password
    if not verify_password(password_data.old_password, db_mother.hashed_password):
        return False # Old password incorrect
        
    # 3. Hash new password
    new_hash = get_password_hash(password_data.new_password)
    
    # 4. Update and Save
    db_mother.hashed_password = new_hash
    db.add(db_mother)
    db.commit()
    db.refresh(db_mother)
    return True
            