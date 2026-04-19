from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Conveções previsíveis de nome ajudam bastante em migrations,
# troubleshootings e manutenção futura

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata_obj = MetaData(naming_convention=NAMING_CONVENTION)

class Base(DeclarativeBase):
    """
    Classe base de todos os modelos ORM.

    Centralizamos o metadata para deixar o Alembic enxergar
    as tabelas corretamente e gerar migrations consistentes.
    """ 
    metadata = metadata_obj 