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

# --- [3. 🤖 AI 초정밀 전략 분석 엔진 12.0 (개별 프로젝트 서사형)] ---
def generate_hyper_ai_insight(p_df, prog_name, full_df):
    baseline_all = full_df[full_df['프로그램명'] != '이상한 변호사 우영우']
    this_year = p_df['연도'].iloc[0]
    baseline_year = baseline_all[baseline_all['연도'] == this_year]
    if baseline_year.empty: baseline_year = baseline_all

    my_avg_2049 = p_df['수도권 2049'].mean()
    my_avg_hh = p_df['수도권 가구'].mean()
    my_peak_2049 = p_df['수도권 2049'].max()
    my_peak_ep = int(p_df.loc[p_df['수도권 2049'].idxmax(), '회차'])
    my_first_2049 = p_df.sort_values('회차').iloc[0]['수도권 2049']
    my_last_2049 = p_df.sort_values('회차').iloc[-1]['수도권 2049']
    total_eps = int(p_df['회차'].max())

    all_avg_2049 = baseline_all['수도권 2049'].mean()
    yr_avg_2049 = baseline_year['수도권 2049'].mean()
    yr_avg_hh = baseline_year['수도권 가구'].mean()
    
    growth = (my_peak_2049 / my_first_2049 - 1) * 100 if my_first_2049 > 0 else 0
    retention = (my_last_2049 / my_peak_2049 * 100) if my_peak_2049 > 0 else 0
    yr_perf = (my_avg_2049 / yr_avg_2049 - 1) * 100

    insight = f"## 🧐 [{prog_name}] 프로젝트 전략 리포트\n\n"
    
    # [1. 위상 진단]
    insight += "### 🏆 1. 채널 내 실질적 위상\n"
    insight += f"- **{prog_name}**은 {this_year}년 ENA 드라마 평균 대비 **{yr_perf:+.1f}%**의 성과 편차를 보였습니다. "
    if yr_perf > 0:
        insight += f"동시기 경쟁작들 사이에서 채널의 타겟 소구력을 상향 견인한 주역이었습니다.\n"
    else:
        insight += f"당시 시장 흐름에 비해 타겟 유입력이 다소 약화된 양상을 남겼습니다.\n"

    # [2. 타겟 분석]
    target_ratio = (my_avg_2049 / my_avg_hh * 100) if my_avg_hh > 0 else 0
    channel_ratio = (all_avg_2049 / baseline_all['수도권 가구'].mean() * 100)
    insight += "\n### 🎯 2. 타겟 유입 정밀 진단\n"
    insight += f"- 본 작품의 2049 타겟 집중도는 **{target_ratio:.1f}%**로 집계되었습니다. (채널 평균: {channel_ratio:.1f}%)\n"
    if target_ratio > channel_ratio + 1:
        insight += f"  👉 가구 시청률보다 타겟 화제성이 앞선 작품으로, 광고주가 선호하는 **고효율 인벤토리**로서 가치를 증명했습니다.\n"
    elif target_ratio < channel_ratio - 1:
        insight += f"  👉 전체 가구 규모에 비해 핵심 타겟(2049)의 이탈이 두드러지며 **시청층 노후화**에 대한 과제를 남겼습니다.\n"
    else:
        insight += "  👉 채널의 보편적인 시청 분포를 그대로 따르며 안정적인 밸런스를 유지했습니다.\n"

    # [💡 3. 화제성 확장성 정밀 분석 - '드라마 특징'에 집중]
    insight += "\n### 📈 3. 프로젝트 화제성 전개 양상\n"
    insight += f"- **{prog_name}**은 1회({my_first_2049:.3f}%)로 시작해 **{my_peak_ep}회**에서 최고점인 **{my_peak_2049:.3f}%**에 도달했습니다.\n"
    
    # 전개 패턴별 맞춤 서사
    if my_peak_ep >= total_eps * 0.8: # 후반부 피크
        insight += f"  👉 종영 직전인 **{my_peak_ep}회**까지 에너지를 끌어올린 '후반 집중형' 흐름입니다. 서사의 빌드업이 시청자들에게 유효하게 작용하며 마지막까지 긴장감을 유지한 사례입니다.\n"
    elif my_peak_ep <= total_eps * 0.3: # 초반 피크 후 하락
        insight += f"  👉 방송 초반인 **{my_peak_ep}회**에 이미 최고 화제성을 소진한 '전반 편중형' 흐름입니다. 초반 입소문 유입(growth: {growth:+.1f}%)은 강력했으나, 이후 전개에서 시청자를 락인(Lock-in)할 만한 뒷심이 부족했습니다.\n"
    else: # 중반 피크
        insight += f"  👉 중반부인 **{my_peak_ep}회**를 기점으로 화제성의 변곡점을 맞이했습니다. 특정 에피소드나 자극적인 전개가 일시적 고점을 형성했으나, 그 탄력을 종영까지 지속하는 데에는 한계가 있었습니다.\n"

    # [💡 4. 전략적 성과 결론 - 과거형 결론]
    insight += "\n### 📂 4. 전략적 성과 최종 결론\n"
    
    if retention < 70:
        insight += f"- **[이탈 제어 실패]:** 최고점 대비 종영 유지율이 **{retention:.1f}%**에 그쳤습니다. **{prog_name}**이 보여준 초반의 경이로운 우상향({growth:+.1f}%)은 기획의 승리였으나, 후반부 서사 동력 상실로 인해 프로젝트의 최종 완성도 면에서는 유실이 컸던 결과로 기록되었습니다.\n"
    elif growth > 40:
        insight += f"- **[바이럴 포텐셜 증명]:** 첫 방송 대비 시청률을 **{growth:.1f}%**나 끌어올린 저력은 **{prog_name}**만의 독보적인 성과입니다. 비록 종영 시점엔 수치가 변동했으나, 방영 기간 내내 채널의 화제성 지수를 견인한 효자 IP 역할을 완수했습니다.\n"
    elif yr_perf < -15:
        insight += f"- **[타겟 불일치 확인]:** 당시 {this_year}년 시청 트렌드와 본 프로젝트의 소구점이 어긋났음이 수치로 입증되었습니다. 소재의 참신함은 있었으나 대중적 확산에는 도달하지 못한 전략적 미달 사례로 남았습니다.\n"
    else:
        insight += f"- **[안정적 교두보 확보]:** 특별한 폭등이나 급락 없이 채널의 기본 체력을 지켜냈습니다. 차기 대작 편성을 위한 안정적인 시청권을 방어하며 가교 역할을 충실히 수행한 프로젝트였습니다.\n"

    return insight

