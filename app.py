import streamlit as st
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
import calendar


# ============================================================
# CẤU HÌNH
# ============================================================

st.set_page_config(
    page_title="Tính lãi tiền gửi",
    page_icon="💰",
    layout="wide"
)


# ============================================================
# HÀM TIỆN ÍCH
# ============================================================

def money(value):
    """
    Định dạng tiền Việt Nam.
    """
    value = Decimal(str(value)).quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP
    )
    return f"{value:,.0f} ₫"


def days_between(start_date, end_date):
    """
    Tính số ngày được hưởng lãi:
    - Tính ngày gửi.
    - Không tính ngày rút.

    Ví dụ:
    Gửi 01/01, rút 02/01 -> 1 ngày.
    Gửi 01/01, rút 01/02 -> 31 ngày.
    """
    return (end_date - start_date).days


def add_months(original_date, months):
    """
    Cộng số tháng vào một ngày.
    Nếu ngày đích không tồn tại (ví dụ 31/01 + 1 tháng),
    lấy ngày cuối cùng của tháng đích.
    """
    month_index = original_date.month - 1 + months

    year = original_date.year + month_index // 12
    month = month_index % 12 + 1

    day = min(
        original_date.day,
        calendar.monthrange(year, month)[1]
    )

    return date(year, month, day)


def get_full_months_and_remaining_days(start_date, end_date):
    """
    Tách khoảng thời gian thành:
    - số tháng tròn
    - số ngày lẻ

    Ngày bắt đầu được tính, ngày kết thúc không tính.
    """
    if end_date <= start_date:
        return 0, 0

    months = (
        (end_date.year - start_date.year) * 12
        + (end_date.month - start_date.month)
    )

    candidate = add_months(start_date, months)

    if candidate > end_date:
        months -= 1
        candidate = add_months(start_date, months)

    remaining_days = (end_date - candidate).days

    return months, remaining_days


def calculate_simple_interest(
    principal,
    annual_rate,
    start_date,
    end_date
):
    """
    Lãi đơn:
        Lãi = Gốc × Lãi suất năm × Số ngày / 365
    """
    total_days = days_between(start_date, end_date)

    interest = (
        principal
        * annual_rate
        * Decimal(total_days)
        / Decimal("365")
    )

    return interest


def calculate_monthly_interest_simple(
    principal,
    annual_rate,
    start_date,
    end_date
):
    """
    Tính lãi theo từng tháng để hiển thị.

    Mỗi tháng được tính theo số ngày thực tế,
    mẫu số 365.
    """
    rows = []

    current = start_date
    month_number = 1

    while current < end_date:
        next_month = add_months(current, 1)

        period_end = min(next_month, end_date)

        number_of_days = (period_end - current).days

        interest = (
            principal
            * annual_rate
            * Decimal(number_of_days)
            / Decimal("365")
        )

        rows.append({
            "Tháng": month_number,
            "Từ ngày": current,
            "Đến trước ngày": period_end,
            "Số ngày": number_of_days,
            "Tiền lãi": interest
        })

        current = period_end
        month_number += 1

    return rows


def calculate_compound_interest(
    principal,
    annual_rate,
    start_date,
    end_date,
    term_months
):
    """
    Lãi kép.

    Lãi kép chỉ được dùng với hình thức nhận lãi cuối kỳ.

    Mỗi kỳ hạn đầy đủ:
        Gốc mới = Gốc cũ × (1 + lãi suất kỳ hạn)

    Trong đó lãi suất kỳ hạn được quy đổi từ lãi suất năm
    theo số ngày thực tế của kỳ / 365.

    Phần ngày lẻ cuối cùng:
        tính lãi đơn trên số dư hiện tại.
    """

    total_days = days_between(start_date, end_date)

    if total_days <= 0:
        return {
            "interest": Decimal("0"),
            "final_amount": principal,
            "rows": []
        }

    rows = []

    current_date = start_date
    current_principal = principal
    period_number = 1

    while True:
        next_period_date = add_months(
            start_date,
            period_number * term_months
        )

        # Nếu kỳ tiếp theo vượt quá ngày rút,
        # phần còn lại là kỳ chưa đủ.
        if next_period_date > end_date:
            break

        period_days = (
            next_period_date - current_date
        ).days

        if period_days <= 0:
            break

        period_interest = (
            current_principal
            * annual_rate
            * Decimal(period_days)
            / Decimal("365")
        )

        old_principal = current_principal

        current_principal += period_interest

        rows.append({
            "Kỳ": period_number,
            "Loại": "Kỳ hạn đầy đủ",
            "Từ ngày": current_date,
            "Đến trước ngày": next_period_date,
            "Số ngày": period_days,
            "Tiền đầu kỳ": old_principal,
            "Tiền lãi": period_interest,
            "Tiền cuối kỳ": current_principal
        })

        current_date = next_period_date
        period_number += 1

    # Phần ngày lẻ cuối cùng
    if current_date < end_date:
        remaining_days = (end_date - current_date).days

        remaining_interest = (
            current_principal
            * annual_rate
            * Decimal(remaining_days)
            / Decimal("365")
        )

        old_principal = current_principal
        current_principal += remaining_interest

        rows.append({
            "Kỳ": period_number,
            "Loại": "Ngày lẻ",
            "Từ ngày": current_date,
            "Đến trước ngày": end_date,
            "Số ngày": remaining_days,
            "Tiền đầu kỳ": old_principal,
            "Tiền lãi": remaining_interest,
            "Tiền cuối kỳ": current_principal
        })

    total_interest = current_principal - principal

    return {
        "interest": total_interest,
        "final_amount": current_principal,
        "rows": rows
    }


