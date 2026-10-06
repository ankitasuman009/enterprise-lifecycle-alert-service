# Refactored local_build/src/core/template_manager.py
from jinja2 import Environment, FileSystemLoader
import os

def render_template(template_name, context):
    template_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_name)
    return template.render(context)

if __name__ == "__main__":
    # Clean local sanity test
    test_context = {"name": "Test Employee", "year": "2026"}
    print(render_template("onboarding_alert.html", test_context))
