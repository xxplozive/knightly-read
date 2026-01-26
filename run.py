#!/usr/bin/env python3
"""Main entry point for the news aggregator."""
import logging
import sys
import os
import json
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

        # Create CNAME file for custom domain
        cname_path = BASE_DIR / 'output' / 'CNAME'
        cname_path.write_text('knightlyread.com')

        # Copy days.json to output for special day banner
        import shutil
        days_source = BASE_DIR / 'data' / 'days.json'
        if days_source.exists():
            shutil.copy(days_source, BASE_DIR / 'output' / 'days.json')
            logger.info("Copied days.json to output")

        # Generate logo and favicon from source image
        logo_source = BASE_DIR / 'assets' / 'logo-source.png'
        if logo_source.exists():
            from PIL import Image
            img = Image.open(logo_source)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            width, height = img.size

            # Resize for header logo (120px height for 3x retina, displays at 40px)
            new_height = 120
            new_width = int(width * new_height / height)
            logo_dark = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logo_dark.save(BASE_DIR / 'output' / 'logo-dark.png')

            # Create inverted version for dark mode
            pixel_data = list(img.getdata())
            inv_data = [(255-p[0], 255-p[1], 255-p[2], p[3]) if p[3] > 30 else (255, 255, 255, 0) for p in pixel_data]
            img_light = img.copy()
            img_light.putdata(inv_data)
            logo_light = img_light.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logo_light.save(BASE_DIR / 'output' / 'logo-light.png')

            # Favicon - crop to square then resize
            crop_size = min(width, height)
            left = (width - crop_size) // 2
            top = (height - crop_size) // 2
            knight_sq = img.crop((left, top, left + crop_size, top + crop_size))
            knight_sq.resize((32, 32), Image.Resampling.LANCZOS).save(BASE_DIR / 'output' / 'favicon.png')
            knight_sq.resize((180, 180), Image.Resampling.LANCZOS).save(BASE_DIR / 'output' / 'apple-touch-icon.png')
            logger.info("Generated logo and favicon images")

        # Generate quiz if enabled and API key available
        quiz_config = aggregator.config['settings'].get('quiz', {})
        output_quiz_path = BASE_DIR / 'output' / 'quiz.json'
        fallback_quiz_path = BASE_DIR / 'output' / 'quiz.json'  # tracked in git as fallback

        if quiz_config.get('enabled', False):
            # Check if existing quiz is still valid
            quiz_needs_refresh = True
            if output_quiz_path.exists():
                try:
                    with open(output_quiz_path, 'r') as f:
                        existing_quiz = json.load(f)
                    valid_until = existing_quiz.get('valid_until', '')
                    if valid_until:
                        valid_date = datetime.strptime(valid_until, '%Y-%m-%d').date()
                        today = datetime.now().date()
                        if today <= valid_date:
                            logger.info(f"Quiz still valid until {valid_until}, skipping regeneration")
                            quiz_needs_refresh = False
                        else:
                            logger.info(f"Quiz expired on {valid_until}, will regenerate")
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.warning(f"Could not read existing quiz: {e}")

            if quiz_needs_refresh:
                api_key = os.environ.get('ANTHROPIC_API_KEY')
                if api_key:
                    from src.quiz_generator import QuizGenerator
                    logger.info("Generating weekly quiz...")
                    quiz_gen = QuizGenerator(api_key)
                    quiz_data = quiz_gen.generate_quiz(data, aggregator.config['settings'])
                    if quiz_data:
                        with open(output_quiz_path, 'w') as f:
                            json.dump(quiz_data, f, indent=2)
                        logger.info(f"Quiz generated: {output_quiz_path}")
                    else:
                        logger.warning("Quiz generation failed")
                else:
                    logger.info("Quiz needs refresh but ANTHROPIC_API_KEY not set, using existing")

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Aggregation complete in {elapsed:.2f}s")
        logger.info(f"Output: {BASE_DIR / 'output' / 'index.html'}")

    except Exception as e:
        logger.exception(f"Aggregation failed: {e}")
        raise


if __name__ == '__main__':
    main()