def calculate_monthly_schedule(
    principal,
    annual_rate,
    start_date,
    end_date,
    compound=False,
    term_months=1
):
    """
    Tạo bảng lãi theo tháng.

    Với lãi đơn:
        tiền lãi mỗi tháng tính trên số tiền gốc ban đầu.

    Với lãi kép:
        phần lãi được cộng vào gốc theo từng kỳ hạn.
    """

    if not compound:
        return calculate_monthly_interest_simple(
            principal,
            annual_rate,
            start_date,
            end_date
        )

    result = calculate_compound_interest(
        principal,
        annual_rate,
        start_date,
        end_date,
        term_months
    )

    rows = result["rows"]

    monthly_rows = []

    for index, row in enumerate(rows, start=1):
        monthly_rows.append({
            "Tháng/Kỳ": index,
            "Loại": row["Loại"],
            "Từ ngày": row["Từ ngày"],
            "Đến trước ngày": row["Đến trước ngày"],
            "Số ngày": row["Số ngày"],
            "Tiền đầu kỳ": row["Tiền đầu kỳ"],
            "Tiền lãi": row["Tiền lãi"],
            "Tiền cuối kỳ": row["Tiền cuối kỳ"]
        })

    return monthly_rows


# ============================================================
# GIAO DIỆN
# ============================================================

st.title("💰 TÍNH LÃI TIỀN GỬI")

st.caption(
    "Quy ước: 1 năm = 365 ngày | Ngày gửi được tính lãi | "
    "Ngày rút không tính lãi"
)

st.divider()


# ============================================================
# NHẬP THÔNG TIN
# ============================================================

col1, col2 = st.columns(2)

with col1:
    st.subheader("Thông tin tiền gửi")

    principal_input = st.number_input(
        "Số tiền gửi",
        min_value=0,
        value=100_000_000,
        step=1_000_000,
        format="%.0f",
        help="Số tiền gốc khách hàng gửi."
    )

    annual_rate_input = st.number_input(
        "Lãi suất theo năm (%)",
        min_value=0.0,
        value=6.0,
        step=0.1,
        format="%.2f",
        help="Ví dụ: 6%/năm nhập 6."
    )

    term_months = st.selectbox(
        "Kỳ hạn",
        options=[1, 2, 3, 6, 9, 12, 18, 24, 36],
        index=5,
        format_func=lambda x: f"{x} tháng"
    )

with col2:
    st.subheader("Hình thức tính lãi")

    interest_payment = st.radio(
        "Hình thức nhận lãi",
        options=[
            "Cuối kỳ",
            "Hàng tháng",
            "Đầu kỳ"
        ],
        horizontal=True
    )

    interest_type = st.radio(
        "Loại lãi",
        options=[
            "Lãi đơn",
            "Lãi kép"
        ],
        horizontal=True
    )

    if interest_type == "Lãi kép" and interest_payment != "Cuối kỳ":
        st.warning(
            "Lãi kép chỉ áp dụng cho hình thức nhận lãi cuối kỳ. "
            "Hệ thống sẽ tự động chuyển sang lãi đơn."
        )

        effective_interest_type = "Lãi đơn"
    else:
        effective_interest_type = interest_type


# ============================================================
# NGÀY GỬI / NGÀY RÚT
# ============================================================

st.subheader("Thời gian gửi tiền")

date_col1, date_col2 = st.columns(2)

with date_col1:
    start_date = st.date_input(
        "Ngày khách hàng gửi tiền",
        value=date.today()
    )

with date_col2:
    default_end_date = add_months(start_date, term_months)

    end_date = st.date_input(
        "Ngày khách hàng rút tiền",
        value=default_end_date
    )


# ============================================================
# KIỂM TRA DỮ LIỆU
# ============================================================

if principal_input <= 0:
    st.error("Số tiền gửi phải lớn hơn 0.")
    st.stop()

if annual_rate_input < 0:
    st.error("Lãi suất không được âm.")
    st.stop()

