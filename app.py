# 4 Phase app.py Comments:

### 3. How to Test Phase 4 Note that `app.py` imports `pandas` (which comes pre-installed with Streamlit) for the horizontal bar chart.
# Run `streamlit run app.py` and verify these scenarios:
# 1. **Traditional vs. Roth 401(k) Tax Effect:** Run a `$95,000` salary with `8%` **Traditional 401(k)** and `0%` Roth, then run a second scenario with `0%` Traditional and `8%` **Roth 401(k)**.
# Compare both rows in the **Saved Scenarios** table—your total 401(k) saved is identical, while your current Net Take-Home is higher with Traditional 401(k) due to immediate pre-tax savings.
# 2. **One-Time Bonus Check:** Enter `$2,000` in **One-Time Bonus (\$)** and verify that it adds `$2,000` to your current paycheck's Gross Pay (taxed at `22%` federal supplemental rate) while keeping the **Projected Full-Year Summary** cleanly anchored to your recurring base pay.

#Designed by Rodney Smith 11/14/2026
import io
from dataclasses import asdict
from typing import List
import pandas as pd
import streamlit as st
from calculator import (
    FilingStatus,
    PayFrequency,
    PayrollCalculator,
    PayrollInput,
    PayrollResult,
    PayType,
)

# Page Configuration
st.set_page_config(
    page_title="Personal Paycheck Planner - Phase 4",
    page_icon="💵",
    layout="centered",
)

# Initialize Session State
if "last_result" not in st.session_state:
    st.session_state.last_result: PayrollResult | None = None
if "payroll_history" not in st.session_state:
    st.session_state.payroll_history: List[PayrollResult] = []


