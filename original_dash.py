import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import re
import urllib.parse

# --- [1. 보안 시스템] ---
def check_password():
    def password_entered():
        if st.session_state.get("password", "") == "ena1234":
            st.session_state["password_correct"] = True
            if "password" in st.session_state:
                del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if not st.session_state.get("password_correct", False):
        st.text_input("🔒 ENA 드라마 전략 리포트 비밀번호", type="password", on_change=password_entered, key="password")
        return False
    return True

st.set_page_config(page_title="ENA 오리지널 드라마 전략 센터", layout="wide")
if not check_password():
    st.stop()

# --- [2. 데이터 로드 설정] ---
SHEET_ID = "1HQ7s7lgj49q9TJTxB8rNHrey-zczdJjkPvRb8RVZrLg"
GID_MINUTE = "981672100" 

@st.cache_data(ttl=60)
def load_drama_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
    try:
        df = pd.read_csv(url, skiprows=4)
        new_cols = list(df.columns)
        if len(new_cols) >= 13: 
            new_cols[2], new_cols[3], new_cols[4] = '연도', '프로그램명', '회차'
            new_cols[5], new_cols[6], new_cols[7], new_cols[8] = '요일', '일자', '시작시간', '종료시간'
            new_cols[9], new_cols[10], new_cols[12] = '수도권 2049', '수도권 가구', '전국 가구'
            df.columns = new_cols
        df = df.dropna(subset=['프로그램명']).copy()
        def clean_val(x):
            if pd.isna(x): return 0
            res = re.findall(r"[-+]?\d*\.\d+|\d+", str(x).replace(',', ''))
            return float(res[0]) if res else 0
        for col in ['연도', '회차', '수도권 2049', '수도권 가구', '전국 가구']:
            if col in df.columns: df[col] = df[col].apply(clean_val)
        df['연도'] = df['연도'].astype(int)
        df['회차'] = df['회차'].astype(int)
        return df[df['연도'] > 2000]
    except Exception as e:
        st.error(f"드라마 데이터 로드 실패: {e}")
        return None

@st.cache_data(ttl=60)
def load_minute_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_MINUTE}"
    try:
        raw_df = pd.read_csv(url, header=None, low_memory=False)
        dates = raw_df.iloc[3].ffill().fillna("")
        regions = raw_df.iloc[4].fillna("")
        targets = raw_df.iloc[5].fillna("")
        combined_cols = [f"{d}_{r}_{t}".strip("_") for d, r, t in zip(dates, regions, targets)]
        data_df = raw_df.iloc[7:].copy()
        data_df.columns = combined_cols
        return data_df
    except Exception as e:
        st.error(f"분당 데이터 로드 실패: {e}")
        return None

df_drama = load_drama_data()
df_min = load_minute_data()

