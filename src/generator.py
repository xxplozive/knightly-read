"""Generates static HTML output using Jinja2."""
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from datetime import datetime, timezone
import json


class HTMLGenerator:
    def __init__(self, template_dir: str, output_dir: str):
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, data: dict, default_region: str = 'us'):
        """Generate static HTML files."""
        template = self.env.get_template('index.html')

        generated_at = datetime.now(timezone.utc).strftime('%b %d, %I:%M %p UTC')

        html = template.render(
            regions=data,
            default_region=default_region,
            generated_at=generated_at
        )

        output_path = self.output_dir / 'index.html'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        # Also save JSON for potential API use
        json_path = self.output_dir / 'data.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
