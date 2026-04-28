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
        if st.session_state.get("password", "") == "qwe123":
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

# --- [2. 데이터 로드 및 정제] ---
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
        df['프로그램명'] = df['프로그램명'].astype(str).str.strip()
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

# --- [3. 🤖 AI 초정밀 전략 분석 엔진 12.5 (파트 4 곡선 패턴 인식 추가)] ---
def generate_hyper_ai_insight(p_df, prog_name, full_df):
    baseline_all = full_df[~full_df['프로그램명'].str.contains('우영우', na=False)]
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
    
    growth = (my_peak_2049 / my_first_2049 - 1) * 100 if my_first_2049 > 0 else 0
    retention = (my_last_2049 / my_peak_2049 * 100) if my_peak_2049 > 0 else 0
    yr_perf = (my_avg_2049 / yr_avg_2049 - 1) * 100

    insight = f"## 🧐 [{prog_name}] 프로젝트 전략 리포트\n\n"
    insight += "### 🏆 1. 채널 내 실질적 위상\n"
    insight += f"- **{prog_name}**은 {this_year}년 ENA 드라마 평균 대비 **{yr_perf:+.1f}%**의 성과 편차를 보였습니다. "
    if yr_perf > 0: insight += f"동시기 경쟁작들 사이에서 채널의 타겟 소구력을 상향 견인한 주역이었습니다.\n"
    else: insight += f"당시 시장 흐름에 비해 타겟 유입력이 다소 약화된 양상을 남겼습니다.\n"

    target_ratio = (my_avg_2049 / my_avg_hh * 100) if my_avg_hh > 0 else 0
    channel_ratio = (all_avg_2049 / baseline_all['수도권 가구'].mean() * 100)
    insight += "\n### 🎯 2. 타겟 유입 정밀 진단\n"
    insight += f"- 본 작품의 2049 타겟 집중도는 **{target_ratio:.1f}%**로 집계되었습니다. (채널 평균: {channel_ratio:.1f}%)\n"
    if target_ratio > channel_ratio + 0.5:
        insight += f"  👉 가구 시청률보다 타겟 화제성이 앞선 작품으로, 광고주가 선호하는 **고효율 인벤토리**로서 가치를 증명했습니다.\n"
    elif target_ratio < channel_ratio - 0.5:
        insight += f"  👉 전체 가구 규모에 비해 핵심 타겟(2049)의 이탈이 두드러지며 **시청층 노후화**에 대한 과제를 남겼습니다.\n"
    else:
        insight += "  👉 채널의 보편적인 시청 분포를 그대로 따르며 안정적인 밸런스를 유지했습니다.\n"

    insight += "\n### 📈 3. 프로젝트 화제성 전개 양상\n"
    insight += f"- **{prog_name}**은 1회({my_first_2049:.3f}%)로 시작해 **{my_peak_ep}회**에서 최고점인 **{my_peak_2049:.3f}%**에 도달했습니다.\n"
    if my_peak_ep >= total_eps * 0.8:
        insight += f"  👉 종영 직전인 **{my_peak_ep}회**까지 에너지를 끌어올린 '후반 집중형' 흐름입니다. 서사의 빌드업이 시청자들에게 유효하게 작용하며 마지막까지 긴장감을 유지한 사례입니다.\n"
    elif my_peak_ep <= total_eps * 0.3:
        insight += f"  👉 방송 초반인 **{my_peak_ep}회**에 이미 최고 화제성을 소진한 '전반 편중형' 흐름입니다. 초반 입소문 유입(growth: {growth:+.1f}%)은 강력했으나, 이후 전개에서 시청자를 락인(Lock-in)할 만한 뒷심이 부족했습니다.\n"
    else:
        insight += f"  👉 중반부인 **{my_peak_ep}회**를 기점으로 화제성의 변곡점을 맞이했습니다. 특정 에피소드가 일시적 고점을 형성했으나 그 탄력을 종영까지 지속하는 데에는 한계가 있었습니다.\n"

    # 💡 [여기서부터 완벽 교체] 단순 성장률이 아닌 '전체 방영 곡선(Curve)'과 '실제 수치'를 결합한 입체적 패턴 진단
    insight += "\n### 📂 4. 전략적 성과 최종 결론\n"
    
    ep_vals = p_df['수도권 2049'].tolist()
    ep_nums = p_df['회차'].tolist()
    n_eps = len(ep_vals)
    
    if n_eps >= 6:
        peak_val = max(ep_vals)
        peak_idx = ep_vals.index(peak_val)
        peak_ep = ep_nums[peak_idx]
        
        min_val = min(ep_vals)
        min_idx = ep_vals.index(min_val)
        min_ep = ep_nums[min_idx]
        
        first_val = ep_vals[0]
        last_val = ep_vals[-1]
        
        # 전반부 vs 중후반부 데이터 분리
        mid_point = n_eps // 2
        drop_rate = (1 - (min_val / peak_val)) * 100 if peak_val > 0 else 0
        rebound_rate = ((last_val / ep_vals[-2]) - 1) * 100 if ep_vals[-2] > 0 else 0
        
        # 패턴 1: 딜리버리맨 케이스 (전반적인 시청률 기근 및 채널 평균 대폭 하회)
        if yr_perf < -30 and peak_val < yr_avg_2049 * 0.7:
            insight += f"- **[절대적 유입량 부족 및 고전]:** 채널 평균 대비 **{yr_perf:.1f}%**라는 수치가 보여주듯, 방영 기간 내내 타겟 시청층의 이목을 끄는 데 큰 어려움을 겪었습니다. 최고 시청률조차 **{peak_val:.3f}%**({peak_ep}회)에 그치며 유의미한 반등 모멘텀을 만들지 못했습니다. 기획된 소재나 장르가 당시 ENA의 주 시청 타겟과 완전히 엇갈렸거나, 대진운 등 외부 요인의 타격이 컸던 뼈아픈 사례로 남았습니다.\n"
            
        # 패턴 2: 클라이맥스 케이스 (초반 고점 -> 중반 푹 꺼짐 -> 막판 결말 버프)
        elif peak_idx < mid_point and drop_rate > 30 and rebound_rate > 15:
            insight += f"- **[중반부 락인(Lock-in) 붕괴 및 결말 버프]:** 전반부인 **{peak_ep}회({peak_val:.3f}%)**에 일찌감치 고점을 찍은 뒤, 극 중반인 **{min_ep}회({min_val:.3f}%)**까지 시청률이 무려 **{drop_rate:.1f}%**나 증발하는 심각한 허리 부실 현상을 보였습니다. 다행히 최종회에서 직전 회차 대비 **{rebound_rate:.1f}%** 급반등({last_val:.3f}%)하며 간신히 체면은 치렀으나, 이는 서사의 몰입이라기보다 '결말 확인용' 일회성 복귀일 확률이 높습니다. 초반 후킹력은 좋았으나 스토리를 끌고 가는 동력이 크게 부족했습니다.\n"
            
        # 패턴 3: 용두사미형 (초반 고점 -> 끝까지 우하향 이탈)
        elif peak_idx < mid_point and drop_rate > 25 and rebound_rate <= 15:
            insight += f"- **[우하향 곡선 및 뒷심 상실]:** {peak_ep}회에 최고점({peak_val:.3f}%)을 기록한 이후 뚜렷한 하락세가 멈추지 않았습니다. 최고점 대비 최저점({min_val:.3f}%, {min_ep}회)의 낙폭이 **{drop_rate:.1f}%**에 달하며, 최종회까지 반등을 만들어내지 못했습니다. 초기 마케팅과 참신함으로 첫 유입은 끌어냈으나, 전개의 흡인력이 대중의 체류 시간을 끝까지 담보하지 못한 전형적인 '용두사미' 패턴입니다.\n"
            
        # 패턴 4: 진정한 효자 IP (견고한 우상향)
        elif peak_idx >= n_eps - 2 and first_val < peak_val and drop_rate < 30:
            insight += f"- **[견고한 우상향 및 완벽한 락인]:** 첫 회({first_val:.3f}%) 시작 이후 큰 폭의 시청자 이탈(최대 낙폭 {drop_rate:.1f}%) 없이 후반부로 갈수록 탄력을 받는 훌륭한 시청률 곡선을 그렸습니다. 종영 직전인 **{peak_ep}회에 최고점({peak_val:.3f}%)**을 경신했다는 것은 극의 빌드업이 대중에게 완벽히 먹혀들었음을 방증합니다. 코어 팬덤을 끝까지 끌고 간 모범적인 우상향 웰메이드 프로젝트입니다.\n"
            
        # 패턴 5: 콘크리트 박스권 (오르지도 내리지도 않음)
        elif drop_rate < 20:
            insight += f"- **[단단한 박스권 및 코어 유지]:** 방영 내내 최고점({peak_val:.3f}%)과 최저점({min_val:.3f}%)의 차이가 불과 **{drop_rate:.1f}%** 이내로 좁게 묶이며, 이탈 없는 콘크리트 시청층을 보여주었습니다. 폭발적인 외부 바이럴(신규 유입)은 부족했으나, 극의 톤앤매너를 좋아하는 고정 타겟층이 단 한 번의 큰 이탈 없이 자리를 지켜준 안정적인 성과입니다.\n"
            
        # 패턴 6: 롤러코스터 (위아래 기복이 심함)
        else:
            insight += f"- **[불안정한 시청 롤러코스터]:** 최고점({peak_val:.3f}%, {peak_ep}회)과 최저점({min_val:.3f}%, {min_ep}회) 사이의 변동폭이 크고 흐름을 예측하기 힘든 패턴을 보였습니다. 에피소드의 재미나 외부 경쟁 상황에 따라 시청자가 들고 나는 현상이 심했습니다. 시청 습관이 단단히 정착되지 않은 만큼, 향후 유사 기획 시 방영 시간대 고정이나 전후 리드인(Lead-in)의 강력한 전략적 지원이 필요해 보입니다.\n"
    else:
        # 단막극 혹은 데이터가 부족한 경우
        if retention < 70:
            insight += f"- **[이탈 제어 실패]:** 최고점 대비 종영 유지율이 **{retention:.1f}%**에 그쳤습니다. 방영 기간 내내 시청층 하락을 방어하는 데 뚜렷한 취약점을 드러냈습니다.\n"
        elif growth > 40:
            insight += f"- **[화제성 견인 증명]:** 첫 회 대비 시청률을 급격히 끌어올리며 방영 기간 내내 시청자들의 이목을 사로잡는 강력한 에너지를 발휘했습니다.\n"
        else:
            insight += f"- **[안정적 교두보 확보]:** 특별한 폭등이나 급락 없이 채널의 기본 체력을 지켜내며 편성 띠의 교두보 역할을 충실히 수행했습니다.\n"

    return insight

