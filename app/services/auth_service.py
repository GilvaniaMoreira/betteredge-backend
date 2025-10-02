from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin
from app.core.security import verify_password, get_password_hash, create_access_token
from datetime import timedelta
from app.core.config import settings


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user_data: UserCreate) -> User:
        try:
            hashed_password = get_password_hash(user_data.password)
            db_user = User(
                email=user_data.email,
                password=hashed_password,
                is_active=True
            )
            self.db.add(db_user)
            await self.db.commit()
            await self.db.refresh(db_user)
            return db_user
        except Exception as e:
            print(f"User creation error: {e}")
            await self.db.rollback()
            raise e

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def authenticate_user(self, user_data: UserLogin) -> User | None:
        try:
            user = await self.get_user_by_email(user_data.email)
            if not user:
                return None
            
            try:
                if not verify_password(user_data.password, user.password):
                    return None
            except Exception as e:
                print(f"Password verification failed for user {user.email}: {e}")
                return None
                
            return user
        except Exception as e:
            print(f"Authentication error: {e}")
            return None

    async def create_access_token(self, user: User) -> str:
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=access_token_expires
        )
        return access_token