if end_date <= start_date:
    st.error(
        "Ngày rút tiền phải lớn hơn ngày gửi tiền."
    )
    st.stop()


# ============================================================
# CHUYỂN KIỂU DỮ LIỆU
# ============================================================

principal = Decimal(str(principal_input))
annual_rate = Decimal(str(annual_rate_input)) / Decimal("100")

total_days = days_between(
    start_date,
    end_date
)


# ============================================================
# THÔNG TIN TỔNG QUAN
# ============================================================

st.divider()

st.subheader("📌 Thông tin kỳ gửi")

info1, info2, info3, info4 = st.columns(4)

with info1:
    st.metric(
        "Số tiền gửi",
        money(principal)
    )

with info2:
    st.metric(
        "Lãi suất",
        f"{annual_rate_input:.2f}%/năm"
    )

with info3:
    st.metric(
        "Số ngày tính lãi",
        f"{total_days} ngày"
    )

with info4:
    st.metric(
        "Kỳ hạn",
        f"{term_months} tháng"
    )


st.info(
    f"Thời gian tính lãi: từ **{start_date.strftime('%d/%m/%Y')}** "
    f"đến trước ngày **{end_date.strftime('%d/%m/%Y')}** "
    f"→ **{total_days} ngày**."
)


# ============================================================
# TÍNH TOÁN
# ============================================================

is_compound = (
    effective_interest_type == "Lãi kép"
    and interest_payment == "Cuối kỳ"
)


# ------------------------------------------------------------
# LÃI ĐƠN
# ------------------------------------------------------------

if not is_compound:

    total_interest = calculate_simple_interest(
        principal,
        annual_rate,
        start_date,
        end_date
    )

    final_amount = principal + total_interest

    monthly_rows = calculate_monthly_schedule(
        principal=principal,
        annual_rate=annual_rate,
        start_date=start_date,
        end_date=end_date,
        compound=False,
        term_months=term_months
    )

    # Xử lý hình thức nhận lãi
    if interest_payment == "Hàng tháng":
        received_interest = total_interest
        received_principal = principal
        amount_at_withdrawal = principal
    elif interest_payment == "Đầu kỳ":
        received_interest = total_interest
        received_principal = principal
        amount_at_withdrawal = principal
    else:
        received_interest = total_interest
        received_principal = principal
        amount_at_withdrawal = final_amount


# ------------------------------------------------------------
# LÃI KÉP
# ------------------------------------------------------------

else:

    compound_result = calculate_compound_interest(
        principal=principal,
        annual_rate=annual_rate,
        start_date=start_date,
        end_date=end_date,
        term_months=term_months
    )

    total_interest = compound_result["interest"]
    final_amount = compound_result["final_amount"]

    monthly_rows = calculate_monthly_schedule(
        principal=principal,
        annual_rate=annual_rate,
        start_date=start_date,
        end_date=end_date,
        compound=True,
        term_months=term_months
    )

    received_interest = total_interest
    received_principal = principal
    amount_at_withdrawal = final_amount


# ============================================================
# KẾT QUẢ TỔNG
# ============================================================

st.divider()

st.subheader("💵 Kết quả tính lãi")

result1, result2, result3 = st.columns(3)

with result1:
    st.metric(
        "Tổng tiền lãi",
        money(total_interest)
    )

with result2:
    st.metric(
        "Tiền gốc",
        money(principal)
    )

with result3:
    st.metric(
        "Tổng tiền nhận khi rút",
        money(amount_at_withdrawal)
    )


# ============================================================
# THÔNG TIN HÌNH THỨC NHẬN LÃI
# ============================================================

st.subheader("📋 Chi tiết hình thức nhận lãi")

if interest_payment == "Cuối kỳ":
    st.success(
        f"Khách hàng nhận **gốc + lãi** vào ngày "
        f"{end_date.strftime('%d/%m/%Y')}: "
        f"**{money(amount_at_withdrawal)}**."
    )

elif interest_payment == "Hàng tháng":
    st.info(
        "Tiền lãi được chi trả theo từng tháng. "
        "Tiền gốc được giữ nguyên và nhận lại vào ngày rút tiền."
    )

elif interest_payment == "Đầu kỳ":
    st.info(
        "Tiền lãi được xác định theo toàn bộ thời gian gửi "
        "và trả vào đầu kỳ. Tiền gốc được nhận vào ngày rút tiền."
    )


# ============================================================
# BẢNG LÃI HÀNG THÁNG / TỪNG KỲ
# ============================================================

st.subheader("📊 Tiền lãi hàng tháng / từng kỳ")

