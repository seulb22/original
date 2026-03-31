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
        
        # 💡 PD님 원본 구조 매칭 (G열: 일자, H열: 시작, I열: 종료)
        if len(new_cols) >= 13: 
            new_cols[2], new_cols[3], new_cols[4] = '연도', '프로그램명', '회차'
            new_cols[5], new_cols[6], new_cols[7], new_cols[8] = '요일', '일자', '시작시간', '종료시간'
            new_cols[9], new_cols[10], new_cols[12] = '수도권 2049', '수도권 가구', '전국 가구'
            df.columns = new_cols

        df = df.dropna(subset=['프로그램명'])
        df = df[df['프로그램명'].str.strip() != '']
        
        def clean_val(x):
            if pd.isna(x): return 0
            res = re.findall(r"[-+]?\d*\.\d+|\d+", str(x).replace(',', ''))
            return float(res[0]) if res else 0

        for col in ['연도', '회차', '수도권 2049', '수도권 가구', '전국 가구']:
            if col in df.columns:
                df[col] = df[col].apply(clean_val)
        
        df['연도'] = df['연도'].astype(int)
        if '회차' in df.columns:
            df['회차'] = df['회차'].astype(int)
        
        df = df[df['연도'] > 2000]

        # 편성 블록 카테고리화
        def categorize_slot(day, program):
            day, prog = str(day).strip(), str(program).strip()
            if prog == '악인전기' or (day in ['일요일', '일']):
                if prog == '악인전기': return '🔄 일월 드라마'
                if day in ['월요일', '화요일', '월', '화']: return '🌙 월화 드라마'
                if day in ['일요일', '일']: return '🔄 일월 드라마'
            if day in ['월요일', '화요일', '월', '화']: return '🌙 월화 드라마'
            if day in ['수요일', '목요일', '수', '목']: return '☀️ 수목 드라마'
            if day in ['금요일', '토요일', '금', '토']: return '🔥 금토 드라마'
            if day in ['토요일', '일요일', '토', '일']: return '🏢 토일 드라마'
            return '기타 편성'
        df['편성요일블록'] = df.apply(lambda x: categorize_slot(x.get('요일', ''), x.get('프로그램명', '')), axis=1)

        def categorize_timeslot(time_val):
            try:
                t_str = str(time_val).strip()
                parts = re.findall(r'\d+', t_str)
                if len(parts) >= 2:
                    h, m = int(parts[0]), int(parts[1])
                    if h == 21 and m <= 10: return "🕙 21:00 블록"
                    elif h == 22: return "🕙 22:00 블록"
                    else: return f"🕙 {h:02d}:00 블록"
                return "기타 시간대"
            except: return "기타 시간대"
        df['편성시간대'] = df['시작시간'].apply(categorize_timeslot)
        return df
    except Exception as e:
        st.error(f"드라마 데이터 로드 실패: {e}")
        return None

@st.cache_data(ttl=60)
def load_minute_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_MINUTE}"
    try:
        raw_df = pd.read_csv(url, header=None, low_memory=False)
        # PD님 가이드: 4행(Date), 5행(Region), 6행(Target) 매칭
        dates = raw_df.iloc[3].ffill().fillna("")
        regions = raw_df.iloc[4].fillna("")
        targets = raw_df.iloc[5].fillna("")
        combined_cols = []
        for d, r, t in zip(dates, regions, targets):
            combined_cols.append(f"{d}_{r}_{t}".strip("_"))
        data_df = raw_df.iloc[7:].copy()
        data_df.columns = combined_cols
        return data_df
    except Exception as e:
        st.error(f"분당 데이터 로드 실패: {e}")
        return None

df_drama = load_drama_data()
df_min = load_minute_data()

# --- [3. 분석 리포트 함수] ---
def generate_advanced_ai_report(p_df, prog_name, full_df):
    p_df = p_df.sort_values('회차').reset_index(drop=True)
    if len(p_df) < 2: return f"**[{prog_name}]** 데이터가 부족하여 분석이 어렵습니다."
    avg_all = full_df.groupby('프로그램명')[['수도권 2049', '수도권 가구', '전국 가구']].mean()
    rank_2049 = avg_all['수도권 2049'].rank(ascending=False, method='min')
    my_rank = int(rank_2049.loc[prog_name])
    avg_2049 = p_df['수도권 2049'].mean()
    avg_hh = p_df['수도권 가구'].mean()
    target_ratio = (avg_2049 / avg_hh * 100) if avg_hh > 0 else 0
    report = f"### 💡 [{prog_name}] 핵심 성과 심층 분석\n"
    report += f"- **채널 내 포지션:** 역대 드라마 중 수도권 2049 기준 **전체 {my_rank}위** (평균 {avg_2049:.3f}%)\n"
    report += f"- **타겟 집중도:** 가구 대비 2049 비중 **{target_ratio:.1f}%**\n"
    return report

