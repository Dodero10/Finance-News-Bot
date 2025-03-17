import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from bs4 import BeautifulSoup

# Cấu hình Selenium
CHROMEDRIVER_PATH = "E:\Thesis\Crawl\chromedriver-win64\chromedriver.exe"

options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

# Không chạy chế độ headless để xem trình duyệt
service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)

def click_see_more(max_clicks=200):
    """Nhấn 'Xem thêm' tối đa max_clicks lần hoặc đến khi không còn nút"""
    click_count = 0
    prev_article_count = 0
    
    # Lấy số lượng bài viết ban đầu
    soup = BeautifulSoup(driver.page_source, "html.parser")
    all_articles = soup.find_all(["h2", "h3"], class_="story__heading")
    prev_article_count = len(all_articles)
    print(f"📊 Số lượng bài viết ban đầu: {prev_article_count}")
    
    no_change_count = 0  # Đếm số lần số bài viết không thay đổi
    max_no_change = 3    # Số lần tối đa cho phép không thay đổi

    while click_count < max_clicks:
        try:
            # Cuộn xuống cuối trang để đảm bảo nút "Xem thêm" hiển thị
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Tìm nút "Xem thêm"
            try:
                see_more_btn = driver.find_element(By.CLASS_NAME, "control__loadmore")
            except:
                print("⛔ Không tìm thấy nút 'Xem thêm', kết thúc.")
                break
                
            # Kiểm tra xem nút có hiển thị và có thể click được không
            if not see_more_btn.is_displayed() or not see_more_btn.is_enabled():
                print("⛔ Nút 'Xem thêm' không khả dụng, kết thúc.")
                break
                
            driver.execute_script("arguments[0].scrollIntoView();", see_more_btn)
            time.sleep(2)  # Đảm bảo thời gian cho trang tải đầy đủ
            
            # Click nút bằng JavaScript để đảm bảo click được
            driver.execute_script("arguments[0].click();", see_more_btn)
            click_count += 1
            print(f"🔄 Đã bấm 'Xem thêm' lần {click_count}/{max_clicks} ...")
            
            # Đợi để trang tải thêm bài viết
            time.sleep(7)  # Tăng thời gian chờ lên để trang có thời gian phản hồi
            
            # Kiểm tra số lượng bài viết hiển thị sau khi bấm
            soup = BeautifulSoup(driver.page_source, "html.parser")
            visible_articles = []
            
            # Tìm tất cả các thẻ h2 và h3 với class story__heading
            all_articles = soup.find_all(["h2", "h3"], class_="story__heading")
            current_article_count = len(all_articles)
            print(f"📊 Số lượng bài viết hiện tại: {current_article_count}")
            
            # Kiểm tra xem số bài viết có tăng không
            if current_article_count <= prev_article_count:
                no_change_count += 1
                print(f"⚠️ Số lượng bài viết không tăng lần {no_change_count}/{max_no_change}")
                if no_change_count >= max_no_change:
                    print("⛔ Đã đạt số lần không tăng tối đa, kết thúc.")
                    break
            else:
                no_change_count = 0  # Reset biến đếm nếu số bài viết tăng
                
            prev_article_count = current_article_count
            
            # Thêm thời gian nghỉ để tránh tải trang quá nhanh
            time.sleep(3)

        except Exception as e:
            print(f"⛔ Lỗi khi bấm 'Xem thêm': {str(e)}")
            break
            
    print(f"✅ Đã hoàn thành việc tải thêm bài viết. Tổng số lần bấm: {click_count}/{max_clicks}")

