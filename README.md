# BizPlan Generator

AI 기반 예비창업패키지 사업계획서 자동 생성기입니다. Claude Code 스킬 + 웹앱으로 사용 가능합니다.

## Features

- 창업 아이템 정보만 입력하면 **예비창업패키지 사업계획서** 자동 생성
- 시장 조사 자동 연결 (Statista, PitchBook, THE VC, 네이버 등)
- 경쟁사 분석 + 포지셔닝 맵 차트 자동 생성
- TAM/SAM/SOM 시장 규모 분석
- Founder-Market Fit 분석
- 파일 업로드 — 참고 자료 반영 (다중 파일 가능)
- 최종 산출물: **PDF + DOCX + 차트 + 단계별 .md 파일**

## 사용 방법

### 1. Claude Code 스킬

```bash
git clone https://github.com/daniel8824-del/bizplan-generator.git ~/.claude/skills/business-plan-2026
```

Claude Code에서:
```
/bizplan AI 기반 강의 콘텐츠 자동 생성 SaaS
```

### 2. 웹앱

```bash
pip install -r requirements.txt
cp .env.example .env
# .env에 OPENROUTER_API_KEY 설정
uvicorn app.main:app --port 8001
```

브라우저에서 `http://localhost:8001` 접속

### 3. Railway 배포

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/template)

Railway URL: https://bizplan-generator.up.railway.app

## API Keys

`.env` 파일에 설정:
```
OPENROUTER_API_KEY=필수 (Claude Sonnet 4.6)
FIRECRAWL_API_KEY=필수 (시장 조사 — Statista, PitchBook 등 검색)
```

## Pipeline

```
Phase 1: 아이템 구체화
  └── 00_item_brief.md

Phase 2: 시장 조사 (5단계)
  ├── 01_market_size.md (시장 규모 + TAM/SAM/SOM)
  ├── 02_target_customers.md (타겟 고객 + 페르소나)
  ├── 03_competitors.md (경쟁사 분석)
  ├── 04_go_to_market.md (시장 진입 전략)
  └── 05_founder_fit.md (창업자 적합성)

Phase 3: 사업계획서 작성
  └── 06_사업계획서_최종.md

Phase 4: 최종 출력
  ├── 사업계획서.pdf
  ├── 사업계획서.docx
  └── charts/*.png (시장 규모, 경쟁사 포지셔닝 등)
```

## Tech Stack

- FastAPI + Jinja2 (웹앱)
- OpenRouter API — Claude Sonnet 4.6 (사업계획서 작성)
- matplotlib (차트 자동 생성)
- python-docx (DOCX 생성)
- Pretendard 폰트 (한글 차트)

## License

MIT
