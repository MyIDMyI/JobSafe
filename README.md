# JobSafe

관심기업을 등록해 두면 고용24의 **임금체불 명단공개 사업주 여부**를 반복 점검하고, 이전 결과와 달라진 내용을 확인할 수 있도록 만든 구직자용 웹앱입니다.

## 현재 구현 상태

- 관심기업 등록 / 목록 조회 / 삭제
- 등록 직후 첫 점검 자동 실행
- 고용24 임금체불 명단공개 사업주 여부 조회
- 점검 결과 PostgreSQL 저장
- 이전 결과와 현재 결과 비교
- 변경 발생 기업 강조 표시
- 기업별 점검 이력 조회
- 공공데이터 출처와 마지막 점검 시각 표시
- 조회 실패와 `임금체불 명단공개 미대상`을 명확히 구분
- 중복 사업자등록번호 등록 방지
- 고용24에서 `대상(Y)`으로 확인된 기업의 고용노동부 체불사업주 공개명단 상세정보 후보 조회
- 배포용 자동 점검 API와 GitHub Actions 스케줄 워크플로 준비

> `임금체불 명단공개 미대상`은 현재 조회 기준으로 공개 대상이 아니라는 뜻입니다. 해당 기업의 전체 근무환경이나 임금 지급 상태가 안전하다는 의미로 해석하지 않습니다.

## MVP 범위

현재 실제로 이용 권한을 확보한 **고용24 임금체불 명단공개 사업주 여부 API**를 핵심 판정 데이터로 사용합니다.

고용보험료 체납 사업주 여부와 중대재해 발표·공표 사업주 여부는 현재 사용할 수 있는 인증 권한이 없어 MVP에서 제외했습니다. 추후 이용 권한을 확보하면 동일한 점검 구조에 추가할 수 있습니다.

## 공공데이터 연동

### 1. 고용24 OPEN API

고용24 OPEN API - 임금체불 명단공개 사업주 여부

공식 요청 URL:

```text
https://www.work24.go.kr/cm/openApi/call/wk/callOpenApiSvcInfo210L41.do
```

요청값:

- `authKey`: 발급받은 인증키
- `returnType=XML`
- `brno`: 사업자등록번호
- `bzmn`: 사업장관리번호 (선택)

주요 응답값:

- `lnkSucsYn`: 연계 성공 여부
- `judgReltYn`: `Y`=명단공개 대상, `N`=미대상
- `errMsgCd`, `errMsg`: 오류 정보

### 2. 고용노동부 체불사업주 명단공개

고용24에서 `judgReltYn=Y`가 확인된 경우, 사용자가 상세정보 조회 버튼을 누르면 고용노동부 공식 **체불사업주 명단공개** 페이지를 읽어 사업장명이 일치하는 공개명단 후보를 찾습니다.

현재 고용노동부 공개 페이지에서 표시되는 항목만 사용합니다.

- 성명
- 나이
- 사업장명
- 주소지(사업주)
- 소재지(사업장)
- 체불액(원)

이 상세조회는 별도 OPEN API가 아니라 **고용노동부 공식 공개 웹페이지의 HTML을 서버에서 파싱**하는 방식입니다. 공개 페이지 구조가 바뀌면 파서 수정이 필요할 수 있습니다.

또한 공개명단에는 사업자등록번호가 표시되지 않기 때문에 JobSafe는 `(주)`, `주식회사`, 공백 등 상호 표기 차이를 정규화한 뒤 **사업장명 일치 후보**를 보여줍니다. 사업자등록번호로 동일 사업체임을 확정하는 기능은 아닙니다.

## 기술 스택

- Frontend: React + Vite
- Backend: FastAPI + SQLAlchemy
- Database: SQLite(로컬 개발) / PostgreSQL(온라인 배포)
- Public data: 고용24 OPEN API + 고용노동부 체불사업주 공식 공개 페이지
- HTML parser: Beautiful Soup
- Hosting: Render Static Site + Render Web Service + Render PostgreSQL
- CI: GitHub Actions

## 배포 주소

- 웹앱: `https://jobsafe-web.onrender.com`
- API: `https://jobsafe-api.onrender.com`
- Health check: `https://jobsafe-api.onrender.com/health`

## 로컬 실행

### Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## 환경변수

### Backend

```env
APP_ENV=development
DATABASE_URL=sqlite:///./jobsafe.db
FRONTEND_ORIGINS=http://localhost:5173
WORK24_AUTH_KEY=
CRON_SECRET=
```

- `DATABASE_URL`: 로컬은 SQLite, 배포 환경은 PostgreSQL URL
- `FRONTEND_ORIGINS`: 허용할 프론트엔드 주소
- `WORK24_AUTH_KEY`: 발급받은 고용24 OPEN API 인증키
- `CRON_SECRET`: 자동 점검 엔드포인트 호출용 비밀값

실제 키와 비밀값은 GitHub에 커밋하지 않습니다.

### Frontend

- `VITE_API_BASE_URL`: 배포된 FastAPI 서버 주소

## 자동 점검

백엔드에는 다음 자동 점검 엔드포인트가 준비되어 있습니다.

```text
POST /api/maintenance/run-checks
X-Cron-Secret: <CRON_SECRET>
```

`.github/workflows/daily-check.yml`은 매일 **09:00 KST**에 이 엔드포인트를 호출하도록 작성되어 있습니다.

실제 예약 실행을 활성화하려면:

1. 워크플로 파일이 기본 브랜치(`main`)에 포함되어 있어야 합니다.
2. Render `jobsafe-api`의 `CRON_SECRET`과 동일한 값을 GitHub Repository Secret `JOBSAFE_CRON_SECRET`에 등록합니다.
3. GitHub Actions의 `JobSafe Daily Check`가 정상 실행되는지 확인합니다.

Render 무료 Cron Job은 사용할 수 없어 GitHub Actions 스케줄 방식으로 준비했습니다.

## 구현 원칙

1. 고용24가 반환한 원본 판정값을 임의로 바꾸지 않습니다.
2. API 호출 실패를 `미대상`으로 처리하지 않습니다.
3. 최초 점검은 변경사항으로 표시하지 않습니다.
4. 두 번째 점검부터 이전 저장값과 비교합니다.
5. 온라인 배포에서는 SQLite 대신 PostgreSQL을 사용합니다.
6. 사용 권한이 없는 API를 추정해서 호출하지 않습니다.
7. `미대상` 결과를 기업의 안전성 보장으로 표현하지 않습니다.
8. 고용노동부 상세조회에서는 공식 페이지에 실제 공개된 항목만 표시합니다.
9. 사업장명 일치 결과를 사업자등록번호 기준 동일 사업체라고 단정하지 않습니다.

## 현재 한계와 향후 확장

- 현재는 로그인 없는 단일 사용자형 MVP라 공개 서비스에서 사용자별 관심기업 분리는 지원하지 않습니다.
- 현재 핵심 위험정보 항목은 임금체불 공개정보 1종입니다.
- 자동 점검 워크플로는 기본 브랜치 반영과 GitHub Secret 설정 후 활성화됩니다.
- 고용노동부 상세조회는 공식 웹페이지 HTML 구조 변경에 영향을 받을 수 있습니다.
- 상세 공개명단은 사업자등록번호를 제공하지 않아 사업장명 기준 후보 매칭 방식입니다.
- 추후 중대재해·고용보험 관련 공공데이터를 확보하면 점검 항목을 확장할 수 있습니다.
- 이후 AI는 공공데이터 결과를 설명하는 역할로만 추가하고 기업의 안전/위험을 임의 평가하지 않도록 설계할 예정입니다.
