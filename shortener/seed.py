"""Seed demo links for the 'sudha-gelvi' showcase: python -m shortener.seed"""
from .config import Settings
from .api import create_app

DEMO_LINKS = {
    "sudha-gelvi": "https://github.com/sudharanigelivi",
    "sudha-docs": "https://docs.github.com/en/copilot",
    "sudha-py": "https://www.python.org/",
}


def main() -> None:
    settings = Settings.from_env()
    app = create_app(settings)
    for alias, url in DEMO_LINKS.items():
        try:
            link = app.state.service.create(url, alias, None)
            print(f"{settings.base_url}/{link.code} -> {url}")
        except Exception as exc:  # alias already seeded or rejected
            print(f"skip {alias}: {exc}")


if __name__ == "__main__":
    main()
