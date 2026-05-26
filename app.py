"""Text Marketing LM — Streamlit 3-column studio (tsbookmaker pattern)."""
from __future__ import annotations

import io
import time
import uuid
import zipfile
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from core import llm as llm_mod
from core import subtitle as subtitle_mod
from core import user_settings as settings_mod
from core.runner import StudioResult, run_all, run_one
from studio import list_studios, sections
from studio._base import StudioContext

load_dotenv()

APP_DIR = Path(__file__).resolve().parent
PROJECTS_DIR = APP_DIR / "data" / "projects"
KNOWLEDGE_PATH = APP_DIR / "knowledge" / "channel-style-research.md"

st.set_page_config(page_title="Text Marketing LM", layout="wide", initial_sidebar_state="expanded")


# ─────────────────────────── session state ───────────────────────────
def _init_state() -> None:
    st.session_state.setdefault("settings", settings_mod.load())
    st.session_state.setdefault("project_name", "")
    st.session_state.setdefault("subtitle_result", None)
    st.session_state.setdefault("results", {})  # key -> StudioResult
    st.session_state.setdefault("selected_key", None)
    st.session_state.setdefault("ping_status", None)


def _load_channel_guide() -> str:
    if not KNOWLEDGE_PATH.exists():
        return ""
    return KNOWLEDGE_PATH.read_text(encoding="utf-8")


def _project_dir() -> Path | None:
    name = (st.session_state.project_name or "").strip()
    if not name:
        return None
    p = PROJECTS_DIR / name
    p.mkdir(parents=True, exist_ok=True)
    return p


def _save_source(text: str) -> None:
    pd = _project_dir()
    if pd:
        (pd / "source.txt").write_text(text, encoding="utf-8")


def _load_existing_results() -> None:
    pd = _project_dir()
    if not pd:
        return
    for s in list_studios():
        out = pd / s.key / s.output_filename
        if out.exists() and s.key not in st.session_state.results:
            st.session_state.results[s.key] = StudioResult(
                key=s.key, title=s.title, status="done",
                output=out.read_text(encoding="utf-8"), output_path=out,
            )


# ─────────────────────────── sidebar ───────────────────────────
def render_sidebar() -> None:
    s: settings_mod.Settings = st.session_state.settings
    with st.sidebar:
        st.header("⚙ API 설정")

        s.base_url = st.text_input("API URL", value=s.base_url, help="Ubion LiteLLM 프록시 주소")
        s.api_key = st.text_input("API 키", value=s.api_key, type="password", help="사내 대시보드(/ui/)에서 발급한 virtual key")
        st.caption(f"모델: 💰 **{settings_mod.FIXED_MODEL}** (저렴, 고정)")

        with st.expander("고급 설정", expanded=False):
            s.temperature = st.slider("Temperature", 0.0, 1.5, s.temperature, step=0.1)
            s.max_tokens = st.slider("Max Tokens", 1024, 16384, s.max_tokens, step=512)
            s.parallelism = st.slider("병렬 실행", 1, 8, s.parallelism)

        st.subheader("공통 변수")
        s.target_keyword = st.text_input("타깃 키워드", value=s.target_keyword, placeholder="예: AI 마케팅 자동화")
        s.brand_name = st.text_input("브랜드명", value=s.brand_name, placeholder="예: Acme Corp")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("연결 테스트", use_container_width=True):
                provider_obj = llm_mod.build_provider(s)
                ok, msg = provider_obj.ping()
                st.session_state.ping_status = (ok, msg)
        with c2:
            if st.button("💾 저장", use_container_width=True, type="primary"):
                settings_mod.save(s)
                st.success("저장 완료")

        if st.session_state.ping_status:
            ok, msg = st.session_state.ping_status
            (st.success if ok else st.error)(f"{'✅' if ok else '❌'} {msg}")

        st.divider()
        st.subheader("프로젝트")
        existing = sorted(
            [p.name for p in PROJECTS_DIR.iterdir() if p.is_dir()] if PROJECTS_DIR.exists() else []
        )
        chosen = st.selectbox(
            "프로젝트 선택",
            options=["(새 프로젝트)"] + existing,
            index=(existing.index(st.session_state.project_name) + 1)
            if st.session_state.project_name in existing else 0,
        )
        if chosen == "(새 프로젝트)":
            new_name = st.text_input("새 프로젝트 이름", value="", placeholder=f"project-{datetime.now():%Y%m%d}")
            if st.button("➕ 만들기", use_container_width=True):
                final = new_name.strip() or f"project-{datetime.now():%Y%m%d-%H%M%S}"
                st.session_state.project_name = final
                st.session_state.results = {}
                st.session_state.subtitle_result = None
                _project_dir()
                st.rerun()
        else:
            if chosen != st.session_state.project_name:
                st.session_state.project_name = chosen
                st.session_state.results = {}
                pd = PROJECTS_DIR / chosen
                src = pd / "source.txt"
                if src.exists():
                    txt = src.read_text(encoding="utf-8")
                    st.session_state.subtitle_result = subtitle_mod.SubtitleResult(
                        text=txt, line_count=txt.count("\n") + 1, char_count=len(txt), source_format="txt",
                    )
                _load_existing_results()
                st.rerun()


