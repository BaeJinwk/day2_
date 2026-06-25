import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="금융 거래 대시보드", layout="wide")
st.title("금융 거래 통합 대시보드")

# ── 파일 업로드 ───────────────────────────────────────────────────
st.sidebar.header("데이터 업로드")
file_user = st.sidebar.file_uploader("user_account.xlsx", type=["xlsx", "xls"], key="user")
file_tx   = st.sidebar.file_uploader("transaction_history.xlsx", type=["xlsx", "xls"], key="tx")

if not file_user or not file_tx:
    st.info("사이드바에서 두 엑셀 파일을 업로드하면 대시보드가 표시됩니다.")
    st.sidebar.markdown("""
**필요한 파일**
- `user_account.xlsx` — 고객 정보 (user_id 포함)
- `transaction_history.xlsx` — 거래 내역 (user_id 포함)
""")
    st.stop()

# ── 데이터 로드 & 병합 ────────────────────────────────────────────
df_user = pd.read_excel(file_user)
df_tx   = pd.read_excel(file_tx)

if "user_id" not in df_user.columns or "user_id" not in df_tx.columns:
    st.error("두 파일 모두 'user_id' 컬럼이 있어야 합니다.")
    st.stop()

df = pd.merge(df_tx, df_user, on="user_id", how="left")

# 날짜 파싱
date_col = next((c for c in df.columns if "일시" in c or "날짜" in c or "date" in c.lower()), None)
if date_col:
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df["월"] = df[date_col].dt.to_period("M").astype(str)

amount_col = next((c for c in df.columns if "금액" in c and "수수료" not in c and "잔액" not in c and "월평균" not in c), None)

# ── 사이드바 필터 ─────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.header("필터")

if "VIP등급" in df.columns:
    vip_options = ["전체"] + sorted(df["VIP등급"].dropna().unique().tolist())
    vip_sel = st.sidebar.selectbox("VIP 등급", vip_options)
else:
    vip_sel = "전체"

if "거래유형" in df.columns:
    type_options = ["전체"] + sorted(df["거래유형"].dropna().unique().tolist())
    type_sel = st.sidebar.selectbox("거래 유형", type_options)
else:
    type_sel = "전체"

if "상태" in df.columns:
    status_options = ["전체"] + sorted(df["상태"].dropna().unique().tolist())
    status_sel = st.sidebar.selectbox("거래 상태", status_options)
else:
    status_sel = "전체"

# 필터 적용
filtered = df.copy()
if vip_sel != "전체" and "VIP등급" in df.columns:
    filtered = filtered[filtered["VIP등급"] == vip_sel]
if type_sel != "전체" and "거래유형" in df.columns:
    filtered = filtered[filtered["거래유형"] == type_sel]
if status_sel != "전체" and "상태" in df.columns:
    filtered = filtered[filtered["상태"] == status_sel]

# ── 요약 지표 ─────────────────────────────────────────────────────
st.subheader("요약 지표")
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("총 거래 건수", f"{len(filtered):,}건")
with c2:
    if amount_col:
        total_amt = filtered[amount_col].sum()
        st.metric("총 거래 금액", f"₩{total_amt:,.0f}")
with c3:
    if amount_col:
        avg_amt = filtered[amount_col].mean()
        st.metric("평균 거래 금액", f"₩{avg_amt:,.0f}")
with c4:
    unique_users = filtered["user_id"].nunique()
    st.metric("고객 수", f"{unique_users:,}명")

st.divider()

# ── 차트 행 1 ─────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    if "월" in filtered.columns and amount_col:
        st.subheader("월별 거래 금액 추이")
        monthly = (
            filtered.groupby("월")[amount_col]
            .sum()
            .reset_index()
            .sort_values("월")
            .set_index("월")
        )
        st.line_chart(monthly)

with col2:
    if "거래유형" in filtered.columns and amount_col:
        st.subheader("거래 유형별 금액")
        by_type = (
            filtered.groupby("거래유형")[amount_col]
            .sum()
            .reset_index()
            .set_index("거래유형")
        )
        st.bar_chart(by_type)

# ── 차트 행 2 ─────────────────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    if "카테고리" in filtered.columns and amount_col:
        st.subheader("카테고리별 거래 금액")
        by_cat = (
            filtered.groupby("카테고리")[amount_col]
            .sum()
            .reset_index()
            .sort_values(amount_col, ascending=False)
            .set_index("카테고리")
        )
        st.bar_chart(by_cat)

with col4:
    if "VIP등급" in filtered.columns and amount_col:
        st.subheader("VIP 등급별 거래 금액")
        by_vip = (
            filtered.groupby("VIP등급")[amount_col]
            .sum()
            .reset_index()
            .set_index("VIP등급")
        )
        st.bar_chart(by_vip)

# ── 차트 행 3 ─────────────────────────────────────────────────────
col5, col6 = st.columns(2)

with col5:
    if "채널" in filtered.columns:
        st.subheader("채널별 거래 건수")
        by_channel = (
            filtered["채널"].value_counts().reset_index()
        )
        by_channel.columns = ["채널", "건수"]
        st.bar_chart(by_channel.set_index("채널"))

with col6:
    if "상태" in filtered.columns:
        st.subheader("거래 상태 분포")
        by_status = filtered["상태"].value_counts().reset_index()
        by_status.columns = ["상태", "건수"]
        st.bar_chart(by_status.set_index("상태"))

# ── 성별 분석 ─────────────────────────────────────────────────────
if "성별" in filtered.columns and amount_col:
    st.divider()
    st.subheader("성별 거래 분석")
    col7, col8 = st.columns(2)

    with col7:
        by_gender_cnt = filtered.groupby("성별").size().reset_index(name="거래건수").set_index("성별")
        st.bar_chart(by_gender_cnt)

    with col8:
        by_gender_amt = (
            filtered.groupby("성별")[amount_col]
            .sum()
            .reset_index()
            .rename(columns={amount_col: "거래금액"})
            .set_index("성별")
        )
        st.bar_chart(by_gender_amt)

# ── 병합 데이터 테이블 ────────────────────────────────────────────
st.divider()
st.subheader("병합 데이터 상세")

display_cols = [c for c in [
    "거래ID", "user_id", "이름", "거래일시", "거래유형", "거래금액(원)",
    "카테고리", "상태", "채널", "VIP등급", "성별", "신용등급"
] if c in filtered.columns]

show_df = filtered[display_cols].copy() if display_cols else filtered.copy()

if amount_col and amount_col in show_df.columns:
    show_df[amount_col] = show_df[amount_col].apply(
        lambda x: f"₩{x:,.0f}" if pd.notna(x) else ""
    )

st.dataframe(show_df.reset_index(drop=True), use_container_width=True, hide_index=True)

# ── 원본 데이터 탭 ────────────────────────────────────────────────
st.divider()
with st.expander("원본 데이터 보기"):
    tab1, tab2 = st.tabs(["user_account", "transaction_history"])
    with tab1:
        st.dataframe(df_user, use_container_width=True, hide_index=True)
    with tab2:
        st.dataframe(df_tx, use_container_width=True, hide_index=True)
