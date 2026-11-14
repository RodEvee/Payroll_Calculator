# Phase 4 payroll_engine
#Phase 4 app.py comments
#Supplemental Bonus Engine (calculator.py): Adds an optional one-time Bonus ($) input taxed at the IRS 22% flat supplemental federal rate (plus applicable state and FICA taxes), without distorting your annualized base tax bracket.
#Post-Tax Deductions (Roth 401(k) & Other): Separates Pre-Tax Traditional 401(k)(which lowers taxable income) from Post-Tax Roth 401(k) and Other Post-Tax Deductions (which come out after taxes).
#Full-Year Annualized Projection: Automatically computes your Projected Annual Gross, Total Annual Retirement Savings (Traditional + Roth 401k), Total Annual Taxes, and Projected Annual Net Pay based on your regular recurring paycheck.

#Designed by Rodney Smith 11/14/2026

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


class PayType(str, Enum):
    HOURLY = "Hourly"
    SALARY = "Annual Salary"


class PayFrequency(str, Enum):
    WEEKLY = "Weekly (52/yr)"
    BI_WEEKLY = "Bi-Weekly (26/yr)"
    SEMI_MONTHLY = "Semi-Monthly (24/yr)"
    MONTHLY = "Monthly (12/yr)"

    @property
    def periods_per_year(self) -> int:
        mapping = {
            PayFrequency.WEEKLY: 52,
            PayFrequency.BI_WEEKLY: 26,
            PayFrequency.SEMI_MONTHLY: 24,
            PayFrequency.MONTHLY: 12,
        }
        return mapping[self]


class FilingStatus(str, Enum):
    SINGLE = "Single"
    MARRIED_JOINT = "Married Filing Jointly"
    HEAD_OF_HOUSEHOLD = "Head of Household"


# 2026 IRS Standard Deductions (Rev. Proc. 2025-32)
STANDARD_DEDUCTIONS_2026: Dict[FilingStatus, float] = {
    FilingStatus.SINGLE: 16100.0,
    FilingStatus.MARRIED_JOINT: 32200.0,
    FilingStatus.HEAD_OF_HOUSEHOLD: 24150.0,
}

# 2026 IRS Progressive Tax Brackets: (upper_bound, marginal_rate)
FEDERAL_BRACKETS_2026: Dict[FilingStatus, List[Tuple[float, float]]] = {
    FilingStatus.SINGLE: [
        (12400.0, 0.10),
        (50400.0, 0.12),
        (105700.0, 0.22),
        (201775.0, 0.24),
        (256225.0, 0.32),
        (640600.0, 0.35),
        (float("inf"), 0.37),
    ],
    FilingStatus.MARRIED_JOINT: [
        (24800.0, 0.10),
        (100800.0, 0.12),
        (211400.0, 0.22),
        (403550.0, 0.24),
        (512450.0, 0.32),
        (768700.0, 0.35),
        (float("inf"), 0.37),
    ],
    FilingStatus.HEAD_OF_HOUSEHOLD: [
        (17700.0, 0.10),
        (67450.0, 0.12),
        (105700.0, 0.22),
        (201750.0, 0.24),
        (256200.0, 0.32),
        (640600.0, 0.35),
        (float("inf"), 0.37),
    ],
}

ADDITIONAL_MEDICARE_THRESHOLD: Dict[FilingStatus, float] = {
    FilingStatus.SINGLE: 200000.0,
    FilingStatus.MARRIED_JOINT: 250000.0,
    FilingStatus.HEAD_OF_HOUSEHOLD: 200000.0,
}


@dataclass(frozen=True)
class PayrollInput:
    employee_name: str
    pay_type: PayType
    pay_frequency: PayFrequency
    filing_status: FilingStatus
    hourly_rate: float = 0.0
    hours_worked: float = 0.0
    annual_salary: float = 0.0
    bonus_amount: float = 0.0
    trad_401k_percent: float = 0.0
    roth_401k_percent: float = 0.0
    health_insurance: float = 0.0
    other_posttax_deduction: float = 0.0
    state_tax_percent: float = 0.0

    def validate(self) -> Optional[str]:
        """Validates inputs and returns an error message if invalid, else None."""
        if not self.employee_name.strip():
            return "Employee name cannot be empty."
        if self.pay_type == PayType.HOURLY:
            if self.hourly_rate <= 0:
                return "Hourly rate must be greater than $0.00."
            if self.hours_worked <= 0:
                return "Hours worked must be greater than 0."
            if self.hours_worked > 168:
                return "Hours worked cannot exceed 168 hours in a single week."
        elif self.pay_type == PayType.SALARY:
            if self.annual_salary <= 0:
                return "Annual salary must be greater than $0.00."

        if self.bonus_amount < 0:
            return "Bonus amount cannot be negative."
        if not (0 <= self.trad_401k_percent <= 100):
            return "Traditional 401(k) must be between 0% and 100%."
        if not (0 <= self.roth_401k_percent <= 100):
            return "Roth 401(k) must be between 0% and 100%."
        if (self.trad_401k_percent + self.roth_401k_percent) > 100:
            return "Combined Traditional and Roth 401(k) contributions cannot exceed 100%."
        if self.health_insurance < 0:
            return "Health insurance deduction cannot be negative."
        if self.other_posttax_deduction < 0:
            return "Other post-tax deductions cannot be negative."
        if not (0 <= self.state_tax_percent <= 100):
            return "State tax rate must be between 0% and 100%."

        return None


