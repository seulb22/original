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

# --- [3. 🤖 AI 초정밀 패턴 분석 엔진 7.0] ---
def generate_hyper_ai_insight(p_df, prog_name, full_df):
    # 우영우 제외 보정
    baseline_df = full_df[full_df['프로그램명'] != '이상한 변호사 우영우']
    
    # 💡 [핵심] 해당 연도의 평균과 비교 (시장 상황 반영)
    this_year = p_df['연도'].iloc[0]
    year_baseline = baseline_df[baseline_df['연도'] == this_year]
    if year_baseline.empty: year_baseline = baseline_df # 데이터 없으면 전체 기준
    
    year_avg_2049 = year_baseline['수도권 2049'].mean()
    year_avg_hh = year_baseline['수도권 가구'].mean()
    
    # 작품 지표
    my_avg_2049 = p_df['수도권 2049'].mean()
    my_avg_hh = p_df['수도권 가구'].mean()
    my_first_2049 = p_df.sort_values('회차').iloc[0]['수도권 2049']
    my_peak_2049 = p_df['수도권 2049'].max()
    my_last_2049 = p_df.sort_values('회차').iloc[-1]['수도권 2049']
    
    # 지수 산출
    growth_idx = (my_peak_2049 / my_first_2049) if my_first_2049 > 0 else 1
    target_power = (my_avg_2049 / year_avg_2049) if year_avg_2049 > 0 else 1
    hh_power = (my_avg_hh / year_avg_hh) if year_avg_hh > 0 else 1

    insight = f"### 🧐 [{prog_name}] AI 팩트 체크 리포트\n"
    st.caption(f"※ {this_year}년 방영 드라마 평균 대비 상대적 성과를 분석한 결과입니다.")

    # [1단계: 성격 규정]
    insight += "📊 **1. 작품 성격 분석**\n"
    if growth_idx >= 1.5 and target_power > 1.2:
        insight += "- **[개천에서 용 난 대박작]** 낮은 인지도로 시작했으나 입소문만으로 시장을 평정했습니다. 타겟 유입력과 확장성이 모두 최상급입니다.\n"
    elif growth_idx < 1.1 and target_power > 1.2:
        insight += "- **[충성 팬덤 기반의 니치작]** 신규 유입은 적으나 시작부터 끝까지 핵심 타겟을 꽉 잡았습니다. 바이럴보다는 기획 단계의 타겟팅 적중이 승인입니다.\n"
    elif hh_power > 1.2 and target_power < 0.8:
        insight += "- **[속 빈 강정형 대중작]** 가구 시청률은 높아 보이나 정작 돈 되는 2049는 다 빠져나갔습니다. 편성 시간대 덕을 봤을 뿐, 콘텐츠 경쟁력은 의문입니다.\n"
    elif growth_idx < 0.9:
        insight += "- **[전략적 실패/용두사미]** 첫방 이후 시청자가 계속 탈주하고 있습니다. 서사가 타겟의 기대치를 전혀 충족하지 못하고 있습니다.\n"
    else:
        insight += "- **[안정적 방어형]** 큰 위기 없이 채널의 기본 체력을 유지해준 작품입니다.\n"

    # [2단계: 타겟 경쟁력 직설]
    insight += "\n🎯 **2. 수도권 2049 타깃 경쟁력**\n"
    t_diff = (target_power - 1) * 100
    if t_diff > 20:
        insight += f"- **결과:** {this_year}년 평균 대비 **{t_diff:.1f}% 압도적 우위**. 광고주가 가장 좋아할 만한 'A급 인벤토리'입니다.\n"
    elif t_diff < -20:
        insight += f"- **결과:** {this_year}년 평균 대비 **{abs(t_diff):.1f}% 미달**. 2049 타겟에게 완전히 소외되었습니다. 마케팅 포인트 재설정이 시급합니다.\n"
    else:
        insight += f"- **결과:** 평균 수준 유지. 딱히 매력적이지도, 나쁘지도 않은 평범한 타겟 소구력입니다.\n"

    # [3단계: 뒷심 진단]
    insight += "\n📈 **3. 화제성 및 뒷심(Retention)**\n"
    if my_last_2049 >= my_peak_2049 * 0.95:
        insight += "- **진단:** 최고점의 시청률을 종영까지 지켜냈습니다. 팬덤의 충성도가 매우 견고합니다.\n"
    elif my_last_2049 < my_peak_2049 * 0.7:
        insight += f"- **진단:** 최고점 대비 **{int((1-my_last_2049/my_peak_2049)*100)}% 폭락**하며 종영했습니다. 후반부 전개 실패에 따른 시청자 이탈이 심각합니다.\n"
    else:
        insight += "- **진단:** 후반부 화제성이 다소 정체되었으나 무난하게 마무리되었습니다.\n"

    return insight

