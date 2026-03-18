"""
writer.py — OpenRouter API로 사업계획서 작성 (SKILL.md 수준 프롬프트)
"""

import httpx
import os
from typing import Optional

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

SYSTEM_PROMPT = """당신은 정부 창업지원사업 사업계획서 전문 컨설턴트입니다.
"예비창업패키지" 사업계획서를 전문적으로 작성하며, 다수의 서류 심사 합격 사례를 만든 경험이 있습니다.

## 작성 스타일 (Perplexity Computer 수준)

서술형 문단 중심. 표는 일정/예산/팀/협력기관/개요요약에만 사용.

◦ = 소주제 (볼드, 콜론 뒤에 핵심 메시지)
- = 세부 내용 (2~3문장 문단, 데이터+출처 인라인)

## 절대 금지
1. 본문을 표로 정리하지 마라 — 표는 일정/예산/팀/협력기관/개요요약에만
2. ### #### 소제목 남발하지 마라 — ◦ 마커로 충분
3. 섹션 제목에 — (em dash) 쓰지 마라 — _ (언더스코어) 사용
4. 데이터를 표에 가두지 마라 — 문장 안에 녹여라
5. 짧은 한 줄 불렛 쓰지 마라 — 각 - 항목은 최소 2문장
6. "~입니다" 경어체 쓰지 마라 — "~임", "~함", "~있음" 체로 작성
"""


async def call_openrouter(prompt: str, model: str = "anthropic/claude-sonnet-4.6",
                          system: str = SYSTEM_PROMPT,
                          api_key: str = None, max_tokens: int = 8000) -> str:
    """OpenRouter API 호출"""
    key = api_key or OPENROUTER_API_KEY
    if not key:
        raise ValueError("OpenRouter API 키가 설정되지 않았습니다.")

    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.3,
            }
        )
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        else:
            raise Exception(f"OpenRouter 에러: {resp.status_code} {resp.text[:200]}")


async def write_phase1(item_info: dict, api_key: str) -> str:
    """Phase 1: 아이템 구체화"""
    upload_section = item_info.get('_upload_context', '')

    prompt = f"""다음 창업 아이템을 예비창업패키지 심사위원이 바로 이해할 수 있는 수준으로 구체화해주세요.

아이템: {item_info.get('item', '')}
문제: {item_info.get('problem', '')}
고객: {item_info.get('target', '')}
이력: {item_info.get('founder', '')}
팀: {item_info.get('team', '')}
기업명: {item_info.get('company', '')}
{upload_section}

다음을 작성해주세요:

### 1. 창업아이템명 후보
| 구분 | 제안명 | 설명 |
|------|--------|------|
| 안 1 | | 기능이 직관적으로 드러나는 이름 |
| 안 2 | | 고객 가치가 드러나는 이름 |
| 안 3 | | 시장 타깃이 명확한 이름 |
| 추천 | | 선정 이유 |

### 2. 문제 정의 구조화
| 항목 | 현재 문제 | 현장 Pain Point |
각 항목별로 구체적인 현재 문제와 현장의 실제 불편을 서술.
→ 핵심 문제 정의 문장 3개 도출

### 3. 솔루션 구조화
| 단계 | 기능 | 제공 가치 |
최소 5단계 이상, 각 기능이 고객에게 주는 구체적 가치.
→ 한 줄 솔루션 정의 도출

### 4. 목표 고객
- 1차 타겟: 구체적 특징, 규모
- 2차 타겟: 확장 대상

### 5. 팀 구성 요약"""

    return await call_openrouter(prompt, api_key=api_key)


