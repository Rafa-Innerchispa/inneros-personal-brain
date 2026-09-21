from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    out = Path(__file__).resolve().parent / ".runtime" / "brightdata_last.json"
    payload = {
        "provider": "brightdata",
        "verified_live_query": "AI hackathons San Francisco September 2026",
        "organic": [
            {
                "title": "AI Events in San Francisco | AI Tinkerers Meetups 2026",
                "description": "San Francisco hosts meetups, talks, and builder demos.",
                "link": "https://sf.aitinkerers.org/",
            },
            {
                "title": "AI Events in San Francisco",
                "description": "Discover upcoming AI events in San Francisco, including hackathons and builder events.",
                "link": "https://luma.com/discover/sf/ai",
            },
            {
                "title": "Data & AI Hackathon at AWS Builder Loft San Francisco",
                "description": "AWS Builder Loft hosts Data & AI hackathon events for builders in San Francisco.",
                "link": "https://builder.aws.com/",
            },
        ],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