# --- [3. 🤖 AI 초정밀 팩트 체크 엔진 7.0 (보정 및 복구 완료)] ---
def generate_hyper_ai_insight(p_df, prog_name, full_df):
    # 💡 [보정] 우영우 제외 베이스라인
    baseline_df = full_df[full_df['프로그램명'] != '이상한 변호사 우영우']
    this_year = p_df['연도'].iloc[0]
    year_baseline = baseline_df[baseline_df['연도'] == this_year]
    if year_baseline.empty: year_baseline = baseline_df
    
    year_avg_2049 = year_baseline['수도권 2049'].mean()
    year_avg_hh = year_baseline['수도권 가구'].mean()
    
    my_avg_2049 = p_df['수도권 2049'].mean()
    my_avg_hh = p_df['수도권 가구'].mean()
    my_first_2049 = p_df.sort_values('회차').iloc[0]['수도권 2049']
    my_peak_2049 = p_df['수도권 2049'].max()
    my_last_2049 = p_df.sort_values('회차').iloc[-1]['수도권 2049']
    
    growth_idx = (my_peak_2049 / my_first_2049) if my_first_2049 > 0 else 1
    target_power = (my_avg_2049 / year_avg_2049) if year_avg_2049 > 0 else 1
    hh_power = (my_avg_hh / year_avg_hh) if year_avg_hh > 0 else 1

    insight = f"### 🧐 [{prog_name}] AI 팩트 체크 리포트\n"
    st.caption(f"※ '우영우' 제외 {this_year}년 드라마 평균 대비 분석 결과입니다.")

    # [1단계: 성격 규정]
    insight += "📊 **1. 작품 성격 분석**\n"
    if growth_idx >= 1.5 and target_power > 1.2:
        insight += "- **[개천에서 용 난 대박작]** 입소문만으로 시장을 장악했습니다. 확장성이 최상급입니다.\n"
    elif growth_idx < 1.1 and target_power > 1.2:
        insight += "- **[충성 팬덤 기반의 니치작]** 신규 유입은 적으나 핵심 타겟을 끝까지 사수했습니다.\n"
    elif hh_power > 1.2 and target_power < 0.8:
        insight += "- **[속 빈 강정형 대중작]** 가구는 높으나 핵심 타겟(2049)은 경쟁사에 뺏긴 실속 없는 성적입니다.\n"
    elif growth_idx < 0.9:
        insight += "- **[전략적 실패/용두사미]** 첫방 이후 시청자가 계속 이탈하고 있습니다. 서사 동력 상실이 우려됩니다.\n"
    else:
        insight += "- **[안정적 방어형]** 채널의 기본 체력을 안정적으로 유지해준 자산입니다.\n"

    # [2단계: 시청층 구조 진단]
    insight += "\n🏢 **2. 시청층 구조 진단 (입체 비교)**\n"
    if (my_avg_2049 > year_avg_2049) and (my_avg_hh > year_avg_hh):
        insight += f"- **구조: [채널 필승작]** 가구와 타겟 모두 역대 평균 상회. **최고의 효자 작품**입니다.\n"
    elif (my_avg_2049 > year_avg_2049) and (my_avg_hh <= year_avg_hh):
        insight += f"- **구조: [2049 특화작]** 가구는 낮으나 젊은 타겟 응집력이 압도적인 **고효율 광고 상품**입니다.\n"
    elif (my_avg_2049 <= year_avg_2049) and (my_avg_hh > year_avg_hh):
        insight += f"- **구조: [매스/노후화 경보]** 가구 유입은 성공적이나 2049 유인책이 부족한 **고연령 편중** 상태입니다.\n"
    else:
        insight += f"- **구조: [전략적 고립]** 가구와 타겟 모두 채널 베이스라인 미달. 장르적 재검토가 필수적입니다.\n"

    # [3단계: 뒷심 진단]
    insight += "\n📈 **3. 화제성 및 뒷심**\n"
    if my_last_2049 >= my_peak_2049 * 0.95: insight += "- **진단:** 최고점 시청률을 종영까지 지켜낸 강력한 팬덤을 확인했습니다.\n"
    elif my_last_2049 < my_peak_2049 * 0.7: insight += f"- **진단:** 최고점 대비 **{int((1-my_last_2049/my_peak_2049)*100)}% 폭락**. 후반부 경쟁력 상실이 뼈아픕니다.\n"
    else: insight += "- **진단:** 화제성이 다소 정체되었으나 무난한 마무리입니다.\n"

    return insight