# --- [4. 메인 화면 구성] ---
if df_drama is not None and not df_drama.empty:
    st.sidebar.title("🎬 통합 분석 컨트롤러")
    if st.sidebar.button("🔄 데이터 강제 새로고침", type="primary"):
        load_drama_data.clear()
        load_minute_data.clear()
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**📅 분석 연도 (추세/랭킹 적용)**")
    years = sorted(df_drama['연도'].unique(), reverse=True)
    year_cols = st.sidebar.columns(3)
    selected_year = [y for i, y in enumerate(years) if year_cols[i % 3].checkbox(str(y), value=True, key=f"yr_{y}")]
    
    f_df = df_drama[df_drama['연도'].isin(selected_year)]
    progs = sorted(f_df['프로그램명'].unique())
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**🎥 비교 프로그램 선택**")
    col1, col2 = st.sidebar.columns(2)
    if col1.button("✅ 전체 선택"):
        for p in progs: st.session_state[f"prog_{p}"] = True
        st.rerun()
    if col2.button("❌ 전체 해제"):
        for p in progs: st.session_state[f"prog_{p}"] = False
        st.rerun()

    selected_progs = [p for p in progs if st.session_state.get(f"prog_{p}", False)]
    with st.sidebar.container(height=250):
        for p in progs:
            st.checkbox(p, key=f"prog_{p}")

    st.title("📊 ENA 드라마 전략 분석 리포트")
    tab1, tab2, tab3, tab4 = st.tabs(["📈 시청률 추세 대조", "🏆 편성 랭킹 보드", "🔍 프로그램 심층 분석", "⏱️ 분당 시청률 분석"])
    
    with tab1:
        if selected_progs:
            d_df = f_df[f_df['프로그램명'].isin(selected_progs)].sort_values(['프로그램명', '회차'])
            fig1 = px.line(d_df, x='회차', y='수도권 2049', color='프로그램명', markers=True)
            st.plotly_chart(fig1, width='stretch')
        else: st.warning("왼쪽 사이드바에서 드라마를 선택하세요.")

    with tab2:
        rank_metric = st.radio("📊 기준 지표", ["수도권 2049", "수도권 가구", "전국 가구"], horizontal=True, key="rank_radio")
        r1, r2 = st.columns(2)
        with r1:
            st.markdown("#### 🥇 전체 평균 순위")
            avg_df = f_df.groupby('프로그램명')[rank_metric].mean().round(3).reset_index().sort_values(rank_metric, ascending=False).reset_index(drop=True)
            avg_df.index += 1
            st.dataframe(avg_df.style.format({rank_metric: "{:.3f}%"}), width='stretch')
        with r2:
            st.markdown("#### 🎯 맞춤 회차 순위")
            all_eps = sorted([int(e) for e in f_df['회차'].unique() if e > 0])
            sel_eps = st.multiselect("분석할 회차 선택", all_eps, default=[1] if 1 in all_eps else [])
            if sel_eps:
                ep_avg_df = f_df[f_df['회차'].isin(sel_eps)].groupby('프로그램명')[rank_metric].mean().round(3).reset_index().sort_values(rank_metric, ascending=False).reset_index(drop=True)
                ep_avg_df.index += 1
                st.dataframe(ep_avg_df.style.format({rank_metric: "{:.3f}%"}), width='stretch')

    with tab3:
        st.subheader("🔍 프로그램별 전략 심층 진단")
        target_p = st.selectbox("🎯 분석 대상 선택", sorted(df_drama['프로그램명'].unique()))
        if target_p:
            p_df = df_drama[df_drama['프로그램명'] == target_p].sort_values('회차')
            
            # 💡 [핵심] 훨씬 더 날카롭고 구체적인 AI 진단 리포트 출력
            st.markdown(generate_hyper_ai_insight(p_df, target_p, df_drama))
            
            st.divider()
            m1, m2, m3 = st.columns(3)
            m1.metric("최고 수도권 2049", f"{p_df['수도권 2049'].max():.3f}%")
            m2.metric("최고 수도권 가구", f"{p_df['수도권 가구'].max():.3f}%")
            m3.metric("최고 전국 가구", f"{p_df['전국 가구'].max():.3f}%")
            fig3 = px.line(p_df, x='회차', y=['수도권 2049', '수도권 가구', '전국 가구'], markers=True, title=f"[{target_p}] 주요 지표 추이")
            st.plotly_chart(fig3, width='stretch')

    with tab4:
        st.subheader("⏱️ 분당 시청률 정밀 분석 (2025~)")
        if df_min is None or df_min.empty: st.warning("데이터 로드 실패")
        else:
            c1, c2 = st.columns(2)
            with c1: 
                latest_progs = sorted(df_drama[df_drama['연도'] >= 2025]['프로그램명'].unique())
                sel_min_ps = st.multiselect("🎯 프로그램 선택", latest_progs, key="min_ps")
            with c2:
                min_eps = sorted(df_drama[df_drama['프로그램명'].isin(sel_min_ps)]['회차'].unique()) if sel_min_ps else []
                sel_min_es = st.multiselect("🔢 회차 선택", min_eps, key="min_es")
            if sel_min_ps and sel_min_es:
                metric_map = {"수도권 2049": ("수도권", "개인2049"), "수도권 가구": ("수도권", "유료방송가구"), "전국 가구": ("National", "유료방송가구")}
                choice = st.radio("📊 지표 선택", list(metric_map.keys()), horizontal=True, key="min_met")
                reg, aud = metric_map[choice]
                def clean_d(d): return "".join(re.findall(r'\d+', str(d)))
                fig4 = go.Figure()
                for p in sel_min_ps:
                    for e in sel_min_es:
                        info = df_drama[(df_drama['프로그램명'] == p) & (df_drama['회차'] == e)]
                        if not info.empty:
                            target_d = clean_d(info.iloc[0]['일자'])
                            s_t, e_t = str(info.iloc[0]['시작시간']).strip(), str(info.iloc[0]['종료시간']).strip()
                            matching_col = [c for c in df_min.columns if target_d in clean_d(c) and reg in c and aud in c]
                            if matching_col:
                                col = matching_col[0]
                                df_min['time_key'] = df_min.iloc[:, 3].astype(str).str.split(' - ').str[0]
                                plot_df = df_min[(df_min['time_key'] >= s_t) & (df_min['time_key'] <= e_t)].copy()
                                plot_df[col] = pd.to_numeric(plot_df[col].astype(str).str.replace(',',''), errors='coerce').fillna(0)
                                if not plot_df.empty:
                                    fig4.add_trace(go.Scatter(x=plot_df['time_key'], y=plot_df[col], mode='lines', name=f"[{p}] {e}회"))
                                    pk_v, pk_t = plot_df[col].max(), plot_df.loc[plot_df[col].idxmax(), 'time_key']
                                    fig4.add_trace(go.Scatter(x=[pk_t], y=[pk_v], mode='markers+text', text=[f"{pk_v:.3f}%"], textposition="top center", marker=dict(color='red', size=12, symbol='triangle-up'), name=f"Peak ({p})"))
                fig4.update_layout(height=600, template="plotly_white", xaxis=dict(title="방송 시간", tickangle=45), hovermode="x unified")
                st.plotly_chart(fig4, width='stretch')
else:
    st.info("데이터 로딩 중...")