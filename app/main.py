from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload
from starlette import status

from app import models, crud, schemas
from app.crud import create_user, create_user_role
from app.database import engine, get_db
from app.auth import authenticate_user, create_access_token, get_current_user
from app.schemas import UserCreate, UserRead, RoleRead, ServiceRead, RoleCreate, UserRoleCreate, ServiceCreate, \
    UserRoleRead, DeleteUserServer, DeleteUser, Token
from app.models import User, Role, Service, UserRole

models.Base.metadata.create_all(bind=engine)

app = FastAPI()




@app.post("/create_user/", response_model=UserRead)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):

    # Создание нового пользователя
    new_user = create_user(db, user)
    return new_user

@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post('/create_role', response_model=RoleRead)
def create_role(role: RoleCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    existing_role = db.query(Role).filter(
        (Role.name == role.name)
    ).first()
    if existing_role:
        raise HTTPException(
            status_code=400,
            detail="Role already registered"
        )

    db_role = models.Role(name=role.name)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

@app.post('/create_service', response_model=ServiceRead)
def create_service(service: ServiceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing_service = db.query(Service).filter(
        (Service.name == service.name)
    ).first()
    if existing_service:
        raise HTTPException(
            status_code=400,
            detail="Service already registered"
        )

    db_service = models.Service(name=service.name)
    db.add(db_service)
    db.commit()
    db.refresh(db_service)

    user_role = UserRole(user_id=current_user.id, service_id=db_service.id, role_id=1) #role_id - admin, пользователь сразу после создания пользователя должен вызвать два раза роут /create_role (см. ReadMe.md)
    db.add(user_role)
    db.commit()

    return db_service


@app.post("/get_role_to_user/", response_model=UserRoleRead)
def get_role_to_user(user: UserRoleCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user = db.query(User).filter(User.username == user.username).first()
    current_user_who_gives = db.query(User).filter(User.username == user.who_gives_role).first()

    if not current_user:
        raise HTTPException(status_code=400,
                            detail="User with given credentials does not exist"
                            )
    if not current_user_who_gives:
        raise HTTPException(status_code=400,
                            detail="User with given credentials does not exist"
                            )

    service = db.query(Service).filter(Service.name == user.service).first()
    if not service:
        raise HTTPException(status_code=400,
                            detail="Service does not exist"
                            )
    user_role = (
        db.query(UserRole)
        .options(joinedload(UserRole.role))
        .filter(UserRole.user_id == current_user_who_gives.id, UserRole.service_id == service.id)
        .first()
    )

    if user_role.role.name != "admin":
        raise HTTPException(status_code=400,
                            detail="You can not give roles. You are not"
                                   " admin on this server."
                            )

    new_user_role = create_user_role(db, user)
    return new_user_role


@app.post("/delete_user_from_service/")
def delete_user_from_service(user:DeleteUserServer, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user = db.query(User).filter(User.username == user.who_delete_username).first()
    current_user_to_delete = db.query(User).filter(User.username == user.username_to_delete).first()
    if not current_user:
        raise HTTPException(status_code=400,
                            detail="User who delete with given credentials does not exist"
                            )
    if not current_user_to_delete:
        raise HTTPException(status_code=400,
                            detail="User to delete with given credentials does not exist"
                            )

    # Получаем услугу по её имени
    service = db.query(Service).filter(Service.name == user.service).first()
    if not service:
        raise HTTPException(status_code=400,
                            detail="Service does not exist"
                            )

    # Получаем связанный UserRole для пользователя и сервиса
    user_role = (
        db.query(UserRole)
        .options(joinedload(UserRole.role))
        .filter(UserRole.user_id == current_user.id, UserRole.service_id == service.id)
        .first()
    )

    if user_role.role.name != "admin":
        raise HTTPException(status_code=400,
                            detail="You can not delete users from this server. You are not"
                                   " admin on this server."
                            )
    try:
        s = db.query(UserRole).filter(UserRole.user_id == current_user_to_delete.id, UserRole.service_id == service.id).first()
        db.delete(s)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=400,
                            detail=f"Can not delete user: {e}"
                            )



@app.post("/delete_user/")
def delete_user(user:DeleteUser, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if user.username_to_delete == user.who_delete_username:
        try:
            user_del = db.query(User).filter(User.username==user.username_to_delete).first()
            db.delete(user_del)
            db.commit()
        except Exception as e:
            raise HTTPException(status_code=400,
                                detail=f"Error to delete: {e}"
                                )
    else:
        raise HTTPException(status_code=400,
                            detail=f"To delete user you may be this user."
                            )


@app.get("/users/")
def get_users(service: str = None, username: str = None, limit: int = 10, offset: int = 0, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user = db.query(User).filter(User.username == username).first()
    if not current_user:
        raise HTTPException(status_code=400, detail="User with given credentials does not exist")

    current_service = db.query(Service).filter(Service.name == service).first()
    if not current_service:
        raise HTTPException(status_code=400, detail="Service does not exist")

    user_role = (
        db.query(UserRole)
        .options(joinedload(UserRole.role))
        .filter(UserRole.user_id == current_user.id, UserRole.service_id == current_service.id)
        .first()
    )

    if user_role.role.name != "admin":
        raise HTTPException(status_code=400, detail="You cannot get the list of users. You are not an admin.")

    users = crud.get_users(db, service=service, limit=limit, offset=offset)  # Добавляем пагинацию
    return {"users": users}


