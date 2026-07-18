# pip3 install icrawler

from icrawler.builtin import BingImageCrawler

def download_images(search_query, num_images=50):
    folder_path = f"./{search_query}/"
    crawler = BingImageCrawler(
        storage={'root_dir': folder_path},
        downloader_threads=4
    )
    crawler.crawl(keyword=search_query, max_num=num_images)
    print("Done downloading images!")

if __name__ == "__main__":
    search_query = input("Enter the search query: ")
    num_images = int(input("Enter the number of images to download: "))
    download_images(search_query, num_images)