# --- [4. 메인 화면 구성] ---
if df_drama is not None and not df_drama.empty:
    st.sidebar.title("🎬 통합 분석 컨트롤러")
    if st.sidebar.button("🔄 데이터 강제 새로고침", type="primary"):
        load_drama_data.clear()
        load_minute_data.clear()
        st.rerun()
    
    st.sidebar.markdown("---")
    years = sorted(df_drama['연도'].unique(), reverse=True)
    year_cols = st.sidebar.columns(3)
    selected_year = [y for i, y in enumerate(years) if year_cols[i % 3].checkbox(str(y), value=True, key=f"yr_{y}")]
    
    f_df = df_drama[df_drama['연도'].isin(selected_year)]
    progs = sorted(f_df['프로그램명'].unique())
    
    if "first_load_done" not in st.session_state:
        for p in progs: st.session_state[f"prog_{p}"] = True
        st.session_state["first_load_done"] = True

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
            st.markdown(generate_hyper_ai_insight(p_df, target_p, df_drama))
            st.divider()
            m1_v, m1_e = p_df['수도권 2049'].max(), p_df.loc[p_df['수도권 2049'].idxmax(), '회차']
            m2_v, m2_e = p_df['수도권 가구'].max(), p_df.loc[p_df['수도권 가구'].idxmax(), '회차']
            m3_v, m3_e = p_df['전국 가구'].max(), p_df.loc[p_df['전국 가구'].idxmax(), '회차']
            c1, c2, c3 = st.columns(3)
            c1.metric("최고 수도권 2049", f"{m1_v:.3f}%", f"{m1_e}회")
            c2.metric("최고 수도권 가구", f"{m2_v:.3f}%", f"{m2_e}회")
            c3.metric("최고 전국 가구", f"{m3_v:.3f}%", f"{m3_e}회")
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
                chart_data = []
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
                                        pk_v = plot_df[col].max()
                                        chart_data.append({'p': p, 'e': e, 'm': m_name, 'df': plot_df, 'col': col, 'peak': pk_v})

                chart_data.sort(key=lambda x: x['peak'], reverse=True)
                for item in chart_data:
                    p, e, m_name, plot_df, col, pk_v = item['p'], item['e'], item['m'], item['df'], item['col'], item['peak']
                    fig4.add_trace(go.Scatter(x=plot_df['time_key'], y=plot_df[col], mode='lines', name=f"{p} {e}회_{m_name}"))
                    pk_t = plot_df.loc[plot_df[col].idxmax(), 'time_key']
                    bt_v, bt_t = plot_df[col].min(), plot_df.loc[plot_df[col].idxmin(), 'time_key']
                    peak_cards.append({"label": f"{p} {e}회 {m_name}", "val": pk_v, "time": pk_t})
                    fig4.add_trace(go.Scatter(x=[pk_t], y=[pk_v], mode='markers', marker=dict(color='red', size=10, symbol='triangle-up'), showlegend=False))
                    fig4.add_trace(go.Scatter(x=[bt_t], y=[bt_v], mode='markers', marker=dict(color='blue', size=10, symbol='triangle-down'), showlegend=False))

                if peak_cards:
                    peak_cards.sort(key=lambda x: x['val'], reverse=True)
                    st.divider(); cols = st.columns(min(len(peak_cards), 4))
                    for i, c in enumerate(peak_cards):
                        with cols[i % 4]: st.metric(f"🏆 {c['label']} 최고", f"{c['val']:.3f}%", f"⏰ {c['time']}")
                    st.divider()

                fig4.update_layout(height=500, template="plotly_white", xaxis=dict(title="방송 시간", tickangle=45), hovermode="x unified",
                                   legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02))
                st.plotly_chart(fig4, width='stretch')
else:
    st.info("데이터 로딩 중...")