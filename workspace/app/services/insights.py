import re

from huggingface_hub import InferenceClient

from config import HF_API_TOKEN, HF_API_TIMEOUT, HF_MODEL, PROMPT_PATH


def load_prompts() -> dict[str, str]:
    if not PROMPT_PATH.exists():
        return {"summary": "", "insight": ""}

    text = PROMPT_PATH.read_text(encoding="utf-8")
    sections = {"summary": "", "insight": ""}
    current = None
    for line in text.splitlines():
        if line.strip() == "[SUMMARY_PROMPT]":
            current = "summary"
            continue
        if line.strip() == "[INSIGHT_PROMPT]":
            current = "insight"
            continue
        if current:
            sections[current] += line + "\n"
    return {k: v.strip() for k, v in sections.items()}


def _format_stats(stats: dict) -> str:
    lines = [
        f"총 탄소발자국: {stats.get('total_t_co2eq', 0)} t CO2eq",
        f"분석 지역 수: {stats.get('region_count', 0)}",
        f"분석 기간 수: {stats.get('period_count', 0)}",
    ]
    if stats.get("top_regions"):
        lines.append("상위 지역(톤):")
        for name, val in stats["top_regions"].items():
            lines.append(f"  - {name}: {val}")
    if stats.get("top_upjong_t"):
        lines.append("상위 업종(톤):")
        for name, val in stats["top_upjong_t"].items():
            lines.append(f"  - {name}: {val}")
    return "\n".join(lines)


def _call_hf_api(prompt: str) -> str:
    if not HF_API_TOKEN:
        return (
            "Hugging Face API 토큰이 설정되지 않았습니다. "
            "`.env` 파일에 `HF_API_TOKEN`을 추가해 주세요."
        )

    client = InferenceClient(token=HF_API_TOKEN, timeout=HF_API_TIMEOUT)
    try:
        response = client.chat_completion(
            model=HF_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as exc:
        err = str(exc)
        if "503" in err or "loading" in err.lower():
            return "모델이 로딩 중입니다. 잠시 후 다시 시도해 주세요."
        return f"AI 분석 요청 중 오류가 발생했습니다: {exc}"


def _fallback_summary(stats: dict) -> tuple[str, str]:
    total = stats.get("total_t_co2eq", 0)
    regions = stats.get("top_regions", {})
    upjong = stats.get("top_upjong_t", {})

    top_region = next(iter(regions), ("-", 0))
    top_upjong_name = next(iter(upjong), "-")

    summary = (
        f"선택 조건 기준 총 탄소발자국은 약 {total:,.2f} t CO2eq입니다. "
        f"배출이 가장 큰 지역은 {top_region[0]}({top_region[1]:,.2f} t)이며, "
        f"업종별로는 {top_upjong_name} 부문의 비중이 두드러집니다."
    )
    insights = (
        "· 운송·숙박·식음료 등 탄소집약 업종의 지출 구조를 점검하면 감축 여지를 파악할 수 있습니다.\n"
        "· 상위 배출 지역은 계절·이벤트별 수요 관리와 대중교통·친환경 숙박 인센티브를 검토해 보세요.\n"
        "· 동일 광역 내 시군구 간 격차가 크면 지역 맞춤형 탄소저감 정책을 우선 적용할 수 있습니다."
    )
    return summary, insights


def generate_ai_content(stats: dict, selection_summary: str) -> tuple[str, str]:
    prompts = load_prompts()
    stats_text = _format_stats(stats)

    summary_prompt = prompts.get("summary", "").format(
        stats=stats_text,
        selection=selection_summary,
    )
    insight_prompt = prompts.get("insight", "").format(
        stats=stats_text,
        selection=selection_summary,
    )

    if not HF_API_TOKEN:
        return _fallback_summary(stats)

    summary_raw = _call_hf_api(summary_prompt)
    insight_raw = _call_hf_api(insight_prompt)

    if _is_error_response(summary_raw):
        return _fallback_summary(stats)

    summary = _clean_text(summary_raw)
    insights = _clean_text(insight_raw)
    return summary, insights


def _is_error_response(text: str) -> bool:
    return bool(
        re.search(r"오류|error|토큰|503|401|403", text, re.IGNORECASE)
    )


def _clean_text(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text.strip())
