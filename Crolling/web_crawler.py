import requests
from bs4 import BeautifulSoup

def crawl(url):
    # URL 요청
    response = requests.get(url)
    if response.status_code == 200:
        html = response.text
        # BeautifulSoup으로 HTML 파싱
        soup = BeautifulSoup(html, 'html.parser')
        # 예시: 모든 제목 태그(<h1>, <h2> 등)를 가져오기
        titles = soup.find_all(['h1', 'h2', 'h3'])
        for title in titles:
            print(title.get_text())
    else:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")

if __name__ == "__main__":
    url = 'https://example.com'  # 크롤링할 URL을 입력하세요
    crawl(url)
