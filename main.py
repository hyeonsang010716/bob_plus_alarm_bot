from playwright.sync_api import sync_playwright
import requests
import os
from datetime import datetime

def send_images_to_teams(webhook_url, image_urls, post_url, post_title):
    try:
        if not image_urls:
            print("전송할 이미지가 없습니다.")
            return False
        
        # 첫 번째 이미지와 나머지 이미지 분리
        first_image = image_urls[0]
        other_images = image_urls[1:] if len(image_urls) > 1 else []
        
        # Teams Adaptive Card 메시지 생성
        body_content = [
            {
                "type": "TextBlock",
                "text": f"🍽 {post_title} 🍽",
                "size": "Large",
                "weight": "Bolder"
            },
            {
                "type": "Image",
                "url": first_image
            }
        ]
        
        # 나머지 이미지가 있으면 ImageSet으로 추가
        if other_images:
            body_content.append({
                "type": "ImageSet",
                "imageSize": "Large",
                "images": [{"type": "Image", "url": url} for url in other_images]
            })
        
        # 게시물 URL 추가
        body_content.append({
            "type": "TextBlock",
            "text": f"[게시물 바로가기]({post_url})",
            "wrap": True
        })
        
        message = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "contentUrl": None,
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.2",
                        "body": body_content
                    }
                }
            ]
        }
        
        # Teams webhook으로 전송
        headers = {"Content-Type": "application/json"}
        response = requests.post(webhook_url, headers=headers, json=message)
        
        if response.status_code == 200:
            print(f"Teams 전송 성공: {len(image_urls)}개 이미지")
            return True
        else:
            print(f"Teams 전송 실패: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Teams 전송 중 오류 발생: {e}")
        return False

def extract_and_send_images():
    # 환경 변수에서 Teams webhook URL 가져오기
    webhook_url = os.environ.get('TEAMS_WEBHOOK_URL')
    if not webhook_url:
        raise ValueError("TEAMS_WEBHOOK_URL 환경 변수가 설정되지 않았습니다.")
    
    with sync_playwright() as p:
        # 브라우저 실행 (headless=False로 디버깅 가능)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 카카오 채널 메인 페이지로 이동
        print("카카오 채널 접속 중...")
        page.goto("https://pf.kakao.com/_Kyxlxbn")
        page.wait_for_load_state("networkidle")
        
        # 페이지 로드 추가 대기
        page.wait_for_timeout(3000)
        
        # 첫 번째 게시물 찾기
        print("첫 번째 게시물 찾는 중...")
        first_post = page.locator(".link_board").first
        
        # 첫 번째 게시물 클릭
        first_post.click()
        page.wait_for_load_state("networkidle")
        
        # 페이지 전환 대기
        page.wait_for_timeout(3000)
        
        post_url = page.url
        print(f"게시물 URL: {post_url}")
        
        # 게시물 제목 추출
        print("게시물 제목 추출 중...")
        post_title = "카카오 채널 새 이미지"  # 기본값
        try:
            # 여러 선택자 시도
            title_element = page.locator(".tit_card").first
            if title_element.count() > 0:
                post_title = title_element.inner_text()
            else:
                # 다른 선택자 시도
                title_element = page.locator(".tit_info").first
                if title_element.count() > 0:
                    post_title = title_element.inner_text()
            print(f"게시물 제목: {post_title}")
        except Exception as e:
            print(f"제목 추출 실패, 기본값 사용: {e}")
        
        # 이미지 추출 - 여러 선택자 시도
        print("이미지 추출 중...")
        image_urls = []
        
        # 선택자 1: item_archive_image
        images = page.locator(".item_archive_image img").all()
        if not images:
            # 선택자 2: 다른 이미지 컨테이너
            images = page.locator(".wrap_content img").all()
        if not images:
            # 선택자 3: 모든 이미지 태그
            images = page.locator("img").all()
        
        # 이미지 URL 수집
        for img in images:
            try:
                src = img.get_attribute("src")
                if src and not src.startswith("data:"):  # base64 이미지 제외
                    # 썸네일 URL을 원본 이미지 URL로 변환 (카카오 이미지 서버 패턴)
                    if "thumb" in src:
                        src = src.replace("/thumb/", "/original/")
                    if src not in image_urls:  # 중복 제거
                        image_urls.append(src)
            except:
                continue
        
        print(f"총 {len(image_urls)}개의 이미지를 찾았습니다.")
        
        # 모든 이미지를 한 번에 Teams로 전송
        if image_urls:
            success = send_images_to_teams(webhook_url, image_urls, post_url, post_title)
            if success:
                print(f"\n모든 이미지를 Teams로 전송했습니다.")
            else:
                print(f"\nTeams 전송에 실패했습니다.")
                browser.close()
                exit(1)
        else:
            print("전송할 이미지가 없습니다.")
        
        browser.close()

# 실행
if __name__ == "__main__":
    extract_and_send_images()