# -*- coding: utf-8 -*-
import os
import sys
import json
import argparse
import datetime
from src.scraper import get_latest_bandai_ipgo
from src.notifier import send_bandai_ipgo_alert

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "settings.json")
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "last_ipgo.json")

def load_settings():
    """설정 파일 로드"""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] 설정 파일 로드 실패: {e}")
    return {"target_keyword": "반다이", "preview_count": 5}

def load_last_state():
    """이전 알림 상태 로드"""
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] 이전 상태 데이터 로드 실패: {e}")
    return {"buy_id": None, "title": None}

def save_last_state(state_data):
    """현재 상태 저장"""
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(state_data, f, ensure_ascii=False, indent=2)
    print(f"[*] 상태 파일 저장 완료: {DATA_PATH}")

def main():
    parser = argparse.ArgumentParser(description="조이하비 반다이 입고예정 알리미")
    parser.add_argument("--force", action="store_true", help="변동 여부와 관계없이 강제로 디스코드 알림 발송")
    parser.add_argument("--dry-run", action="store_true", help="디스코드 발송 건너뛰기 (콘솔 출력만)")
    args = parser.parse_args()

    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if args.dry_run:
        print("[*] Dry-run 모드 활성화: 디스코드 웹훅 전송 안 함")
        webhook_url = ""

    settings = load_settings()
    target_kw = settings.get("target_keyword", "반다이")
    preview_cnt = settings.get("preview_count", 5)

    print(f"[*] 모니터링 대상: '{target_kw}' (미리보기 개수: {preview_cnt}개)")

    # 이전 상태 로드
    last_state = load_last_state()
    prev_buy_id = last_state.get("buy_id")
    is_first_run = (prev_buy_id is None)

    # 최신 공지 및 상품 정보 크롤링
    latest_ipgo = get_latest_bandai_ipgo(target_keyword=target_kw, preview_count=preview_cnt)
    if not latest_ipgo:
        print("[!] 최신 입고 공지를 가져오지 못했습니다. 프로그램을 종료합니다.")
        return

    curr_buy_id = latest_ipgo["buy_id"]
    curr_title = latest_ipgo["title"]

    print(f"\n[*] 확인된 최신 공지 buyID: {curr_buy_id} ('{curr_title}')")
    print(f"[*] 이전에 기록된 buyID: {prev_buy_id}")

    # 알림 발송 조건: 최초 실행이거나, 새로운 buyID가 등록되었거나, 강제 실행인 경우
    should_notify = is_first_run or (curr_buy_id != prev_buy_id) or args.force

    if should_notify:
        if is_first_run:
            print("[*] 최초 실행 감지: 현재 최신 정보를 기준으로 첫 알림을 전송하고 상태를 등록합니다.")
        elif curr_buy_id != prev_buy_id:
            print(f"[🎉 신규 공지 발견!] 새로운 반다이 입고 공지가 등록되었습니다! ({prev_buy_id} -> {curr_buy_id})")
        elif args.force:
            print("[*] 강제 알림 옵션(--force)으로 알림을 전송합니다.")

        # 디스코드 알림 발송
        send_bandai_ipgo_alert(webhook_url, latest_ipgo)

        # 상태 파일 업데이트
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        save_last_state({
            "buy_id": curr_buy_id,
            "title": curr_title,
            "url": latest_ipgo["url"],
            "total_items": latest_ipgo["total_count"],
            "last_alerted_at": now_str
        })
    else:
        print("[*] 새로운 반다이 입고 예정 공지가 없습니다. (알림 생략)")

if __name__ == "__main__":
    main()
