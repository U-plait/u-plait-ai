from fastapi import Depends
from sqlalchemy.orm import Session
from app.utils.banword_filter import BanwordFilter
from app.core.database import get_db

banword_filter: BanwordFilter = None

def init_banword_filter(db: Session):
    global banword_filter
    if banword_filter is None:
        banword_filter = BanwordFilter.from_db(db)
    return banword_filter

def get_banword_filter(db: Session = Depends(get_db)) -> BanwordFilter:
    return init_banword_filter(db)