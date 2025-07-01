import json
import re
import base64
import httpx
import os
import time
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

def get_api_keys():
    keys = []
    i = 1
    while True:
        key_name = f"GOOGLE_API_KEY_{i}"
        key = os.getenv(key_name)
        if key:
            keys.append(key)
            i += 1
        else:
            # Also check for a default key
            default_key = os.getenv("GOOGLE_API_KEY")
            if default_key and default_key not in keys:
                keys.append(default_key)
            break
    
    if not keys:
        raise ValueError("Không tìm thấy API key nào. Hãy kiểm tra file .env của bạn.")
    
    print(f"Đã tìm thấy {len(keys)} API key.")
    return keys

API_KEYS = get_api_keys()
current_key_index = 0

def get_model(key_index):
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", api_key=API_KEYS[key_index])
    print(f"Đang sử dụng API key #{key_index + 1}")
    return model

model = get_model(current_key_index)

def extract_images_from_content(content):
    """Extract images and their captions from markdown content."""
    image_pattern = r"!\[(.*?)\]\((.*?)\)"
    return re.findall(image_pattern, content)

def parse_image(image_url):
    """Use Gemini to parse an image and return its content in markdown."""
    global current_key_index, model
    
    rate_limited_keys = set()
    
    try:
        print(f"  Đang tải xuống hình ảnh: {image_url}")
        image_data = base64.b64encode(httpx.get(image_url).content).decode("utf-8")
        print("  Đã tải hình ảnh thành công")
    except Exception as e:
        print(f"  Lỗi khi tải hình ảnh: {e}")
        return None
    
    message = HumanMessage(
        content=[
            {"type": "text", "text": "Parse image and return the content. If it is the table, return the content in markdown format. If it is a chart, return the content in markdown format and description of the chart. Else return the content in description of image."},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
            },
        ],
    )
    
    while len(rate_limited_keys) < len(API_KEYS):
        try:
            print(f"  Đang phân tích hình ảnh bằng Gemini (API key #{current_key_index + 1})...")
            response = model.invoke([message])
            print("  Đã phân tích xong hình ảnh")
            return response.content
            
        except Exception as e:
            error_message = str(e).lower()
            
            if "rate limit" in error_message or "quota" in error_message or "429" in error_message:
                print(f"  API key #{current_key_index + 1} đã bị rate limit")
                
                rate_limited_keys.add(current_key_index)
                
                current_key_index = (current_key_index + 1) % len(API_KEYS)
                
                model = get_model(current_key_index)
            else:
                print(f"  Lỗi không phải rate limit khi xử lý hình ảnh: {e}")
                current_key_index = (current_key_index + 1) % len(API_KEYS)
                model = get_model(current_key_index)
    
    print("  Đã thử tất cả API key và tất cả đều bị rate limit.")
    return None

def process_json_file(input_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_articles = len(data)
    print(f"Tổng số mẫu cần xử lý: {total_articles}")

    for idx, article in enumerate(data):
        start_time = time.time()
        print(f"\nĐang xử lý mẫu {idx+1}/{total_articles}: {article.get('title', 'Không có tiêu đề')}")
        content = article.get('content', '')
        
        images = extract_images_from_content(content)
        print(f"Tìm thấy {len(images)} hình ảnh trong mẫu này")
        
        if 'metadata' not in article:
            article['metadata'] = {}
        
        article['metadata']['images'] = []
        
        for img_idx, (caption, image_url) in enumerate(images):
            print(f"Đang xử lý hình ảnh {img_idx+1}/{len(images)}")
            parsed_content = parse_image(image_url)
            
            image_data = {
                'id': img_idx + 1,
                'url': image_url,
                'caption': caption,
                'parsed_content': parsed_content
            }
            article['metadata']['images'].append(image_data)
            
            image_pattern = f"!\\[{re.escape(caption)}\\]\\({re.escape(image_url)}\\)"
            content = re.sub(image_pattern, "[Image]", content, count=1)
        
        article['content'] = content
        
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        elapsed_time = time.time() - start_time
        print(f"Đã xử lý và lưu mẫu {idx+1}/{total_articles} trong {elapsed_time:.2f} giây")
    
    print(f"\nĐã hoàn thành xử lý tất cả {total_articles} mẫu")
    return data

if __name__ == "__main__":
    input_file = "data/quoc_te.json"
    processed_data = process_json_file(input_file)
    print(f"Đã xử lý {len(processed_data)} mẫu, dữ liệu đã được cập nhật trong file {input_file}") 