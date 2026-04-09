#!/usr/bin/env python3
"""
CleanOps Cold Outreach Lead Generator

Searches Google Places API for cleaning businesses in major US cities,
extracts contact information, attempts to find email addresses from
business websites, and outputs a CSV of leads.

Usage:
    python3 cleanops-outreach.py

Output:
    ../leads/cleanops-leads.csv
"""

import csv
import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
LEADS_DIR = PROJECT_ROOT / "leads"
OUTPUT_CSV = LEADS_DIR / "cleanops-leads.csv"

CREDENTIALS_PATHS = [
    PROJECT_ROOT / ".credentials.env",
    Path.home() / ".openclaw" / "workspace" / "vertexhub-app" / ".env.local",
]

TARGET_CITIES = [
    "Atlanta, GA",
    "Dallas, TX",
    "Houston, TX",
    "Phoenix, AZ",
    "Charlotte, NC",
    "Nashville, TN",
    "Orlando, FL",
    "Tampa, FL",
    "San Antonio, TX",
    "Austin, TX",
    "Denver, CO",
    "Raleigh, NC",
    "Jacksonville, FL",
    "Columbus, OH",
    "Indianapolis, IN",
]

SEARCH_QUERY = "cleaning service"
MAX_RESULTS_PER_CITY = 20  # Google Places returns up to 20 per page

