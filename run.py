#!/usr/bin/env python3
"""Main entry point for the news aggregator."""
import logging
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent

# Setup logging
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'aggregator.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    # Add src to path
    sys.path.insert(0, str(BASE_DIR))

    from src.aggregator import NewsAggregator
    from src.generator import HTMLGenerator

    logger.info("Starting news aggregation...")
    start_time = datetime.now()

    try:
        # Aggregate news
        aggregator = NewsAggregator(BASE_DIR / 'config' / 'feeds.yaml')
        data = aggregator.aggregate()

        # Count total articles
        total = sum(len(r['articles']) for r in data.values())
        logger.info(f"Aggregated {total} articles across {len(data)} regions")

        # Generate HTML
        generator = HTMLGenerator(
            template_dir=BASE_DIR / 'templates',
            output_dir=BASE_DIR / 'output'
        )
        generator.generate(data, default_region='us')

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Aggregation complete in {elapsed:.2f}s")
        logger.info(f"Output: {BASE_DIR / 'output' / 'index.html'}")

    except Exception as e:
        logger.exception(f"Aggregation failed: {e}")
        raise


if __name__ == '__main__':
    main()
