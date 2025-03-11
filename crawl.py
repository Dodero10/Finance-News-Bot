import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# Cấu hình Selenium
options = Options()
# options.add_argument("--headless")  # Comment hoặc xóa dòng này để hiển thị trình duyệt
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
service = Service("E:\Thesis\Crawl\chromedriver-win64\chromedriver.exe")  # Đường dẫn đến ChromeDriver

driver = webdriver.Chrome(service=service, options=options)

def scroll_page():
    """Cuộn trang để tải thêm bài viết"""
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def get_article_links(limit=1000000):
    """Lấy danh sách các liên kết bài viết, bao gồm cả những bài cần cuộn mới hiện"""
    url = "https://znews.vn/kinh-te-so.html"
    driver.get(url)
    time.sleep(3)
    
    links = set()
    no_new_articles_count = 0  # Đếm số lần cuộn không có bài mới
    
    while len(links) < limit:
        previous_length = len(links)
        scroll_page()
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        articles = soup.find_all("article", class_="article-item")
        
        for article in articles:
            link_tag = article.find("a", href=True)
            if link_tag:
                links.add(link_tag["href"])
        
        # Kiểm tra xem có bài viết mới không
        if len(links) == previous_length:
            no_new_articles_count += 1
        else:
            no_new_articles_count = 0
            
        # Nếu cuộn 3 lần liên tiếp không có bài mới, dừng lại
        if no_new_articles_count >= 3:
            print("Không tìm thấy bài viết mới sau 3 lần cuộn, kết thúc tìm kiếm.")
            break
            
    return list(links)

def get_article_details(url):
    """Lấy thông tin chi tiết của bài viết từ liên kết"""
    driver.get(url)
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # Lấy tiêu đề
    title = soup.find("h1", class_="the-article-title").text.strip() if soup.find("h1", class_="the-article-title") else ""
    
    # Lấy tác giả
    author_tag = soup.find("p", class_="author")
    author = author_tag.text.strip() if author_tag else "Không rõ"
    
    # Lấy thời gian đăng
    time_published = soup.find("li", class_="the-article-publish").text.strip() if soup.find("li", class_="the-article-publish") else ""
    
    # Lấy mô tả ngắn
    summary = soup.find("p", class_="the-article-summary").text.strip() if soup.find("p", class_="the-article-summary") else ""
    
    # Lấy nội dung bài viết
    content = "\n".join([p.text.strip() for p in soup.find_all("p") if "the-article-summary" not in p.get("class", [])])
    
    # Lấy danh mục bài viết
    category_tag = soup.find("a", class_="parent_cate")
    category = category_tag.text.strip() if category_tag else "Không rõ"
    
    # Lấy tags
    tags = [tag.text.strip() for tag in soup.find_all("span", class_="tag-item")]
    
    # Lấy ảnh minh họa
    image_tag = soup.find("img", class_="unveil")
    image_url = image_tag["src"] if image_tag else ""
    
    return {
        "title": title,
        "author": author,
        "time_published": time_published,
        "summary": summary,
        "content": content,
        "category": category,
        "tags": tags,
        "image_url": image_url,
        "url": url
    }

def save_to_json(data, filename="articles.json", mode="a"):
    """Lưu dữ liệu vào file JSON"""
    try:
        # Đọc dữ liệu hiện có
        existing_data = []
        if mode == "a":
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = []
        
        # Thêm dữ liệu mới
        if isinstance(data, list):
            existing_data.extend(data)
        else:
            existing_data.append(data)
            
        # Ghi lại toàn bộ dữ liệu
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Lỗi khi lưu dữ liệu: {str(e)}")

def main():
    article_urls = get_article_links(limit=1000000)
    print(f"Tìm thấy {len(article_urls)} bài viết.")
    
    for i, url in enumerate(article_urls, start=1):
        try:
            print(f"[{i}/{len(article_urls)}] Đang lấy bài viết từ: {url}")
            article = get_article_details(url)
            save_to_json(article, filename="kinh_te_so.json")
            print(f"Đã lưu bài viết: {article['title']}")
        except Exception as e:
            print(f"Lỗi khi xử lý bài viết {url}: {str(e)}")
            continue
    
    print("Hoàn thành crawl dữ liệu")
    driver.quit()

if __name__ == "__main__":
    main()