# Email templates keyed by step number
EMAIL_TEMPLATES = {
    1: {
        "day": 0,
        "subject": "Quick question about {business_name}",
        "body": (
            "Hi {contact_name},\n\n"
            "I noticed {business_name} offers cleaning services in {city}. "
            "I'm curious -- are you still managing your schedule and clients "
            "by text message?\n\n"
            "We built CleanOps specifically for cleaning businesses like yours. "
            "It handles scheduling, client management, GPS check-in, photo proof, "
            "and invoicing -- all in one place.\n\n"
            "Would you be open to trying it free for 14 days?\n\n"
            "Start your free trial: https://cleanops-web.vercel.app\n\n"
            "Best,\nTuhin\nFounder, CleanOps"
        ),
    },
    2: {
        "day": 3,
        "subject": "How {city} cleaning businesses save 10 hours/week",
        "body": (
            "Hi {contact_name},\n\n"
            "Most cleaning business owners spend 10+ hours a week on scheduling, "
            "invoicing, and client communication. That's an entire workday lost "
            "to admin every single week.\n\n"
            "CleanOps automates all of it:\n\n"
            "- Drag-and-drop scheduling (no more text message chains)\n"
            "- One-tap invoicing with Stripe payments (get paid faster)\n"
            "- GPS check-in so clients know you showed up\n"
            "- Photo proof of every job (builds trust, wins referrals)\n"
            "- Client portal where customers can book and pay online\n\n"
            "Imagine getting those 10 hours back every week.\n\n"
            "Try it free for 14 days: https://cleanops-web.vercel.app\n\n"
            "Best,\nTuhin\nFounder, CleanOps"
        ),
    },
    3: {
        "day": 7,
        "subject": "From 5 clients to 20 in 3 months",
        "body": (
            "Hi {contact_name},\n\n"
            "One of our users, a solo cleaner in Atlanta, went from managing "
            "5 clients on paper to 20 clients with CleanOps in just 3 months.\n\n"
            "Here's what changed:\n\n"
            "- She stopped losing bookings to missed text messages\n"
            "- Her clients started rebooking through the online portal\n"
            "- Photo proof of every job led to a wave of referrals\n"
            "- Automated invoicing meant she actually got paid on time\n\n"
            "She didn't hire anyone. She didn't run ads. She just got organized.\n\n"
            "If {business_name} is ready to grow without the chaos, CleanOps can help.\n\n"
            "14-day free trial -- no credit card needed: https://cleanops-web.vercel.app\n\n"
            "Best,\nTuhin\nFounder, CleanOps"
        ),
    },
    4: {
        "day": 14,
        "subject": "Should I close your file?",
        "body": (
            "Hi {contact_name},\n\n"
            "I've reached out a few times about helping {business_name} streamline "
            "operations. I don't want to be a bother -- should I close your file?\n\n"
            "No hard feelings either way. If you ever want to try CleanOps, the "
            "14-day free trial is always open:\n\n"
            "https://cleanops-web.vercel.app\n\n"
            "Wishing {business_name} all the best.\n\n"
            "Tuhin\nFounder, CleanOps"
        ),
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_api_key() -> str:
    """Load GOOGLE_PLACES_API_KEY from credential files."""
    for path in CREDENTIALS_PATHS:
        if not path.exists():
            continue
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                if key.strip() == "GOOGLE_PLACES_API_KEY":
                    return value.strip().strip('"').strip("'")

    # Fallback to environment variable
    env_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if env_key:
        return env_key

    print("ERROR: GOOGLE_PLACES_API_KEY not found in credential files or environment.")
    print(f"Searched: {[str(p) for p in CREDENTIALS_PATHS]}")
    sys.exit(1)


def google_places_search(api_key: str, query: str, location: str) -> list[dict]:
    """
    Search Google Places API (Text Search) for businesses.
    Returns a list of place results.
    """
    base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": f"{query} in {location}",
        "key": api_key,
        "type": "establishment",
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        if data.get("status") not in ("OK", "ZERO_RESULTS"):
            print(f"  WARNING: Places API returned status={data.get('status')} "
                  f"for {location}")
            return []

        return data.get("results", [])

    except Exception as e:
        print(f"  ERROR searching {location}: {e}")
        return []


def get_place_details(api_key: str, place_id: str) -> dict:
    """
    Get detailed information for a place including phone, website.
    """
    base_url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,formatted_phone_number,website,url",
        "key": api_key,
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        if data.get("status") == "OK":
            return data.get("result", {})
    except Exception as e:
        print(f"  ERROR getting details for {place_id}: {e}")

    return {}


def scrape_email_from_website(website_url: str) -> str | None:
    """
    Attempt to find an email address on a business website.
    Basic scraping -- looks for mailto: links and email patterns.
    """
    if not website_url:
        return None

    try:
        req = urllib.request.Request(
            website_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        # Look for mailto: links first
        mailto_pattern = r'mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})'
        mailto_matches = re.findall(mailto_pattern, html)
        if mailto_matches:
            return mailto_matches[0].lower()

        # Fall back to general email pattern in page text
        email_pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, html)

        # Filter out common non-business emails
        skip_domains = {
            "example.com", "sentry.io", "wixpress.com", "w3.org",
            "schema.org", "googleapis.com", "google.com", "facebook.com",
            "twitter.com", "instagram.com", "jquery.com", "wordpress.org",
        }
        filtered = [
            e.lower() for e in emails
            if not any(d in e.lower() for d in skip_domains)
            and not e.lower().endswith(".png")
            and not e.lower().endswith(".jpg")
        ]

        if filtered:
            return filtered[0]

    except Exception:
        pass  # Website unreachable or parsing error -- skip silently

    return None


def extract_city_from_address(address: str) -> str:
    """Extract city name from a formatted address string."""
    parts = [p.strip() for p in address.split(",")]
    if len(parts) >= 3:
        return parts[-3]  # Typically: street, city, state zip, country
    if len(parts) >= 2:
        return parts[-2]
    return parts[0] if parts else ""


def render_email(template_num: int, business_name: str, contact_name: str,
                 city: str) -> tuple[str, str]:
    """
    Render an email template with personalization fields filled in.
    Returns (subject, body).
    """
    tmpl = EMAIL_TEMPLATES[template_num]
    fields = {
        "business_name": business_name,
        "contact_name": contact_name or "there",
        "city": city,
    }
    subject = tmpl["subject"].format(**fields)
    body = tmpl["body"].format(**fields)
    return subject, body


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print("=" * 60)
    print("CleanOps Cold Outreach Lead Generator")
    print("=" * 60)

    api_key = load_api_key()
    print(f"API key loaded (ends with ...{api_key[-4:]})")

    # Ensure output directory exists
    LEADS_DIR.mkdir(parents=True, exist_ok=True)

    all_leads = []
    seen_place_ids = set()

    for city in TARGET_CITIES:
        print(f"\nSearching: {SEARCH_QUERY} in {city}")
        results = google_places_search(api_key, SEARCH_QUERY, city)
        print(f"  Found {len(results)} results")

        for place in results[:MAX_RESULTS_PER_CITY]:
            place_id = place.get("place_id", "")
            if place_id in seen_place_ids:
                continue
            seen_place_ids.add(place_id)

            name = place.get("name", "")
            address = place.get("formatted_address", "")

            # Get detailed info (phone, website)
            details = get_place_details(api_key, place_id)
            phone = details.get("formatted_phone_number", "")
            website = details.get("website", "")
            maps_url = details.get("url", "")

            # Try to find email from website
            email = scrape_email_from_website(website) if website else None

            lead_city = extract_city_from_address(address)

            lead = {
                "business_name": name,
                "address": address,
                "city": lead_city,
                "phone": phone,
                "website": website,
                "email": email or "",
                "google_maps_url": maps_url,
                "source": "google_places",
                "date_found": datetime.now().strftime("%Y-%m-%d"),
                "outreach_status": "new",
                "email_1_sent": "",
                "email_2_sent": "",
                "email_3_sent": "",
                "email_4_sent": "",
                "replied": "no",
                "notes": "",
            }
            all_leads.append(lead)
            print(f"    + {name} | {phone} | {email or 'no email'}")

            # Rate limit to avoid hitting API quotas
            time.sleep(0.2)

        # Pause between cities
        time.sleep(1)

    # Write CSV
    if all_leads:
        fieldnames = list(all_leads[0].keys())
        with open(OUTPUT_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_leads)
        print(f"\nWrote {len(all_leads)} leads to {OUTPUT_CSV}")
    else:
        print("\nNo leads found. Check your API key and network connection.")

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Cities searched:  {len(TARGET_CITIES)}")
    print(f"Total leads:      {len(all_leads)}")
    emails_found = sum(1 for l in all_leads if l["email"])
    print(f"Emails found:     {emails_found}")
    print(f"Email hit rate:   {emails_found / len(all_leads) * 100:.1f}%"
          if all_leads else "N/A")
    print(f"Output file:      {OUTPUT_CSV}")

    # Print email template preview
    print("\n" + "=" * 60)
    print("EMAIL TEMPLATE PREVIEW (Email 1)")
    print("=" * 60)
    if all_leads:
        sample = all_leads[0]
        subj, body = render_email(
            1,
            sample["business_name"],
            "there",
            sample["city"],
        )
        print(f"Subject: {subj}\n")
        print(body)


if __name__ == "__main__":
    main()
