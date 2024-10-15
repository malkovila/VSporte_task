from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from passlib.context import CryptContext
from sqlalchemy import and_, or_

from app.models import Role, User, UserRole, Service

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def create_user_role(db: Session, user: schemas.UserRoleCreate):
    existing_user = db.query(User).filter(
        (User.username == user.username)
    ).first()
    if not existing_user:
        raise HTTPException(status_code=400,
                            detail="User with given credentials does not exist"
                            )


    existing_role = db.query(Role).filter(
        (Role.name == user.role)
    ).first()

    if not existing_role:
        raise HTTPException(status_code=400,
                            detail="Role does not exist"
                            )


    existing_user_role = (
        db.query(UserRole)
        .join(User)
        .join(Role)
        .join(Service)
        .filter(
    User.username == user.username,
            Service.name == user.service
        )
        .first()
    )

    if existing_user_role:
        raise HTTPException(
            status_code=400,
            detail="User already has role on this server"
        )

    role = db.query(Role).filter_by(name=user.role).first()
    service = db.query(Service).filter_by(name=user.service).first()
    db_user = db.query(User).filter_by(username=user.username).first()

    new_user_role = UserRole(
        user_id=db_user.id,
        role_id=role.id,
        service_id=service.id
    )
    db.add(new_user_role)
    db.commit()
    return new_user_role


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)


    # Проверка на существование пользователя с таким же email или username
    existing_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400,
            detail="User with given credentials already exist"
       )

    db_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_users(db, service, limit=10, offset=0):
    users = (
        db.query(User.username, User.email)
        .join(UserRole, User.id == UserRole.user_id)
        .join(Service, UserRole.service_id == Service.id)
        .filter(Service.name == service)
        .limit(limit)        # Ограничение на количество записей
        .offset(offset)      # Сдвиг для пагинации
        .all()
    )
    return [{"username": user[0], "email": user[1]} for user in users]


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
