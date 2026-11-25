import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path


def ensure_browser_assets():
    """Ensure only public, pinned browser libraries are available."""
    root = Path(__file__).parent
    vendor = root / 'static' / 'vendor'
    required = ('pdf.min.js', 'pdf.worker.min.js', 'cmaps/Adobe-Korea1-UCS2.bcmap',
                'ocr/tesseract.min.js', 'ocr/worker.min.js', 'ocr/tesseract-core-simd-lstm.wasm.js',
                'ocr/lang/kor.traineddata.gz', 'ocr/lang/eng.traineddata.gz')
    if all((vendor / name).is_file() for name in required):
        return
    from bootstrap_vendor import install_vendor
    install_vendor(vendor)
    if not all((vendor / name).is_file() for name in required):
        raise RuntimeError('브라우저 분석 도구를 준비하지 못했습니다.')


def main():
    ensure_browser_assets()
    st.set_page_config(page_title='졸업 에이전트', page_icon='🎓', layout='wide', initial_sidebar_state='collapsed')
    st.markdown('<style>header[data-testid="stHeader"] {visibility:hidden} .block-container {padding: 1rem 1rem 2rem; max-width: 1500px}</style>', unsafe_allow_html=True)
    html = (Path(__file__).parent / 'client' / 'index.html').read_text(encoding='utf-8')
    components.html(html, height=2200, scrolling=True)


if __name__ == '__main__':
    main()
