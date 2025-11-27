import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
import string
from sqlalchemy.orm import Session
from sqlalchemy import or_
from . import models, schemas
from passlib.context import CryptContext

# --- CONFIGURATION (Replace with your details) ---
# For development, using Gmail App Password is easiest.
# 1. Turn on 2-Step Verification in Google Account.
# 2. Search for "App Passwords" and create one.
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "akithaperera6@gmail.com" # <--- REPLACE THIS
SENDER_PASSWORD = "yorzrasoojnanqpd"   # <--- REPLACE THIS (16 chars)

# Setup password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    return pwd_context.hash(password_bytes)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# --- Helper: Generate Random Password ---
def generate_secure_password(length=10):
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(secrets.choice(alphabet) for i in range(length))

# --- Helper: Send Email ---
def send_credentials_email(to_email, username, password, name):
    try:
        message = MIMEMultipart()
        message["From"] = SENDER_EMAIL
        message["To"] = to_email
        message["Subject"] = "Welcome to Rakawaranaya - Your Credentials"

        body = f"""
        Dear {name},

        Welcome to the Rakawaranaya National Midwife System.
        Your account has been successfully created by the Medical Officer of Health.

        Here are your login credentials for the Mobile Application:
        --------------------------------------------------
        Username: {username}
        Password: {password}
        --------------------------------------------------

        Please log in to the app and change your password immediately.

        Best regards,
        Ministry of Health (MOH)
        """
        
        message.attach(MIMEText(body, "plain"))

        # Connect to Server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls() # Secure the connection
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, message.as_string())
        server.quit()
        
        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

# ---------------------------------------------------------
# ------------------- MOH OFFICER CRUD --------------------
# ---------------------------------------------------------

def get_moh_officer_by_username(db: Session, username: str):
    return db.query(models.MOHOfficer).filter(models.MOHOfficer.username == username).first()

def create_moh_officer(db: Session, moh: schemas.MOHOfficerCreate):
    hashed_password = get_password_hash(moh.password)
    db_moh = models.MOHOfficer(
        username=moh.username, 
        hashed_password=hashed_password, 
        full_name=moh.full_name,
        moh_area=moh.moh_area,
        email=moh.email
    )
    db.add(db_moh)
    db.commit()
    db.refresh(db_moh)
    return db_moh

# ---------------------------------------------------------
# --------------------- MIDWIFE CRUD ----------------------
# ---------------------------------------------------------

def get_midwife(db: Session, midwife_id: int):
    return db.query(models.Midwife).filter(models.Midwife.id == midwife_id).first()

def get_midwife_by_username(db: Session, username: str):
    return db.query(models.Midwife).filter(models.Midwife.username == username).first()

# Legacy function (Mobile App Registration - if needed)
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

# --- WEB PORTAL: Full Midwife Registration with Auto-Credentials ---
def register_full_midwife(db: Session, midwife_data: schemas.MidwifeRegistration):
    # 1. Auto-set Username
    final_username = midwife_data.nic
    
    # 2. Check for ANY conflict (NIC, Username, Email, Phone)
    existing_midwife = db.query(models.Midwife).filter(
        or_(
            models.Midwife.username == final_username,
            models.Midwife.nic == midwife_data.nic,
            models.Midwife.email == midwife_data.email,
            models.Midwife.phone_number == midwife_data.phone_number
        )
    ).first()

    if existing_midwife:
        # Ideally, you'd return WHICH field failed, but returning None triggers the 400 error
        return None 
    
    # 3. Generate Password
    generated_password = generate_secure_password()
    hashed_password = get_password_hash(generated_password)
    
    # 4. Create DB Object
    db_midwife = models.Midwife(
        username=final_username,
        hashed_password=hashed_password,
        full_name=midwife_data.full_name,
        nic=midwife_data.nic,
        date_of_birth=midwife_data.date_of_birth,
        phone_number=midwife_data.phone_number,
        email=midwife_data.email,
        residential_address=midwife_data.residential_address,
        slmc_reg_no=midwife_data.slmc_reg_no,
        service_grade=midwife_data.service_grade,
        assigned_moh_area=midwife_data.assigned_moh_area,
        is_active=midwife_data.is_active
    )
    
    db.add(db_midwife)
    db.commit()
    db.refresh(db_midwife)
    
    # 5. Send Email
    print(f"\n[CREDENTIALS GENERATED] ...") 
    if midwife_data.email:
        send_credentials_email(midwife_data.email, final_username, generated_password, midwife_data.full_name)
    
    return db_midwife