@dataclass(frozen=True)
class PayrollResult:
    employee_name: str
    pay_frequency: str
    filing_status: str
    periods_per_year: int
    # Earnings
    regular_pay: float
    overtime_pay: float
    bonus_pay: float
    gross_pay: float
    # Pre-Tax
    trad_401k_deduction: float
    health_insurance_deduction: float
    total_pretax_deductions: float
    taxable_income: float
    # Taxes
    federal_tax: float
    marginal_federal_rate: float
    effective_federal_rate: float
    state_tax: float
    social_security_tax: float
    medicare_tax: float
    total_taxes: float
    # Post-Tax
    roth_401k_deduction: float
    other_posttax_deduction: float
    total_posttax_deductions: float
    # Net & Annualized Projections (Based on recurring base pay excluding one-time bonus)
    net_pay: float
    annual_gross_base: float
    annual_401k_total: float
    annual_taxes_base: float
    annual_net_base: float


class PayrollCalculator:
    STANDARD_WORK_WEEK: float = 40.0
    OVERTIME_MULTIPLIER: float = 1.5
    SUPPLEMENTAL_BONUS_FED_RATE: float = 0.22
    SOCIAL_SECURITY_RATE: float = 0.062
    SOCIAL_SECURITY_WAGE_CAP_2026: float = 184500.0
    MEDICARE_RATE: float = 0.0145
    ADDITIONAL_MEDICARE_RATE: float = 0.009

    @classmethod
    def _compute_annual_federal_tax(
        cls, annual_taxable_income: float, filing_status: FilingStatus
    ) -> Tuple[float, float]:
        """Returns (annual_federal_tax, marginal_rate_percent)."""
        if annual_taxable_income <= 0:
            return 0.0, 10.0

        brackets = FEDERAL_BRACKETS_2026[filing_status]
        tax = 0.0
        previous_limit = 0.0
        marginal_rate = 0.10

        for upper_limit, rate in brackets:
            if annual_taxable_income > previous_limit:
                marginal_rate = rate
                taxable_in_bracket = min(annual_taxable_income, upper_limit) - previous_limit
                tax += taxable_in_bracket * rate
                previous_limit = upper_limit
            else:
                break

        return tax, marginal_rate * 100.0

    @classmethod
    def calculate(cls, data: PayrollInput) -> PayrollResult:
        """Computes full employee paycheck breakdown with bonuses, Roth 401k, and annual totals."""
        error = data.validate()
        if error:
            raise ValueError(error)

        periods = data.pay_frequency.periods_per_year

        # 1. Gross Earnings (Base vs. One-Time Bonus)
        if data.pay_type == PayType.HOURLY:
            regular_hours = min(data.hours_worked, cls.STANDARD_WORK_WEEK)
            overtime_hours = max(0.0, data.hours_worked - cls.STANDARD_WORK_WEEK)
            regular_pay = regular_hours * data.hourly_rate
            overtime_pay = overtime_hours * (data.hourly_rate * cls.OVERTIME_MULTIPLIER)
            base_gross = regular_pay + overtime_pay
        else:
            regular_pay = data.annual_salary / periods
            overtime_pay = 0.0
            base_gross = regular_pay

        bonus_pay = data.bonus_amount
        gross_pay = base_gross + bonus_pay

        # 2. Pre-Tax Deductions (401k applies to total gross; Health is per paycheck)
        trad_401k = gross_pay * (data.trad_401k_percent / 100.0)
        health_deduction = data.health_insurance
        total_pretax = trad_401k + health_deduction

        if total_pretax > gross_pay:
            raise ValueError("Total pre-tax deductions cannot exceed gross pay.")

        # 3. Federal Income Tax (Base annualized via brackets + Bonus at 22% supplemental rate)
        base_trad_401k = base_gross * (data.trad_401k_percent / 100.0)
        bonus_trad_401k = bonus_pay * (data.trad_401k_percent / 100.0)

        base_income_taxable = max(0.0, base_gross - base_trad_401k - health_deduction)
        bonus_income_taxable = max(0.0, bonus_pay - bonus_trad_401k)
        total_income_taxable = base_income_taxable + bonus_income_taxable

        annualized_base_taxable = base_income_taxable * periods
        standard_deduction = STANDARD_DEDUCTIONS_2026[data.filing_status]
        annual_fed_taxable = max(0.0, annualized_base_taxable - standard_deduction)

        annual_base_fed_tax, marginal_rate = cls._compute_annual_federal_tax(
            annual_fed_taxable, data.filing_status
        )
        base_federal_tax = annual_base_fed_tax / periods
        bonus_federal_tax = bonus_income_taxable * cls.SUPPLEMENTAL_BONUS_FED_RATE
        federal_tax = base_federal_tax + bonus_federal_tax

        effective_fed_rate = (federal_tax / gross_pay * 100.0) if gross_pay > 0 else 0.0

        # 4. State & FICA Taxes
        state_tax = total_income_taxable * (data.state_tax_percent / 100.0)
        base_state_tax = base_income_taxable * (data.state_tax_percent / 100.0)

        base_fica_wages = max(0.0, base_gross - health_deduction)
        total_fica_wages = max(0.0, gross_pay - health_deduction)

        annual_fica_est = (base_fica_wages * periods) + bonus_pay
        capped_ss_annual = min(annual_fica_est, cls.SOCIAL_SECURITY_WAGE_CAP_2026)
        # Proportional Social Security for current paycheck
        ss_ratio = (capped_ss_annual / annual_fica_est) if annual_fica_est > 0 else 0.0
        social_security_tax = total_fica_wages * cls.SOCIAL_SECURITY_RATE * ss_ratio

        base_medicare = total_fica_wages * cls.MEDICARE_RATE
        addl_threshold = ADDITIONAL_MEDICARE_THRESHOLD[data.filing_status]
        excess_medicare_annual = max(0.0, annual_fica_est - addl_threshold)
        addl_medicare = (excess_medicare_annual * cls.ADDITIONAL_MEDICARE_RATE) / periods
        medicare_tax = base_medicare + addl_medicare

        total_taxes = federal_tax + state_tax + social_security_tax + medicare_tax

        # 5. Post-Tax Deductions (Roth 401k + Other)
        roth_401k = gross_pay * (data.roth_401k_percent / 100.0)
        other_posttax = data.other_posttax_deduction
        total_posttax = roth_401k + other_posttax

        # 6. Net Take-Home Pay
        net_pay = gross_pay - total_pretax - total_taxes - total_posttax
        if net_pay < 0:
            raise ValueError("Total deductions and taxes exceed gross pay.")

        # 7. Annualized Base Projections (Recurring paycheck x periods per year)
        annual_base_fica = base_fica_wages * periods
        base_ss = (
            min(annual_base_fica, cls.SOCIAL_SECURITY_WAGE_CAP_2026)
            * cls.SOCIAL_SECURITY_RATE
            / periods
        )
        base_addl_med = (
            max(0.0, annual_base_fica - addl_threshold)
            * cls.ADDITIONAL_MEDICARE_RATE
            / periods
        )
        base_med = (base_fica_wages * cls.MEDICARE_RATE) + base_addl_med
        base_total_taxes = base_federal_tax + base_state_tax + base_ss + base_med
        base_roth_401k = base_gross * (data.roth_401k_percent / 100.0)
        base_net_pay = (
            base_gross
            - (base_trad_401k + health_deduction)
            - base_total_taxes
            - (base_roth_401k + other_posttax)
        )

        return PayrollResult(
            employee_name=data.employee_name.strip(),
            pay_frequency=data.pay_frequency.value,
            filing_status=data.filing_status.value,
            periods_per_year=periods,
            regular_pay=round(regular_pay, 2),
            overtime_pay=round(overtime_pay, 2),
            bonus_pay=round(bonus_pay, 2),
            gross_pay=round(gross_pay, 2),
            trad_401k_deduction=round(trad_401k, 2),
            health_insurance_deduction=round(health_deduction, 2),
            total_pretax_deductions=round(total_pretax, 2),
            taxable_income=round(total_income_taxable, 2),
            federal_tax=round(federal_tax, 2),
            marginal_federal_rate=round(marginal_rate, 1),
            effective_federal_rate=round(effective_fed_rate, 2),
            state_tax=round(state_tax, 2),
            social_security_tax=round(social_security_tax, 2),
            medicare_tax=round(medicare_tax, 2),
            total_taxes=round(total_taxes, 2),
            roth_401k_deduction=round(roth_401k, 2),
            other_posttax_deduction=round(other_posttax, 2),
            total_posttax_deductions=round(total_posttax, 2),
            net_pay=round(net_pay, 2),
            annual_gross_base=round(base_gross * periods, 2),
            annual_401k_total=round((base_trad_401k + base_roth_401k) * periods, 2),
            annual_taxes_base=round(base_total_taxes * periods, 2),
            annual_net_base=round(base_net_pay * periods, 2),
        )