# --- [4. 메인 대시보드 구성] ---
if df_drama is not None and not df_drama.empty:
    st.sidebar.title("🎬 통합 분석 컨트롤러")
    if st.sidebar.button("🔄 데이터 새로고침", type="primary"):
        load_drama_data.clear()
        load_minute_data.clear()
        st.rerun()
    
    st.sidebar.markdown("---")
    years = sorted(df_drama['연도'].unique(), reverse=True)
    year_cols = st.sidebar.columns(3)
    selected_year = [y for i, y in enumerate(years) if year_cols[i % 3].checkbox(str(y), value=True, key=f"yr_{y}")]
    
    f_df = df_drama[df_drama['연도'].isin(selected_year)]
    progs = sorted(f_df['프로그램명'].unique())
    
    # 처음 접속 시 전체 선택
    if "first_load_done" not in st.session_state:
        for p in progs: st.session_state[f"prog_{p}"] = True
        st.session_state["first_load_done"] = True

    st.sidebar.markdown("---")
    st.sidebar.markdown("**🎥 비교 프로그램 선택**")
    c1, c2 = st.sidebar.columns(2)
    if c1.button("✅ 전체 선택"):
        for p in progs: st.session_state[f"prog_{p}"] = True
        st.rerun()
    if c2.button("❌ 전체 해제"):
        for p in progs: st.session_state[f"prog_{p}"] = False
        st.rerun()

    selected_progs = [p for p in progs if st.session_state.get(f"prog_{p}", False)]
    with st.sidebar.container(height=250):
        for p in progs: st.checkbox(p, key=f"prog_{p}")

    st.title("📊 ENA 드라마 전략 분석 리포트")
    tab1, tab2, tab3, tab4 = st.tabs(["📈 시청률 추세 대조", "🏆 편성 랭킹 보드", "🔍 프로그램 심층 분석", "⏱️ 분당 시청률 분석"])
    
    with tab1:
        if selected_progs:
            d_df = f_df[f_df['프로그램명'].isin(selected_progs)].sort_values(['프로그램명', '회차'])
            fig1 = px.line(d_df, x='회차', y='수도권 2049', color='프로그램명', markers=True)
            st.plotly_chart(fig1, width='stretch')

    with tab2:
        rank_metric = st.radio("📊 기준 지표", ["수도권 2049", "수도권 가구", "전국 가구"], horizontal=True)
        r1, r2 = st.columns(2)
        with r1:
            avg_df = f_df.groupby('프로그램명')[rank_metric].mean().round(3).reset_index().sort_values(rank_metric, ascending=False).reset_index(drop=True)
            avg_df.index += 1
            st.dataframe(avg_df.style.format({rank_metric: "{:.3f}%"}), width='stretch')
        with r2:
            all_eps = sorted([int(e) for e in f_df['회차'].unique() if e > 0])
            sel_eps = st.multiselect("회차 선택", all_eps, default=[1] if 1 in all_eps else [])
            if sel_eps:
                ep_avg_df = f_df[f_df['회차'].isin(sel_eps)].groupby('프로그램명')[rank_metric].mean().round(3).reset_index().sort_values(rank_metric, ascending=False).reset_index(drop=True)
                ep_avg_df.index += 1
                st.dataframe(ep_avg_df.style.format({rank_metric: "{:.3f}%"}), width='stretch')

    with tab3:
        st.subheader("🔍 프로그램별 전략 심층 진단")
        target_p = st.selectbox("🎯 분석 대상", sorted(df_drama['프로그램명'].unique()))
        if target_p:
            p_df = df_drama[df_drama['프로그램명'] == target_p].sort_values('회차')
            # 💡 [복구 완료] AI 인사이트 엔진 7.0 출력
            st.markdown(generate_hyper_ai_insight(p_df, target_p, df_drama))
            st.divider()
            m1_v, m1_e = p_df['수도권 2049'].max(), p_df.loc[p_df['수도권 2049'].idxmax(), '회차']
            m2_v, m2_e = p_df['수도권 가구'].max(), p_df.loc[p_df['수도권 가구'].idxmax(), '회차']
            m3_v, m3_e = p_df['전국 가구'].max(), p_df.loc[p_df['전국 가구'].idxmax(), '회차']
            m1, m2, m3 = st.columns(3)
            m1.metric("최고 수도권 2049", f"{m1_v:.3f}%", f"{m1_e}회")
            m2.metric("최고 수도권 가구", f"{m2_v:.3f}%", f"{m2_e}회")
            m3.metric("최고 전국 가구", f"{m3_v:.3f}%", f"{m3_e}회")
            fig3 = px.line(p_df, x='회차', y=['수도권 2049', '수도권 가구', '전국 가구'], markers=True, title=f"[{target_p}] 주요 지표 추이")
            st.plotly_chart(fig3, width='stretch')

    with tab4:
        st.subheader("⏱️ 분당 시청률 정밀 분석 (2025~)")
        if df_min is None or df_min.empty: st.warning("데이터 로드 실패")
        else:
            c1, c2 = st.columns(2)
            with c1: latest_progs = sorted(df_drama[df_drama['연도'] >= 2025]['프로그램명'].unique()); sel_min_ps = st.multiselect("🎯 프로그램 선택", latest_progs, key="min_ps")
            with c2: min_eps = sorted(df_drama[df_drama['프로그램명'].isin(sel_min_ps)]['회차'].unique()) if sel_min_ps else []; sel_min_es = st.multiselect("🔢 회차 선택", min_eps, key="min_es")
            
            if sel_min_ps and sel_min_es:
                st.markdown("**📊 분석 지표 선택 (복수 선택 가능)**")
                met_c1, met_c2, met_c3 = st.columns(3)
                sel_metrics = []
                if met_c1.checkbox("수도권 2049", value=True, key="m_2049"): sel_metrics.append("수도권 2049")
                if met_c2.checkbox("수도권 가구", value=False, key="m_su_hh"): sel_metrics.append("수도권 가구")
                if met_c3.checkbox("전국 가구", value=False, key="m_nat_hh"): sel_metrics.append("전국 가구")
                
                metric_map = {"수도권 2049": ("수도권", "개인2049"), "수도권 가구": ("수도권", "유료방송가구"), "전국 가구": ("National", "유료방송가구")}
                peak_cards = []
                fig4 = go.Figure()
                
                for p in sel_min_ps:
                    for e in sel_min_es:
                        info = df_drama[(df_drama['프로그램명'] == p) & (df_drama['회차'] == e)]
                        if not info.empty:
                            target_d = "".join(re.findall(r'\d+', str(info.iloc[0]['일자'])))
                            s_t, e_t = str(info.iloc[0]['시작시간']).strip(), str(info.iloc[0]['종료시간']).strip()
                            for m_name in sel_metrics:
                                reg, aud = metric_map[m_name]
                                matching_col = [c for c in df_min.columns if target_d in "".join(re.findall(r'\d+', str(c))) and reg in c and aud in c]
                                if matching_col:
                                    col = matching_col[0]
                                    df_min['time_key'] = df_min.iloc[:, 3].astype(str).str.split(' - ').str[0]
                                    plot_df = df_min[(df_min['time_key'] >= s_t) & (df_min['time_key'] <= e_t)].copy()
                                    plot_df[col] = pd.to_numeric(plot_df[col].astype(str).str.replace(',',''), errors='coerce').fillna(0)
                                    if not plot_df.empty:
                                        fig4.add_trace(go.Scatter(x=plot_df['time_key'], y=plot_df[col], mode='lines', name=f"{p} {e}회_{m_name}"))
                                        pk_v, pk_t = plot_df[col].max(), plot_df.loc[plot_df[col].idxmax(), 'time_key']
                                        bt_v, bt_t = plot_df[col].min(), plot_df.loc[plot_df[col].idxmin(), 'time_key']
                                        peak_cards.append({"label": f"{p} {e}회 {m_name}", "val": pk_v, "time": pk_t})
                                        fig4.add_trace(go.Scatter(x=[pk_t], y=[pk_v], mode='markers', marker=dict(color='red', size=10, symbol='triangle-up'), showlegend=False))
                                        fig4.add_trace(go.Scatter(x=[bt_t], y=[bt_v], mode='markers', marker=dict(color='blue', size=10, symbol='triangle-down'), showlegend=False))

                if peak_cards:
                    st.divider(); cols = st.columns(min(len(peak_cards), 4))
                    for i, c in enumerate(peak_cards):
                        with cols[i % 4]: st.metric(f"🏆 {c['label']} 최고", f"{c['val']:.3f}%", f"⏰ {c['time']}")
                    st.divider()

                fig4.update_layout(height=500, template="plotly_white", xaxis=dict(title="방송 시간", tickangle=45), hovermode="x unified",
                                   legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02))
                st.plotly_chart(fig4, width='stretch')
else:
    st.info("데이터 로딩 중...")