# ---------------------------------------------------------
# ---------------------- MOTHER CRUD ----------------------
# ---------------------------------------------------------

def get_mother_by_nic(db: Session, nic: str):
    return db.query(models.Mother).filter(models.Mother.nic == nic).first()

def get_mother(db: Session, mother_id: int):
    return db.query(models.Mother).filter(models.Mother.id == mother_id).first()

def get_mothers_by_midwife(db: Session, midwife_id: int, skip: int = 0, limit: int = 100, search: str = None):
    query = db.query(models.Mother).filter(models.Mother.midwife_id == midwife_id)
    
    if search:
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

def update_mother(db: Session, mother_id: int, mother_update: schemas.MotherUpdate):
    db_mother = get_mother(db, mother_id)
    if not db_mother:
        return None
    
    update_data = mother_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_mother, key, value)

    db.add(db_mother)
    db.commit()
    db.refresh(db_mother)
    return db_mother

def update_mother_password(db: Session, mother_id: int, password_data: schemas.PasswordChange):
    db_mother = get_mother(db, mother_id)
    if not db_mother:
        return False
        
    if not verify_password(password_data.old_password, db_mother.hashed_password):
        return False 
        
    new_hash = get_password_hash(password_data.new_password)
    db_mother.hashed_password = new_hash
    db.add(db_mother)
    db.commit()
    db.refresh(db_mother)
    return True

# ---------------------------------------------------------
# ------------------ HEALTH RECORDS CRUD ------------------
# ---------------------------------------------------------

def create_health_record(db: Session, record: schemas.HealthRecordCreate, mother_id: int):
    db_record = models.HealthRecord(**record.dict(), mother_id=mother_id)
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def get_health_records_for_mother(db: Session, mother_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.HealthRecord).filter(models.HealthRecord.mother_id == mother_id).offset(skip).limit(limit).all()

# ---------------------------------------------------------
# ----------------- PREGNANCY RECORDS CRUD ----------------
# ---------------------------------------------------------

def create_pregnancy_record(db: Session, record: schemas.PregnancyRecordCreate, mother_id: int):
    db_record = models.PregnancyRecord(**record.dict(), mother_id=mother_id)
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def get_pregnancy_records_for_mother(db: Session, mother_id: int):
    return db.query(models.PregnancyRecord).filter(models.PregnancyRecord.mother_id == mother_id).all()

# ---------------------------------------------------------
# ----------------- DELIVERY RECORDS CRUD -----------------
# ---------------------------------------------------------

def create_delivery_record(db: Session, record: schemas.DeliveryRecordCreate, mother_id: int):
    db_record = models.DeliveryRecord(**record.dict(), mother_id=mother_id)
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def get_delivery_records_for_mother(db: Session, mother_id: int):
    return db.query(models.DeliveryRecord).filter(models.DeliveryRecord.mother_id == mother_id).all()

# ---------------------------------------------------------
# ------------------ ANTENATAL PLAN CRUD ------------------
# ---------------------------------------------------------

def create_antenatal_plan(db: Session, plan: schemas.AntenatalPlanCreate, mother_id: int):
    db_plan = models.AntenatalPlan(**plan.dict(), mother_id=mother_id)
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

def get_antenatal_plans_for_mother(db: Session, mother_id: int):
    return db.query(models.AntenatalPlan).filter(models.AntenatalPlan.mother_id == mother_id).all()
            