from playwright.sync_api import sync_playwright
import requests
import os
from datetime import datetime

def send_image_to_teams(webhook_url, image_url, post_url, post_title, index):
    try:
        # 이미지 다운로드
        response = requests.get(image_url)
        if response.status_code != 200:
            print(f"이미지 다운로드 실패: {image_url}")
            return False
        
        # Teams Adaptive Card 메시지 생성
        message = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": post_title,
            "themeColor": "FEE500",
            "title": post_title,
            "sections": [{
                "facts": [{
                    "name": "게시물 URL",
                    "value": f"[바로가기]({post_url})"
                }, {
                    "name": "업로드 시간",
                    "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }],
                "images": [{
                    "image": image_url
                }]
            }]
        }
        
        # Teams webhook으로 전송
        headers = {"Content-Type": "application/json"}
        response = requests.post(webhook_url, headers=headers, json=message)
        
        if response.status_code == 200:
            print(f"이미지 #{index} Teams 전송 성공")
            return True
        else:
            print(f"Teams 전송 실패: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"이미지 전송 중 오류 발생: {e}")
        return False

def extract_and_send_images():
    # 환경 변수에서 Teams webhook URL 가져오기
    webhook_url = os.environ.get('TEAMS_WEBHOOK_URL')
    if not webhook_url:
        raise ValueError("TEAMS_WEBHOOK_URL 환경 변수가 설정되지 않았습니다.")
    
    with sync_playwright() as p:
        # 브라우저 실행
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 카카오 채널 메인 페이지로 이동
        print("카카오 채널 접속 중...")
        page.goto("https://pf.kakao.com/_Kyxlxbn")
        page.wait_for_load_state("networkidle")
        
        # 첫 번째 게시물 찾기
        print("첫 번째 게시물 찾는 중...")
        first_post = page.locator(".box_list_board").first.locator(".link_board").first
        
        # 첫 번째 게시물 클릭
        first_post.click()
        page.wait_for_load_state("networkidle")
        post_url = page.url
        print(f"게시물 URL: {post_url}")
        
        # 게시물 제목 추출
        print("게시물 제목 추출 중...")
        post_title = "카카오 채널 새 이미지"  # 기본값
        try:
            title_element = page.locator(".tit_card").first
            if title_element.count() > 0:
                post_title = title_element.inner_text()
                print(f"게시물 제목: {post_title}")
        except Exception as e:
            print(f"제목 추출 실패, 기본값 사용: {e}")
        
        # 이미지 추출
        print("이미지 추출 중...")
        images = page.locator(".item_archive_image img").all()
        
        # 이미지 URL 수집
        image_urls = []
        for img in images:
            src = img.get_attribute("src")
            if src:
                image_urls.append(src)
        
        print(f"총 {len(image_urls)}개의 이미지를 찾았습니다.")
        
        # 각 이미지를 Teams로 전송
        success_count = 0
        for i, url in enumerate(image_urls):
            if send_image_to_teams(webhook_url, url, post_url, post_title, i+1):
                success_count += 1
        
        browser.close()
        print(f"\n총 {success_count}/{len(image_urls)}개의 이미지를 Teams로 전송했습니다.")
        
        # GitHub Actions에서 성공 여부를 확인할 수 있도록 실패 시 exit code 1 반환
        if success_count == 0 and len(image_urls) > 0:
            exit(1)

# 실행
if __name__ == "__main__":
    extract_and_send_images()