def get_article_links():
    """Lấy danh sách link từ tất cả các bài viết trên trang"""
    url = "https://www.tinnhanhchungkhoan.vn/ck-quoc-te/"
    driver.get(url)
    time.sleep(3)
    click_see_more()
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # Tìm chính xác div theo yêu cầu
    category_timeline = soup.find("div", class_="category-timeline")
    
    if category_timeline:
        # Tìm div con với class="box-content content-list"
        content_list = category_timeline.find("div", class_="box-content content-list", attrs={"data-source": "zone-timeline-13"})
        
        if content_list:
            print("✅ Đã tìm thấy div target chính xác")
            # Đếm số lượng bài viết trong div này
            articles_in_target = content_list.find_all("article", class_="story")
            print(f"📊 Số bài viết trong div target: {len(articles_in_target)}")
            
            # Tìm tất cả các thẻ h2 và h3 với class=story__heading trong div này
            all_headings = content_list.find_all(["h2", "h3"], class_="story__heading")
            print(f"📊 Tổng số heading trong div target: {len(all_headings)}")
            
            links = []
            for heading in all_headings:
                link_tag = heading.find("a", class_="cms-link", href=True)
                if link_tag:
                    full_url = link_tag["href"]
                    # Kiểm tra xem URL có đầy đủ domain chưa
                    if not full_url.startswith("http"):
                        if full_url.startswith("/"):
                            full_url = "https://www.tinnhanhchungkhoan.vn" + full_url
                        else:
                            full_url = "https://www.tinnhanhchungkhoan.vn/" + full_url
                    links.append(full_url)
        else:
            print("⚠️ Không tìm thấy div.box-content.content-list trong div.category-timeline")
            # Fallback: tìm kiếm trên toàn bộ trang
            all_headings = soup.find_all(["h2", "h3"], class_="story__heading")
            print(f"📊 Tổng số bài viết trên toàn trang: {len(all_headings)}")
            
            links = []
            for heading in all_headings:
                link_tag = heading.find("a", class_="cms-link", href=True)
                if link_tag:
                    full_url = link_tag["href"]
                    # Kiểm tra xem URL có đầy đủ domain chưa
                    if not full_url.startswith("http"):
                        if full_url.startswith("/"):
                            full_url = "https://www.tinnhanhchungkhoan.vn" + full_url
                        else:
                            full_url = "https://www.tinnhanhchungkhoan.vn/" + full_url
                    links.append(full_url)
    else:
        print("⚠️ Không tìm thấy div.category-timeline")
        # Fallback: tìm kiếm trên toàn bộ trang
        all_headings = soup.find_all(["h2", "h3"], class_="story__heading")
        print(f"📊 Tổng số bài viết trên toàn trang: {len(all_headings)}")
        
        links = []
        for heading in all_headings:
            link_tag = heading.find("a", class_="cms-link", href=True)
            if link_tag:
                full_url = link_tag["href"]
                # Kiểm tra xem URL có đầy đủ domain chưa
                if not full_url.startswith("http"):
                    if full_url.startswith("/"):
                        full_url = "https://www.tinnhanhchungkhoan.vn" + full_url
                    else:
                        full_url = "https://www.tinnhanhchungkhoan.vn/" + full_url
                links.append(full_url)

    # Loại bỏ trùng lặp
    links = list(dict.fromkeys(links))
    print(f"✅ Đã thu thập {len(links)} bài viết không trùng lặp.")
    return links

