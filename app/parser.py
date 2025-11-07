from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


@dataclass
class OlxAd:
    ad_id: str
    title: str
    price: str
    location_date: str
    size: Optional[str]
    url: str
    image_url: Optional[str]


def _build_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1366,768")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    return driver


def fetch_today_ads(listing_url: str, timeout_sec: int = 20) -> List[OlxAd]:
    driver = _build_driver()
    try:
        driver.get(listing_url)
        # allow dynamic content to load
        time.sleep(3)
        ads: List[OlxAd] = []

        cards = driver.find_elements(By.CSS_SELECTOR, '[data-testid="l-card"][id]')
        for card in cards:
            try:
                ad_id = card.get_attribute("id") or ""
                if not ad_id:
                    continue

                # Location-date line must contain "Сьогодні"
                loc_date_el = card.find_element(By.CSS_SELECTOR, '[data-testid="location-date"]')
                loc_date = loc_date_el.text.strip()
                if "Сьогодні" not in loc_date:
                    continue

                title_el = card.find_element(By.CSS_SELECTOR, '[data-cy="ad-card-title"] h4')
                title = title_el.text.strip()

                price_el = card.find_element(By.CSS_SELECTOR, '[data-testid="ad-price"]')
                price = price_el.text.strip()

                # size is optional, appears with blueprint icon sibling span
                size_text = None
                try:
                    size_span = card.find_element(By.CSS_SELECTOR, '.css-1kfqt7f span')
                    size_text = size_span.text.strip()
                except Exception:
                    size_text = None

                # url inside main anchor
                link_el = card.find_element(By.CSS_SELECTOR, 'a.css-1tqlkj0')
                href = link_el.get_attribute("href") or ""
                if href.startswith("/"):
                    href = "https://www.olx.ua" + href

                # image url if present
                image_url = None
                try:
                    img_el = card.find_element(By.CSS_SELECTOR, 'img')
                    image_url = img_el.get_attribute("src")
                except Exception:
                    image_url = None

                ads.append(OlxAd(
                    ad_id=ad_id,
                    title=title,
                    price=price,
                    location_date=loc_date,
                    size=size_text,
                    url=href,
                    image_url=image_url,
                ))
            except Exception:
                continue

        return ads
    finally:
        driver.quit()


