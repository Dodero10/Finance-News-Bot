import pandas as pd
import os

def add_difficulty_column():
    # Đọc file synthetic_news.csv để lấy mapping query -> difficulty
    synthetic_df = pd.read_csv('evaluation/data_eval/synthetic_data/synthetic_news.csv')
    
    # Tạo dictionary mapping từ query đến difficulty
    query_to_difficulty = dict(zip(synthetic_df['query'], synthetic_df['difficulty']))
    
    # Danh sách các file cần xử lý
    result_files = [
        'evaluation/data_eval/results/react_agent_eval_results.csv',
        'evaluation/data_eval/results/multi_agent_eval_results.csv', 
        'evaluation/data_eval/results/reflexion_agent_eval_results.csv',
        'evaluation/data_eval/results/rewoo_agent_eval_results.csv'
    ]
    
    for file_path in result_files:
        if os.path.exists(file_path):
            print(f"\n=== Xử lý file: {file_path} ===")
            
            # Đọc file kết quả
            results_df = pd.read_csv(file_path)
            
            # Thêm cột difficulty bằng cách mapping từ input column
            results_df['difficulty'] = results_df['input'].map(query_to_difficulty)
            
            # Kiểm tra xem có query nào không tìm thấy difficulty không
            missing_difficulty = results_df[results_df['difficulty'].isna()]
            if not missing_difficulty.empty:
                print(f"Warning: {len(missing_difficulty)} queries không tìm thấy difficulty:")
                print(missing_difficulty['input'].tolist())
            
            # Sắp xếp lại thứ tự các cột để difficulty ở vị trí thứ 2
            columns = ['input', 'difficulty'] + [col for col in results_df.columns if col not in ['input', 'difficulty']]
            results_df = results_df[columns]
            
            # Lưu file mới
            results_df.to_csv(file_path, index=False)
            
            print(f"Đã thêm cột difficulty vào {file_path}")
            print(f"Tổng số dòng: {len(results_df)}")
            print(f"Số dòng có difficulty: {results_df['difficulty'].notna().sum()}")
            
            # Hiển thị thống kê difficulty
            print("Thống kê difficulty:")
            print(results_df['difficulty'].value_counts())
        else:
            print(f"File không tồn tại: {file_path}")

if __name__ == "__main__":
    add_difficulty_column() 