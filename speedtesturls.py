import os
from tqdm import tqdm

def generate_chunked_urls(base_url, total_records, chunk_size, output_dir="output_chunks"):
    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"Starting generation for {total_records:,} total lines.")
    print(f"Files will split every {chunk_size:,} lines.")

    current_chunk = 1
    lines_written_in_chunk = 0
    file_handle = None

    try:
        for i in tqdm(range(1, total_records + 1), desc="Generating", unit="line"):
            # Open a new file chunk if we don't have an active one
            if file_handle is None:
                file_path = os.path.join(output_dir, f"urls_part_{current_chunk}.txt")
                file_handle = open(file_path, "w", encoding="utf-8")
            
            file_handle.write(f"{base_url}{i}\n")
            lines_written_in_chunk += 1
            
            # If the current chunk reaches the limit, close it to open a new one on next loop
            if lines_written_in_chunk >= chunk_size:
                file_handle.close()
                file_handle = None
                lines_written_in_chunk = 0
                current_chunk += 1

    except KeyboardInterrupt:
        print("\nProcess stopped early by user.")
    finally:
        if file_handle and not file_handle.closed:
            file_handle.close()
    
    print(f"\nDone! Generated {current_chunk if lines_written_in_chunk > 0 else current_chunk - 1} file(s) in '{output_dir}/'.")

if __name__ == "__main__":
    # Placeholder domain for safe testing
    DOMAIN = "https://example.com/item/"
    
    # EXAMPLE SETUP: Total lines (35M) is larger than Chunk Limit (10M).
    # This will automatically create 4 separate files: 
    # Part 1 (10M), Part 2 (10M), Part 3 (10M), and Part 4 (5M).
    TOTAL_LINES = 35000000  
    CHUNK_LIMIT = 10000000  
    
    generate_chunked_urls(DOMAIN, TOTAL_LINES, CHUNK_LIMIT)
