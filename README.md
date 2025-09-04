# 카카오 채널 이미지 자동 추출 및 Teams 전송

매일 오전 11시에 카카오 채널의 최신 게시물에서 이미지를 추출하여 Microsoft Teams로 자동 전송하는 GitHub Actions 워크플로우입니다.

## 기능

- 카카오 채널의 최신 게시물에서 이미지 자동 추출
- **OCR을 통한 점심 메뉴판 자동 인식** (선택사항)
- 메뉴 항목을 구조화하여 Teams로 전송
- 매일 오전 10시 30분 자동 실행 (딜레이 시간 고려)

## 설정 방법

### 1. Teams Webhook URL 생성

1. Microsoft Teams에서 채널 선택
2. 채널 옵션 메뉴에서 "커넥터" 선택
3. "Incoming Webhook" 검색 및 추가
4. Webhook 이름 설정 후 생성
5. 생성된 Webhook URL 복사

### 2. GitHub Secrets 설정

필수 시크릿:
- `TEAMS_WEBHOOK_URL`: Teams Webhook URL

선택 시크릿 (메뉴 OCR 기능 사용시):
- `AZURE_COGNITIVE_API_ENDPOINT`: Azure Document Intelligence API 엔드포인트
- `AZURE_COGNITIVE_API_KEY`: Azure Document Intelligence API 키
- `OPENAI_API_KEY`: OpenAI API 키 (메뉴 추출용)

설정 방법:
1. GitHub 저장소의 Settings → Secrets and variables → Actions
2. "New repository secret" 클릭
3. 각 시크릿의 Name과 Value 입력
4. "Add secret" 클릭

## 작동 방식

1. **자동 실행**: 매일 한국시간 오전 11시 (UTC 02:00)에 자동 실행
2. **수동 실행**: GitHub Actions 페이지에서 "Run workflow" 버튼으로 수동 실행 가능

## 워크플로우 순서

1. 카카오 채널 페이지 접속 (https://pf.kakao.com/_Kyxlxbn)
2. 첫 번째 게시물 클릭
3. 게시물 내 모든 이미지 추출
4. (선택) OCR을 통해 이미지에서 메뉴판 감지 및 메뉴 추출
5. Teams Adaptive Card 형식으로 전송 (메뉴 정보 포함)

## 파일 구조

```
.
├── .github/
│   └── workflows/
│       └── extract-and-send-images.yml  # GitHub Actions 워크플로우
├── main.py                               # 이미지 추출 및 전송 스크립트
├── ocr_menu_extractor.py                # OCR 및 메뉴 추출 모듈
├── requirements.txt                      # Python 의존성
└── README.md                            # 이 파일
```

## 로컬 실행 방법

```bash
# 의존성 설치
pip install -r requirements.txt
playwright install chromium

# 필수 환경 변수 설정
export TEAMS_WEBHOOK_URL="your-webhook-url"

# 선택 환경 변수 설정 (OCR 기능 사용시)
export AZURE_COGNITIVE_API_ENDPOINT="your-azure-endpoint"
export AZURE_COGNITIVE_API_KEY="your-azure-key"
export OPENAI_API_KEY="your-openai-key"

# 실행
python main.py
```

## 주의사항

- Teams Webhook URL은 보안상 중요한 정보이므로 절대 코드에 직접 포함하지 마세요
- GitHub Secrets를 통해 안전하게 관리하세요
- 워크플로우 실행 시간은 GitHub Actions의 서버 부하에 따라 약간의 지연이 있을 수 있습니다