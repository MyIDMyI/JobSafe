# JobSafe

관심기업을 등록해 두면 고용24의 **임금체불 명단공개 사업주 여부**를 반복 점검하고, 이전 결과와 달라진 내용을 확인할 수 있도록 만든 구직자용 웹앱입니다.

## 현재 MVP 범위

현재 실제로 인증키를 발급받은 고용24 API만 사용합니다.

- 관심기업 등록 및 목록 관리
- 임금체불 명단공개 사업주 여부 조회
- 점검 결과 DB 저장
- 이전 점검 결과와 현재 결과 비교
- 결과가 달라졌을 때 변경사항 표시
- 조회 실패와 미대상(N)을 구분해 표시
- 이후 생성형 AI 설명 기능 추가 예정

고용보험료 체납 사업주 여부와 중대재해 발표·공표 사업주 여부는 현재 사용할 수 있는 인증 권한을 확보하지 못했기 때문에 MVP에서 제외합니다. 추후 이용 가능해지면 확장 기능으로 추가할 수 있습니다.

> '미대상'은 현재 조회 기준으로 명단공개 대상이 아니라는 뜻입니다. 해당 기업의 전체 근무환경이나 임금 지급 상태를 보장하는 결과로 해석하지 않습니다.

## 사용 공공 API

고용24 OPEN API - 임금체불 명단공개 사업주 여부

공식 요청 URL:

```text
https://www.work24.go.kr/cm/openapi/app-form/sa-employ-improve-form-pay-back.do
```

현재 구현에서 사용하는 필수 요청값:

- `authKey`: 발급받은 인증키
- `returnType=XML`
- `brno`: 사업자등록번호
- `bzmn`: 사업장관리번호

주요 응답값:

- `lnkSucsYn`: 연계 성공 여부
- `judgReltYn`: Y=명단공개 대상, N=미대상
- `errMsgCd`, `errMsg`: 오류 정보

## 기술 스택

- Frontend: React + Vite
- Backend: FastAPI + SQLAlchemy
- Database: SQLite(로컬 개발) / PostgreSQL(온라인 배포)
- Public data: 고용24 OPEN API
- Deployment target: Vercel + Render 계열 Python 호스팅 + PostgreSQL

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

백엔드는 기본적으로 `http://localhost:8000`에서 실행됩니다.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

프론트엔드는 기본적으로 `http://localhost:5173`에서 실행됩니다.

## 환경변수

### Backend

```env
APP_ENV=development
DATABASE_URL=sqlite:///./jobsafe.db
FRONTEND_ORIGINS=http://localhost:5173
WORK24_AUTH_KEY=
```

- `DATABASE_URL`: 로컬은 SQLite, 배포 환경은 PostgreSQL URL 사용
- `FRONTEND_ORIGINS`: 허용할 프론트엔드 주소
- `WORK24_AUTH_KEY`: 발급받은 고용24 OPEN API 인증키

실제 API 키는 절대로 GitHub에 커밋하지 않습니다. 로컬에서는 `.env`, 배포 환경에서는 호스팅 서비스의 Environment Variables에 등록합니다.

### Frontend

- `VITE_API_BASE_URL`: 배포된 FastAPI 서버 주소

## 구현 원칙

1. 고용24가 반환한 원본 판정값을 임의로 바꾸지 않습니다.
2. API 호출 실패를 '미대상'으로 처리하지 않습니다.
3. 최초 점검은 변경사항으로 표시하지 않습니다.
4. 두 번째 점검부터 이전 저장값과 비교합니다.
5. 온라인 배포에서는 SQLite 대신 PostgreSQL을 사용합니다.
6. 사용 권한이 없는 API를 임의로 호출하거나 추정 URL로 연결하지 않습니다.

## 다음 단계

1. 발급받은 `WORK24_AUTH_KEY`를 로컬 환경변수에 등록
2. 실제 사업장 테스트 데이터로 고용24 API 호출 검증
3. 응답 XML과 오류 케이스 확인
4. 기업 상세 화면 및 검사 이력 화면 구현
5. 생성형 AI 설명 기능 구현
6. PostgreSQL 연결 후 온라인 배포

