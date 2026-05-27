"""Text Marketing LM — Streamlit 3-column studio (tsbookmaker pattern)."""
from __future__ import annotations

import io
import shutil
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
from core.runner import StudioResult, find_studio_dir, run_all, run_one, studio_dir_name
from studio import get_studio, list_studios, sections
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
        folder = find_studio_dir(pd, s)
        if folder is None:
            continue
        out = folder / "output.md"
        if out.exists() and s.key not in st.session_state.results:
            html_path = folder / "output.html"
            html_text = html_path.read_text(encoding="utf-8") if html_path.exists() else ""
            cards_dir = folder / "cards"
            png_paths = sorted(cards_dir.glob("card_*.png")) if cards_dir.exists() else []
            docx_path = folder / "output.docx"
            st.session_state.results[s.key] = StudioResult(
                key=s.key, title=s.title, status="done",
                output=out.read_text(encoding="utf-8"), output_path=out,
                html=html_text, html_path=html_path if html_path.exists() else None,
                png_paths=png_paths,
                docx_path=docx_path if docx_path.exists() else None,
            )


# ─────────────────────────── sidebar (project mgmt only) ───────────────────────────
def render_sidebar() -> None:
    with st.sidebar:
        st.header("📂 프로젝트")
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
            if st.button("➕ 만들기", type="primary", use_container_width=True):
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

        if st.session_state.project_name:
            st.caption(f"📁 `data/projects/{st.session_state.project_name}/`")

            with st.expander("🗑 프로젝트 삭제", expanded=False):
                st.caption(f"`{st.session_state.project_name}` 프로젝트 폴더(자막·15개 산출물 전체)를 디스크에서 삭제합니다.")
                confirm = st.checkbox("네, 정말 삭제합니다", key=f"del_confirm_{st.session_state.project_name}")
                if st.button("🗑 삭제 실행", disabled=not confirm, use_container_width=True, type="secondary"):
                    pd = PROJECTS_DIR / st.session_state.project_name
                    try:
                        if pd.exists():
                            shutil.rmtree(pd)
                        st.session_state.project_name = ""
                        st.session_state.results = {}
                        st.session_state.subtitle_result = None
                        st.session_state.selected_key = None
                        st.session_state.pop("_last_upload_key", None)
                        st.toast("프로젝트 삭제 완료", icon="🗑")
                        st.rerun()
                    except Exception as e:
                        st.error(f"삭제 실패: {type(e).__name__}: {e}")


