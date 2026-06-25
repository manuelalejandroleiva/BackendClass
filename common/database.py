from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base


class BaseModel:
    def to_dict(self, exclude: set = None):
        result = {
            c.key: getattr(self, c.key)
            for c in sa_inspect(self).mapper.column_attrs
        }
        if exclude:
            for key in exclude:
                result.pop(key, None)
        return result


# Shared Base for all models
Base = declarative_base(cls=BaseModel)
