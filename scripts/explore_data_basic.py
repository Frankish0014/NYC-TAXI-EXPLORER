import csv
import os

def explore_data_basic():
    """Basic data exploration without pandas"""
    file_path = 'data/raw/train.csv'
    
    if not os.path.exists(file_path):
        print(f'ERROR: File not found at {file_path}')
        print('Please make sure train.csv is in data/raw/ directory')
        return
    
    print('=== BASIC DATA EXPLORATION ===')
    print(f'Exploring: {file_path}')
    
    # Count rows and show columns
    row_count = 0
    columns = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            
            # Read header
            try:
                columns = next(reader)
                print(f'Columns: {columns}')
                print(f'Number of columns: {len(columns)}')
            except StopIteration:
                print('File is empty')
                return
            
            # Count rows and show sample
            sample_rows = []
            for i, row in enumerate(reader):
                row_count += 1
                if i < 3:  # First 3 data rows
                    sample_rows.append(row)
                if i >= 10000:  # Stop after 10k rows for quick check
                    break
            
            print(f'Number of data rows (sampled): {row_count:,}')
            print('\nSample data rows (first 5 values):')
            for i, row in enumerate(sample_rows):
                print(f'Row {i+1}: {row[:5]}...')
                
    except Exception as e:
        print(f'Error reading file: {e}')
    
    return columns, row_count

if __name__ == '__main__':
    explore_data_basic()
