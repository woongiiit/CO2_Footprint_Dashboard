import os
import zipfile
import pandas as pd
import numpy as np

def generate_tourist_spending_data():
    # 1. 랜덤 시트 고정 (재현성 확보)
    np.random.seed(42)

    # 2. 기준 필드 파일 로드 (파일명이 다를 경우 수정 필요)
    sigungu_file = '시군구 필드.csv'
    upjong_file = '업종 필드.csv'

    if not os.path.exists(sigungu_file) or not os.path.exists(upjong_file):
        print(f"오류: '{sigungu_file}' 또는 '{upjong_file}' 파일이 현재 폴더에 존재하지 않습니다.")
        return

    sigungu_df = pd.read_csv(sigungu_file)
    upjong_df = pd.read_csv(upjong_file)

    # 시군구 명 결합 (광역 + 기초) 및 업종 중분류 리스트 추출
    sigungu_list = (sigungu_df['광역지자체 명'] + " " + sigungu_df['기초지자체 명']).tolist()
    upjong_list = upjong_df['중분류'].unique().tolist()

    # 25년 5월 ~ 26년 4월 기간 설정
    months = [
        '202505', '202506', '202507', '202508', '202509', '202510',
        '202511', '202512', '202601', '202602', '202603', '202604'
    ]

    # 3. 현실적 데이터 매핑을 위한 특수 지역 정의
    coastal_keywords = ['강릉', '속초', '동해', '삼척', '고성', '양양', '해운대', '기장', '수영', '남구', '영도', '사하', '강화', '옹진', '연수', '울주', '여수', '목포', '순천', '광양', '고흥', '보성', '장흥', '강진', '해남', '영암', '무안', '함평', '영광', '완도', '진도', '신안', '창원', '통영', '사천', '거제', '남해', '하동', '포항', '경주시', '영덕', '울진', '울릉', '서귀포', '제주시', '당진', '서산', '보령', '태안', '서천', '군산', '김제', '부안', '고창']
    airports = [('인천광역시', '중구'), ('서울특별시', '강서구'), ('부산광역시', '강서구'), ('제주특별자치도', '제주시'), ('대구광역시', '동구'), ('충청북도', '청주시'), ('전라남도', '여수시'), ('울산광역시', '북구'), ('광주광역시', '광산구'), ('경상북도', '포항시')]
    ski_resorts = [('강원특별자치도', '평창군'), ('강원특별자치도', '정선군'), ('강원특별자치도', '홍천군'), ('강원특별자치도', '춘천시'), ('강원특별자치도', '원주시'), ('강원특별자치도', '횡성군'), ('경기도', '용인시'), ('경기도', '광주시'), ('경기도', '남양주시'), ('경기도', '이천시'), ('경기도', '포천시'), ('전북특별자치도', '무주군'), ('경상남도', '양산시')]
    duty_free_regions = ['서울특별시', '인천광역시', '부산광역시', '제주특별자치도']

    # 4. 업종별 기본 소비 규모 산정 함수
    def get_base_amount(gwangyeok, gicho, upjong):
        base_cats = {
            '일반외식업': 4000000000, '대형쇼핑몰': 1500000000, '기타관광쇼핑': 800000000,
            '제과음료업': 600000000, '호텔': 1000000000, '콘도': 400000000,
            '캠핑장/펜션': 250000000, '골프장': 500000000, '관광유원시설': 300000000,
            '문화서비스': 150000000, '레저용품쇼핑': 200000000, '면세점': 10000000,
            '스키장': 1000000, '여행업': 80000000, '렌터카': 100000000,
            '수상운송': 5000000, '육상운송': 120000000, '항공운송': 1000000,
            '뷰티': 200000000, '의료관광': 50000000, '기타숙박': 200000000, '기타레저': 150000000
        }
        
        amount = base_cats.get(upjong, 100000000)
        
        # 지역 거점별 기본 규모 가중치
        reg_scale = 1.0
        if gwangyeok == '서울특별시':
            reg_scale = 4.0
            if gicho in ['강남구', '중구', '서초구', '송파구', '마포구', '종로구']:
                reg_scale = 8.0
        elif gwangyeok == '경기도':
            reg_scale = 2.5
            if gicho in ['수원시', '성남시', '고양시', '용인시']:
                reg_scale = 4.5
        elif gwangyeok == '부산광역시':
            reg_scale = 2.5
            if gicho in ['해운대구', '진구', '중구']:
                reg_scale = 5.0
        elif gwangyeok == '제주특별자치도':
            reg_scale = 4.0
        elif gwangyeok in ['인천광역시', '대구광역시', '대전광역시', '광주광역시', '울산광역시']:
            reg_scale = 1.8
        elif gwangyeok in ['강원특별자치도']:
            reg_scale = 2.0
            if gicho in ['강릉시', '속초시', '원주시', '춘천시']:
                reg_scale = 3.5
        else:
            reg_scale = 1.0
            
        amount *= reg_scale
        
        # 업종별 특수 입지 조건 반영
        if upjong == '면세점':
            if gwangyeok in duty_free_regions and gicho in ['중구', '강남구', '해운대구', '제주시', '서귀포시']:
                amount = 3000000000 * reg_scale
            elif (gwangyeok, gicho) in airports:
                amount = 5000000000 * reg_scale
            else:
                amount = np.random.randint(0, 500000)
                
        elif upjong == '항공운송':
            if (gwangyeok, gicho) in airports:
                amount = 4000000000 * reg_scale
            else:
                amount = np.random.randint(0, 100000)
                
        elif upjong == '스키장':
            if (gwangyeok, gicho) in ski_resorts:
                amount = 1500000000 * reg_scale
            else:
                amount = 0
                
        elif upjong == '수상운송':
            is_coastal = any(k in gicho for k in coastal_keywords) or gwangyeok == '제주특별자치도'
            if is_coastal:
                amount = 400000000 * reg_scale
            else:
                amount = np.random.randint(100000, 2000000)
                
        elif upjong == '렌터카':
            if gwangyeok == '제주특별자치도':
                amount = 2500000000
                
        if upjong in ['콘도', '캠핑장/펜션']:
            if gwangyeok in ['강원특별자치도', '제주특별자치도'] or any(k in gicho for k in ['가평', '양평', '강화', '경주시']):
                amount *= 3.0
            elif gwangyeok in ['서울특별시', '대구광역시', '대전광역시', '광주광역시']:
                amount *= 0.1
                
        if upjong in ['의료관광', '뷰티']:
            if gwangyeok == '서울특별시' and gicho in ['강남구', '서초구']:
                amount *= 5.0
                
        # 지역 기본 난수 반영
        amount *= np.random.uniform(0.85, 1.15)
        return int(amount)

    # 기본 베이스 금액 사전 연산
    print("기본 지역별 소비 베이스를 구축 중입니다...")
    base_amounts_dict = {}
    for idx, row in sigungu_df.iterrows():
        gwangyeok = row['광역지자체 명']
        gicho = row['기초지자체 명']
        sig_name = f"{gwangyeok} {gicho}"
        base_amounts_dict[sig_name] = {}
        for upjong in upjong_list:
            base_amounts_dict[sig_name][upjong] = get_base_amount(gwangyeok, gicho, upjong)

    # 5. 월별 업종 계절성 지수 정의 (12개 값: 5월~다음해 4월 순)
    seasonal_multipliers = {
        '스키장': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 3.5, 5.0, 4.0, 0.2, 0.0],
        '캠핑장/펜션': [1.2, 1.3, 2.3, 2.6, 1.2, 1.4, 0.6, 0.7, 0.6, 0.5, 0.7, 1.0],
        '수상운송': [1.2, 1.5, 2.5, 2.8, 1.2, 1.1, 0.4, 0.3, 0.3, 0.4, 0.6, 1.0],
        '콘도': [1.2, 1.1, 1.9, 2.2, 1.1, 1.3, 0.8, 1.6, 1.5, 1.2, 0.9, 1.1],
        '호텔': [1.2, 1.1, 1.8, 2.1, 1.1, 1.2, 0.9, 1.7, 1.4, 1.2, 0.9, 1.1],
        '기타숙박': [1.1, 1.1, 1.6, 1.8, 1.1, 1.2, 0.8, 1.3, 1.2, 1.1, 0.9, 1.0],
        '골프장': [1.5, 1.4, 0.9, 0.8, 1.4, 1.6, 0.9, 0.3, 0.2, 0.4, 1.1, 1.4],
        '관광유원시설': [1.6, 1.3, 1.5, 1.8, 1.2, 1.5, 0.7, 0.8, 0.8, 0.8, 1.0, 1.4],
        '면세점': [1.2, 1.1, 1.2, 1.2, 1.3, 1.2, 1.0, 1.4, 1.2, 1.1, 0.9, 1.1],
        '대형쇼핑몰': [1.2, 1.0, 1.1, 1.1, 1.3, 1.1, 1.0, 1.4, 1.2, 1.1, 0.9, 1.1],
        '기타관광쇼핑': [1.2, 1.0, 1.1, 1.1, 1.2, 1.1, 1.0, 1.3, 1.1, 1.1, 0.9, 1.1],
        '레저용품쇼핑': [1.3, 1.1, 1.2, 1.1, 1.2, 1.3, 0.8, 0.7, 0.7, 0.8, 1.1, 1.3],
        '일반외식업': [1.2, 1.1, 1.2, 1.3, 1.1, 1.1, 0.9, 1.3, 1.1, 1.0, 1.0, 1.1],
        '제과음료업': [1.3, 1.2, 1.3, 1.4, 1.1, 1.1, 0.9, 1.2, 1.0, 1.0, 1.1, 1.2],
        '항공운송': [1.3, 1.1, 1.8, 2.0, 1.3, 1.4, 0.9, 1.4, 1.5, 1.3, 1.0, 1.2],
        '렌터카': [1.3, 1.2, 2.0, 2.2, 1.2, 1.4, 0.8, 1.1, 1.2, 1.1, 0.9, 1.2],
        '여행업': [1.3, 1.1, 1.6, 1.8, 1.2, 1.3, 0.9, 1.4, 1.5, 1.3, 1.0, 1.2],
        '육상운송': [1.2, 1.1, 1.2, 1.3, 1.3, 1.2, 0.9, 1.1, 1.1, 1.1, 1.0, 1.1],
        '문화서비스': [1.3, 1.1, 1.1, 1.2, 1.1, 1.2, 0.9, 1.3, 1.1, 1.0, 1.0, 1.2],
        '기타레저': [1.3, 1.1, 1.3, 1.4, 1.2, 1.2, 0.8, 0.8, 0.8, 0.8, 1.0, 1.2],
        '뷰티': [1.1, 1.1, 1.1, 1.1, 1.0, 1.1, 1.0, 1.2, 1.1, 1.0, 1.0, 1.1],
        '의료관광': [1.1, 1.1, 1.2, 1.2, 1.0, 1.0, 1.0, 1.2, 1.2, 1.0, 1.0, 1.1]
    }

    generated_files = []

    # 6. 월별 파일 생성 루프
    print("월별 데이터를 생성 중입니다...")
    for m_idx, month in enumerate(months):
        data = []
        for sig_name in sigungu_list:
            row_data = {'시군구': sig_name}
            for upjong in upjong_list:
                base = base_amounts_dict[sig_name][upjong]
                multiplier = seasonal_multipliers[upjong][m_idx]
                # 매월 발생하는 상하 4%의 미세 노이즈 반영
                noise = np.random.uniform(0.96, 1.04)
                val = int(base * multiplier * noise)
                row_data[upjong] = val
            data.append(row_data)
        
        df_month = pd.DataFrame(data)
        filename = f'관광소비지출_{month}.csv'
        
        # 한글 깨짐 방지를 위해 utf-8-sig 인코딩 적용
        df_month.to_csv(filename, index=False, encoding='utf-8-sig')
        generated_files.append(filename)
        print(f" - 생성 완료: {filename}")

    # 7. 하나의 zip 파일로 압축 후 개별 CSV 삭제
    zip_name = '관광소비지출_데이터_202505_202604.zip'
    print(f"파일들을 {zip_name}으로 압축하는 중입니다...")
    with zipfile.ZipFile(zip_name, 'w') as zipf:
        for file in generated_files:
            zipf.write(file)
            os.remove(file) # 로컬 디렉토리 정리를 위해 원본 개별 csv 삭제

    print(f"\n[성공] 총 {len(generated_files)}개의 월별 파일이 성공적으로 '{zip_name}'으로 압축되었습니다.")

if __name__ == "__main__":
    # 실행에 필요한 패키지 체크 안내
    try:
        import pandas
        import numpy
    except ImportError:
        print("필수 라이브러리가 없습니다. 터미널에 다음 명령어를 입력하세요: pip install pandas numpy")
    else:
        generate_tourist_spending_data()