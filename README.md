# BizPlan Generator

AI 기반 예비창업패키지 사업계획서 자동 생성기입니다. Claude Code 스킬 + 웹앱으로 사용 가능합니다.

## Features

- 창업 아이템 정보만 입력하면 **예비창업패키지 사업계획서** 자동 생성
- 시장 조사 (Statista, PitchBook, THE VC 등 자동 연결)
- 경쟁사 분석 + 포지셔닝 맵 차트
- TAM/SAM/SOM 시장 규모 분석
- 최종 산출물: **PDF + DOCX + 차트**
- 파일 업로드 (참고 자료 반영)

## Installation (Claude Code Skill)

```bash
git clone https://github.com/daniel8824-del/bizplan-generator.git ~/.claude/skills/business-plan-2026
```

## Usage

Claude Code에서:
```
/bizplan AI 기반 강의 콘텐츠 자동 생성 SaaS
```

## Web App

```bash
pip install -r requirements.txt
uvicorn app.main:app --port 8001
```

Railway 배포: https://bizplan-generator.up.railway.app

## API Keys

```
OPENROUTER_API_KEY=필수 (Claude Sonnet 4.6)
```

## License

MIT
