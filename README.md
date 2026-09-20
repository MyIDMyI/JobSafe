# JobSafe

관심기업을 등록해 두면 고용24의 정부 공개 사업주 정보를 반복 점검하고, 이전 결과와 달라진 내용을 확인할 수 있도록 만든 구직자용 웹앱입니다.

## MVP 범위

- 관심기업 등록 및 목록 관리
- 임금체불 명단공개 여부 조회
- 고용보험료 체납 여부 조회
- 중대재해 발표·공표 여부 조회 구조
- 점검 결과 저장 및 이전 결과와 변경 비교
- 조회 실패와 미대상을 구분해 표시
- 이후 생성형 AI 설명 기능 추가 예정

> 공개정보에 해당하지 않는다고 해서 해당 기업의 전체 근무환경이나 안전성이 보장되는 것은 아닙니다.

## 기술 스택

- Frontend: React + Vite
- Backend: FastAPI + SQLAlchemy
- Database: SQLite(로컬 개발) / PostgreSQL(배포)
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

- `DATABASE_URL`: 로컬은 SQLite, 배포 환경은 PostgreSQL URL 사용
- `FRONTEND_ORIGINS`: 허용할 프론트엔드 주소
- `WORK24_AUTH_KEY`: 고용24 OPEN API 인증키
- `WORK24_SERIOUS_ACCIDENT_URL`: 중대재해 API 공식 요청 URL 확인 후 설정

실제 API 키는 절대로 GitHub에 커밋하지 않고 배포 서비스의 환경변수로 관리합니다.

### Frontend

- `VITE_API_BASE_URL`: 배포된 FastAPI 서버 주소

## 현재 구현 상태

초기 MVP 브랜치에서는 화면과 DB 구조, 임금체불/고용보험료 체납 조회 클라이언트, 검사 이력 및 변경 감지 골격까지 구현합니다. 고용24 인증키가 발급되면 실제 호출 테스트 후 XML 응답과 예외 케이스를 다시 검증합니다.

중대재해 API는 서비스 목록 존재 여부까지만 확인된 상태이므로, 요청 URL과 파라미터를 공식 명세에서 확인한 뒤 연결합니다. 확인되지 않은 URL을 추정해서 코드에 넣지 않습니다.

## 배포 원칙

온라인 배포 환경에서는 SQLite 대신 PostgreSQL을 사용합니다. 호스팅 환경의 로컬 파일 시스템은 재시작 또는 재배포 시 유지되지 않을 수 있기 때문입니다.

