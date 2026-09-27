# -*- coding: utf-8 -*-
import re
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.joyhobby.co.kr/mall/ipgo.asp?siteid=joyhobby"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.joyhobby.co.kr/"
}

def get_latest_bandai_ipgo(target_keyword: str = "반다이", preview_count: int = 5) -> dict:
    """
    조이하비 입고예정 페이지에서 지정한 키워드(기본: 반다이)의 가장 최신 입고 공지를 찾고,
    해당 공지의 상품 목록(최대 preview_count개)과 전체 정보를 추출합니다.
    """
    print(f"[*] 조이하비 입고예정 목록 조회 중: {BASE_URL}")
    session = requests.Session()
    session.headers.update(HEADERS)

    resp = session.get(BASE_URL, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.content.decode('euc-kr', errors='replace'), 'html.parser')

    # 1. 상단 공지 목록에서 대상 키워드가 포함된 링크 찾기
    notices = []
    for a in soup.find_all('a', href=re.compile(r'buyID=\d+', re.I)):
        text = a.get_text(strip=True)
        if target_keyword in text:
            href = a['href']
            m = re.search(r'buyID=(\d+)', href)
            if m:
                buy_id = int(m.group(1))
                notices.append({
                    'buy_id': buy_id,
                    'title': text,
                    'href': href
                })

    if not notices:
        print(f"[!] '{target_keyword}' 관련 입고 공지를 찾을 수 없습니다.")
        return None

    # buyID가 가장 큰 항목을 최신 공지로 선택
    latest = max(notices, key=lambda x: x['buy_id'])
    buy_id = latest['buy_id']
    title = latest['title']
    detail_url = f"https://www.joyhobby.co.kr{latest['href']}" if latest['href'].startswith('/') else latest['href']

    print(f"[*] 최신 {target_keyword} 입고 공지 발견: {title} (buyID: {buy_id})")
    print(f"[*] 상세 페이지 조회 중: {detail_url}")

    # 2. 상세 페이지 접속하여 입고 예정 상품들 파싱
    det_resp = session.get(detail_url, timeout=15)
    det_resp.raise_for_status()
    det_soup = BeautifulSoup(det_resp.content.decode('euc-kr', errors='replace'), 'html.parser')

    items_by_code = {}

    for a in det_soup.find_all('a', href=re.compile(r'ProductCode=', re.I)):
        href = a['href']
        m = re.search(r'ProductCode=([A-Za-z0-9_]+)', href)
        if not m:
            continue
        code = m.group(1)
        text = a.get_text(strip=True)

        if code not in items_by_code:
            full_href = f"https://www.joyhobby.co.kr/mall/{href}" if not href.startswith('http') else href
            items_by_code[code] = {
                'code': code,
                'title': '',
                'price': '가격 문의',
                'link': full_href
            }

        # 가격 링크 (예: 상품코드: BD5063944 ( BANDAI )판매가:47,300원)
        if text.startswith('상품코드:'):
            p_match = re.search(r'판매가\s*:\s*([\d,]+)\s*원?', text)
            if p_match:
                items_by_code[code]['price'] = f"{p_match.group(1)}원"
        # 상품명 링크
        elif len(text) > 3:
            items_by_code[code]['title'] = text

    # 유효한 상품명만 필터링
    parsed_items = [v for v in items_by_code.values() if v['title']]
    total_count = len(parsed_items)

    print(f"[*] 해당 공지의 입고예정 상품: 총 {total_count}개 확인됨")

    return {
        'buy_id': buy_id,
        'title': title,
        'url': detail_url,
        'items': parsed_items[:preview_count],
        'total_count': total_count
    }
