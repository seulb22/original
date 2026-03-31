import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import re

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

# --- [2. 데이터 로드] ---
SHEET_ID = "1HQ7s7lgj49q9TJTxB8rNHrey-zczdJjkPvRb8RVZrLg"

@st.cache_data(ttl=60)
def load_drama_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    try:
        df = pd.read_csv(url, skiprows=4)
        new_cols = list(df.columns)
        
        # 💡 [핵심 업데이트] I열(8번 인덱스)에 '종료시간' 추가 및 시청률 열 한 칸씩 이동
        if len(new_cols) >= 13: # 전체 열 개수 증가 대비
            new_cols[2], new_cols[3], new_cols[4] = '연도', '프로그램명', '회차'
            new_cols[5], new_cols[7] = '요일', '시작시간'
            new_cols[8] = '종료시간' # <--- 새로 추가된 I열
            new_cols[9], new_cols[10], new_cols[12] = '수도권 2049', '수도권 가구', '전국 가구' # <--- 한 칸씩 밀림
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
        st.error(f"데이터 로드 실패: {e}")
        return None

df = load_drama_data()

def generate_advanced_ai_report(p_df, prog_name, full_df):
    p_df = p_df.sort_values('회차').reset_index(drop=True)
    if len(p_df) < 2:
        return f"**[{prog_name}]** 데이터가 부족하여 심층 분석이 어렵습니다. (최소 2회 이상 필요)\n"

    avg_all = full_df.groupby('프로그램명')[['수도권 2049', '수도권 가구', '전국 가구']].mean()
    rank_2049 = avg_all['수도권 2049'].rank(ascending=False, method='min')
    rank_hh = avg_all['전국 가구'].rank(ascending=False, method='min')
    total_progs = len(avg_all)

    my_rank_2049 = int(rank_2049.loc[prog_name])
    my_rank_hh = int(rank_hh.loc[prog_name])

    first_2049 = p_df.iloc[0]['수도권 2049']
    peak_2049 = p_df['수도권 2049'].max()
    peak_2049_ep = p_df.loc[p_df['수도권 2049'].idxmax()]['회차'] if peak_2049 > 0 else 0
    avg_2049 = p_df['수도권 2049'].mean()

    first_hh = p_df.iloc[0]['수도권 가구']
    peak_hh = p_df['수도권 가구'].max()
    peak_hh_ep = p_df.loc[p_df['수도권 가구'].idxmax()]['회차'] if peak_hh > 0 else 0
    avg_hh = p_df['수도권 가구'].mean()
    
    avg_nat_hh = p_df['전국 가구'].mean()

    growth_2049 = ((peak_2049 - first_2049) / first_2049 * 100) if first_2049 > 0 else 0
    target_ratio = (avg_2049 / avg_hh * 100) if avg_hh > 0 else 0
    retention_2049 = ((p_df.iloc[1]['수도권 2049'] - first_2049) / first_2049 * 100) if first_2049 > 0 else 0

    report = f"### 💡 [{prog_name}] 핵심 성과 심층 분석\n\n"

    report += "🏆 **1. 역대 오리지널 통합 포지셔닝**\n"
    report += f"- **핵심 타겟 (수도권 2049):** 역대 {total_progs}개 드라마 중 **전체 {my_rank_2049}위** (평균 {avg_2049:.3f}%)\n"
    report += f"- **대중성 (전국 가구):** 역대 {total_progs}개 드라마 중 **전체 {my_rank_hh}위** (평균 {avg_nat_hh:.3f}%)\n"
    if my_rank_2049 < my_rank_hh:
        report += "  👉 전국 가구 순위보다 2049 타겟 순위가 더 높습니다. 대중적인 인지도 대비 **젊은 시청층의 코어 팬덤이 훨씬 강력했던 작품**으로 평가됩니다.\n"
    elif my_rank_2049 > my_rank_hh:
        report += "  👉 2049 타겟보다 전국 가구 순위가 높게 나타납니다. 특정 타겟을 넘어 **다양한 연령대에서 보편적인 사랑을 받은 대중성 확보작**입니다.\n"
    else:
        report += "  👉 2049와 가구 시청률 순위가 밸런스를 맞추며 채널 전반의 성과를 견인했습니다.\n"

    report += "\n🎯 **2. 메인 타겟 (수도권 2049) 화제성 분석**\n"
    report += f"- **최고점 도달:** 첫 방송({first_2049:.3f}%)에서 출발해 **{int(peak_2049_ep)}회에 최고 {peak_2049:.3f}%**를 달성했습니다.\n"
    if growth_2049 >= 50:
        report += f"- **우상향 파워:** 첫방 대비 무려 **{growth_2049:.1f}% 폭풍 성장**하며 방영 내내 막강한 입소문(바이럴)과 화제성을 증명했습니다.\n"
    elif growth_2049 > 0:
        report += f"- **안정적 상승:** 첫방 대비 **{growth_2049:.1f}%의 상승률**을 기록, 극의 전개와 함께 타겟 시청자를 안정적으로 유입시켰습니다.\n"

    report += "\n🧲 **3. 타겟 집중도 및 초반 락인(Lock-in) 효과**\n"
    report += f"- **가구 내 2049 비중:** 가구 시청자 중 2049 타겟이 차지하는 비중은 **{target_ratio:.1f}%** 입니다. "
    if target_ratio >= 35: report += "(트렌드 리딩 작품 수준의 높은 수치)\n"
    else: report += "(가족 단위 시청이 두드러지는 수치)\n"
    
    if retention_2049 > 0:
        report += f"- **초반 훅(Hook):** 2회 차 2049 시청률이 1회 대비 **{retention_2049:.1f}% 올랐습니다.** 1회 방송 직후 타겟층의 호기심을 완벽하게 자극하여 이탈 없이 성공적으로 묶어두었습니다.\n"
    else:
        report += f"- **초반 유지율:** 2회 차 2049 시청률 변동폭은 **{retention_2049:.1f}%** 입니다. 스토리 초반부 진입 장벽이나 타 채널 동시간대 이슈를 교차 검증할 필요가 있습니다.\n"

    return report