# ─────────────────────────── top bar (API 설정) ───────────────────────────
def render_top_api_bar() -> None:
    s: settings_mod.Settings = st.session_state.settings
    configured = bool(s.api_key)
    ping = st.session_state.ping_status
    if ping is not None:
        ok, _ = ping
        badge = "✅ 연결 확인됨" if ok else "❌ 연결 실패"
    elif configured:
        badge = "🟡 키 저장됨 · 연결 미확인"
    else:
        badge = "⚠️ API 키 미설정 — 펼쳐서 입력하세요"

    with st.expander(f"⚙ API 설정 — {badge} · 텍스트 `{settings_mod.FIXED_MODEL}` · 이미지 `{s.image_model}`", expanded=not configured):
        st.markdown("**📝 텍스트 LLM** (블로그·보도자료)")
        c1, c2 = st.columns([2, 3])
        with c1:
            s.base_url = st.text_input("API URL", value=s.base_url, help="Ubion LiteLLM 프록시 주소")
        with c2:
            s.api_key = st.text_input("API 키", value=s.api_key, type="password", help="사내 대시보드(/ui/)에서 발급한 virtual key")

        st.markdown("**🖼 이미지 모델** (카드뉴스 5종 · 비워두면 위 API URL/키 재사용)")
        i1, i2, i3 = st.columns([2, 2, 2])
        with i1:
            s.image_base_url = st.text_input(
                "이미지 API URL",
                value=s.image_base_url,
                placeholder="비워두면 위 URL 재사용",
                help="나중에 로컬 이미지 모델 붙일 때 여기에 로컬 URL 입력",
            )
        with i2:
            s.image_api_key = st.text_input(
                "이미지 API 키",
                value=s.image_api_key,
                type="password",
                placeholder="비워두면 위 키 재사용",
            )
        with i3:
            s.image_model = st.text_input(
                "이미지 모델",
                value=s.image_model,
                placeholder=settings_mod.IMAGE_MODEL,
                help="Gemini Nano Banana / gpt-image-2 / 향후 로컬 모델 이름",
            )

        with st.expander("고급 설정", expanded=False):
            c3, c4, c5 = st.columns(3)
            with c3:
                s.temperature = st.slider("Temperature", 0.0, 1.5, s.temperature, step=0.1)
            with c4:
                s.max_tokens = st.slider("Max Tokens", 1024, 16384, s.max_tokens, step=512)
            with c5:
                s.parallelism = st.slider("병렬 실행", 1, 8, s.parallelism)

        b1, b2, b3 = st.columns([1, 1, 4])
        with b1:
            if st.button("연결 테스트", use_container_width=True):
                provider_obj = llm_mod.build_provider(s)
                ok, msg = provider_obj.ping()
                st.session_state.ping_status = (ok, msg)
                st.rerun()
        with b2:
            if st.button("💾 저장", use_container_width=True, type="primary"):
                settings_mod.save(s)
                st.toast("API 설정 저장 완료", icon="💾")
        with b3:
            if ping is not None:
                ok, msg = ping
                (st.success if ok else st.error)(f"{'✅' if ok else '❌'} {msg}")


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
            missing.append("**1단계** — 좌측 사이드바(`📂 프로젝트`) → `(새 프로젝트)` 선택 → 이름 입력 → `➕ 만들기`")
        if not has_subtitle:
            missing.append("**2단계** — 우측 `🎬 자막 소스` 패널에서 .srt/.vtt/.ass/.txt 업로드")
        missing.append("**3단계** — 여기서 `▶ 텍스트 10개 일괄 실행` (카드뉴스는 개별 ▶ 클릭)")
        st.info("\n\n".join(missing))
        return

    # Bulk = text-only (blogs + press release). Card studios run via
    # Jinja2 + Playwright (no per-card API charge — local browser render).
    text_studios = [s for s in list_studios() if not s.png_renderer]
    n_text = len(text_studios)
    st.caption(
        f"💰 일괄 실행 = 텍스트 {n_text}개만 (블로그 + 보도자료) · "
        f"카드뉴스 5종은 HTML+Playwright 캡처(추가 API 비용 없음). 카드별 ▶ 재실행으로 개별 생성."
    )

    col_a, col_b, col_c = st.columns([2, 0.8, 0.8])
    with col_a:
        if st.button(
            f"▶ 텍스트 {n_text}개 일괄 실행",
            type="primary", use_container_width=True, disabled=not ready,
            help="블로그 9개 + 보도자료 1개. 카드뉴스는 비용 발생이라 개별 실행.",
        ):
            _run_bulk()
    with col_b:
        done_n = sum(1 for r in st.session_state.results.values() if r.status == "done")
        st.metric("완료", f"{done_n}/15")
    with col_c:
        with st.popover("🗑 초기화", use_container_width=True, disabled=not st.session_state.results):
            st.caption("15개 산출물을 모두 비웁니다. 자막·프로젝트는 유지됩니다.")
            if st.checkbox("네, 모두 비웁니다", key="del_all_confirm"):
                if st.button("🗑 전체 초기화 실행", use_container_width=True):
                    _delete_all_results()
                    st.rerun()

    for section_name, studios in sections().items():
        with st.expander(section_name, expanded=True):
            for s in studios:
                r = st.session_state.results.get(s.key)
                icon = STATUS_ICON.get(r.status if r else "pending", "⚪")
                has_done = bool(r and r.status == "done")
                row = st.columns([0.4, 4, 0.9, 0.9, 0.5])
                row[0].markdown(f"### {icon}")
                row[1].markdown(f"**{s.title}**  \n<span style='color:#888;font-size:0.85em'>{s.description}</span>", unsafe_allow_html=True)
                if row[2].button("열기", key=f"open_{s.key}", use_container_width=True, disabled=not has_done):
                    st.session_state.selected_key = s.key
                if row[3].button("재실행", key=f"rerun_{s.key}", use_container_width=True):
                    _run_single(s.key)
                if row[4].button("🗑", key=f"del_{s.key}", use_container_width=True, disabled=not r, help="이 스튜디오 산출물 비우기"):
                    _delete_one_result(s.key)
                    st.rerun()
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
        extra={
            "target_keyword": s.target_keyword,
            "brand_name": s.brand_name,
            "image_base_url": settings_mod.effective_image_url(s),
            "image_api_key": settings_mod.effective_image_key(s),
            "image_model": s.image_model,
        },
        parallelism=s.parallelism,
        max_tokens=s.max_tokens,
        temperature=s.temperature,
    )


