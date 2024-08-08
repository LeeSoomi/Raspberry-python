import requests
import os
import time
import urllib.request
from bs4 import BeautifulSoup

def download_images(search_query, num_images=50):
    folder_path = f"./{search_query}/"
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)

    count = 0
    page = 0
    while count < num_images:
        try:
            url = f"https://www.google.com/search?q={search_query}&tbm=isch&start={page*20}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            img_tags = soup.find_all('img')

            for img_tag in img_tags:
                if count >= num_images:
                    break
                img_url = img_tag.get('src') or img_tag.get('data-src')
                if not img_url or not img_url.startswith('http'):
                    continue
                
                img_name = f"{search_query}{count}.jpg"
                urllib.request.urlretrieve(img_url, os.path.join(folder_path, img_name))
                print(f"Downloading image {count + 1}")
                count += 1
                time.sleep(1)  # 사이트의 접속 제한을 피하기 위한 대기 시간 설정
            page += 1  # 다음 페이지로 이동
        except Exception as e:
            print(f"Error downloading image {count + 1}: {e}")
            continue

    print("Done downloading images!")

if __name__ == "__main__":
    search_query = input("Enter the search query: ")  # 검색어 입력
    num_images = int(input("Enter the number of images to download: "))  # 다운로드할 이미지 수 입력
    download_images(search_query, num_images=num_images)