# --- [4. 메인 UI 구성] ---
if df_drama is not None and not df_drama.empty:
    st.sidebar.title("🎬 통합 분석 컨트롤러")
    
    if st.sidebar.button("🔄 데이터 강제 새로고침", type="primary"):
        load_drama_data.clear(); load_minute_data.clear(); st.rerun()
    
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
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 시청률 추세 대조", "🔮 입체 분석", "🏆 편성 랭킹 보드", "🔍 프로그램 심층 분석", "⏱️ 분당 시청률 분석"])
    
    def filter_woo_internal(df_in, toggle_val):
        return df_in[~df_in['프로그램명'].str.contains('우영우', na=False)] if not toggle_val else df_in

    with tab1:
        show_woo_tab1 = st.toggle("차트에 '우영우' 데이터 포함하기", value=True, key="woo_trend")
        if selected_progs:
            d_df = f_df[f_df['프로그램명'].isin(selected_progs)].sort_values(['프로그램명', '회차'])
            chart_df = filter_woo_internal(d_df, show_woo_tab1)
            
            st.subheader("🎯 수도권 2049 추세")
            st.plotly_chart(px.line(chart_df, x='회차', y='수도권 2049', color='프로그램명', markers=True), width='stretch')
            st.divider()
            st.subheader("🏠 수도권 가구 추세")
            st.plotly_chart(px.line(chart_df, x='회차', y='수도권 가구', color='프로그램명', markers=True), width='stretch')
            st.divider()
            st.subheader("📺 전국 가구 추세")
            st.plotly_chart(px.line(chart_df, x='회차', y='전국 가구', color='프로그램명', markers=True), width='stretch')
        else: st.warning("분석할 드라마를 선택하세요.")

    with tab2:
        st.subheader("🔮 프로그램 성과 및 시청 안정성 입체 분석")
        show_woo_tab2 = st.toggle("분석에 '우영우' 데이터 포함하기", value=False, key="woo_matrix")
        
        if selected_progs:
            active_df = filter_woo_internal(f_df[f_df['프로그램명'].isin(selected_progs)], show_woo_tab2)
            
            st.markdown("#### 1️⃣ 성과 상관관계 (타겟 가성비 분석)")
            m_list = ["수도권 2049", "수도권 가구", "전국 가구"]
            c1, c2 = st.columns(2)
            x_ax = c1.selectbox("横축(X) 지표", m_list, index=0)
            y_ax = c2.selectbox("縦축(Y) 지표", m_list, index=1)
            
            bubble_data = []
            for p in active_df['프로그램명'].unique():
                p_sub = active_df[active_df['프로그램명'] == p]
                if not p_sub.empty:
                    avg_x, avg_y = p_sub[x_ax].mean(), p_sub[y_ax].mean()
                    avg_2049 = p_sub['수도권 2049'].mean()
                    avg_su_hh = p_sub['수도권 가구'].mean()
                    target_ratio = (avg_2049 / avg_su_hh * 100) if avg_su_hh > 0 else 0
                    bubble_data.append({"프로그램명": p, x_ax: avg_x, y_ax: avg_y, "타겟가성비": target_ratio})
            
            if bubble_data:
                b_df = pd.DataFrame(bubble_data)
                fig_bubble = px.scatter(b_df, x=x_ax, y=y_ax, size="타겟가성비", color="프로그램명", text="프로그램명", size_max=40, template="plotly_white")
                fig_bubble.update_traces(textposition='top center'); st.plotly_chart(fig_bubble, width='stretch')
                
                st.info("💡 **버블 차트 가이드:** X축과 Y축은 선택 지표를, **버블의 크기**는 가구 시청률 대비 수도권 2049 시청률의 비중(타겟 가성비)을 나타냅니다. 우상단에 위치할수록 대중성을, 버블이 클수록 젊은 타겟을 꽉 잡은 고효율 작품입니다.")
                
                top3_bubble = b_df.sort_values("타겟가성비", ascending=False).head(3)
                if not top3_bubble.empty:
                    st.markdown("**🏆 [타겟 가성비 Top 3] 가구 시청률 대비 2049 타겟이 가장 밀집된 알짜 작품**")
                    for _, row in top3_bubble.iterrows():
                        st.markdown(f"- **{row['프로그램명']}**: 가구 시청자 중 2049 타겟 비중이 **{row['타겟가성비']:.1f}%**에 달해, 가장 뛰어난 광고 가치를 증명했습니다.")
            
            st.divider()
            
            st.markdown("#### 2️⃣ 시청률 변동성 및 타점 분석")
            box_met = st.selectbox("변동성 분석 지표 선택", m_list, index=0)
            fig_box = px.box(active_df, x="프로그램명", y=box_met, color="프로그램명", points="all", template="plotly_white")
            st.plotly_chart(fig_box, width='stretch')
            
            st.info("💡 **박스 플롯 가이드:** 상자가 위쪽에 위치할수록(높이가 높을수록) 기본 타점이 압도적인 작품입니다. 세로 길이(편차)가 짧으면 콘크리트 팬덤을, 길면 화제성에 따른 폭발적 유입(롤러코스터)을 의미합니다.")
            
            stats_df = active_df.groupby('프로그램명').agg(
                편차=(box_met, 'std'),
                평균=(box_met, 'mean')
            ).reset_index()
            
            top3_box = stats_df.sort_values('평균', ascending=False).head(3)
            
            if not top3_box.empty:
                st.markdown(f"**🚀 [시청률 타점 Top 3] {box_met} 기준 가장 높은 곳에서 노는(평균 타점이 높은) 작품**")
                for _, row in top3_box.iterrows():
                    cv = row['편차'] / row['평균'] if row['평균'] > 0 else 0
                    if cv < 0.2:
                        desc = "박스 길이가 짧고 타점이 높아, 회차별 기복 없이 굳건한 콘크리트 팬덤을 꽉 잡았습니다."
                    else:
                        desc = "박스가 위아래로 길게 뻗어 있어 회차별 유입 기복이 크지만, 그만큼 특정 회차에서 폭발적인 포텐셜을 터뜨린 저력이 돋보입니다."
                        
                    st.markdown(f"- **{row['프로그램명']}**: 평균 **{row['평균']:.3f}%**의 압도적 타점! 👉 {desc}")
        else: st.warning("분석할 드라마를 먼저 선택하세요.")

    with tab3:
        rank_metric = st.radio("📊 기준 지표", ["수도권 2049", "수도권 가구", "전국 가구"], horizontal=True, key="rank_radio")
        r1, r2 = st.columns(2)
        with r1:
            st.markdown("**📁 프로그램 전체 평균 순위**")
            avg_df = f_df.groupby('프로그램명')[rank_metric].mean().round(3).reset_index().sort_values(rank_metric, ascending=False).reset_index(drop=True)
            avg_df.index += 1; st.dataframe(avg_df.style.format({rank_metric: "{:.3f}%"}), width='stretch')
        with r2:
            st.markdown("**🔢 특정 회차 비교**")
            show_final_only = st.checkbox("🏁 각 프로그램별 '최종회(마지막 회차)'만 비교하기")
            
            if show_final_only:
                final_eps_data = f_df.sort_values(['프로그램명', '회차']).drop_duplicates('프로그램명', keep='last')
                ep_avg_df = final_eps_data.groupby('프로그램명')[rank_metric].mean().round(3).reset_index().sort_values(rank_metric, ascending=False).reset_index(drop=True)
                st.info("💡 각 드라마의 마지막 방송(10회, 16회 등) 성적만 모아온 결과입니다.")
            else:
                all_eps = sorted([int(e) for e in f_df['회차'].unique() if e > 0])
                sel_eps = st.multiselect("비교할 회차 번호 선택", all_eps, default=[1] if 1 in all_eps else [])
                if sel_eps:
                    ep_avg_df = f_df[f_df['회차'].isin(sel_eps)].groupby('프로그램명')[rank_metric].mean().round(3).reset_index().sort_values(rank_metric, ascending=False).reset_index(drop=True)
                else:
                    ep_avg_df = pd.DataFrame()

            if not ep_avg_df.empty:
                ep_avg_df.index += 1
                st.dataframe(ep_avg_df.style.format({rank_metric: "{:.3f}%"}), width='stretch')

    with tab4:
        target_p = st.selectbox("🎯 분석 대상 선택", sorted(df_drama['프로그램명'].unique()), key="deep_target")
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
            st.plotly_chart(px.line(p_df, x='회차', y=['수도권 2049', '수도권 가구', '전국 가구'], markers=True), width='stretch')

    with tab5:
        st.subheader("⏱️ 분당 시청률 정밀 분석 (2025~)")
        if df_min is not None:
            c1, c2 = st.columns(2)
            with c1: latest_progs = sorted(df_drama[df_drama['연도'] >= 2025]['프로그램명'].unique()); sel_min_ps = st.multiselect("🎯 프로그램 선택", latest_progs, key="min_ps")
            with c2: min_eps = sorted(df_drama[df_drama['프로그램명'].isin(sel_min_ps)]['회차'].unique()) if sel_min_ps else []; sel_min_es = st.multiselect("🔢 회차 선택", min_eps, key="min_es")
            if sel_min_ps and sel_min_es:
                st.markdown("**📊 분석 지표 선택 (복수 선택 가능)**")
                met_c1, met_c2, met_c3 = st.columns(3); sel_metrics = []
                if met_c1.checkbox("수도권 2049", value=True, key="m_2049"): sel_metrics.append("수도권 2049")
                if met_c2.checkbox("수도권 가구", value=False, key="m_su_hh"): sel_metrics.append("수도권 가구")
                if met_c3.checkbox("전국 가구", value=False, key="m_nat_hh"): sel_metrics.append("전국 가구")
                
                metric_map = {"수도권 2049": ("수도권", "개인2049"), "수도권 가구": ("수도권", "유료방송가구"), "전국 가구": ("National", "유료방송가구")}
                peak_cards = []; fig4 = go.Figure(); chart_data = []
                for p in sel_min_ps:
                    for e in sel_min_es:
                        info = df_drama[(df_drama['프로그램명'] == p) & (df_drama['회차'] == e)]
                        if not info.empty:
                            target_d = "".join(re.findall(r'\d+', str(info.iloc[0]['일자'])))
                            s_t, e_t = str(info.iloc[0]['시작시간']).strip(), str(info.iloc[0]['종료시간']).strip()
                            for m_name in sel_metrics:
                                reg, aud = metric_map[m_name]; matching_col = [c for c in df_min.columns if target_d in "".join(re.findall(r'\d+', str(c))) and reg in c and aud in c]
                                if matching_col:
                                    col = matching_col[0]; df_min['time_key'] = df_min.iloc[:, 3].astype(str).str.split(' - ').str[0]
                                    plot_df = df_min[(df_min['time_key'] >= s_t) & (df_min['time_key'] <= e_t)].copy()
                                    plot_df[col] = pd.to_numeric(plot_df[col].astype(str).str.replace(',',''), errors='coerce').fillna(0)
                                    if not plot_df.empty: chart_data.append({'p': p, 'e': e, 'm': m_name, 'df': plot_df, 'col': col, 'peak': plot_df[col].max()})
                
                m_order = {"수도권 2049": 1, "수도권 가구": 2, "전국 가구": 3}
                chart_data.sort(key=lambda x: (x['e'], m_order.get(x['m'], 4)))
                
                for item in chart_data:
                    p, e, m_name, plot_df, col, pk_v = item['p'], item['e'], item['m'], item['df'], item['col'], item['peak']
                    fig4.add_trace(go.Scatter(x=plot_df['time_key'], y=plot_df[col], mode='lines', name=f"{p} {e}회_{m_name}"))
                    pk_t = plot_df.loc[plot_df[col].idxmax(), 'time_key']; bt_v, bt_t = plot_df[col].min(), plot_df.loc[plot_df[col].idxmin(), 'time_key']
                    peak_cards.append({"label": f"{p} {e}회 {m_name}", "val": pk_v, "time": pk_t})
                    fig4.add_trace(go.Scatter(x=[pk_t], y=[pk_v], mode='markers', marker=dict(color='red', size=10, symbol='triangle-up'), showlegend=False))
                    fig4.add_trace(go.Scatter(x=[bt_t], y=[bt_v], mode='markers', marker=dict(color='blue', size=10, symbol='triangle-down'), showlegend=False))
                
                if peak_cards:
                    st.divider(); cols = st.columns(min(len(peak_cards), 4))
                    for i, c in enumerate(peak_cards):
                        with cols[i % 4]: st.metric(f"🏆 {c['label']} 최고", f"{c['val']:.3f}%", f"⏰ {c['time']}")
                fig4.update_layout(height=500, template="plotly_white", xaxis=dict(title="방송 시간", tickangle=45), hovermode="x unified", legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02))
                st.plotly_chart(fig4, width='stretch')
else:
    st.info("데이터 로딩 중...")