# --- [4. 메인 화면 및 사이드바 로직 복구] ---
if df_drama is not None and not df_drama.empty:
    st.sidebar.title("🎬 통합 분석 컨트롤러")
    if st.sidebar.button("🔄 최신 시트 데이터 강제 새로고침", type="primary"):
        load_drama_data.clear()
        load_minute_data.clear()
        st.rerun()
        
    st.sidebar.markdown("---")
    
    # 💡 [복구] 연도 선택 3열 배치
    st.sidebar.markdown("**📅 분석 연도 (추세/랭킹 탭 적용)**")
    years = sorted(df_drama['연도'].unique(), reverse=True)
    year_cols = st.sidebar.columns(3)
    selected_year = [y for i, y in enumerate(years) if year_cols[i % 3].checkbox(str(y), value=True, key=f"yr_{y}")]
    
    st.sidebar.markdown("---")
    slots = ['🌙 월화 드라마', '☀️ 수목 드라마', '🔥 금토 드라마', '🏢 토일 드라마', '🔄 일월 드라마', '기타 편성']
    sel_slot = st.sidebar.selectbox("📅 요일 블록 선택", ["전체 요일 보기"] + slots)
    time_slots = sorted(df_drama['편성시간대'].unique())
    sel_time = st.sidebar.selectbox("⏰ 편성 시간대 선택", ["전체 시간대 보기"] + time_slots)
    
    f_df = df_drama[df_drama['연도'].isin(selected_year)]
    if sel_slot != "전체 요일 보기": f_df = f_df[f_df['편성요일블록'] == sel_slot]
    if sel_time != "전체 시간대 보기": f_df = f_df[f_df['편성시간대'] == sel_time]
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**🎥 비교 프로그램 선택 (추세 탭 적용)**")
    progs = sorted(f_df['프로그램명'].unique())
    c1, c2 = st.sidebar.columns(2)
    if c1.button("✅ 전체 선택"):
        for p in progs: st.session_state[f"prog_{p}"] = True
    if c2.button("❌ 전체 해제"):
        for p in progs: st.session_state[f"prog_{p}"] = False
    
    selected_progs = []
    with st.sidebar.container(height=250):
        for p in progs:
            if st.checkbox(p, value=st.session_state.get(f"prog_{p}", False), key=f"prog_{p}"):
                selected_progs.append(p)

    st.title("📊 ENA 드라마 전략 분석 리포트")
    tab1, tab2, tab3, tab4 = st.tabs(["📈 시청률 추세 대조", "🏆 편성 조건별 랭킹 보드", "🔍 프로그램 심층 분석", "⏱️ 분당 시청률 분석"])
    
    # === TAB 1: 추세 대조 (PD님 원본 로직) ===
    with tab1:
        if selected_progs:
            display_df = f_df[f_df['프로그램명'].isin(selected_progs)]
            st.subheader("🏁 다중 비교 요약 (평균)")
            m1, m2, m3 = st.columns(3)
            m1.metric("수도권 2049", f"{display_df['수도권 2049'].mean():.3f}%")
            m2.metric("수도권 가구", f"{display_df['수도권 가구'].mean():.3f}%")
            m3.metric("전국 가구", f"{display_df['전국 가구'].mean():.3f}%")
            st.divider()
            fig1 = px.line(display_df.sort_values(['프로그램명', '회차']), x='회차', y='수도권 2049', color='프로그램명', markers=True)
            fig1.update_layout(template="plotly_white", height=500, xaxis=dict(dtick=1))
            st.plotly_chart(fig1, use_container_width=True)
            st.subheader("📝 상세 편성 데이터 로그")
            st.dataframe(display_df.sort_values(['연도', '프로그램명', '회차'], ascending=[False, True, True]), width='stretch')
        else: st.warning("비교할 프로그램을 왼쪽 필터에서 선택해주세요.")

    # === TAB 2: 랭킹 보드 (PD님 원본 구조: 전체 평균 + 맞춤 회차) ===
    with tab2:
        st.subheader("🏆 필터 조건 맞춤형 랭킹 보드")
        rank_metric = st.radio("📊 순위 산정 기준 지표", ["수도권 2049", "수도권 가구", "전국 가구"], horizontal=True)
        st.divider()
        if not f_df.empty:
            r1, r2 = st.columns(2)
            with r1:
                st.markdown("#### 🥇 선택 조건 내 전체 평균 순위")
                avg_df = f_df.groupby('프로그램명')[rank_metric].mean().round(3).reset_index().sort_values(rank_metric, ascending=False).reset_index(drop=True)
                avg_df.index += 1
                st.dataframe(avg_df.style.format({rank_metric: "{:.3f}%"}), width='stretch')
            with r2:
                st.markdown("#### 🎯 맞춤 회차 랭킹 보드")
                all_eps = sorted([int(e) for e in f_df['회차'].unique() if e > 0])
                default_eps = [1, 2] if 1 in all_eps and 2 in all_eps else ([1] if 1 in all_eps else [])
                sel_eps = st.multiselect("분석할 회차를 선택하세요", all_eps, default=default_eps)
                if sel_eps:
                    ep_avg_df = f_df[f_df['회차'].isin(sel_eps)].groupby('프로그램명')[rank_metric].mean().round(3).reset_index().sort_values(rank_metric, ascending=False).reset_index(drop=True)
                    ep_avg_df.index += 1
                    st.dataframe(ep_avg_df.style.format({rank_metric: "{:.3f}%"}), width='stretch')

    # === TAB 3: 심층 분석 (PD님 원본 AI 리포트 로직) ===
    with tab3:
        st.subheader("🔍 ENA 오리지널 심층 분석 보고서")
        c_yr, c_pg = st.columns(2)
        with c_yr: target_yr = st.selectbox("📅 방영 연도 선택", ["전체 연도"] + sorted(df_drama['연도'].unique(), reverse=True))
        with c_pg:
            plist = sorted(df_drama['프로그램명'].unique()) if target_yr == "전체 연도" else sorted(df_drama[df_drama['연도'] == target_yr]['프로그램명'].unique())
            target_prog = st.selectbox("🎯 분석 프로그램", plist)
        if target_prog:
            prog_df = df_drama[df_drama['프로그램명'] == target_prog].sort_values('회차')
            st.markdown(generate_advanced_ai_report(prog_df, target_prog, df_drama))
            fig3 = px.line(prog_df, x='회차', y=['수도권 2049', '수도권 가구', '전국 가구'], markers=True, title=f"[{target_prog}] 성과 추이")
            st.plotly_chart(fig3, use_container_width=True)

    # === TAB 4: 분당 시청률 분석 (현재 작동 중인 정밀 로직) ===
    with tab4:
        st.subheader("⏱️ 분당 시청률 정밀 분석 (2025~)")
        if df_min is None or df_min.empty:
            st.warning("분당 데이터를 로드하지 못했습니다.")
        else:
            c1, c2 = st.columns(2)
            with c1: 
                latest_progs = sorted(df_drama[df_drama['연도'] >= 2025]['프로그램명'].unique())
                sel_min_ps = st.multiselect("🎯 프로그램 선택 (2025년 이후)", latest_progs, key="min_ps")
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
                                    bt_v, bt_t = plot_df[col].min(), plot_df.loc[plot_df[col].idxmin(), 'time_key']
                                    fig4.add_trace(go.Scatter(x=[bt_t], y=[bt_v], mode='markers+text', text=[f"{bt_v:.3f}%"], textposition="bottom center", marker=dict(color='blue', size=12, symbol='triangle-down'), name=f"Bottom ({p})"))
                                    st.write(f"📈 **{p} {e}회** 👉 최고: **{pk_v:.3f}%** ({pk_t}) | 최저: **{bt_v:.3f}%** ({bt_t})")
                fig4.update_layout(height=600, template="plotly_white", xaxis=dict(title="방송 시간", tickangle=45), hovermode="x unified")
                st.plotly_chart(fig4, use_container_width=True)
else:
    st.info("데이터 로딩 중...")