# ─────────────────────────── left: studios ───────────────────────────
STATUS_ICON = {"pending": "⚪", "running": "🟡", "done": "✅", "error": "❌"}


def render_studio_panel() -> None:
    st.subheader("🎛 스튜디오")
    has_project = bool(st.session_state.project_name)
    has_subtitle = bool(st.session_state.subtitle_result)
    ready = has_project and has_subtitle
    if not ready:
        missing = []
        if not has_project:
            missing.append("**1단계** — 사이드바(⚙ 왼쪽 `»` 클릭) → `프로젝트 선택` → `(새 프로젝트)` → 이름 입력 → `➕ 만들기`")
        if not has_subtitle:
            missing.append("**2단계** — 우측 `자막 소스` 패널에서 .srt/.vtt/.ass/.txt 업로드")
        missing.append("**3단계** — 여기서 `▶ 전체 17개 실행`")
        st.info("\n\n".join(missing))
        return

    col_a, col_b = st.columns([2, 1])
    with col_a:
        if st.button("▶ 전체 17개 실행", type="primary", use_container_width=True, disabled=not ready):
            _run_bulk()
    with col_b:
        done_n = sum(1 for r in st.session_state.results.values() if r.status == "done")
        st.metric("완료", f"{done_n}/17")

    for section_name, studios in sections().items():
        with st.expander(section_name, expanded=True):
            for s in studios:
                r = st.session_state.results.get(s.key)
                icon = STATUS_ICON.get(r.status if r else "pending", "⚪")
                row = st.columns([0.4, 4, 1, 1])
                row[0].markdown(f"### {icon}")
                row[1].markdown(f"**{s.title}**  \n<span style='color:#888;font-size:0.85em'>{s.description}</span>", unsafe_allow_html=True)
                if row[2].button("열기", key=f"open_{s.key}", use_container_width=True, disabled=not (r and r.status == "done")):
                    st.session_state.selected_key = s.key
                if row[3].button("재실행", key=f"rerun_{s.key}", use_container_width=True):
                    _run_single(s.key)
                if r and r.status == "error":
                    st.caption(f"❌ {r.error.splitlines()[0] if r.error else 'unknown error'}")


def _build_ctx() -> StudioContext | None:
    pd = _project_dir()
    if not pd or not st.session_state.subtitle_result:
        return None
    s = st.session_state.settings
    return StudioContext(
        project_dir=pd,
        subtitle_text=st.session_state.subtitle_result.text,
        channel_guide=_load_channel_guide(),
        llm=llm_mod.build_provider(s),
        extra={"target_keyword": s.target_keyword, "brand_name": s.brand_name},
        parallelism=s.parallelism,
    )


def _run_bulk() -> None:
    ctx = _build_ctx()
    if not ctx:
        st.error("프로젝트와 자막을 먼저 준비하세요.")
        return
    progress = st.progress(0.0, text="시작 중…")
    total = len(list_studios())
    done = {"n": 0}

    def _cb(r: StudioResult) -> None:
        if r.status in ("done", "error"):
            done["n"] += 1
            progress.progress(done["n"] / total, text=f"{r.title} {STATUS_ICON[r.status]}")
        st.session_state.results[r.key] = r

    t0 = time.time()
    report = run_all(ctx, on_progress=_cb)
    st.session_state.results.update(report.results)
    elapsed = time.time() - t0
    progress.progress(1.0, text=f"완료 ({elapsed:.1f}s)")
    st.toast(f"17개 스튜디오 실행 완료 — {elapsed:.1f}s", icon="✅")