def get_article_details(url):
    """Lấy thông tin chi tiết từ bài viết"""
    driver.get(url)
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    title = soup.find("h1", class_="article__header").text.strip() if soup.find("h1", class_="article__header") else ""
    author = soup.find("a", class_="cms-author").text.strip() if soup.find("a", class_="cms-author") else "Không rõ"
    time_published = soup.find("time", class_="time").text.strip() if soup.find("time", class_="time") else "Không rõ"
    summary = soup.find("div", class_="article__sapo").text.strip() if soup.find("div", class_="article__sapo") else ""
    
    # Xử lý content sang định dạng markdown
    content_markdown = ""
    content_div = soup.find("div", class_="article__body", attrs={"itemprop": "articleBody"})
    if content_div:
        # Loại bỏ các phần quảng cáo
        for ads in content_div.find_all("div", class_="ads_middle"):
            ads.extract()
            
        # Xử lý từng phần tử
        for element in content_div.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'table', 'ul', 'ol', 'figure', 'div']):
            if element.name == 'p':
                # Kiểm tra xem đoạn văn có chứa hình ảnh không
                img = element.find('img')
                if img:
                    img_src = img.get('src', '')
                    img_alt = img.get('alt', 'Hình ảnh')
                    # Kiểm tra xem có phải là hình ảnh lazy-load không
                    data_src = img.get('data-src', '')
                    data_original = img.get('data-original', '')
                    
                    # Ưu tiên lấy URL thực của hình ảnh thay vì placeholder
                    if data_src and not img_src.startswith('data:'):
                        img_src = data_src
                    elif data_original and not img_src.startswith('data:'):
                        img_src = data_original
                    elif img_src.startswith('data:'):
                        # Tìm data-src hoặc data-original nếu src là base64
                        if data_src:
                            img_src = data_src
                        elif data_original:
                            img_src = data_original
                        else:
                            # Nếu không tìm thấy url thật, bỏ qua hình ảnh này
                            text = element.text.strip()
                            if text:
                                # Xử lý định dạng đậm
                                if element.find('strong'):
                                    for strong in element.find_all('strong'):
                                        strong_text = strong.text
                                        text = text.replace(strong_text, f"**{strong_text}**")
                                content_markdown += f"{text}\n\n"
                            continue
                    
                    # Thêm hình ảnh vào markdown
                    content_markdown += f"![{img_alt}]({img_src})\n\n"
                else:
                    text = element.text.strip()
                    if not text:  # Bỏ qua đoạn văn trống
                        continue
                        
                    # Xử lý định dạng đậm
                    if element.find('strong'):
                        for strong in element.find_all('strong'):
                            strong_text = strong.text
                            text = text.replace(strong_text, f"**{strong_text}**")
                    
                    content_markdown += f"{text}\n\n"
                    
            elif element.name.startswith('h'):
                # Xử lý tiêu đề
                level = int(element.name[1])
                text = element.text.strip()
                content_markdown += f"{'#' * level} {text}\n\n"
                
            elif element.name == 'table':
                # Xử lý bảng có chứa hình ảnh
                img = element.find('img')
                if img:
                    img_src = img.get('src', '')
                    img_alt = img.get('alt', 'Hình ảnh')
                    
                    # Kiểm tra lazy-loaded images
                    data_src = img.get('data-src', '')
                    data_original = img.get('data-original', '')
                    
                    if data_src and (not img_src or img_src.startswith('data:')):
                        img_src = data_src
                    elif data_original and (not img_src or img_src.startswith('data:')):
                        img_src = data_original
                    
                    if img_src and not img_src.startswith('data:'):
                        content_markdown += f"![{img_alt}]({img_src})\n\n"
                
            elif element.name == 'figure':
                # Xử lý figure (thường chứa hình ảnh)
                img = element.find('img')
                if img:
                    img_src = img.get('src', '')
                    img_alt = img.get('alt', 'Hình ảnh')
                    
                    # Kiểm tra lazy-loaded images
                    data_src = img.get('data-src', '')
                    data_original = img.get('data-original', '')
                    
                    if data_src and (not img_src or img_src.startswith('data:')):
                        img_src = data_src
                    elif data_original and (not img_src or img_src.startswith('data:')):
                        img_src = data_original
                    
                    if img_src and not img_src.startswith('data:'):
                        # Tìm caption nếu có
                        figcaption = element.find('figcaption')
                        if figcaption:
                            img_alt = figcaption.text.strip()
                        
                        content_markdown += f"![{img_alt}]({img_src})\n\n"
            
            elif element.name == 'div' and element.find('img'):
                # Xử lý div chứa hình ảnh
                for img in element.find_all('img'):
                    img_src = img.get('src', '')
                    img_alt = img.get('alt', 'Hình ảnh')
                    
                    # Kiểm tra lazy-loaded images
                    data_src = img.get('data-src', '')
                    data_original = img.get('data-original', '')
                    
                    if data_src and (not img_src or img_src.startswith('data:')):
                        img_src = data_src
                    elif data_original and (not img_src or img_src.startswith('data:')):
                        img_src = data_original
                    
                    if img_src and not img_src.startswith('data:'):
                        content_markdown += f"![{img_alt}]({img_src})\n\n"
                
            elif element.name == 'ul':
                for li in element.find_all('li'):
                    content_markdown += f"* {li.text.strip()}\n"
                content_markdown += "\n"
                
            elif element.name == 'ol':
                for i, li in enumerate(element.find_all('li'), 1):
                    content_markdown += f"{i}. {li.text.strip()}\n"
                content_markdown += "\n"
    
    # Lấy đúng tag từ div.article__tag
    tags = []
    article_tag_div = soup.find("div", class_="article__tag")
    if article_tag_div:
        box_content = article_tag_div.find("div", class_="box-content")
        if box_content:
            for tag_link in box_content.find_all("a"):
                tag_text = tag_link.text.strip()
                if tag_text:
                    tags.append(tag_text)
    
    # Lấy ảnh đại diện
    image_tag = soup.find("figure", class_="article__avatar")
    image_url = ""
    if image_tag and image_tag.find("img"):
        image_url = image_tag.find("img")["src"]

    print("Title: ", title)
    print("Author: ", author)
    print("Time published: ", time_published)
    print("Summary: ", summary)
    print("Content: ", content_markdown)
    print("Tags: ", tags)
    print("Image URL: ", image_url)

    return {
        "title": title,
        "author": author,
        "time_published": time_published,
        "summary": summary,
        "content": content_markdown,
        "tags": tags,
        "image_url": image_url,
        "url": url
    }

