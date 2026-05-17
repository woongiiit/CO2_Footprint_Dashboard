import os
import pandas as pd

def calculate_tourism_carbon_footprint(input_filename, output_filename):
    """
    관광소비지출 데이터를 기반으로 시군구별/업종별 탄소발자국을 산정하는 함수
    
    :param input_filename: 관광소비지출 CSV 파일명 (예: '관광소비지출_202505.csv')
    :param output_filename: 계산 결과가 저장될 CSV 파일명
    """
    # 1. 파일 존재 여부 확인
    if not os.path.exists(input_filename):
        print(f"오류: 입력 파일 '{input_filename}'을 찾을 수 없습니다.")
        return

    # 2. 데이터 불러오기
    print(f"'{input_filename}' 데이터를 로드하는 중...")
    df = pd.read_csv(input_filename)

    # 3. 만원 지출당 탄소배출계수 설정 (단위: kg CO2eq / 만원)
    # 경제확장 투입산출 모델(EEIO) 가이드라인 기반 가중치
    emission_factors_per_10k = {
        '항공운송': 3.50,
        '수상운송': 2.80,
        '렌터카': 2.20,
        '육상운송': 1.50,
        '일반외식업': 1.60,
        '제과음료업': 1.20,
        '호텔': 1.40,
        '콘도': 1.20,
        '스키장': 1.80,
        '기타숙박': 0.90,
        '캠핑장/펜션': 0.70,
        '대형쇼핑몰': 0.85,
        '면세점': 0.80,
        '레저용품쇼핑': 0.75,
        '기타관광쇼핑': 0.70,
        '골프장': 0.65,
        '관광유원시설': 0.60,
        '기타레저': 0.50,
        '문화서비스': 0.40,
        '의료관광': 0.45,
        '뷰티': 0.35,
        '여행업': 0.15
    }

    # 4. 수식 적용을 위해 원(KRW) 단위 배출계수로 변환 (계수 / 10,000)
    ef_per_won = {upjong: factor / 10000.0 for upjong, factor in list(emission_factors_per_10k.items())}

    # 5. 계산용 복사본 데이터프레임 생성
    result_df = pd.DataFrame()
    result_df['시군구'] = df['시군구']

    # 6. 업종별 탄소발자국 산정 (수식: 지출액 * 원당 배출계수)
    print("업종별 탄소발자국 산정 수식을 적용 중입니다...")
    carbon_col_names = []
    
    for upjong, ef in list(ef_per_won.items()):
        if upjong in df.columns:
            col_name = f'{upjong}_탄소발자국(kg_CO2eq)'
            # 각 행(지역)의 지출 데이터에 배출계수를 곱해 개별 배출량 계산
            result_df[col_name] = df[upjong] * ef
            carbon_col_names.append(col_name)
        else:
            print(f"경고: 입력 파일에 '{upjong}' 업종 컬럼이 존재하지 않습니다. 건너뜁니다.")

    # 7. 종합 탄소발자국 지표 생성 (총합 계산 및 톤 단위 변환)
    # 총 탄소발자국(kg) = 모든 업종별 탄소발자국의 합
    result_df['총_탄소발자국(kg_CO2eq)'] = result_df[carbon_col_names].sum(axis=1)
    
    # 총 탄소발자국(t) = 총 탄소발자국(kg) / 1,000
    result_df['총_탄소발자국(t_CO2eq)'] = result_df['총_탄소발자국(kg_CO2eq)'] / 1000.0

    # 8. 소수점 둘째 자리까지 반올림 정렬
    metric_cols = carbon_col_names + ['총_탄소발자국(kg_CO2eq)', '총_탄소발자국(t_CO2eq)']
    result_df[metric_cols] = result_df[metric_cols].round(2)

    # 9. 결과 파일 저장 (한글 깨짐 방지를 위해 utf-8-sig 사용)
    result_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
    print(f"\n[성공] 탄소발자국 산정이 완료되었습니다!")
    print(f"결과 파일 저장 경로: {output_filename}")
    
    # 데이터 요약 미리보기 출력
    print("\n--- 상위 5개 지역 산정 결과 요약 (t CO2eq) ---")
    print(result_df[['시군구', '총_탄소발자국(t_CO2eq)']].head())


if __name__ == "__main__":
    # 실행할 입력 파일명과 내보낼 파일명 설정
    input_file = '관광소비지출_202505.csv'
    output_file = '관광탄소발자국_산정결과_202505.csv'
    
    calculate_tourism_carbon_footprint(input_file, output_file)