def _run_single(key: str) -> None:
    ctx = _build_ctx()
    if not ctx:
        st.error("프로젝트와 자막을 먼저 준비하세요.")
        return
    with st.spinner(f"{key} 재실행 중…"):
        r = run_one(ctx, key)
    st.session_state.results[key] = r
    if r.status == "done":
        st.toast(f"{r.title} 재생성 완료", icon="✅")
        st.session_state.selected_key = key
    else:
        st.error(f"실패: {r.error.splitlines()[0] if r.error else 'unknown'}")


# ─────────────────────────── center: output preview ───────────────────────────
def render_output_panel() -> None:
    st.subheader("📄 산출물")
    key = st.session_state.selected_key
    if not key or key not in st.session_state.results:
        st.caption("좌측에서 완료된 스튜디오의 **열기** 버튼을 누르세요.")
        if st.session_state.results:
            _render_zip_download()
        return

    r: StudioResult = st.session_state.results[key]
    st.markdown(f"#### {r.title}")
    if r.status != "done":
        st.warning(f"상태: {r.status}")
        if r.error:
            st.code(r.error)
        return

    tab_view, tab_raw = st.tabs(["미리보기", "Markdown 원본"])
    with tab_view:
        st.markdown(r.output)
    with tab_raw:
        st.code(r.output, language="markdown")

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "💾 .md 다운로드",
            data=r.output.encode("utf-8"),
            file_name=f"{r.key}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with c2:
        _render_zip_download(container=c2)


def _render_zip_download(container=None) -> None:
    done = [r for r in st.session_state.results.values() if r.status == "done"]
    if not done:
        return
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for r in done:
            zf.writestr(f"{r.key}.md", r.output)
    target = container or st
    target.download_button(
        f"📦 전체 ZIP ({len(done)}개)",
        data=buf.getvalue(),
        file_name=f"{st.session_state.project_name or 'output'}.zip",
        mime="application/zip",
        use_container_width=True,
        key=f"zip_{uuid.uuid4().hex[:6]}",
    )


# ─────────────────────────── right: source ───────────────────────────
def render_source_panel() -> None:
    st.subheader("🎬 자막 소스")
    if not st.session_state.project_name:
        st.info("사이드바에서 프로젝트를 먼저 만드세요.")
        return

    uploaded = st.file_uploader(
        "자막 업로드 (.srt / .vtt / .ass / .txt)",
        type=["srt", "vtt", "ass", "ssa", "txt"],
        accept_multiple_files=False,
    )
    if uploaded is not None:
        upload_key = f"{uploaded.name}:{uploaded.size}"
        if st.session_state.get("_last_upload_key") != upload_key:
            result = subtitle_mod.parse(uploaded.name, raw_bytes=uploaded.getvalue())
            st.session_state.subtitle_result = result
            st.session_state._last_upload_key = upload_key
            _save_source(result.text)
        st.success(f"자막 파싱 완료 ({st.session_state.subtitle_result.source_format})")

    r = st.session_state.subtitle_result
    if r:
        m1, m2, m3 = st.columns(3)
        m1.metric("라인", f"{r.line_count:,}")
        m2.metric("글자", f"{r.char_count:,}")
        m3.metric("형식", r.source_format)
        with st.expander("정규화된 본문 미리보기", expanded=False):
            preview = r.text[:1500] + ("…" if len(r.text) > 1500 else "")
            st.text_area("preview", preview, height=240, label_visibility="collapsed")
    else:
        st.caption("자막을 업로드하면 17개 스튜디오가 활성화됩니다.")

    st.divider()
    with st.expander("ℹ️ 산출물 정책", expanded=False):
        st.markdown(
            "- 자막 원문은 외부 노출 금지. **재가공된 텍스트만** 산출됩니다.\n"
            "- 17개 산출물은 `data/projects/<프로젝트>/<key>/output.md`에 저장됩니다.\n"
            "- 채널별 톤·길이 규칙은 [knowledge/channel-style-research.md](knowledge/channel-style-research.md) 참조."
        )


# ─────────────────────────── main ───────────────────────────
def main() -> None:
    _init_state()
    render_sidebar()
    st.title("Text Marketing LM")
    st.caption("자막 1개 → 17가지 마케팅 텍스트 자산 (블로그·뉴스레터·LinkedIn·카드뉴스·SEO·PAS·광고·푸시·랜딩·리뷰·페르소나·태그·프로모션·보도자료 …)")

    left, center, right = st.columns([1.1, 1.4, 0.9], gap="medium")
    # Render right (source) first so subtitle_result is set before left (studios) checks it.
    with right:
        render_source_panel()
    with left:
        render_studio_panel()
    with center:
        render_output_panel()


if __name__ == "__main__":
    main()
