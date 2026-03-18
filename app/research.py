"""
research.py — 시장 조사 데이터 수집 모듈
Firecrawl API로 Statista, PitchBook, Grand View Research 등 검색
"""

import httpx
import asyncio
import os
from typing import Optional

FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "fc-d5c2972fa0ea453180e7b986bb6e5bdb")
FIRECRAWL_BASE = "https://api.firecrawl.dev/v1"


async def firecrawl_search(query: str, limit: int = 5) -> list[dict]:
    """Firecrawl 웹 검색 — Statista, PitchBook 등 고급 소스 포함
    실패 시 DuckDuckGo HTML 검색으로 fallback"""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{FIRECRAWL_BASE}/search",
                headers={"Authorization": f"Bearer {FIRECRAWL_API_KEY}"},
                json={"query": query, "limit": limit}
            )
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("data", data.get("web", []))
                if results:
                    return results
    except Exception:
        pass

    # Fallback: DuckDuckGo HTML 검색
    return await _duckduckgo_fallback(query, limit)


async def _duckduckgo_fallback(query: str, limit: int = 5) -> list[dict]:
    """Firecrawl 실패 시 DuckDuckGo HTML에서 검색 결과 추출"""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0"}
            )
            if resp.status_code == 200:
                import re
                results = []
                # 간단한 HTML 파싱으로 결과 추출
                for match in re.finditer(
                    r'class="result__a"[^>]*href="([^"]*)"[^>]*>([^<]*)</a>.*?'
                    r'class="result__snippet"[^>]*>(.*?)</span>',
                    resp.text, re.DOTALL
                ):
                    if len(results) >= limit:
                        break
                    url = match.group(1)
                    if url.startswith("//duckduckgo.com/l/?uddg="):
                        url = httpx.URL(url).params.get("uddg", url)
                    results.append({
                        "title": match.group(2).strip(),
                        "url": url,
                        "description": re.sub(r'<[^>]+>', '', match.group(3)).strip()
                    })
                return results
    except Exception:
        pass
    return []


async def firecrawl_scrape(url: str) -> Optional[str]:
    """Firecrawl 웹 스크래핑 — 특정 URL 콘텐츠 추출
    실패 시 httpx로 직접 가져옴"""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{FIRECRAWL_BASE}/scrape",
                headers={"Authorization": f"Bearer {FIRECRAWL_API_KEY}"},
                json={"url": url, "formats": ["markdown"]}
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", {}).get("markdown", "")
    except Exception:
        pass

    # Fallback: 직접 fetch
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                import re
                text = re.sub(r'<script[^>]*>.*?</script>', '', resp.text, flags=re.DOTALL)
                text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
                text = re.sub(r'<[^>]+>', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()
                return text[:5000]
    except Exception:
        pass
    return None


async def search_market_size(industry: str) -> dict:
    """시장 규모 조사 — 글로벌 + 국내"""
    queries = [
        f"{industry} market size 2025 2030 CAGR",
        f"site:statista.com {industry} market",
        f"{industry} 시장 규모 한국 2024 2025",
    ]
    results = {}
    for q in queries:
        data = await firecrawl_search(q, limit=5)
        results[q] = [
            {"title": r.get("title", ""), "url": r.get("url", ""),
             "description": r.get("description", r.get("snippet", ""))}
            for r in data[:5]
        ]
    return results


async def search_competitors(industry: str, competitors: list[str] = None) -> dict:
    """경쟁사 분석 — PitchBook/Crunchbase 투자 데이터 포함"""
    results = {}

    # 산업 경쟁사 전체 검색
    data = await firecrawl_search(f"{industry} competitors comparison 2025", limit=5)
    results["industry"] = [
        {"title": r.get("title", ""), "description": r.get("description", "")}
        for r in data[:5]
    ]

    # 개별 경쟁사 투자 데이터
    if competitors:
        for comp in competitors:
            data = await firecrawl_search(
                f"{comp} funding valuation pitchbook crunchbase", limit=3
            )
            results[comp] = [
                {"title": r.get("title", ""), "description": r.get("description", "")}
                for r in data[:3]
            ]

    return results


async def search_target_customers(target: str) -> dict:
    """타겟 고객 세분화 조사"""
    queries = [
        f"{target} 현황 통계 2024 2025",
        f"{target} pain point 문제점",
    ]
    results = {}
    for q in queries:
        data = await firecrawl_search(q, limit=5)
        results[q] = [
            {"title": r.get("title", ""), "description": r.get("description", "")}
            for r in data[:5]
        ]
    return results


async def search_go_to_market(industry: str) -> dict:
    """시장 진입 전략 조사"""
    queries = [
        f"{industry} 구매 프로세스 의사결정 한국",
        f"{industry} 정부 지원사업 2025 2026",
        f"{industry} 인증 요건 규제",
    ]
    results = {}
    for q in queries:
        data = await firecrawl_search(q, limit=5)
        results[q] = [
            {"title": r.get("title", ""), "description": r.get("description", "")}
            for r in data[:5]
        ]
    return results


async def search_thevc(keyword: str) -> Optional[str]:
    """THE VC 국내 스타트업 데이터 스크래핑"""
    return await firecrawl_scrape(f"https://thevc.kr/search?q={keyword}")


# 전체 리서치 병렬 실행
async def run_all_research(industry: str, target: str,
                           competitors: list[str] = None) -> dict:
    """4개 리서치를 병렬로 동시 실행"""
    market, customers, comps, gtm = await asyncio.gather(
        search_market_size(industry),
        search_target_customers(target),
        search_competitors(industry, competitors),
        search_go_to_market(industry),
    )
    return {
        "market_size": market,
        "target_customers": customers,
        "competitors": comps,
        "go_to_market": gtm,
    }
