import streamlit as st
import json
import os
import hashlib
import subprocess
import tempfile
import time
import re
import matplotlib
matplotlib.use("Agg")  # 🔧 반드시 추가해야 Streamlit 등 서버 환경에서 오류 안남
import matplotlib.pyplot as plt


# streamlit-ace import (설치되지 않았을 경우 대비)
try:
    from streamlit_ace import st_ace
    ACE_AVAILABLE = True
except ImportError:
    ACE_AVAILABLE = False

# 페이지 설정
st.set_page_config(
    page_title="스파르타 QA/QC",
    page_icon="💻",
    layout="wide"
)

# 사용자 데이터 파일 경로
USER_DATA_FILE = "users.json"
PROBLEMS_FILE = "problems.json"
SUBMISSIONS_FILE = "submissions.json"

# 관리자 계정 설정
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin1234"

def load_problems():
    """문제 데이터 로드"""
    if os.path.exists(PROBLEMS_FILE):
        with open(PROBLEMS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    # 기본 문제 데이터
    default_problems = {
        "1": {
            "title": "두 수의 합",
            "description": """두 정수 a, b를 입력받아 a + b를 출력하는 프로그램을 작성하세요.

**입력**
첫 번째 줄에 정수 a, b가 주어집니다. (1 ≤ a, b ≤ 1000)

**출력**
a + b를 출력하세요.

**예제**
- 입력: 1 2
- 출력: 3""",
            "difficulty": "쉬움",
            "test_cases": [
                {"input": "1 2", "output": "3"},
                {"input": "5 7", "output": "12"},
                {"input": "10 20", "output": "30"}
            ]
        },
        "2": {
            "title": "최댓값 찾기",
            "description": """n개의 정수가 주어졌을 때, 그 중 최댓값을 찾는 프로그램을 작성하세요.

**입력**
첫 번째 줄에 정수의 개수 n이 주어집니다. (1 ≤ n ≤ 100)
두 번째 줄에 n개의 정수가 공백으로 구분되어 주어집니다.

**출력**
최댓값을 출력하세요.

**예제**
- 입력: 
  3
  1 5 3
- 출력: 5""",
            "difficulty": "보통",
            "test_cases": [
                {"input": "3\n1 5 3", "output": "5"},
                {"input": "5\n10 2 8 1 9", "output": "10"},
                {"input": "1\n42", "output": "42"}
            ]
        },
        "3": {
            "title": "매출 데이터 시각화",
            "description": """주어진 매출 데이터를 pandas DataFrame으로 만들고, matplotlib을 사용해 막대 그래프를 그리는 프로그램을 작성하세요.

**입력**
첫 번째 줄에 월의 개수 n이 주어집니다. (1 ≤ n ≤ 12)
다음 n줄에 걸쳐 월 이름과 매출액이 공백으로 구분되어 주어집니다.

**출력**
- 첫 번째 줄: DataFrame의 모양 (행, 열) - 예: (3, 2)
- 두 번째 줄: 총 매출액의 합
- 세 번째 줄: 평균 매출액 (소수점 둘째 자리에서 반올림)
- 네 번째 줄: "그래프 생성 완료"

**예제**
- 입력:
  3
  1월 1000000
  2월 1500000
  3월 1200000
- 출력:
  (3, 2)
  3700000
  1233333.33
  그래프 생성 완료""",
            "difficulty": "어려움",
            "test_cases": [
                {
                    "input": "3\n1월 1000000\n2월 1500000\n3월 1200000",
                    "output": "(3, 2)\n3700000\n1233333.33\n그래프 생성 완료"
                },
                {
                    "input": "4\n4월 800000\n5월 900000\n6월 1100000\n7월 950000",
                    "output": "(4, 2)\n3750000\n937500.00\n그래프 생성 완료"
                },
                {
                    "input": "2\n8월 2000000\n9월 1800000",
                    "output": "(2, 2)\n3800000\n1900000.00\n그래프 생성 완료"
                }
            ]
        }
    }
    save_problems(default_problems)
    return default_problems

def save_problems(problems):
    """문제 데이터 저장"""
    with open(PROBLEMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(problems, f, ensure_ascii=False, indent=2)

def load_submissions():
    """제출 기록 로드"""
    if os.path.exists(SUBMISSIONS_FILE):
        with open(SUBMISSIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_submissions(submissions):
    """제출 기록 저장"""
    with open(SUBMISSIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(submissions, f, ensure_ascii=False, indent=2)

def save_submission_result(username, problem_id, code, passed_tests, total_tests, success):
    """제출 결과 저장"""
    submissions = load_submissions()
    
    if username not in submissions:
        submissions[username] = []
    
    submission = {
        "problem_id": problem_id,
        "code": code,
        "passed_tests": passed_tests,
        "total_tests": total_tests,
        "success": success,
        "timestamp": time.time(),
        "date": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    submissions[username].append(submission)
    save_submissions(submissions)
    
    # 사용자 정보도 업데이트
    users = load_users()
    if username in users:
        if 'solved_problems' not in users[username]:
            users[username]['solved_problems'] = []
        if 'total_submissions' not in users[username]:
            users[username]['total_submissions'] = 0
        
        users[username]['total_submissions'] += 1
        
        if success and problem_id not in users[username]['solved_problems']:
            users[username]['solved_problems'].append(problem_id)
        
        save_users(users)

def load_users():
    """사용자 데이터 로드"""
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(users):
    """사용자 데이터 저장"""
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def hash_password(password):
    """비밀번호 해시화"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    """회원가입"""
    # 관리자 아이디는 회원가입 불가
    if username == ADMIN_USERNAME:
        return False, "사용할 수 없는 아이디입니다."
    
    users = load_users()
    
    if username in users:
        return False, "이미 존재하는 아이디입니다."
    
    users[username] = {
        "password": hash_password(password),
        "created_at": str(time.time())
    }
    
    save_users(users)
    return True, "회원가입이 완료되었습니다!"

def login_user(username, password):
    """로그인"""
    # 관리자 계정 체크 (해시화하지 않고 직접 비교)
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return True, "관리자 로그인 성공!"
    
    # 일반 사용자 체크
    users = load_users()
    
    if username not in users:
        return False, "존재하지 않는 아이디입니다."
    
    if users[username]["password"] != hash_password(password):
        return False, "비밀번호가 틀렸습니다."
    
    return True, "로그인 성공!"

def is_admin():
    """현재 사용자가 관리자인지 확인"""
    return st.session_state.get('username') == ADMIN_USERNAME

def run_code(code, test_input):
    """사용자 코드 실행 - 인코딩 문제 해결 및 차트 표시"""
    try:
        # 인코딩 환경변수 설정
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['LANG'] = 'ko_KR.UTF-8'  # 리눅스/맥용
        
        # 임시 파일에 코드 저장 (UTF-8 인코딩 명시)
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.py', 
            delete=False, 
            encoding='utf-8'
        ) as f:
            # UTF-8 인코딩 헤더 추가
            f.write('# -*- coding: utf-8 -*-\n')
            f.write('import sys\n')
            f.write('import os\n')
            # Python 버전에 따른 인코딩 설정
            f.write('try:\n')
            f.write('    sys.stdout.reconfigure(encoding="utf-8")\n')  # Python 3.7+
            f.write('    sys.stderr.reconfigure(encoding="utf-8")\n')
            f.write('except:\n')
            f.write('    pass\n')  # 이전 버전에서는 무시
            f.write('\n')
            
            # matplotlib 설정 추가 (차트 저장을 위해)
            if 'matplotlib' in code or 'plt' in code:
                f.write('import matplotlib\n')
                f.write('matplotlib.use("Agg")  # GUI 없이 차트 생성\n')
                f.write('import matplotlib.pyplot as plt\n')
                f.write('plt.rcParams["font.family"] = "DejaVu Sans"  # 한글 폰트 설정\n')
                f.write('\n')
            
            f.write(code)
            temp_file = f.name
        
        # 코드 실행
        process = subprocess.run(
            ['python', '-u', temp_file],  # -u 옵션: unbuffered output
            input=test_input,
            capture_output=True,
            text=True,
            timeout=10,  # 차트 생성 시간을 고려해 10초로 증가
            encoding='utf-8',
            errors='replace',  # 인코딩 에러 시 대체 문자 사용
            env=env
        )
        
        # 차트 파일 확인 및 반환
        chart_files = []
        temp_dir = os.path.dirname(temp_file)
        
        # 일반적인 차트 파일명들 확인
        possible_chart_names = [
            'sales_chart.png', 'chart.png', 'plot.png', 'graph.png',
            'figure.png', 'visualization.png'
        ]
        
        for chart_name in possible_chart_names:
            chart_path = os.path.join(temp_dir, chart_name)
            if os.path.exists(chart_path):
                chart_files.append(chart_path)
        
        # 현재 디렉토리에서도 확인
        for chart_name in possible_chart_names:
            if os.path.exists(chart_name):
                chart_files.append(chart_name)
        
        # 임시 파일 삭제
        try:
            os.unlink(temp_file)
        except:
            pass  # 파일 삭제 실패해도 무시
        
        if process.returncode == 0:
            return True, process.stdout.strip(), None, chart_files
        else:
            error_msg = process.stderr.strip()
            line_number = extract_line_number(error_msg, temp_file)
            return False, error_msg, line_number, []
            
    except subprocess.TimeoutExpired:
        # 타임아웃 시 임시 파일 정리
        try:
            os.unlink(temp_file)
        except:
            pass
        return False, "시간 초과 (10초)", None, []
    except Exception as e:
        return False, f"실행 오류: {str(e)}", None, []

def extract_line_number(error_msg, temp_file):
    """에러 메시지에서 줄 번호 추출 - 인코딩 헤더 보정"""
    try:
        patterns = [
            rf'File "{re.escape(temp_file)}", line (\d+)',
            r'line (\d+)',
            r'Line (\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_msg)
            if match:
                line_num = int(match.group(1))
                # 우리가 추가한 헤더 줄들을 빼고 실제 사용자 코드 줄 번호 계산
                # 추가한 줄: encoding 헤더(1줄) + import sys(1줄) + try-except(5줄) + 빈줄(1줄) = 8줄
                actual_line = max(1, line_num - 8)
                return actual_line
        return None
    except:
        return None

def get_default_code(problem_id):
    """문제별 기본 코드 템플릿 - 인코딩 안전"""
    templates = {
        "1": """# 두 수의 합
# 입력: 두 정수 a, b  
# 출력: a + b

a, b = map(int, input().split())
print(a + b)""",
        "2": """# 최댓값 찾기
# 입력: 정수의 개수 n, n개의 정수
# 출력: 최댓값

n = int(input())
numbers = list(map(int, input().split()))
print(max(numbers))""",
        "3": """# 매출 데이터 시각화
# pandas와 matplotlib 라이브러리 사용
# 입력: 월의 개수 n, n개의 월과 매출액
# 출력: DataFrame 모양, 총매출, 평균매출, 그래프생성완료

import pandas as pd
import matplotlib.pyplot as plt

# 입력 받기
n = int(input())
months = []
sales = []

for i in range(n):
    line = input().split()
    month = line[0]
    sale = int(line[1])
    months.append(month)
    sales.append(sale)

# DataFrame 생성
df = pd.DataFrame({
    '월': months,
    '매출액': sales
})

# 결과 출력
print(df.shape)
print(df['매출액'].sum())
print(f"{df['매출액'].mean():.2f}")

# 그래프 생성 (화면에 표시하지 않고 파일로 저장)
plt.figure(figsize=(10, 6))
plt.bar(df['월'], df['매출액'])
plt.title('월별 매출 현황')
plt.xlabel('월')
plt.ylabel('매출액')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('sales_chart.png')
plt.close()  # 창이 열리지 않도록

print("그래프 생성 완료")""",
        "default": """# 여기에 코드를 작성하세요
# input() 함수로 입력을 받고
# print() 함수로 결과를 출력하세요

"""
    }
    return templates.get(problem_id, templates["default"])

def main_page():
    """메인 페이지 (로그인 후)"""
    if is_admin():
        st.title("🔧 관리자 페이지 - 스파르타 QA/QC")
        st.success(f"관리자님 환영합니다! ({st.session_state.username})")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📝 문제 관리", use_container_width=True):
                st.session_state.page = "admin_problems"
                st.rerun()
            
            if st.button("👥 사용자 관리", use_container_width=True):
                st.session_state.page = "admin_users"
                st.rerun()
        
        with col2:
            if st.button("📊 통계 보기", use_container_width=True):
                st.session_state.page = "admin_stats"
                st.rerun()
            
            if st.button("🚪 로그아웃", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
    else:
        st.title("🎉 스파르타 QA/QC에 오신 것을 환영합니다!")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            st.success(f"안녕하세요, {st.session_state.username}님!")
            
            if st.button("📝 문제 풀기", use_container_width=True):
                st.session_state.page = "problems"
                st.rerun()
            
            if st.button("📊 내 통계", use_container_width=True):
                st.session_state.page = "user_stats"
                st.rerun()
            
            if st.button("🚪 로그아웃", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

def problems_page():
    """문제 목록 페이지"""
    st.title("📝 문제 목록")
    
    problems = load_problems()
    
    st.markdown("---")
    
    for problem_id, problem in problems.items():
        with st.expander(f"**{problem_id}번. {problem['title']}** - {problem['difficulty']}"):
            st.markdown(problem['description'])
            
            if st.button(f"풀어보기", key=f"solve_{problem_id}"):
                st.session_state.current_problem = problem_id
                st.session_state.page = "solve"
                st.rerun()
    
    if st.button("🏠 메인으로 돌아가기"):
        st.session_state.page = "main"
        st.rerun()

def solve_page():
    """문제 풀이 페이지"""
    if 'current_problem' not in st.session_state:
        st.error("선택된 문제가 없습니다.")
        if st.button("문제 목록으로"):
            st.session_state.page = "problems"
            st.rerun()
        return
    
    problems = load_problems()
    problem_id = st.session_state.current_problem
    problem = problems.get(problem_id)
    
    if not problem:
        st.error("문제를 찾을 수 없습니다.")
        return
    
    # 레이아웃: 왼쪽 문제, 오른쪽 코드 에디터
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header(f"📋 {problem_id}번. {problem['title']}")
        st.markdown(f"**난이도:** {problem['difficulty']}")
        st.markdown("---")
        st.markdown(problem['description'])
        
        # 네비게이션 버튼들
        st.markdown("---")
        if st.button("📝 문제 목록"):
            st.session_state.page = "problems"
            st.rerun()
        
        if st.button("🏠 메인으로"):
            st.session_state.page = "main"
            st.rerun()
    
    with col2:
        st.header("💻 코드 작성")
        
        # 에디터 설정 옵션
        with st.expander("⚙️ 에디터 설정"):
            if ACE_AVAILABLE:
                col_theme, col_font, col_wrap = st.columns(3)
                
                with col_theme:
                    theme = st.selectbox(
                        "테마",
                        ["monokai", "github", "tomorrow", "kuroir", "twilight", "xcode", "textmate", "solarized_dark", "solarized_light"],
                        index=0
                    )
                
                with col_font:
                    font_size = st.slider("폰트 크기", 12, 24, 14)
                
                with col_wrap:
                    wrap_enabled = st.checkbox("자동 줄바꿈", value=True)
            else:
                st.info("고급 에디터 기능을 사용하려면 'pip install streamlit-ace'를 실행하세요.")
                theme = "monokai"
                font_size = 14
                wrap_enabled = True
        
        # 코드 에디터 세션 상태 초기화
        if f'code_content_{problem_id}' not in st.session_state:
            st.session_state[f'code_content_{problem_id}'] = get_default_code(problem_id)
        
        # 에러 표시 상태
        error_line = st.session_state.get(f'error_line_{problem_id}', None)
        
        if ACE_AVAILABLE:
            # Ace 코드 에디터
            code = st_ace(
                value=st.session_state[f'code_content_{problem_id}'],
                language='python',
                theme=theme,
                key=f"code_editor_{problem_id}",
                height=350,
                auto_update=True,
                font_size=font_size,
                wrap=wrap_enabled,
                annotations=st.session_state.get(f'code_annotations_{problem_id}', []),
                markers=st.session_state.get(f'code_markers_{problem_id}', [])
            )
        else:
            # 기본 텍스트 에디터
            code = st.text_area(
                "Python 코드를 작성하세요:",
                value=st.session_state[f'code_content_{problem_id}'],
                height=350,
                key=f"code_editor_{problem_id}",
                help="예: print(int(input()) + int(input()))"
            )
        
        # 에러 위치 표시 (ACE가 없을 때)
        if not ACE_AVAILABLE and error_line:
            st.error(f"🔍 에러 위치: {error_line}번째 줄")
            code_lines = code.split('\n')
            if error_line <= len(code_lines):
                st.code(f">>> {code_lines[error_line-1]}", language='python')
        
        # 코드가 변경되면 세션 상태 업데이트
        if code != st.session_state[f'code_content_{problem_id}']:
            st.session_state[f'code_content_{problem_id}'] = code
            # 코드 변경시 이전 에러 표시 제거
            if f'error_line_{problem_id}' in st.session_state:
                del st.session_state[f'error_line_{problem_id}']
            if f'code_annotations_{problem_id}' in st.session_state:
                del st.session_state[f'code_annotations_{problem_id}']
            if f'code_markers_{problem_id}' in st.session_state:
                del st.session_state[f'code_markers_{problem_id}']
        
        # 유틸리티 버튼들
        col_clear, col_template, col_copy = st.columns(3)
        
        with col_clear:
            if st.button("🗑️ 코드 초기화", key=f"clear_{problem_id}"):
                st.session_state[f'code_content_{problem_id}'] = ""
                st.rerun()
        
        with col_template:
            if st.button("📝 템플릿 불러오기", key=f"template_{problem_id}"):
                st.session_state[f'code_content_{problem_id}'] = get_default_code(problem_id)
                st.rerun()
        
        with col_copy:
            if st.button("📋 코드 복사", key=f"copy_{problem_id}"):
                st.code(code, language='python')
                st.info("위 코드를 복사하세요!")
        
        st.markdown("---")
        
        # 실행 버튼들
        col_run, col_submit = st.columns(2)
        
        with col_run:
            if st.button("🧪 테스트 실행", use_container_width=True):
                if code.strip():
                    test_case = problem['test_cases'][0]  # 첫 번째 테스트 케이스로 테스트
                    success, output, error_line, chart_files = run_code(code, test_case['input'])
                    
                    st.subheader("실행 결과")
                    if success:
                        st.success("✅ 실행 성공!")
                        st.code(f"입력: {test_case['input']}")
                        st.code(f"출력: {output}")
                        st.code(f"예상: {test_case['output']}")
                        
                        # 차트 파일이 있으면 표시
                        if chart_files:
                            st.subheader("📊 생성된 차트")
                            for chart_file in chart_files:
                                try:
                                    st.image(chart_file, caption=f"생성된 차트: {os.path.basename(chart_file)}")
                                    st.success(f"🎨 차트가 성공적으로 생성되었습니다: {os.path.basename(chart_file)}")
                                    # 차트 파일 정리
                                    try:
                                        os.unlink(chart_file)
                                    except:
                                        pass
                                except Exception as e:
                                    st.error(f"차트 표시 중 오류: {str(e)}")
                        
                        if output == test_case['output']:
                            st.success("🎉 첫 번째 테스트 케이스 통과!")
                        else:
                            st.warning("❌ 출력이 예상과 다릅니다.")
                    else:
                        st.error("❌ 실행 실패!")
                        st.code(output)
                        
                        # 에러 위치 표시
                        if error_line:
                            st.error(f"🔍 에러 위치: {error_line}번째 줄")
                            
                            # 에러 위치 저장
                            st.session_state[f'error_line_{problem_id}'] = error_line
                            
                            if ACE_AVAILABLE:
                                # 에러 줄 하이라이트를 위한 annotation 설정
                                st.session_state[f'code_annotations_{problem_id}'] = [{
                                    "row": error_line - 1,  # 0-based index
                                    "column": 0,
                                    "text": "에러 발생",
                                    "type": "error"
                                }]
                                
                                # 에러 줄 마커 설정
                                st.session_state[f'code_markers_{problem_id}'] = [{
                                    "startRow": error_line - 1,
                                    "startCol": 0,
                                    "endRow": error_line - 1,
                                    "endCol": 100,
                                    "className": "error-marker",
                                    "type": "background"
                                }]
                            
                            st.rerun()
                else:
                    st.warning("코드를 입력해주세요.")
        
        with col_submit:
            if st.button("📤 제출하기", use_container_width=True):
                if code.strip():
                    st.subheader("채점 결과")
                    
                    passed = 0
                    total = len(problem['test_cases'])
                    
                    for i, test_case in enumerate(problem['test_cases'], 1):
                        success, output, error_line, chart_files = run_code(code, test_case['input'])
                        
                        if success and output == test_case['output']:
                            st.success(f"✅ 테스트 케이스 {i}: 통과")
                            passed += 1
                            
                            # 첫 번째 테스트 케이스에서 차트가 생성되었으면 표시
                            if i == 1 and chart_files:
                                st.subheader("📊 생성된 차트 미리보기")
                                for chart_file in chart_files:
                                    try:
                                        st.image(chart_file, caption=f"생성된 차트: {os.path.basename(chart_file)}")
                                        # 차트 파일 정리
                                        try:
                                            os.unlink(chart_file)
                                        except:
                                            pass
                                    except Exception as e:
                                        st.error(f"차트 표시 중 오류: {str(e)}")
                        else:
                            st.error(f"❌ 테스트 케이스 {i}: 실패")
                            with st.expander(f"테스트 케이스 {i} 상세"):
                                st.code(f"입력: {test_case['input']}")
                                st.code(f"예상 출력: {test_case['output']}")
                                st.code(f"실제 출력: {output if success else '실행 오류'}")
                                
                                # 첫 번째 실패한 케이스에서 에러 위치 표시
                                if not success and error_line and i == 1:
                                    st.error(f"🔍 에러 위치: {error_line}번째 줄")
                                    
                                    # 에러 위치 저장
                                    st.session_state[f'error_line_{problem_id}'] = error_line
                                    
                                    if ACE_AVAILABLE:
                                        # 에러 표시 설정
                                        st.session_state[f'code_annotations_{problem_id}'] = [{
                                            "row": error_line - 1,
                                            "column": 0,
                                            "text": f"테스트 케이스 {i} 실패",
                                            "type": "error"
                                        }]
                                        
                                        st.session_state[f'code_markers_{problem_id}'] = [{
                                            "startRow": error_line - 1,
                                            "startCol": 0,
                                            "endRow": error_line - 1,
                                            "endCol": 100,
                                            "className": "error-marker",
                                            "type": "background"
                                        }]
                    
                    # 결과 요약
                    if passed == total:
                        st.balloons()
                        st.success(f"🎉 모든 테스트 케이스 통과! ({passed}/{total})")
                        # 성공한 제출 기록 저장
                        save_submission_result(st.session_state.username, problem_id, code, passed, total, True)
                    else:
                        st.warning(f"📊 {passed}/{total} 테스트 케이스 통과")
                        # 실패한 제출 기록 저장
                        save_submission_result(st.session_state.username, problem_id, code, passed, total, False)
                else:
                    st.warning("코드를 입력해주세요.")

def admin_problems_page():
    """관리자 문제 관리 페이지"""
    st.title("🔧 문제 관리")
    
    if not is_admin():
        st.error("관리자만 접근할 수 있습니다.")
        return
    
    problems = load_problems()
    
    # 탭으로 구분
    tab1, tab2, tab3 = st.tabs(["📋 문제 목록", "➕ 문제 추가", "✏️ 문제 수정"])
    
    with tab1:
        st.subheader("현재 문제 목록")
        
        if problems:
            for problem_id, problem in problems.items():
                with st.expander(f"**{problem_id}번. {problem['title']}** - {problem['difficulty']}"):
                    st.markdown(problem['description'])
                    st.write(f"**테스트 케이스 개수:** {len(problem['test_cases'])}")
                    
                    if st.button(f"삭제", key=f"delete_{problem_id}", type="secondary"):
                        del problems[problem_id]
                        save_problems(problems)
                        st.success(f"{problem_id}번 문제가 삭제되었습니다!")
                        st.rerun()
        else:
            st.info("등록된 문제가 없습니다.")
    
    with tab2:
        st.subheader("새 문제 추가")
        
        with st.form("add_problem"):
            new_id = st.text_input("문제 번호", help="예: 3")
            new_title = st.text_input("문제 제목", help="예: 구구단 출력")
            new_difficulty = st.selectbox("난이도", ["쉬움", "보통", "어려움"])
            new_description = st.text_area("문제 설명", height=200, 
                                         help="마크다운 형식으로 작성 가능합니다.")
            
            st.subheader("테스트 케이스")
            test_cases = []
            
            # 테스트 케이스 입력
            num_cases = st.number_input("테스트 케이스 개수", min_value=1, max_value=10, value=3)
            
            for i in range(num_cases):
                st.write(f"**테스트 케이스 {i+1}**")
                col1, col2 = st.columns(2)
                with col1:
                    test_input = st.text_area(f"입력 {i+1}", key=f"input_{i}")
                with col2:
                    test_output = st.text_area(f"출력 {i+1}", key=f"output_{i}")
                
                if test_input and test_output:
                    test_cases.append({"input": test_input, "output": test_output})
            
            submitted = st.form_submit_button("문제 추가", type="primary")
            
            if submitted:
                if new_id and new_title and new_description and test_cases:
                    if new_id in problems:
                        st.error("이미 존재하는 문제 번호입니다.")
                    else:
                        problems[new_id] = {
                            "title": new_title,
                            "description": new_description,
                            "difficulty": new_difficulty,
                            "test_cases": test_cases
                        }
                        save_problems(problems)
                        st.success(f"{new_id}번 문제가 추가되었습니다!")
                        st.rerun()
                else:
                    st.error("모든 필드를 입력해주세요.")
    
    with tab3:
        st.subheader("문제 수정")
        
        if problems:
            selected_id = st.selectbox("수정할 문제 선택", list(problems.keys()))
            
            if selected_id:
                problem = problems[selected_id]
                
                with st.form("edit_problem"):
                    edit_title = st.text_input("문제 제목", value=problem['title'])
                    edit_difficulty = st.selectbox("난이도", ["쉬움", "보통", "어려움"], 
                                                 index=["쉬움", "보통", "어려움"].index(problem['difficulty']))
                    edit_description = st.text_area("문제 설명", value=problem['description'], height=200)
                    
                    st.subheader("기존 테스트 케이스")
                    for i, case in enumerate(problem['test_cases']):
                        st.write(f"**케이스 {i+1}**")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.code(f"입력: {case['input']}")
                        with col2:
                            st.code(f"출력: {case['output']}")
                    
                    updated = st.form_submit_button("수정 완료", type="primary")
                    
                    if updated:
                        problems[selected_id]['title'] = edit_title
                        problems[selected_id]['difficulty'] = edit_difficulty
                        problems[selected_id]['description'] = edit_description
                        save_problems(problems)
                        st.success(f"{selected_id}번 문제가 수정되었습니다!")
                        st.rerun()
        else:
            st.info("수정할 문제가 없습니다.")
    
    # 네비게이션
    st.markdown("---")
    if st.button("🏠 관리자 메인으로"):
        st.session_state.page = "main"
        st.rerun()

def admin_stats_page():
    """관리자 통계 페이지"""
    st.title("📊 관리자 통계")
    
    if not is_admin():
        st.error("관리자만 접근할 수 있습니다.")
        return
    
    users = load_users()
    problems = load_problems()
    submissions = load_submissions()
    
    # 전체 통계
    st.subheader("📈 전체 통계")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 사용자 수", len(users))
    
    with col2:
        st.metric("총 문제 수", len(problems))
    
    with col3:
        total_submissions = sum(len(user_subs) for user_subs in submissions.values())
        st.metric("총 제출 수", total_submissions)
    
    with col4:
        # 활성 사용자 (최근 7일 내 제출한 사용자)
        active_users = 0
        current_time = time.time()
        week_ago = current_time - (7 * 24 * 60 * 60)
        
        for user_subs in submissions.values():
            for sub in user_subs:
                if sub['timestamp'] > week_ago:
                    active_users += 1
                    break
        
        st.metric("활성 사용자 (7일)", active_users)
    
    st.markdown("---")
    
    # 문제별 통계
    st.subheader("📋 문제별 통계")
    
    problem_stats = {}
    for problem_id in problems.keys():
        problem_stats[problem_id] = {
            "total_attempts": 0,
            "successful_solves": 0,
            "unique_solvers": set()
        }
    
    # 제출 기록에서 통계 계산
    for username, user_subs in submissions.items():
        for sub in user_subs:
            problem_id = sub['problem_id']
            if problem_id in problem_stats:
                problem_stats[problem_id]["total_attempts"] += 1
                if sub['success']:
                    problem_stats[problem_id]["successful_solves"] += 1
                    problem_stats[problem_id]["unique_solvers"].add(username)
    
    if problem_stats:
        for problem_id, stats in problem_stats.items():
            if problem_id in problems:
                problem = problems[problem_id]
                with st.expander(f"📝 {problem_id}번. {problem['title']} ({problem['difficulty']})"):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("총 시도", stats["total_attempts"])
                    
                    with col2:
                        st.metric("성공 제출", stats["successful_solves"])
                    
                    with col3:
                        st.metric("해결한 사용자", len(stats["unique_solvers"]))
                    
                    with col4:
                        success_rate = (stats["successful_solves"] / stats["total_attempts"] * 100) if stats["total_attempts"] > 0 else 0
                        st.metric("성공률", f"{success_rate:.1f}%")
    else:
        st.info("아직 제출 기록이 없습니다.")
    
    st.markdown("---")
    
    # 사용자 순위
    st.subheader("🏆 사용자 순위")
    
    user_rankings = []
    for username, user_data in users.items():
        solved_count = len(user_data.get('solved_problems', []))
        total_subs = user_data.get('total_submissions', 0)
        user_rankings.append({
            "사용자": username,
            "해결한 문제": solved_count,
            "총 제출": total_subs
        })
    
    # 해결한 문제 수로 정렬
    user_rankings.sort(key=lambda x: x["해결한 문제"], reverse=True)
    
    if user_rankings:
        for i, user in enumerate(user_rankings[:10], 1):  # 상위 10명만 표시
            col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
            
            with col1:
                if i == 1:
                    st.write("🥇")
                elif i == 2:
                    st.write("🥈")
                elif i == 3:
                    st.write("🥉")
                else:
                    st.write(f"{i}위")
            
            with col2:
                st.write(user["사용자"])
            
            with col3:
                st.write(f"{user['해결한 문제']}문제")
            
            with col4:
                st.write(f"{user['총 제출']}회")
    else:
        st.info("아직 사용자 활동이 없습니다.")
    
    # 네비게이션
    st.markdown("---")
    if st.button("🏠 관리자 메인으로"):
        st.session_state.page = "main"
        st.rerun()

def admin_users_page():
    """관리자 사용자 관리 페이지"""
    st.title("👥 사용자 관리")
    
    if not is_admin():
        st.error("관리자만 접근할 수 있습니다.")
        return
    
    users = load_users()
    submissions = load_submissions()
    
    # 탭으로 구분
    tab1, tab2, tab3 = st.tabs(["📋 사용자 목록", "🔍 사용자 상세", "⚙️ 사용자 설정"])
    
    with tab1:
        st.subheader("전체 사용자 목록")
        
        if users:
            # 검색 기능
            search_term = st.text_input("🔍 사용자 검색", placeholder="사용자명을 입력하세요")
            
            # 정렬 옵션
            sort_option = st.selectbox(
                "정렬 기준",
                ["가입일 (최신순)", "가입일 (오래된순)", "해결한 문제 (많은순)", "총 제출 (많은순)", "이름 (가나다순)"]
            )
            
            # 사용자 리스트 필터링 및 정렬
            filtered_users = {}
            for username, user_data in users.items():
                if not search_term or search_term.lower() in username.lower():
                    filtered_users[username] = user_data
            
            # 정렬
            if sort_option == "가입일 (최신순)":
                def get_created_time(item):
                    try:
                        return float(item[1].get('created_at', 0))
                    except (ValueError, TypeError):
                        return 0
                sorted_users = sorted(filtered_users.items(), key=get_created_time, reverse=True)
            elif sort_option == "가입일 (오래된순)":
                def get_created_time(item):
                    try:
                        return float(item[1].get('created_at', 0))
                    except (ValueError, TypeError):
                        return 0
                sorted_users = sorted(filtered_users.items(), key=get_created_time)
            elif sort_option == "해결한 문제 (많은순)":
                sorted_users = sorted(filtered_users.items(), key=lambda x: len(x[1].get('solved_problems', [])), reverse=True)
            elif sort_option == "총 제출 (많은순)":
                sorted_users = sorted(filtered_users.items(), key=lambda x: x[1].get('total_submissions', 0), reverse=True)
            else:  # 이름 순
                sorted_users = sorted(filtered_users.items(), key=lambda x: x[0])
            
            st.write(f"총 {len(sorted_users)}명의 사용자")
            
            # 사용자 목록 표시
            for username, user_data in sorted_users:
                with st.expander(f"👤 {username}"):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        try:
                            created_time = float(user_data.get('created_at', 0))
                            if created_time > 0:
                                created_date = time.strftime("%Y-%m-%d", time.localtime(created_time))
                            else:
                                created_date = "알 수 없음"
                        except (ValueError, TypeError):
                            created_date = "알 수 없음"
                        st.write(f"**가입일:** {created_date}")
                    
                    with col2:
                        solved_count = len(user_data.get('solved_problems', []))
                        st.write(f"**해결한 문제:** {solved_count}개")
                    
                    with col3:
                        total_subs = user_data.get('total_submissions', 0)
                        st.write(f"**총 제출:** {total_subs}회")
                    
                    with col4:
                        user_submissions = submissions.get(username, [])
                        if user_submissions:
                            last_submission = max(user_submissions, key=lambda x: x['timestamp'])
                            last_date = time.strftime("%Y-%m-%d", time.localtime(last_submission['timestamp']))
                            st.write(f"**마지막 활동:** {last_date}")
                        else:
                            st.write("**마지막 활동:** 없음")
                    
                    # 관리 버튼들
                    col_detail, col_reset, col_delete = st.columns(3)
                    
                    with col_detail:
                        if st.button(f"📋 상세보기", key=f"detail_{username}"):
                            # 상세보기는 탭2로 이동하지 않고 현재 탭에서 정보 표시
                            st.write("---")
                            st.write(f"### 📋 {username} 상세 정보")
                            
                            # 기본 정보 표시
                            detail_col1, detail_col2 = st.columns(2)
                            with detail_col1:
                                try:
                                    created_time = float(user_data.get('created_at', 0))
                                    if created_time > 0:
                                        created_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(created_time))
                                    else:
                                        created_date = "알 수 없음"
                                except (ValueError, TypeError):
                                    created_date = "알 수 없음"
                                st.write(f"**가입일:** {created_date}")
                                st.write(f"**해결한 문제:** {len(user_data.get('solved_problems', []))}개")
                            
                            with detail_col2:
                                st.write(f"**총 제출:** {user_data.get('total_submissions', 0)}회")
                                user_subs = submissions.get(username, [])
                                if user_subs:
                                    success_count = sum(1 for sub in user_subs if sub['success'])
                                    success_rate = (success_count / len(user_subs) * 100)
                                    st.write(f"**성공률:** {success_rate:.1f}%")
                                else:
                                    st.write(f"**성공률:** 0%")
                            
                            # 해결한 문제
                            solved_problems = user_data.get('solved_problems', [])
                            if solved_problems:
                                st.write("**해결한 문제:**")
                                problems = load_problems()
                                for problem_id in solved_problems:
                                    if problem_id in problems:
                                        problem = problems[problem_id]
                                        st.write(f"- {problem_id}번. {problem['title']} ({problem['difficulty']})")
                            else:
                                st.write("**해결한 문제:** 없음")
                    
                    with col_reset:
                        if st.button(f"진도 초기화", key=f"reset_{username}", type="secondary"):
                            if st.button(f"정말 초기화하시겠습니까?", key=f"confirm_reset_{username}"):
                                # 해결한 문제와 제출 기록 초기화
                                users[username]['solved_problems'] = []
                                users[username]['total_submissions'] = 0
                                save_users(users)
                                
                                # 제출 기록도 삭제
                                if username in submissions:
                                    del submissions[username]
                                    save_submissions(submissions)
                                
                                st.success(f"{username}의 진도가 초기화되었습니다!")
                                st.rerun()
                    
                    with col_delete:
                        if st.button(f"계정 삭제", key=f"delete_{username}", type="secondary"):
                            # 체크박스로 삭제 확인
                            if st.checkbox(f"{username} 계정을 정말 삭제하시겠습니까?", key=f"confirm_delete_{username}"):
                                if st.button(f"최종 삭제", key=f"final_delete_{username}", type="secondary"):
                                    del users[username]
                                    save_users(users)
                                    
                                    # 제출 기록도 삭제
                                    if username in submissions:
                                        del submissions[username]
                                        save_submissions(submissions)
                                    
                                    st.success(f"{username} 계정이 삭제되었습니다!")
                                    st.rerun()
        else:
            st.info("등록된 사용자가 없습니다.")
    
    with tab2:
        st.subheader("사용자 상세 정보")
        
        if users:
            selected_user = st.selectbox("사용자 선택", list(users.keys()))
            
            if selected_user:
                user_data = users[selected_user]
                user_submissions = submissions.get(selected_user, [])
                
                # 기본 정보
                st.write("### 📋 기본 정보")
                col1, col2 = st.columns(2)
                
                with col1:
                    try:
                        created_time = float(user_data.get('created_at', 0))
                        if created_time > 0:
                            created_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created_time))
                        else:
                            created_date = "알 수 없음"
                    except (ValueError, TypeError):
                        created_date = "알 수 없음"
                    st.write(f"**가입일:** {created_date}")
                    st.write(f"**해결한 문제:** {len(user_data.get('solved_problems', []))}개")
                
                with col2:
                    st.write(f"**총 제출:** {user_data.get('total_submissions', 0)}회")
                    if user_submissions:
                        success_count = sum(1 for sub in user_submissions if sub['success'])
                        success_rate = (success_count / len(user_submissions) * 100)
                        st.write(f"**성공률:** {success_rate:.1f}%")
                    else:
                        st.write(f"**성공률:** 0%")
                
                # 해결한 문제 목록
                st.write("### ✅ 해결한 문제")
                solved_problems = user_data.get('solved_problems', [])
                if solved_problems:
                    problems = load_problems()
                    for problem_id in solved_problems:
                        if problem_id in problems:
                            problem = problems[problem_id]
                            st.write(f"- {problem_id}번. {problem['title']} ({problem['difficulty']})")
                else:
                    st.info("아직 해결한 문제가 없습니다.")
                
                # 최근 제출 기록
                st.write("### 📅 최근 제출 기록 (최근 10개)")
                if user_submissions:
                    recent_subs = sorted(user_submissions, key=lambda x: x['timestamp'], reverse=True)[:10]
                    
                    for sub in recent_subs:
                        col1, col2, col3, col4 = st.columns([2, 3, 1, 1])
                        
                        with col1:
                            st.write(sub['date'])
                        
                        with col2:
                            problems = load_problems()
                            problem_title = problems.get(sub['problem_id'], {}).get('title', '알 수 없음')
                            st.write(f"{sub['problem_id']}번. {problem_title}")
                        
                        with col3:
                            if sub['success']:
                                st.success("성공")
                            else:
                                st.error("실패")
                        
                        with col4:
                            st.write(f"{sub['passed_tests']}/{sub['total_tests']}")
                else:
                    st.info("제출 기록이 없습니다.")
        else:
            st.info("등록된 사용자가 없습니다.")
    
    with tab3:
        st.subheader("사용자 설정")
        
        if users:
            # 일괄 작업
            st.write("### 🔧 일괄 작업")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("### ⚠️ 모든 사용자 진도 초기화")
                reset_confirm = st.checkbox("정말로 모든 사용자의 진도를 초기화하시겠습니까?")
                
                if st.button("모든 사용자 진도 초기화", type="secondary", disabled=not reset_confirm):
                    for username in users.keys():
                        users[username]['solved_problems'] = []
                        users[username]['total_submissions'] = 0
                    save_users(users)
                    
                    # 모든 제출 기록 삭제
                    save_submissions({})
                    
                    st.success("모든 사용자의 진도가 초기화되었습니다!")
                    st.rerun()
            
            with col2:
                st.write("**⚠️ 위험한 작업입니다!**")
                st.write("이 작업은 되돌릴 수 없습니다.")
            
            st.markdown("---")
            
            # 사용자 검색 및 개별 수정
            st.write("### 👤 개별 사용자 수정")
            
            edit_user = st.selectbox("수정할 사용자 선택", list(users.keys()), key="edit_user")
            
            if edit_user:
                user_data = users[edit_user]
                
                with st.form("edit_user_form"):
                    st.write(f"**{edit_user}** 사용자 정보 수정")
                    
                    # 해결한 문제 수동 편집
                    current_solved = user_data.get('solved_problems', [])
                    solved_input = st.text_input(
                        "해결한 문제 번호 (쉼표로 구분)",
                        value=",".join(current_solved),
                        help="예: 1,2,3"
                    )
                    
                    # 총 제출 횟수 수동 편집
                    total_subs = st.number_input(
                        "총 제출 횟수",
                        min_value=0,
                        value=user_data.get('total_submissions', 0)
                    )
                    
                    if st.form_submit_button("수정 완료"):
                        # 해결한 문제 업데이트
                        if solved_input.strip():
                            new_solved = [p.strip() for p in solved_input.split(",") if p.strip()]
                        else:
                            new_solved = []
                        
                        users[edit_user]['solved_problems'] = new_solved
                        users[edit_user]['total_submissions'] = total_subs
                        save_users(users)
                        
                        st.success(f"{edit_user} 사용자 정보가 수정되었습니다!")
                        st.rerun()
        else:
            st.info("등록된 사용자가 없습니다.")
    
    # 네비게이션
    st.markdown("---")
    if st.button("🏠 관리자 메인으로"):
        st.session_state.page = "main"
        st.rerun()

def user_stats_page():
    """사용자 통계 페이지"""
    st.title("📊 내 통계")
    
    username = st.session_state.username
    users = load_users()
    problems = load_problems()
    submissions = load_submissions()
    
    if username not in users:
        st.error("사용자 정보를 찾을 수 없습니다.")
        return
    
    user_data = users[username]
    user_submissions = submissions.get(username, [])
    
    # 기본 통계
    st.subheader(f"👋 {username}님의 활동 통계")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        solved_count = len(user_data.get('solved_problems', []))
        st.metric("해결한 문제", f"{solved_count}개")
    
    with col2:
        total_subs = len(user_submissions)
        st.metric("총 제출", f"{total_subs}회")
    
    with col3:
        total_problems = len(problems)
        progress = (solved_count / total_problems * 100) if total_problems > 0 else 0
        st.metric("진행률", f"{progress:.1f}%")
    
    with col4:
        if user_submissions:
            success_subs = sum(1 for sub in user_submissions if sub['success'])
            success_rate = (success_subs / total_subs * 100) if total_subs > 0 else 0
            st.metric("성공률", f"{success_rate:.1f}%")
        else:
            st.metric("성공률", "0%")
    
    st.markdown("---")
    
    # 최근 활동
    st.subheader("📅 최근 활동")
    
    if user_submissions:
        # 최근 5개 제출만 표시
        recent_submissions = sorted(user_submissions, key=lambda x: x['timestamp'], reverse=True)[:5]
        
        for sub in recent_submissions:
            problem_title = problems.get(sub['problem_id'], {}).get('title', '알 수 없음')
            
            col1, col2, col3, col4 = st.columns([2, 3, 2, 2])
            
            with col1:
                st.write(sub['date'])
            
            with col2:
                st.write(f"{sub['problem_id']}번. {problem_title}")
            
            with col3:
                if sub['success']:
                    st.success("✅ 성공")
                else:
                    st.error("❌ 실패")
            
            with col4:
                st.write(f"{sub['passed_tests']}/{sub['total_tests']}")
    else:
        st.info("아직 제출 기록이 없습니다. 문제를 풀어보세요!")
    
    st.markdown("---")
    
    # 문제별 상태
    st.subheader("📋 문제별 현황")
    
    solved_problems = set(user_data.get('solved_problems', []))
    attempted_problems = set(sub['problem_id'] for sub in user_submissions)
    
    for problem_id, problem in problems.items():
        col1, col2, col3 = st.columns([1, 4, 2])
        
        with col1:
            st.write(f"{problem_id}번")
        
        with col2:
            st.write(f"{problem['title']} ({problem['difficulty']})")
        
        with col3:
            if problem_id in solved_problems:
                st.success("✅ 해결")
            elif problem_id in attempted_problems:
                st.warning("🔄 시도함")
            else:
                st.info("❌ 미시도")
    
    # 네비게이션
    st.markdown("---")
    if st.button("🏠 메인으로 돌아가기"):
        st.session_state.page = "main"
        st.rerun()

def login_page():
    """로그인/회원가입 페이지"""
    st.title("💻 스파르타 QA/QC")
    
    # 중앙 정렬을 위한 컬럼
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("---")
        
        # 탭으로 로그인/회원가입 분리
        tab1, tab2 = st.tabs(["🔑 로그인", "✍️ 회원가입"])
        
        with tab1:
            st.subheader("로그인")
            
            login_username = st.text_input("아이디", key="login_username")
            login_password = st.text_input("비밀번호", type="password", key="login_password")
            
            if st.button("로그인", use_container_width=True):
                if login_username and login_password:
                    success, message = login_user(login_username, login_password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username = login_username
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("아이디와 비밀번호를 모두 입력해주세요.")
        
        with tab2:
            st.subheader("회원가입")
            
            signup_username = st.text_input("아이디", key="signup_username", 
                                          help="한글, 영문, 숫자 모두 가능")
            signup_password = st.text_input("비밀번호", type="password", key="signup_password",
                                          help="4자 이상 입력해주세요")
            signup_password_confirm = st.text_input("비밀번호 확인", type="password", 
                                                  key="signup_password_confirm")
            
            if st.button("회원가입", use_container_width=True):
                if not all([signup_username, signup_password, signup_password_confirm]):
                    st.warning("모든 필드를 입력해주세요.")
                elif len(signup_password) < 4:
                    st.warning("비밀번호는 4자 이상이어야 합니다.")
                elif signup_password != signup_password_confirm:
                    st.warning("비밀번호가 일치하지 않습니다.")
                else:
                    success, message = register_user(signup_username, signup_password)
                    if success:
                        st.success(message)
                        st.info("이제 로그인 탭에서 로그인해주세요!")
                    else:
                        st.error(message)

# 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'page' not in st.session_state:
    st.session_state.page = "main"

# 메인 앱 로직
if st.session_state.logged_in:
    if st.session_state.page == "problems":
        problems_page()
    elif st.session_state.page == "solve":
        solve_page()
    elif st.session_state.page == "admin_problems":
        admin_problems_page()
    elif st.session_state.page == "admin_stats":
        admin_stats_page()
    elif st.session_state.page == "admin_users":
        admin_users_page()
    elif st.session_state.page == "user_stats":
        user_stats_page()
    else:
        main_page()
else:
    login_page()

# 하단 정보
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 12px;'>
    💡 스파르타 QA/QC | Made with Streamlit
    </div>
    """, 
    unsafe_allow_html=True
)
