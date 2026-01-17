"""Generates quiz questions from news headlines using Claude API."""
import anthropic
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


def get_week_id() -> str:
    """Get the current week identifier (e.g., '2026-W03')."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-W%W")


def get_next_saturday() -> str:
    """Get the date of the next Saturday (or today if Saturday)."""
    now = datetime.now(timezone.utc)
    days_until_saturday = (5 - now.weekday()) % 7
    if days_until_saturday == 0 and now.hour >= 8:
        days_until_saturday = 7
    next_sat = now + timedelta(days=days_until_saturday)
    return next_sat.strftime("%Y-%m-%d")


class QuizGenerator:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate_quiz(self, articles: dict, config: dict) -> Optional[dict]:
        """Generate quiz questions from headlines."""
        quiz_config = config.get('quiz', {})
        source_regions = quiz_config.get('source_regions', ['us', 'global'])
        questions_count = quiz_config.get('questions_count', 10)

        # Collect headlines from specified regions
        headlines = []
        for region in source_regions:
            if region not in articles:
                logger.warning(f"Region '{region}' not found in articles")
                continue
            for article in articles[region]['articles'][:15]:
                headlines.append({
                    'title': article['title'],
                    'source': article['source'],
                    'region': region,
                    'country_flag': article.get('country_flag', '')
                })

        if len(headlines) < 5:
            logger.error("Not enough headlines to generate quiz")
            return None

        logger.info(f"Generating quiz from {len(headlines)} headlines")

        prompt = f"""Generate exactly {questions_count} quiz questions for middle school students (ages 11-14) based on these current news headlines.

Requirements:
- Mix of question types: about 6 multiple choice (4 options: A, B, C, D) and 4 true/false
- Questions should be easy to understand - use simple vocabulary
- Each question must be directly answerable from the headline information
- For global news, you can ask about which country/region the news is from
- Make questions educational and engaging

Headlines:
{json.dumps(headlines, indent=2)}

Return ONLY a valid JSON array with exactly {questions_count} questions in this format:
[
  {{
    "question": "The question text here?",
    "type": "multiple_choice",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_index": 0,
    "source_headline": "The headline this question is based on",
    "explanation": "Brief explanation of why this is correct"
  }},
  {{
    "question": "True or False: Statement here?",
    "type": "true_false",
    "options": ["True", "False"],
    "correct_index": 0,
    "source_headline": "The headline this question is based on",
    "explanation": "Brief explanation"
  }}
]

Return ONLY the JSON array, no other text."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text.strip()

            # Parse JSON response
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])

            questions = json.loads(response_text)

            if not isinstance(questions, list) or len(questions) < questions_count:
                logger.error(f"Invalid response: expected {questions_count} questions")
                return None

            logger.info(f"Successfully generated {len(questions)} quiz questions")

            return {
                "questions": questions[:questions_count],
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "week_of": get_week_id(),
                "valid_until": get_next_saturday(),
                "headline_count": len(headlines)
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse quiz response as JSON: {e}")
            return None
        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating quiz: {e}")
            return None
