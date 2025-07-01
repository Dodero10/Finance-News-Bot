import csv

def count_difficulty():
    """Đếm số câu dễ và khó"""
    csv_file = "evaluation/data_eval/synthetic_data/synthetic_news.csv"
    
    easy_count = 0
    hard_count = 0
    
    with open(csv_file, 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        
        for row in csv_reader:
            difficulty = row.get('difficulty', '').strip()
            if difficulty == 'dễ':
                easy_count += 1
            elif difficulty == 'khó':
                hard_count += 1
    
    print(f"Số câu hỏi dễ: {easy_count}")
    print(f"Số câu hỏi khó: {hard_count}")
    print(f"Tổng cộng: {easy_count + hard_count}")

if __name__ == "__main__":
    count_difficulty() 