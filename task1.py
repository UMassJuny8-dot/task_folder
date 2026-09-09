import streamlit as st
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
import urllib.request
import os

# ----------------------------------------
# 1. 한글 폰트 및 페이지 설정 (자동 다운로드 방식 적용)
# ----------------------------------------
st.set_page_config(page_title="무역 분석 대시보드", layout="wide")

@st.cache_resource
def set_korean_font():
    font_url = 'https://github.com/googlefonts/nanumgothic/raw/main/fonts/NanumGothic-Regular.ttf'
    font_path = 'NanumGothic.ttf'
    
    # 폰트 파일이 없으면 깃허브에서 다운로드
    if not os.path.exists(font_path):
        urllib.request.urlretrieve(font_url, font_path)
        
    # 다운로드한 폰트를 matplotlib에 적용
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rc('font', family=font_name)
    plt.rcParams['axes.unicode_minus'] = False

# 폰트 설정 함수 실행
set_korean_font()

# ----------------------------------------
# 2. 데이터 로드 및 전처리
# ----------------------------------------
@st.cache_data
def load_data():
    # 원본 파일 로드
    baci_raw = pd.read_csv('baci_85_sample.csv')
    codes = pd.read_csv('country_codes_sample.csv')
    
    # 무역액 기준(v) 대, 중, 소 등급 생성 (데이터의 3분위수 기준)
    baci_raw['무역액등급'] = pd.qcut(baci_raw['v'], q=3, labels=['소', '중', '대'])
    
    # j 컬럼 기준으로 국가명 병합
    df = pd.merge(baci_raw, codes, on='j', how='left')
    return baci_raw, df

baci_raw, df = load_data()

# ----------------------------------------
# 3. 사이드바 (필터) 설정
# ----------------------------------------
st.sidebar.header("🔍 필터 설정")

# 국가 선택 필터
all_countries = df['country_name'].dropna().unique()
selected_countries = st.sidebar.multiselect(
    "국가 선택", 
    options=all_countries,
    default=all_countries
)

# 무역액 등급 선택 필터
selected_grades = st.sidebar.multiselect(
    "무역액 등급 (대/중/소)",
    options=['대', '중', '소'],
    default=['대', '중', '소']
)

# 필터링 적용
filtered_df = df[
    (df['country_name'].isin(selected_countries)) & 
    (df['무역액등급'].isin(selected_grades))
]

# ----------------------------------------
# 4. 메인 화면 출력
# ----------------------------------------

# 1. 타이틀
st.title("📈 무역 분석 대시보드")
st.markdown("---")

# 2. baci_85_sample.csv 결측치 확인
st.subheader("📌 1. 원본 데이터(baci_85_sample.csv) 결측치")
missing_data = baci_raw.isnull().sum().to_frame(name='결측치 개수').T
st.dataframe(missing_data, use_container_width=True)

# 3. 총 거래건수 및 총 수출액(달러)
st.subheader("📌 2. 핵심 지표")
col1, col2 = st.columns(2)
col1.metric(label="총 거래건수", value=f"{len(filtered_df):,} 건")
col2.metric(label="총 수출액 (달러)", value=f"${filtered_df['v'].sum():,.2f}")

# 4. 히트맵 & 등급분포
st.subheader("📌 3. 데이터 시각화")
col3, col4 = st.columns(2)

with col3:
    st.markdown("**국가별/연도별 수출액 히트맵 (상위 8개국)**")
    if not filtered_df.empty:
        # 상위 8개국 추출
        top8_countries = filtered_df.groupby('country_name')['v'].sum().nlargest(8).index
        heat_df = filtered_df[filtered_df['country_name'].isin(top8_countries)]
        heat_pivot = heat_df.pivot_table(index='country_name', columns='t', values='v', aggfunc='sum').fillna(0)
        
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.heatmap(heat_pivot, annot=True, fmt=".0f", cmap='Blues', linewidths=.5, ax=ax)
        st.pyplot(fig)
    else:
        st.info("필터링된 데이터가 없습니다.")

with col4:
    st.markdown("**무역액 등급 분포**")
    if not filtered_df.empty:
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        sns.countplot(data=filtered_df, x='무역액등급', order=['대', '중', '소'], palette='Pastel1', ax=ax2)
        ax2.set_xlabel("등급")
        ax2.set_ylabel("건수")
        st.pyplot(fig2)
    else:
        st.info("필터링된 데이터가 없습니다.")

# 5. 상위 5개국 * 무역액 등급 교차표 (탭 적용)
st.subheader("📌 4. 상위 5개국 × 무역액 등급 교차표")
if not filtered_df.empty:
    top5_countries = filtered_df.groupby('country_name')['v'].sum().nlargest(5).index
    cross_df = filtered_df[filtered_df['country_name'].isin(top5_countries)]
    
    # 탭 구성 (원본건수 / 정규화비율)
    tab1, tab2 = st.tabs(["원본건수", "정규화비율"])
    
    with tab1:
        cross_raw = pd.crosstab(cross_df['country_name'], cross_df['무역액등급'])
        st.dataframe(cross_raw, use_container_width=True)
        
    with tab2:
        cross_norm = pd.crosstab(cross_df['country_name'], cross_df['무역액등급'], normalize='index')
        st.dataframe(cross_norm.style.format("{:.2%}"), use_container_width=True)
else:
    st.info("조건에 맞는 데이터가 부족하여 교차표를 생성할 수 없습니다.")