def convert_history_to_csv(history: List[PayrollResult]) -> str:
    """Serializes the payroll history list into a CSV string."""
    output = io.StringIO()
    if not history:
        return ""
    fieldnames = list(asdict(history[0]).keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in history:
        writer.writerow(asdict(row))
    return output.getvalue()


st.title("💵 Personal Paycheck Planner")
st.caption("Phase 4: Bonuses, Traditional & Roth 401(k), Visual Breakdown & Annual Summary")

# Top Selectors (Outside form so UI updates dynamically)
col_type, col_freq, col_status = st.columns(3)
with col_type:
    selected_pay_type = st.selectbox(
        "Compensation Type",
        options=list(PayType),
        format_func=lambda x: x.value,
    )
with col_freq:
    selected_frequency = st.selectbox(
        "Pay Frequency",
        options=list(PayFrequency),
        format_func=lambda x: x.value,
        disabled=(selected_pay_type == PayType.HOURLY),
        help="Hourly mode calculates weekly paychecks.",
    )
with col_status:
    selected_filing_status = st.selectbox(
        "2026 Filing Status",
        options=list(FilingStatus),
        format_func=lambda x: x.value,
    )

# Main Calculation Form
with st.form(key="payroll_form_v4"):
    st.subheader("1. Earnings & Bonuses")
    e_name, e_bonus = st.columns(2)
    with e_name:
        employee_name = st.text_input("Label / Name", value="My Paycheck")
    with e_bonus:
        bonus_amount = st.number_input(
            "One-Time Bonus ($)",
            min_value=0.0,
            value=0.0,
            step=100.0,
            format="%.2f",
            help="Taxed at the 22% IRS supplemental federal withholding rate.",
        )

    if selected_pay_type == PayType.HOURLY:
        c1, c2 = st.columns(2)
        with c1:
            hourly_rate = st.number_input(
                "Hourly Rate ($)", min_value=0.0, value=35.00, step=0.50, format="%.2f"
            )
        with c2:
            hours_worked = st.number_input(
                "Hours Worked (Weekly)", min_value=0.0, value=40.0, step=0.5, format="%.1f"
            )
        annual_salary = 0.0
    else:
        annual_salary = st.number_input(
            "Annual Base Salary ($)", min_value=0.0, value=95000.00, step=1000.0, format="%.2f"
        )
        hourly_rate = 0.0
        hours_worked = 0.0

    st.subheader("2. Pre-Tax & Post-Tax Deductions")
    d1, d2 = st.columns(2)
    with d1:
        trad_401k = st.number_input(
            "Traditional 401(k) Pre-Tax (%)",
            min_value=0.0,
            max_value=100.0,
            value=6.0,
            step=0.5,
            format="%.1f",
        )
        health_insurance = st.number_input(
            "Health / Dental / Vision Pre-Tax ($)",
            min_value=0.0,
            value=150.00,
            step=10.0,
            format="%.2f",
        )
    with d2:
        roth_401k = st.number_input(
            "Roth 401(k) Post-Tax (%)",
            min_value=0.0,
            max_value=100.0,
            value=2.0,
            step=0.5,
            format="%.1f",
        )
        other_posttax = st.number_input(
            "Other Post-Tax Deductions ($)",
            min_value=0.0,
            value=0.00,
            step=10.0,
            format="%.2f",
            help="E.g., commuter benefits, garnishments, or post-tax insurance.",
        )

    st.subheader("3. State Income Tax")
    state_tax = st.number_input(
        "State Income Tax Rate (%)",
        min_value=0.0,
        max_value=15.0,
        value=0.0,
        step=0.25,
        format="%.2f",
        help="Set to 0.00% for states with no state income tax (e.g., FL, TX, WA).",
    )

    submitted = st.form_submit_button("Calculate Paycheck", use_container_width=True)

# Form Submission & Error Handling
if submitted:
    active_freq = (
        PayFrequency.WEEKLY if selected_pay_type == PayType.HOURLY else selected_frequency
    )
    payroll_input = PayrollInput(
        employee_name=employee_name,
        pay_type=selected_pay_type,
        pay_frequency=active_freq,
        filing_status=selected_filing_status,
        hourly_rate=hourly_rate,
        hours_worked=hours_worked,
        annual_salary=annual_salary,
        bonus_amount=bonus_amount,
        trad_401k_percent=trad_401k,
        roth_401k_percent=roth_401k,
        health_insurance=health_insurance,
        other_posttax_deduction=other_posttax,
        state_tax_percent=state_tax,
    )

    try:
        result = PayrollCalculator.calculate(payroll_input)
        st.session_state.last_result = result
        st.session_state.payroll_history.append(result)
    except ValueError as e:
        st.error(str(e))
        st.session_state.last_result = None

# Display Current Paycheck Breakdown
if st.session_state.last_result is not None:
    res: PayrollResult = st.session_state.last_result

    st.divider()
    st.subheader(f"Paycheck Summary: {res.employee_name}")

    # Top-Line Paycheck Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Gross Pay", f"${res.gross_pay:,.2f}")
    m2.metric("Total Deductions", f"-${(res.total_pretax_deductions + res.total_posttax_deductions):,.2f}")
    m3.metric("Total Taxes", f"-${res.total_taxes:,.2f}")
    m4.metric("Net Take-Home", f"${res.net_pay:,.2f}")

    # Visual Breakdown Chart
    st.markdown("**Where Your Paycheck Goes**")
    total_retirement = res.trad_401k_deduction + res.roth_401k_deduction
    total_benefits_other = res.health_insurance_deduction + res.other_posttax_deduction

    chart_df = pd.DataFrame(
        {
            "Category": [
                "Net Take-Home Pay",
                "Total Taxes",
                "401(k) Retirement (Trad + Roth)",
                "Health & Other Deductions",
            ],
            "Amount ($)": [
                res.net_pay,
                res.total_taxes,
                total_retirement,
                total_benefits_other,
            ],
        }
    ).set_index("Category")
    st.bar_chart(chart_df, horizontal=True)

    # Detailed Columns
    col_left, col_right = st.columns(2)

    with col_left:
        with st.container(border=True):
            st.markdown("**Earnings & Deductions**")
            st.write(f"Regular Pay: **${res.regular_pay:,.2f}**")
            if res.overtime_pay > 0:
                st.write(f"Overtime Pay (1.5x): **${res.overtime_pay:,.2f}**")
            if res.bonus_pay > 0:
                st.write(f"One-Time Bonus: **${res.bonus_pay:,.2f}**")
            st.divider()
            st.write(f"Traditional 401(k) (Pre-Tax): **-${res.trad_401k_deduction:,.2f}**")
            st.write(f"Health Insurance (Pre-Tax): **-${res.health_insurance_deduction:,.2f}**")
            st.write(f"Roth 401(k) (Post-Tax): **-${res.roth_401k_deduction:,.2f}**")
            if res.other_posttax_deduction > 0:
                st.write(f"Other Post-Tax: **-${res.other_posttax_deduction:,.2f}**")

    with col_right:
        with st.container(border=True):
            st.markdown("**2026 Tax Withholdings**")
            st.write(f"Taxable Income: **${res.taxable_income:,.2f}**")
            st.divider()
            st.write(
                f"Federal Tax ({res.marginal_federal_rate:.0f}% marginal / "
                f"{res.effective_federal_rate:.1f}% eff.): **-${res.federal_tax:,.2f}**"
            )
            st.write(f"State Income Tax: **-${res.state_tax:,.2f}**")
            st.write(f"Social Security (6.2%): **-${res.social_security_tax:,.2f}**")
            st.write(f"Medicare: **-${res.medicare_tax:,.2f}**")

    # Full-Year Recurring Summary
    with st.container(border=True):
        st.markdown(f"**Projected Full-Year Summary ({res.periods_per_year} Pay Periods, Excl. One-Time Bonus)**")
        y1, y2, y3, y4 = st.columns(4)
        y1.metric("Annual Gross", f"${res.annual_gross_base:,.2f}")
        y2.metric("Annual 401(k) Saved", f"${res.annual_401k_total:,.2f}")
        y3.metric("Annual Taxes", f"${res.annual_taxes_base:,.2f}")
        y4.metric("Annual Net Pay", f"${res.annual_net_base:,.2f}")

# Saved Scenarios & CSV Export
if st.session_state.payroll_history:
    st.divider()
    st.subheader(f"Saved Scenarios ({len(st.session_state.payroll_history)})")

    ledger_rows = [
        {
            "Scenario": item.employee_name,
            "Frequency": item.pay_frequency,
            "Gross ($)": f"{item.gross_pay:,.2f}",
            "401(k) ($)": f"{(item.trad_401k_deduction + item.roth_401k_deduction):,.2f}",
            "Taxes ($)": f"{item.total_taxes:,.2f}",
            "Net Pay ($)": f"{item.net_pay:,.2f}",
            "Annual Net ($)": f"{item.annual_net_base:,.2f}",
        }
        for item in st.session_state.payroll_history
    ]
    st.dataframe(ledger_rows, use_container_width=True, hide_index=True)

    b1, b2 = st.columns(2)
    with b1:
        csv_data = convert_history_to_csv(st.session_state.payroll_history)
        st.download_button(
            label="📥 Export Scenarios (CSV)",
            data=csv_data,
            file_name="personal_paycheck_scenarios_2026.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with b2:
        if st.button("🗑️ Clear History", use_container_width=True):
           st.session_state.payroll_history = []
           st.session_state.last_result = None
           st.rerun()