async def write_market_analysis(item_brief: str, research_data: dict, api_key: str) -> str:
    """Phase 2-1: 시장 규모 분석"""
    prompt = f"""아래 아이템과 웹 검색 결과로 시장 규모 분석을 작성하세요.

## 아이템 브리프
{item_brief}

## 웹 검색 결과
{_format_research(research_data)}

다음 형식으로 작성 (서술형, ◦/- 마커):

◦ 글로벌 시장 현황
- 글로벌 [산업] 시장: [년도] [규모] → [년도] [규모] (CAGR [X]%, [출처] [년도]). [추가 데이터]. 최소 3개 조사기관 데이터를 교차 검증하여 서술.
- 관련 하위 시장 (AI 콘텐츠 생성, AI 영상 등) 규모와 CAGR도 포함.

◦ 국내 시장 현황
- 국내 [산업] 시장: [년도] [규모] (CAGR [X]%). [타깃 규모/현황]. ([출처], [년도]).
- 정부/공공기관 발표 자료 우선.

◦ TAM / SAM / SOM
- TAM: 글로벌 전체 시장 (규모, CAGR, 출처)
- SAM: 국내 실질 유통 가능 시장 (규모, 산출 근거)
- SOM: 초기 3년 현실적 확보 시장 (타깃 수 × 단가 × 침투율 1~5% 공식으로 산출)

모든 수치에 출처와 연도를 반드시 인라인으로 명시."""

    return await call_openrouter(prompt, api_key=api_key)


async def write_target_customers(item_brief: str, research_data: dict, api_key: str) -> str:
    """Phase 2-2: 타겟 고객 세분화"""
    prompt = f"""아래 아이템과 검색 결과로 타겟 고객 세분화 보고서를 작성하세요.

## 아이템 브리프
{item_brief}

## 웹 검색 결과
{_format_research(research_data)}

다음을 포함 (서술형):

◦ 1차 타겟
- 규모 (기관 수, 사용자 수 등 구체적 통계)
- 주요 특징, Pain Points
- 구매 의향/구매 기준

◦ 2차 타겟
- 확장 대상과 규모

◦ 고객 페르소나 3개
각 페르소나별로:
| 항목 | 내용 |
|------|------|
| 이름(가명) | |
| 직함 | |
| 주요 업무 | |
| 핵심 Pain Point | |
| 기술 수용도 | |
| 구매 기준 | |
| 최대 관심사 | |

◦ 고객 요구-가치 매핑
| 고객 세그먼트 | 주요 요구사항 | 자사 제공 가치 |"""

    return await call_openrouter(prompt, api_key=api_key)


async def write_competitors(item_brief: str, research_data: dict, api_key: str) -> str:
    """Phase 2-3: 경쟁사 분석"""
    prompt = f"""아래 아이템과 경쟁사 검색 결과로 종합 경쟁사 분석을 작성하세요.

## 아이템 브리프
{item_brief}

## 웹 검색 결과
{_format_research(research_data)}

다음을 포함:

◦ 핵심 기능 커버리지 비교
| 경쟁사 | 기능1 | 기능2 | 기능3 | ... | 한국어 | 가격 |
O = 지원, △ = 부분, X = 미지원
최소 8개 이상 경쟁사 비교.

◦ 주요 경쟁사 심층 분석 (직접/간접/대체재 분류)
| 구분 | 경쟁사 | 강점 | 약점 | 우리의 차별화 | 투자/밸류에이션 |
- 각 경쟁사의 투자 현황, ARR, 밸류에이션을 검색 결과에서 추출하여 포함

◦ 핵심 공백(Gap) 분석
- 시장에서 충족되지 않는 니즈를 구체적으로 서술
- "~을 동시에 제공하는 제품은 현재 존재하지 않음" 형태

◦ 가격대 포지셔닝
- 고가/중간/저가 경쟁사와 우리의 위치"""

    return await call_openrouter(prompt, api_key=api_key)


