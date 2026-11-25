"""Fetch pinned public browser libraries on a fresh Streamlit deployment.

Only public library archives are requested; no transcript or user input is sent.
"""
import hashlib
import io
from pathlib import Path
import tarfile
from urllib.request import Request, urlopen


SOURCES = {
    'pdf': ('https://registry.npmjs.org/pdfjs-dist/-/pdfjs-dist-3.11.174.tgz', '11402926f38e7d5c71e63f4c3fdcfcb9172afd5bd202900994cecfa8ee7a98c4'),
    'tesseract': ('https://registry.npmjs.org/tesseract.js/-/tesseract.js-5.1.1.tgz', '0d08b3722256aacfc652d03b68183a9ed3c997b54778842e7db73ff08a6ae81a'),
    'core': ('https://registry.npmjs.org/tesseract.js-core/-/tesseract.js-core-5.1.1.tgz', '8c1c83c01ecbfcaeb62a5a2d1023ea98162cad082aa47b9c2c39c129847dba8a'),
    'eng': ('https://cdn.jsdelivr.net/npm/@tesseract.js-data/eng@1.0.0/4.0.0_best_int/eng.traineddata.gz', '45b4cb346724ac1774f1c36f42f182b887bcdb28ebe63e6fff90ac41f3fcff91'),
    'kor': ('https://cdn.jsdelivr.net/npm/@tesseract.js-data/kor@1.0.0/4.0.0_best_int/kor.traineddata.gz', '78c21276ab14c9bb734d83be1055d9fe5469a4e7e977c51ad385be5737e61126'),
}


def download(key):
    url, expected = SOURCES[key]
    with urlopen(Request(url, headers={'User-Agent': 'graduation-app-assets/1'}), timeout=60) as response:
        data = response.read(30_000_001)
    if len(data) > 30_000_000 or hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f'공개 라이브러리 무결성 확인 실패: {key}')
    return data


def install_vendor(vendor: Path):
    vendor.mkdir(parents=True, exist_ok=True)
    for key in ('pdf', 'tesseract', 'core'):
        with tarfile.open(fileobj=io.BytesIO(download(key)), mode='r:gz') as archive:
            for item in archive:
                if not item.isfile():
                    continue
                path = item.name
                dest = None
                if key == 'pdf':
                    if path in ('package/build/pdf.min.js', 'package/build/pdf.worker.min.js'):
                        dest = vendor / Path(path).name
                    elif path == 'package/LICENSE':
                        dest = vendor / 'LICENSE-APACHE-2.0.txt'
                    elif path.startswith(('package/cmaps/', 'package/standard_fonts/')):
                        dest = vendor / path.removeprefix('package/')
                elif key == 'tesseract' and path in ('package/dist/tesseract.min.js', 'package/dist/worker.min.js'):
                    dest = vendor / 'ocr' / Path(path).name
                elif key == 'core' and path.startswith('package/tesseract-core') and path.endswith('.wasm.js'):
                    dest = vendor / 'ocr' / Path(path).name
                if dest is not None:
                    if not dest.resolve().is_relative_to(vendor.resolve()):
                        raise ValueError('잘못된 라이브러리 경로')
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(archive.extractfile(item).read())
    for lang in ('eng', 'kor'):
        dest = vendor / 'ocr' / 'lang' / f'{lang}.traineddata.gz'
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(download(lang))