if monthly_rows:

    if not is_compound:

        # ----------------------------------------------------
        # LÃI ĐƠN
        # ----------------------------------------------------

        display_rows = []

        for row in monthly_rows:
            display_rows.append({
                "Tháng": row["Tháng"],
                "Từ ngày": row["Từ ngày"].strftime("%d/%m/%Y"),
                "Đến trước ngày": row["Đến trước ngày"].strftime("%d/%m/%Y"),
                "Số ngày": row["Số ngày"],
                "Tiền lãi": money(row["Tiền lãi"])
            })

        st.dataframe(
            display_rows,
            use_container_width=True,
            hide_index=True
        )

    else:

        # ----------------------------------------------------
        # LÃI KÉP
        # ----------------------------------------------------

        display_rows = []

        for row in monthly_rows:
            display_rows.append({
                "Kỳ": row["Tháng/Kỳ"],
                "Loại": row["Loại"],
                "Từ ngày": row["Từ ngày"].strftime("%d/%m/%Y"),
                "Đến trước ngày": row["Đến trước ngày"].strftime("%d/%m/%Y"),
                "Số ngày": row["Số ngày"],
                "Tiền đầu kỳ": money(row["Tiền đầu kỳ"]),
                "Tiền lãi": money(row["Tiền lãi"]),
                "Tiền cuối kỳ": money(row["Tiền cuối kỳ"])
            })

        st.dataframe(
            display_rows,
            use_container_width=True,
            hide_index=True
        )

else:
    st.info("Không có dữ liệu để hiển thị.")


# ============================================================
# TỔNG KẾT
# ============================================================

st.divider()

st.subheader("🧾 Tổng kết")

summary_col1, summary_col2 = st.columns(2)

with summary_col1:

    st.write(
        f"**Ngày gửi:** "
        f"{start_date.strftime('%d/%m/%Y')}"
    )

    st.write(
        f"**Ngày rút:** "
        f"{end_date.strftime('%d/%m/%Y')}"
    )

    st.write(
        f"**Số ngày tính lãi:** "
        f"{total_days} ngày"
    )

    st.write(
        f"**Kỳ hạn:** "
        f"{term_months} tháng"
    )

    st.write(
        f"**Lãi suất:** "
        f"{annual_rate_input:.2f}%/năm"
    )

    st.write(
        f"**Hình thức nhận lãi:** "
        f"{interest_payment}"
    )

    st.write(
        f"**Phương pháp tính:** "
        f"{effective_interest_type}"
    )

with summary_col2:

    st.write(
        f"**Tiền gốc:** "
        f"{money(principal)}"
    )

    st.write(
        f"**Tổng tiền lãi:** "
        f"{money(total_interest)}"
    )

    st.write(
        f"**Tổng tiền gốc + lãi:** "
        f"{money(final_amount)}"
    )

    if interest_payment == "Cuối kỳ":
        st.success(
            f"**Khách hàng nhận ngày {end_date.strftime('%d/%m/%Y')}: "
            f"{money(amount_at_withdrawal)}**"
        )

    elif interest_payment == "Hàng tháng":
        st.success(
            f"**Gốc nhận ngày {end_date.strftime('%d/%m/%Y')}: "
            f"{money(principal)}**"
        )

        st.write(
            f"Tổng lãi đã/được nhận theo tháng: "
            f"**{money(total_interest)}**"
        )

    elif interest_payment == "Đầu kỳ":
        st.success(
            f"**Gốc nhận ngày {end_date.strftime('%d/%m/%Y')}: "
            f"{money(principal)}**"
        )

        st.write(
            f"Tổng lãi trả đầu kỳ: "
            f"**{money(total_interest)}**"
        )


# ============================================================
# GHI CHÚ NGHIỆP VỤ
# ============================================================

with st.expander("ℹ️ Quy tắc tính lãi đang áp dụng"):

    st.markdown(
        """
### Quy tắc ngày

- Ngày gửi **được tính lãi**.
- Ngày rút **không tính lãi**.
- Ví dụ gửi ngày 01/01 và rút ngày 02/01 thì được tính **1 ngày lãi**.
- Ví dụ gửi ngày 01/01 và rút ngày 01/02 thì được tính **31 ngày lãi**.

### Lãi đơn

Công thức:

`Tiền lãi = Tiền gốc × Lãi suất năm × Số ngày / 365`

Tiền lãi không được nhập vào tiền gốc để tính lãi tiếp.

### Lãi kép

Lãi kép chỉ áp dụng khi chọn **nhận lãi cuối kỳ**.

Sau mỗi kỳ hạn đầy đủ, tiền lãi được cộng vào tiền gốc để tiếp tục tính lãi cho kỳ tiếp theo.

Phần thời gian chưa đủ một kỳ hạn cuối cùng được tính theo lãi đơn trên số dư tại thời điểm bắt đầu phần ngày lẻ.

### Quy ước năm

Hệ thống sử dụng cố định:

`1 năm = 365 ngày`
"""
    )
