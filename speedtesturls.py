import os
from tqdm import tqdm

def generate_chunked_urls(base_url, total_records, chunk_size, output_dir="output_chunks"):
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"Starting generation for {total_records:,} total lines.")
    print(f"Files will be split into chunks of {chunk_size:,} lines each.")

    current_chunk = 1
    lines_written_in_chunk = 0
    file_handle = None

    try:
        # tqdm creates an animated progress bar based on the total iteration count
        for i in tqdm(range(1, total_records + 1), desc="Generating URLs", unit="line"):
            
            # Open a new chunk file if necessary
            if file_handle is None:
                file_path = os.path.join(output_dir, f"urls_part_{current_chunk}.txt")
                file_handle = open(file_path, "w", encoding="utf-8")
            
            # Write the formatted URL
            file_handle.write(f"{base_url}{i}\n")
            lines_written_in_chunk += 1
            
            # Close the current file if the chunk limit is reached
            if lines_written_in_chunk >= chunk_size:
                file_handle.close()
                file_handle = None
                lines_written_in_chunk = 0
                current_chunk += 1

    except KeyboardInterrupt:
        print("\nOperation paused by user.")
    finally:
        # Clean up and ensure the final file is properly closed
        if file_handle and not file_handle.closed:
            file_handle.close()
    
    print("\nGeneration process complete.")

if __name__ == "__main__":
    # Generic configurations
    DOMAIN = "https://example.com/item/"
    
    # Configured for a safe, practical test size within environment limits
    TOTAL_LINES = 50000000  # 50 Million lines
    CHUNK_LIMIT = 10000000  # 10 Million lines per file
    
    generate_chunked_urls(DOMAIN, TOTAL_LINES, CHUNK_LIMIT)