# --- [3. 메인 화면 구성 및 사이드바] ---
if df is not None and not df.empty:
    st.sidebar.title("🎬 통합 분석 컨트롤러")
    
    if st.sidebar.button("🔄 최신 시트 데이터 강제 새로고침", type="primary"):
        load_drama_data.clear()
        st.rerun()
        
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("**📅 분석 연도 (추세/랭킹 탭 적용)**")
    years = sorted(df['연도'].unique(), reverse=True)
    selected_year = []
    year_cols = st.sidebar.columns(3)
    for i, y in enumerate(years):
        if year_cols[i % 3].checkbox(str(y), value=True, key=f"yr_{y}"):
            selected_year.append(y)
    
    st.sidebar.markdown("---")
    slots = ['🌙 월화 드라마', '☀️ 수목 드라마', '🔥 금토 드라마', '🏢 토일 드라마', '🔄 일월 드라마', '기타 편성']
    sel_slot = st.sidebar.selectbox("📅 요일 블록 선택", ["전체 요일 보기"] + slots)
    time_slots = sorted(df['편성시간대'].unique())
    sel_time = st.sidebar.selectbox("⏰ 편성 시간대 선택", ["전체 시간대 보기"] + time_slots)
    
    f_df = df[df['연도'].isin(selected_year)]
    if sel_slot != "전체 요일 보기": f_df = f_df[f_df['편성요일블록'] == sel_slot]
    if sel_time != "전체 시간대 보기": f_df = f_df[f_df['편성시간대'] == sel_time]
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**🎥 비교 프로그램 선택 (추세 탭 적용)**")
    progs = sorted(f_df['프로그램명'].unique())
    
    col1, col2 = st.sidebar.columns(2)
    if col1.button("✅ 전체 선택"):
        for p in progs: st.session_state[f"prog_{p}"] = True
    if col2.button("❌ 전체 해제"):
        for p in progs: st.session_state[f"prog_{p}"] = False

    selected_progs = []
    if progs:
        with st.sidebar.container(height=250):
            for p in progs:
                if f"prog_{p}" not in st.session_state: st.session_state[f"prog_{p}"] = False
                if st.checkbox(p, key=f"prog_{p}"): selected_progs.append(p)

    display_df = f_df[f_df['프로그램명'].isin(selected_progs)]

    st.title("📊 ENA 드라마 전략 분석 리포트")
    tab1, tab2, tab3 = st.tabs(["📈 시청률 추세 대조", "🏆 편성 조건별 랭킹 보드", "🔍 프로그램 심층 분석"])
    
    # === TAB 1 ===
    with tab1:
        if selected_progs:
            st.subheader(f"🏁 다중 비교 요약 (평균)")
            c1, c2, c3 = st.columns(3)
            c1.metric("수도권 2049", f"{display_df['수도권 2049'].mean():.3f}%")
            c2.metric("수도권 가구", f"{display_df['수도권 가구'].mean():.3f}%")
            c3.metric("전국 가구", f"{display_df['전국 가구'].mean():.3f}%")

            st.divider()
            st.subheader("📈 다중 시청률 추세 대조")
            m_cols = st.columns(3)
            sel_metrics = []
            if m_cols[0].checkbox("수도권 2049", value=True): sel_metrics.append("수도권 2049")
            if m_cols[1].checkbox("수도권 가구", value=False): sel_metrics.append("수도권 가구")
            if m_cols[2].checkbox("전국 가구", value=False): sel_metrics.append("전국 가구")
            
            if sel_metrics:
                fig = go.Figure()
                line_styles = {"수도권 2049": "solid", "수도권 가구": "dash", "전국 가구": "dot"}
                if '회차' in display_df.columns: display_df = display_df.sort_values(['프로그램명', '회차'])
                else: display_df = display_df.sort_values(['프로그램명'])
                for p in selected_progs:
                    p_data = display_df[display_df['프로그램명'] == p]
                    for m in sel_metrics:
                        fig.add_trace(go.Scatter(
                            x=p_data['회차'] if '회차' in p_data.columns else p_data.index, y=p_data[m], mode='lines+markers', name=f"[{p}] {m}", line=dict(dash=line_styles[m]), hovertemplate="시청률: %{y:.3f}%<extra></extra>"
                        ))
                fig.update_layout(height=500, template="plotly_white", hovermode="x unified", xaxis=dict(title="회차", dtick=1))
                st.plotly_chart(fig, width='stretch')
                
            st.subheader("📝 상세 편성 데이터 로그")
            st.dataframe(display_df.drop(columns=['전국 2049'], errors='ignore').sort_values(['연도', '프로그램명', '회차'], ascending=[False, True, True]), width='stretch')
        else:
            st.warning("선택된 프로그램이 없습니다. 왼쪽 필터에서 비교할 프로그램을 켜주세요.")

    # === TAB 2 ===
    with tab2:
        st.subheader("🏆 필터 조건 맞춤형 랭킹 보드")
        rank_metric = st.radio("📊 순위 산정 기준 지표", ["수도권 2049", "수도권 가구", "전국 가구"], horizontal=True)
        st.divider()
        if f_df.empty:
            st.warning("선택하신 조건에 해당하는 드라마 데이터가 없습니다.")
        else:
            r1, r2 = st.columns(2)
            with r1:
                st.markdown("#### 🥇 선택 조건 내 전체 평균 순위")
                avg_df = f_df.groupby('프로그램명')[rank_metric].mean().round(3).reset_index()
                avg_df = avg_df.sort_values(rank_metric, ascending=False).reset_index(drop=True)
                avg_df.index = avg_df.index + 1
                st.dataframe(avg_df.style.format({rank_metric: "{:.3f}%"}), width='stretch')

            with r2:
                st.markdown("#### 🎯 맞춤 회차 랭킹 보드")
                if '회차' in f_df.columns:
                    all_eps = sorted([int(e) for e in f_df['회차'].unique() if e > 0])
                    default_eps = [1, 2] if 1 in all_eps and 2 in all_eps else ([1] if 1 in all_eps else [])
                    sel_eps = st.multiselect("분석할 회차를 선택하세요", all_eps, default=default_eps)
                    if sel_eps:
                        ep_df = f_df[f_df['회차'].isin(sel_eps)]
                        ep_avg_df = ep_df.groupby('프로그램명')[rank_metric].mean().round(3).reset_index()
                        ep_avg_df = ep_avg_df.sort_values(rank_metric, ascending=False).reset_index(drop=True)
                        ep_avg_df.index = ep_avg_df.index + 1
                        st.dataframe(ep_avg_df.style.format({rank_metric: "{:.3f}%"}), width='stretch')

    # === TAB 3 ===
    with tab3:
        st.subheader("🔍 ENA 오리지널 심층 분석 보고서")
        st.markdown("특정 드라마의 타겟 성과와 채널 내 포지셔닝을 다각도로 분석합니다.")
        
        c_year, c_prog = st.columns(2)
        with c_year:
            all_years = sorted(df['연도'].unique(), reverse=True)
            target_year = st.selectbox("📅 방영 연도를 선택하세요", ["전체 연도"] + all_years)
        
        with c_prog:
            if target_year == "전체 연도":
                prog_list = sorted(df['프로그램명'].unique())
            else:
                prog_list = sorted(df[df['연도'] == target_year]['프로그램명'].unique())
            
            target_prog = st.selectbox("🎯 심층 분석할 프로그램", prog_list)
        
        if target_prog:
            prog_df = df[df['프로그램명'] == target_prog].sort_values('회차')
            
            def get_peak(p_df, col):
                if p_df.empty or col not in p_df.columns: return 0, 0
                idx = p_df[col].idxmax()
                return p_df.loc[idx, col], p_df.loc[idx, '회차']

            peak_2049, ep_2049 = get_peak(prog_df, '수도권 2049')
            peak_hh, ep_hh = get_peak(prog_df, '수도권 가구')
            peak_nat, ep_nat = get_peak(prog_df, '전국 가구')

            st.markdown("---")
            st.markdown(f"#### 🏁 [{target_prog}] 최고 시청률 지표")
            m1, m2, m3 = st.columns(3)
            m1.metric("최고 수도권 2049", f"{peak_2049:.3f}% ({int(ep_2049)}회)")
            m2.metric("최고 수도권 가구", f"{peak_hh:.3f}% ({int(ep_hh)}회)")
            m3.metric("최고 전국 가구", f"{peak_nat:.3f}% ({int(ep_nat)}회)")
            st.markdown("---")
            
            with st.spinner('방대한 데이터를 딥 다이브 분석 중입니다...'):
                st.markdown(generate_advanced_ai_report(prog_df, target_prog, df))
            
            st.divider()
            st.markdown(f"**📉 [{target_prog}] 시청률 추세**")
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=prog_df['회차'], y=prog_df['수도권 2049'], mode='lines+markers', name="수도권 2049", line=dict(dash='solid', color='#00FFCC', width=3), hovertemplate="2049: %{y:.3f}%<extra></extra>"))
            fig3.add_trace(go.Scatter(x=prog_df['회차'], y=prog_df['수도권 가구'], mode='lines+markers', name="수도권 가구", line=dict(dash='dash', color='#FF0066', width=2), hovertemplate="가구: %{y:.3f}%<extra></extra>"))
            fig3.add_trace(go.Scatter(x=prog_df['회차'], y=prog_df['전국 가구'], mode='lines+markers', name="전국 가구", line=dict(dash='dot', color='#CC00FF', width=2), hovertemplate="전국: %{y:.3f}%<extra></extra>"))
            fig3.update_layout(height=450, template="plotly_white", hovermode="x unified", xaxis=dict(title="회차", dtick=1))
            st.plotly_chart(fig3, width='stretch')

else:
    st.info("데이터 로딩 중...")