def save_to_json(data, filename="tinnhanhchungkhoan_articles.json"):
    """Lưu dữ liệu vào file JSON"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"💾 Đã lưu {len(data)} bài viết vào {filename}")
    except Exception as e:
        print(f"❌ Lỗi khi lưu file JSON: {e}")

def append_to_json(article, filename="tinnhanhchungkhoan_articles.json"):
    """Thêm một bài viết vào file JSON hiện có hoặc tạo file mới nếu chưa tồn tại"""
    try:
        # Kiểm tra file có tồn tại không
        try:
            with open(filename, "r", encoding="utf-8") as f:
                try:
                    # Đọc dữ liệu hiện tại
                    articles = json.load(f)
                except json.JSONDecodeError:
                    # Nếu file rỗng hoặc không phải JSON hợp lệ, tạo mảng mới
                    articles = []
        except FileNotFoundError:
            # Nếu file chưa tồn tại, tạo mảng mới
            articles = []
        
        # Thêm bài viết mới
        articles.append(article)
        
        # Ghi lại vào file
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=4)
        
        print(f"💾 Đã lưu bài viết mới vào {filename}, tổng số: {len(articles)}")
    except Exception as e:
        print(f"❌ Lỗi khi thêm bài viết vào file JSON: {e}")

def test_click_and_crawl_2_articles():
    """Test: Nhấn 'Xem thêm' một lần và crawl 2 bài đầu tiên"""
    url = "https://www.tinnhanhchungkhoan.vn/nhan-dinh/"
    driver.get(url)
    print("✅ Đã mở trang web")
    time.sleep(3)
    
    # Cuộn xuống cuối trang để đảm bảo nút "Xem thêm" hiển thị
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    
    try:
        # Tìm và click nút "Xem thêm"
        see_more_btn = driver.find_element(By.CLASS_NAME, "control__loadmore")
        driver.execute_script("arguments[0].scrollIntoView();", see_more_btn)
        time.sleep(2)
        driver.execute_script("arguments[0].click();", see_more_btn)
        print("✅ Đã nhấn nút 'Xem thêm'")
        time.sleep(7)  # Đợi trang load thêm bài viết
    except Exception as e:
        print(f"⛔ Lỗi khi nhấn 'Xem thêm': {str(e)}")
    
    # Lấy tất cả các bài viết
    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # Tìm div chứa bài viết
    category_timeline = soup.find("div", class_="category-timeline")
    if category_timeline:
        content_list = category_timeline.find("div", class_="box-content content-list")
        if content_list:
            print("✅ Đã tìm thấy div target")
            articles = content_list.find_all("article", class_="story")
            print(f"📊 Tổng số bài viết tìm thấy: {len(articles)}")
            
            # Lấy 2 bài đầu tiên
            links = []
            for i, article in enumerate(articles[:2]):
                heading = article.find(["h2", "h3"], class_="story__heading")
                if heading:
                    link_tag = heading.find("a", class_="cms-link", href=True)
                    if link_tag:
                        full_url = link_tag["href"]
                        if not full_url.startswith("http"):
                            if full_url.startswith("/"):
                                full_url = "https://www.tinnhanhchungkhoan.vn" + full_url
                            else:
                                full_url = "https://www.tinnhanhchungkhoan.vn/" + full_url
                        links.append(full_url)
                        print(f"🔗 Bài {i+1}: {full_url}")
            
            # Khởi tạo file JSON test
            test_file = "test_articles.json"
            try:
                with open(test_file, "w", encoding="utf-8") as f:
                    json.dump([], f)
                print(f"✅ Đã tạo file {test_file} mới")
            except Exception as e:
                print(f"❌ Lỗi khi tạo file test: {str(e)}")
            
            # Crawl chi tiết từng bài và lưu ngay
            for i, link in enumerate(links):
                print(f"\n📝 Đang lấy chi tiết bài {i+1}: {link}")
                article = get_article_details(link)
                
                # Lưu ngay bài viết vừa crawl
                append_to_json(article, test_file)
                
                # Hiển thị thông tin tóm tắt
                print(f"\n===== BÀI {i+1} =====")
                print(f"Tiêu đề: {article['title']}")
                print(f"Tác giả: {article['author']}")
                print(f"Thời gian: {article['time_published']}")
                print(f"Tags: {', '.join(article['tags'])}")
                print("Nội dung (50 ký tự đầu):", article['content'][:50] + "...")
            
            print("\n✅ Đã lưu kết quả test vào test_articles.json")
            
            # Đọc lại file để kiểm tra
            try:
                with open(test_file, "r", encoding="utf-8") as f:
                    saved_articles = json.load(f)
                print(f"✅ Đã kiểm tra file JSON: Có {len(saved_articles)} bài viết")
                return saved_articles
            except Exception as e:
                print(f"❌ Lỗi khi đọc lại file test: {str(e)}")
                return []
        else:
            print("⚠️ Không tìm thấy div.box-content.content-list")
    else:
        print("⚠️ Không tìm thấy div.category-timeline")
    
    return []

def main():
    links = get_article_links()
    time.sleep(10)
    
    output_file = "tinnhanhchungkhoan_quoc_te.json"
    
    # Khởi tạo file JSON trống nếu chưa tồn tại
    try:
        with open(output_file, "r") as f:
            pass
    except FileNotFoundError:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump([], f)
        print(f"✅ Đã tạo file {output_file} mới")

    for i, url in enumerate(links, start=1):
        try:
            print(f"📝 [{i}/{len(links)}] Đang lấy bài viết: {url}")
            article = get_article_details(url)
            
            # Lưu ngay bài viết vừa crawl vào file JSON
            append_to_json(article, output_file)
            
            # Tạm dừng một chút để tránh tải quá nhanh
            time.sleep(1)
        except Exception as e:
            print(f"❌ Lỗi khi xử lý bài viết {url}: {e}")
            continue

    print("✅ Hoàn thành crawl dữ liệu.")
    driver.quit()

if __name__ == "__main__":
    # try:
    #     results = test_click_and_crawl_2_articles()
    #     print("\n✅ Test hoàn thành!")
    # except Exception as e:
    #     print(f"❌ Lỗi: {str(e)}")
    # finally:
    #     time.sleep(5)
    #     driver.quit()
    main()