async def write_go_to_market(item_brief: str, research_data: dict, api_key: str) -> str:
    """Phase 2-4: 시장 진입 전략"""
    prompt = f"""아래 아이템과 검색 결과로 시장 진입 전략을 작성하세요.

## 아이템 브리프
{item_brief}

## 웹 검색 결과
{_format_research(research_data)}

다음을 포함 (서술형, ◦/- 마커):

◦ 고객 의사결정 구조
- 누가 구매를 결정하나, 예산 편성 시기, 구매 경로

◦ 조달/구매 프로세스
- 수의계약(2,000만 원 미만) → 제3자단가계약 → 나라장터 등 경로
- 필요 인증 (GS인증 등)

◦ 정부 지원사업 레버
- 활용 가능한 정부 정책/지원사업 구체적으로

◦ 단계별 진입 전략
- 1단계 (초기 6개월): 타깃, 방법, 시기, KPI
- 2단계 (확장 6~18개월): 타깃, 방법, 시기, KPI
- 3단계 (스케일업 18개월~): 타깃, 방법, 시기, KPI

◦ 예상 장애물 및 해결 방안
◦ 법규/규제 리스크"""

    return await call_openrouter(prompt, api_key=api_key)


async def write_founder_fit(item_brief: str, item_info: dict, api_key: str) -> str:
    """Phase 2-5: Founder-Market Fit 분석"""
    prompt = f"""아래 아이템과 창업자 정보로 Founder-Market Fit 분석을 작성하세요.

## 아이템 브리프
{item_brief}

## 창업자 정보
- 이력: {item_info.get('founder', '')}
- 팀: {item_info.get('team', '')}

다음을 포함:

◦ 창업자 핵심 역량
| 역량 영역 | 보유 역량 | 아이템 연결성 |

◦ 창업자-아이템 연결성
- 왜 이 창업자가 이 문제를 해결하는가 (구체적 기술 경험 서술)
- "~기반 시스템 구축 경력: ~연동, ~설계·운영 경험 보유" 형태로 구체적으로

◦ 경쟁 창업자와의 비교
| 비교 항목 | 우리 창업자 | 일반 IT 창업자 |

◦ 심사위원 설득 포인트 4개

◦ 창업자 포지셔닝 핵심 문장 3개

◦ 실행력 강조
- "MVP 핵심 기능의 N% 이상을 대표자 자체 개발 가능" 형태 포함"""

    return await call_openrouter(prompt, api_key=api_key)


