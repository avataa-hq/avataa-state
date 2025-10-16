from typing import List

from sqlalchemy.orm import declarative_base, Mapped
from sqlalchemy import (
    String,
    BigInteger,
    Boolean,
    TIMESTAMP,
    UniqueConstraint,
    CheckConstraint,
    ForeignKeyConstraint,
)
from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

Base = declarative_base()

possible_brach_types = {"vodafone", "ooredoo", "all"}


class RelatedKPI(Base):
    __tablename__ = "related_kpis"
    main_kpi = Column(
        Integer,
        ForeignKey("kpi.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    related_kpi = Column(
        Integer,
        ForeignKey("kpi.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

    __table_args__ = (
        CheckConstraint(
            "main_kpi != related_kpi", name="check_main_related_kpi_not_equal"
        ),
    )


class KPI(Base):
    __tablename__ = "kpi"
    id: Mapped[int] = Column("id", BigInteger, primary_key=True)
    name: str = Column("name", String, nullable=False)
    description: str = Column("description", String, nullable=True)
    label: str = Column("label", String, nullable=True)
    val_type: str = Column("val_type", String, nullable=False)
    group: str = Column("group", String, nullable=True)
    branch: str = Column("branch", String, nullable=True)
    multiple: bool = Column("multiple", Boolean, default=False)
    object_type: Mapped[int] = Column("object_type", Integer, nullable=True)
    parent_kpi: Mapped[int | None] = Column(
        "parent_kpi", Integer, nullable=True
    )
    child_kpi: Mapped[int | None] = Column("child_kpi", Integer, nullable=True)

    granularities: Mapped[List["Granularity"]] = relationship(
        "Granularity", back_populates="kpi"
    )

    related_kpis = relationship(
        "KPI",
        secondary=RelatedKPI.__table__,
        primaryjoin=id == RelatedKPI.main_kpi,
        secondaryjoin=id == RelatedKPI.related_kpi,
        backref="related_to",
    )

    __table_args__ = (
        UniqueConstraint("name", "object_type"),
        ForeignKeyConstraint(
            ["parent_kpi"], ["kpi.id"], name="kpi_parent_kpi_fkey"
        ),
        ForeignKeyConstraint(
            ["child_kpi"], ["kpi.id"], name="kpi_child_kpi_fkey"
        ),
    )


class Granularity(Base):
    __tablename__ = "granularity"
    id: int = Column("id", BigInteger, primary_key=True)
    kpi_id: int = Column(
        BigInteger, ForeignKey("kpi.id", ondelete="CASCADE"), nullable=False
    )
    name: str = Column(String, nullable=False)
    seconds: int = Column(Integer, nullable=True)

    kpi: Mapped["KPI"] = relationship("KPI", back_populates="granularities")

    __table_args__ = (UniqueConstraint("name", "kpi_id"),)


class KPIValue(Base):
    __tablename__ = "kpi_values"
    id: int = Column("id", BigInteger, primary_key=True)
    kpi_id: int = Column(
        BigInteger,
        ForeignKey("kpi.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    granularity_id: int = Column(
        BigInteger,
        ForeignKey("granularity.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    object_id: int = Column("object_id", Integer, nullable=False, index=True)
    value: str = Column("value", String, nullable=False)
    record_time: datetime = Column(
        "record_time",
        TIMESTAMP(timezone=True),
        default=datetime.utcnow,
        index=True,
    )
    state: str = Column("state", String, nullable=False, index=True)

    def serialize_before_save(self, serializer_func: callable):
        self.value = serializer_func(self.value)

    def deserialize_value(self, deserialize_func: callable):
        self.value = deserialize_func(self.value)

    def validate_value(self, validate_func: callable):
        validate_func(self.value)


class PermissionTemplate(Base):
    __abstract__ = True

    id: Mapped[int] = Column(Integer, primary_key=True)
    root_permission_id: Mapped[int] | None = Column(Integer, nullable=True)
    permission: Mapped[str] = Column(String, nullable=False)
    permission_name: Mapped[str] = Column(String, nullable=False)
    create: Mapped[bool] = Column(Boolean, default=False, nullable=False)
    read: Mapped[bool] = Column(Boolean, default=False, nullable=False)
    update: Mapped[bool] = Column(Boolean, default=False, nullable=False)
    delete: Mapped[bool] = Column(Boolean, default=False, nullable=False)
    admin: Mapped[bool] = Column(Boolean, default=False, nullable=False)
    parent_id: Mapped[int] = Column(Integer, primary_key=True)

    __table_args__ = (UniqueConstraint("parent_id", "permission"),)

    def update_from_dict(self, item: dict):
        for key, value in item.items():
            if not hasattr(self, key):
                continue
            setattr(self, key, value)

    def to_dict(self, only_actions: bool = False):
        res = self.__dict__
        if "_sa_instance_state" in res:
            res.pop("_sa_instance_state")

        if only_actions:
            return {
                "create": res["create"],
                "read": res["read"],
                "update": res["update"],
                "delete": res["delete"],
                "admin": res["admin"],
            }
        return res


class KPIPermission(PermissionTemplate):
    __tablename__ = "kpi_permission"
    root_permission_id: int | None = Column(
        Integer,
        ForeignKey(
            f"{__tablename__}.id", onupdate="CASCADE", ondelete="CASCADE"
        ),
        nullable=True,
        index=True,
    )
    parent_id: int = Column(
        Integer,
        ForeignKey(KPI.__table__.c.id, onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    parent = relationship(
        "KPIPermission",
        backref="child",
        remote_side="KPIPermission.id",
        uselist=False,
    )
