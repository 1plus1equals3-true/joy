# -*- coding: utf-8 -*-
import datetime
import requests

def send_discord_webhook(webhook_url: str, payload: dict) -> bool:
    """디스코드 웹훅 메시지 전송"""
    if not webhook_url:
        print("[!] DISCORD_WEBHOOK_URL이 설정되지 않아 콘솔 출력으로 대체합니다.")
        for emb in payload.get("embeds", []):
            print(f"--- [Embed] {emb.get('title')} ---")
            print(f"URL: {emb.get('url')}")
            print(f"Description:\n{emb.get('description')}")
        return True

    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        if resp.status_code in (200, 204):
            print("[*] 디스코드 알림 전송 완료!")
            return True
        else:
            print(f"[!] 디스코드 전송 실패 (상태 코드 {resp.status_code}): {resp.text}")
            return False
    except Exception as e:
        print(f"[!] 디스코드 전송 중 에러: {e}")
        return False

def send_bandai_ipgo_alert(webhook_url: str, ipgo_info: dict) -> bool:
    """
    조이하비 반다이 프라모델 입고 예정 디스코드 알림 발송
    """
    title = ipgo_info['title']
    detail_url = ipgo_info['url']
    items = ipgo_info['items']
    total_count = ipgo_info['total_count']

    # 상품 미리보기 목록 포맷팅 (예: 1. [원피스] 고잉 메리호 [47,300원])
    item_lines = []
    for idx, it in enumerate(items, 1):
        price_str = f"[{it['price']}]" if it['price'] else "[가격 미정]"
        item_lines.append(f"`{idx}.` [{it['title']}]({it['link']}) **{price_str}**")

    preview_text = "\n".join(item_lines) if item_lines else "입고 예정 상품 목록을 확인하려면 아래 링크를 클릭하세요."

    extra_text = ""
    if total_count > len(items):
        extra_text = f"\n\n*(외 {total_count - len(items)}개 상품 더 있음 - 링크에서 전체 확인)*"

    description = (
        f"조이하비에 새로운 **반다이 프라모델** 입고 예정 공지가 등록되었습니다!\n\n"
        f"🔗 **[입고 예정 페이지 바로가기]({detail_url})**\n\n"
        f"📦 **입고 예정 상품 미리보기 (총 {total_count}개)**\n"
        f"{preview_text}{extra_text}"
    )

    payload = {
        "content": "📢 **[조이하비] 반다이 프라모델 새로운 입고 예정 안내!**",
        "embeds": [{
            "title": f"🗓️ {title}",
            "url": detail_url,
            "description": description,
            "color": 0xE74C3C,  # 반다이 레드
            "footer": {
                "text": "조이하비 입고 알리미 | GitHub Actions"
            },
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }]
    }

    return send_discord_webhook(webhook_url, payload)