def _run_bulk() -> None:
    ctx = _build_ctx()
    if not ctx:
        st.error("프로젝트와 자막을 먼저 준비하세요.")
        return

    # Bulk = text-only (image cards run individually via local Playwright)
    text_keys = [s.key for s in list_studios() if not s.png_renderer]
    with st.spinner(f"텍스트 {len(text_keys)}개 실행 중… (모델: `{ctx.llm.model}`, 병렬 {ctx.parallelism})"):
        t0 = time.time()
        report = run_all(ctx, keys=text_keys)
        elapsed = time.time() - t0

    st.session_state.results.update(report.results)

    done = [r for r in report.results.values() if r.status == "done"]
    errs = [r for r in report.results.values() if r.status == "error"]

    n_total = len(text_keys)
    if done and not errs:
        st.success(f"✅ 텍스트 {n_total}개 모두 완료 · {elapsed:.1f}s")
    elif done:
        st.warning(f"⚠️ {len(done)}/{n_total} 완료, {len(errs)}개 실패 · {elapsed:.1f}s")
    else:
        st.error(f"❌ 모든 스튜디오 실패 · {elapsed:.1f}s — API 키·URL·연결을 확인하세요.")

    if errs:
        with st.expander(f"❌ 실패 상세 ({len(errs)}개)", expanded=True):
            for r in errs[:5]:  # show first 5; rest are similar
                st.markdown(f"**{r.title}**")
                st.code(r.error, language="text")
            if len(errs) > 5:
                st.caption(f"… 외 {len(errs) - 5}개 (모두 비슷한 원인일 가능성)")


def _delete_one_result(key: str) -> None:
    pd = _project_dir()
    if pd:
        try:
            s = get_studio(key)
            # remove both new and legacy folders if either exists
            shutil.rmtree(pd / studio_dir_name(s), ignore_errors=True)
            shutil.rmtree(pd / key, ignore_errors=True)
        except Exception:
            pass
    st.session_state.results.pop(key, None)
    if st.session_state.selected_key == key:
        st.session_state.selected_key = None
    st.toast(f"산출물 비움: {key}", icon="🗑")


def _delete_all_results() -> None:
    pd = _project_dir()
    if pd:
        for s in list_studios():
            shutil.rmtree(pd / studio_dir_name(s), ignore_errors=True)
            shutil.rmtree(pd / s.key, ignore_errors=True)
    st.session_state.results = {}
    st.session_state.selected_key = None
    st.session_state.pop("del_all_confirm", None)
    st.toast("15개 산출물 모두 비움 (자막은 유지)", icon="🗑")


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
def _prefixed_name(key: str, ext: str) -> str:
    """File name like `04_ebook_chapter.md` for downloads."""
    try:
        order = get_studio(key).order
    except Exception:
        return f"{key}.{ext}"
    return f"{order:02d}_{key}.{ext}"


