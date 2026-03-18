# BizPlan Generator

예비창업패키지 사업계획서 자동 생성 파이프라인.
창업 아이템 정보를 입력하면 에이전트가 시장 조사, 경쟁사 분석, 사업계획서를 작성합니다.

## Skills

- `bizplan`: 사업계획서 생성 스킬 (/bizplan, "사업계획서", "예비창업패키지")

## Commands

```bash
pip install -r requirements.txt          # 의존성 설치
uvicorn app.main:app --port 8001         # 웹앱 실행
```

## Critical Rules

- 사업계획서는 **10페이지 이내**
- 서술형 문단 중심 (표는 일정/예산/팀에만)
- **"~임", "~함" 체** (경어체 금지)
- 차트: matplotlib + Pretendard 폰트
- 데이터에는 **출처와 연도** 반드시 명시