async def write_final_bizplan(all_research: str, item_info: dict, api_key: str) -> str:
    """Phase 3: 최종 사업계획서 작성"""
    prompt = f"""아래 리서치 결과를 바탕으로 예비창업패키지 공식 양식에 맞는 사업계획서 전문을 작성하세요.

{all_research}

## 반드시 따를 구조 (정확히 이 순서):

# 예비창업패키지 예비창업자 사업계획서

## □ 일반현황
| 항목 | 내용 |
| 창업아이템명 | [기술명]이 적용된 [기능]의 [제품/서비스] |
| 산출물(협약기간 내 목표) | [산출물과 수량] |
| 직업(직장명 기재 불가) | [직업명] |
| 기업(예정)명 | {item_info.get('company', '')} |

(예비)창업팀 구성 현황(대표자 본인 제외)
| 순번 | 직위 | 담당 업무 | 보유역량(경력 및 학력 등) | 구성 상태 |

## □ 창업 아이템 개요(요약)
| 항목 | 내용 |
명칭+범주 / 아이템 개요 / 문제인식 / 실현가능성 / 성장전략 / 팀구성 - 각 2~3문장 요약

## 1. 문제 인식(Problem)_창업 아이템의 필요성

◦ 국내외 시장 현황: [핵심 메시지]
- (2~3문장 서술형, 데이터+출처 인라인) × 3~4개

◦ 핵심 문제: [문제의 본질]
- 시간 비용: (서술형 2~3문장)
- 금전 비용: (서술형 2~3문장)
- 품질 편차: (서술형 2~3문장)
- 디지털 전환 지체: (서술형 2~3문장)

◦ 문제 해결을 위한 창업 아이템의 필요성
- (서술형 2~3문장) × 2개

## 2. 실현 가능성(Solution)_창업 아이템의 개발 계획

◦ 창업 아이템 개발 계획 (협약기간 12개월 내 [산출물] N종 완성)
- 핵심 기능 모듈 N종: ① [모듈] ② [모듈] ③ [모듈] ④ [모듈]
- 부분 수정 기능: (설명)
- LMS/표준 연동: (설명)

◦ 차별성 및 경쟁력 확보 전략
- End-to-End: 경쟁사는 [A사](기능1만), [B사](기능2만)... 우리는 전 과정 완결.
- 한국어/국내 맞춤화: (설명)
- 가격 경쟁력: 고가 [A사] $[가격]/년 대비 (전략)

◦ 정부지원사업비 집행 방향
- 1단계(20백만원): (구체적 용도)
- 2단계(20백만원): (구체적 용도)

< 사업추진 일정(협약기간 내) >
| 구분 | 추진 내용 | 추진 기간 | 세부 내용 |
(4~5행)

< 1단계 정부지원사업비 집행계획 >
| 비목 | 산출 근거 | 정부지원사업비(원) |
산출근거는 "AI 백엔드 개발자 프리랜서 계약 (월 200만원 × 5개월)" 형태. 합계 20,000,000.

< 2단계 정부지원사업비 집행계획 >
| 비목 | 산출 근거 | 정부지원사업비(원) |
합계 20,000,000.

## 3. 성장전략(Scale-up)_사업화 추진 전략

◦ 경쟁사 분석 및 목표 시장 진입 전략
- 경쟁 구도: 글로벌 N개 경쟁사 분석 결과, [포지션]은 비어있음.
- 1차 타겟 진입: [기관 N개] 중 [정부 지원사업] 선정 N개 집중 공략.
- 진입 타이밍: [예산 편성 주기]에 맞춰 영업. 수의계약으로 빠른 레퍼런스.
- 레퍼런스 전략: N개 무료 PoC → 성과 데이터 → 유료 전환.

◦ 비즈니스 모델 (수익화 모델)
- [모델1]: [가격]. [전체 확보 시 ARR X억 원].
- [모델2]: [보완 과금].
- [확장]: [2차 시장] 순차 확장.

◦ 투자 유치 전략
- 예비창업패키지 → 초기창업패키지 딥테크형 → TIPS 단계별.
- 레퍼런스 확보 후 [VC 유형] 대상 추진. IR 핵심 지표 포함.

◦ 전체 사업 로드맵 및 중장기 사회적 가치
- 환경: (구체적)
- 사회: (구체적)
- 지배구조: (구체적)

< 사업추진 일정(전체 사업단계) >
| 구분 | 추진 내용 | 추진 기간 | 세부 내용 |

## 4. 팀 구성(Team)_대표자 및 팀원 구성 계획

◦ 대표자 역량
- [도구/기술명] 기반 [시스템] 구축 경력: [연동/설계/운영] 경험 보유. (2~3문장 구체적)
- [아이템] 관련 프로토타입 직접 개발 경험: [워크플로우] 구현 검증 완료. (2~3문장)
- [교육/자격]: [관련 교육 이수] 및 창업 준비 중.
- [아이템명] 창업 아이템은 대표자가 직접 보유한 [기술]을 기반으로 하며, MVP 핵심 기능의 70% 이상을 대표자 자체 개발 가능.

< 팀 구성(안) >
| 구분 | 직위 | 담당 업무 | 보유역량(경력 및 학력 등) | 구성 상태 |

< 협력 기관 현황 및 협업 방안 >
| 구분 | 파트너명 | 보유역량 | 협업방안 | 협력 시기 |
최소 3개 이상 협력기관."""

    return await call_openrouter(prompt, api_key=api_key, max_tokens=12000)


def _format_research(data: dict) -> str:
    """리서치 데이터를 프롬프트용 텍스트로 변환"""
    lines = []
    for key, results in data.items():
        lines.append(f"\n### {key}")
        if isinstance(results, list):
            for r in results:
                title = r.get("title", "")
                desc = r.get("description", r.get("snippet", ""))
                lines.append(f"- {title}: {desc}")
        elif isinstance(results, dict):
            for sub_key, sub_results in results.items():
                lines.append(f"\n#### {sub_key}")
                if isinstance(sub_results, list):
                    for r in sub_results:
                        title = r.get("title", "")
                        desc = r.get("description", "")
                        lines.append(f"- {title}: {desc}")
    return "\n".join(lines)