def render_output_panel() -> None:
    st.subheader("📄 산출물")
    key = st.session_state.selected_key
    if not key or key not in st.session_state.results:
        st.caption("좌측에서 완료된 스튜디오의 **열기** 버튼을 누르세요.")
        if st.session_state.results:
            _render_zip_download()
        return

    r: StudioResult = st.session_state.results[key]
    head_l, head_r = st.columns([5, 1])
    with head_l:
        st.markdown(f"#### {r.title}")
    with head_r:
        with st.popover("🗑 삭제", use_container_width=True):
            st.caption(f"`{r.key}` 산출물을 삭제합니다. (`▶ 재실행` 또는 `▶ 전체 15개 실행`으로 다시 생성 가능)")
            if st.button("🗑 이 산출물 삭제", type="primary", use_container_width=True, key=f"out_del_{r.key}"):
                _delete_one_result(r.key)
                st.rerun()

    if r.status != "done":
        st.warning(f"상태: {r.status}")
        if r.error:
            st.code(r.error)
        return

    studio_obj = get_studio(r.key)
    has_png = bool(r.png_paths)
    has_docx = bool(r.docx_path)

    tabs = ["📝 미리보기", "🎨 HTML 미리보기", "🔧 Markdown 원본"]
    if has_png:
        tabs.insert(1, "🖼 PNG 카드")
    tab_objs = st.tabs(tabs)
    ti = 0
    with tab_objs[ti]:
        st.markdown(r.output)
    ti += 1
    if has_png:
        with tab_objs[ti]:
            cols = st.columns(min(len(r.png_paths), 5))
            for i, p in enumerate(r.png_paths):
                with cols[i % len(cols)]:
                    st.image(str(p), caption=f"card_{i + 1}.png", use_container_width=True)
        ti += 1
    with tab_objs[ti]:
        if r.html:
            is_card = studio_obj.html_renderer.startswith("cards_")
            height = 1800 if is_card else 900
            st.components.v1.html(r.html, height=height, scrolling=True)
        else:
            st.caption("HTML 미리보기 없음. 재실행하면 생성됩니다.")
    ti += 1
    with tab_objs[ti]:
        st.code(r.output, language="markdown")

    if has_png:
        st.caption(f"🖼 Playwright HTML 캡처 · 카드 {len(r.png_paths)}장 · 로컬 렌더 (API 비용 없음)")
    if r.png_error:
        st.warning(f"🖼 PNG 메모: {r.png_error}")
    if r.docx_error:
        st.warning(f"📄 DOCX 실패: {r.docx_error}")

    cols = st.columns(5)
    with cols[0]:
        st.download_button(
            "💾 .md", data=r.output.encode("utf-8"),
            file_name=_prefixed_name(r.key, "md"),
            mime="text/markdown", use_container_width=True,
            key=f"dl_md_{r.key}",
        )
    with cols[1]:
        if r.html:
            st.download_button(
                "🎨 .html", data=r.html.encode("utf-8"),
                file_name=_prefixed_name(r.key, "html"),
                mime="text/html", use_container_width=True,
                key=f"dl_html_{r.key}",
            )
        else:
            st.button("🎨 .html", disabled=True, use_container_width=True, key=f"dl_html_dis_{r.key}")
    with cols[2]:
        if has_png:
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for i, p in enumerate(r.png_paths, start=1):
                    zf.writestr(f"card_{i}.png", p.read_bytes())
            st.download_button(
                f"🖼 PNG {len(r.png_paths)}장",
                data=buf.getvalue(),
                file_name=f"{_prefixed_name(r.key, 'png')[:-4]}_cards.zip",
                mime="application/zip", use_container_width=True,
                key=f"dl_png_{r.key}",
            )
        else:
            st.button("🖼 PNG", disabled=True, use_container_width=True, key=f"dl_png_dis_{r.key}")
    with cols[3]:
        if has_docx and r.docx_path is not None:
            st.download_button(
                "📄 .docx",
                data=r.docx_path.read_bytes(),
                file_name=_prefixed_name(r.key, "docx"),
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
                key=f"dl_docx_{r.key}",
            )
        else:
            st.button("📄 .docx", disabled=True, use_container_width=True, key=f"dl_docx_dis_{r.key}")
    with cols[4]:
        _render_zip_download(container=cols[4])


def _render_zip_download(container=None) -> None:
    done = [r for r in st.session_state.results.values() if r.status == "done"]
    if not done:
        return
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for r in done:
            md_name = _prefixed_name(r.key, "md")
            zf.writestr(f"md/{md_name}", r.output)
            if r.html:
                html_name = _prefixed_name(r.key, "html")
                zf.writestr(f"html/{html_name}", r.html)
            if r.png_paths:
                try:
                    s_obj = get_studio(r.key)
                    folder = f"png/{s_obj.order:02d}_{r.key}"
                except KeyError:
                    folder = f"png/{r.key}"
                for i, p in enumerate(r.png_paths, start=1):
                    try:
                        zf.writestr(f"{folder}/card_{i}.png", p.read_bytes())
                    except OSError:
                        pass
            if r.docx_path is not None:
                try:
                    zf.writestr(f"docx/{_prefixed_name(r.key, 'docx')}", r.docx_path.read_bytes())
                except OSError:
                    pass
    target = container or st
    target.download_button(
        f"📦 ZIP ({len(done)})",
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
        st.caption("자막을 업로드하면 15개 스튜디오가 활성화됩니다.")

    st.divider()
    st.subheader("📝 공통 변수")
    s = st.session_state.settings
    s.target_keyword = st.text_input("타깃 키워드", value=s.target_keyword, placeholder="예: AI 마케팅 자동화", key="kw")
    s.brand_name = st.text_input("브랜드명", value=s.brand_name, placeholder="예: Acme Corp", key="brand")
    st.caption("15개 스튜디오 프롬프트에 자동 주입됩니다. (선택)")

    st.divider()
    with st.expander("ℹ️ 산출물 정책", expanded=False):
        st.markdown(
            "- 자막 원문은 외부 노출 금지. **재가공된 텍스트만** 산출됩니다.\n"
            "- 15개 산출물은 `data/projects/<프로젝트>/<key>/output.md`에 저장됩니다.\n"
            "- 채널별 톤·길이 규칙은 [knowledge/channel-style-research.md](knowledge/channel-style-research.md) 참조."
        )


# ─────────────────────────── main ───────────────────────────
def main() -> None:
    _init_state()
    render_sidebar()
    st.title("Subtitle Marketing Studio")
    st.caption("자막 1개 → 15개 채널-레디 산출물 (블로그 9 · 보도자료 · 카드뉴스 5 · Threads·Instagram·KakaoTalk)")
    render_top_api_bar()

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
