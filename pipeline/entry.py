from config.qdrant_config import QDRANT_COLLECTION_NAME, QDRANT_CHUNKS_NAME
from pipeline.pipeline import (
    Pipeline, CrawlStep, PreprocessStep, 
     EmbeddingStep, DatabaseLoadStep
)
import argparse
import os



def main():
    parser = argparse.ArgumentParser(description='Property Data Pipeline')
    parser.add_argument('--url', type=str, 
                        default='https://batdongsan.com.vn/ban-can-ho-chung-cu')
    parser.add_argument('--max-items', type=int, default=10)
    args = parser.parse_args()
    
    # Build the pipeline
    pipeline = (
        Pipeline()
        .add_step(CrawlStep(
            base_url=args.url,
            max_items=args.max_items,
        ))
        .add_step(PreprocessStep())
        .add_step(EmbeddingStep())
        .add_step(DatabaseLoadStep())
    )
    
    result = pipeline.run()
    
    print(f"\nPipeline completed!")
    print(f"  - Crawled: {result.metadata.get('crawled_count', 0)} items")
    print(f"  - Processed: {result.metadata.get('processed_count', 0)} items")
    print(f"  - Embedding: Used {result.metadata.get('total_tokens', 0)} token in total")
    print(f"  - Load to: {QDRANT_COLLECTION_NAME} and {QDRANT_CHUNKS_NAME}")
    print(f"  - Collection size: {result.metadata.get('collection_size', 0)}")


if __name__ == "__main__":
    main()