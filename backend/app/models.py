from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    business_registration_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    workplace_management_number: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    job_posting_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    checks: Mapped[list["CheckResult"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
        order_by=lambda: CheckResult.checked_at.desc(),
    )


class CheckResult(Base):
    __tablename__ = "check_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True,
    )
    wage_arrears_status: Mapped[str] = mapped_column(
        String(20),
        default="not_checked",
        nullable=False,
    )
    changed_fields: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    company: Mapped[Company] = relationship(back_populates="checks")
