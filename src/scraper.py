import re
import math
import json
import urllib.parse
from pathlib import Path
from cloakbrowser import launch


def get_page_count(url):
    sum_clinics = 0
    cards_count = 0

    with launch(headless=False) as browser:
        page = browser.new_page()
        page.goto(url)

        page.wait_for_load_state("networkidle")

        try:
            page.wait_for_selector('.new_filters_block__count', timeout=15000)
            text_sum_clinics = page.locator(
                '.new_filters_block__count').inner_text()
            numbers = re.findall(r"\d+", text_sum_clinics)
            if numbers:
                sum_clinics = int(numbers[0])
        except Exception as e:
            print(f"Failed to get the total number of clinics: {e}")

        try:
            page.wait_for_selector('.js-results-item', timeout=15000)
            cards = page.locator('.js-results-item')
            cards_count = cards.count()
        except Exception as e:
            print(f"Не удалось посчитать карточки: {e}")

        if sum_clinics > 0 and cards_count > 0:
            page_count = math.ceil(sum_clinics/cards_count)
        else:
            page_count = 1

        print(
            f"Total clinics: {sum_clinics}, Per page: {cards_count}. Pages parsed: {page_count}"
        )

        return page_count


def get_all_urls(base_url, page_count):
    urls_list = []

    with launch(headless=False) as browser:
        page = browser.new_page()

        # for page_num in range(1, + page_count + 1):
        for page_num in range(1, 3):
            if page_num == 1:
                page_url = base_url
            else:
                page_url = f"{base_url}?page={page_num}"

            print(f"Парсим страницу {page_num}: {page_url}")

            try:
                page.goto(page_url)
                page.wait_for_load_state('networkidle')

                page.wait_for_selector('.title-link', timeout=15000)
                page_urls = page.locator(
                    '.title-link').evaluate_all("elements => elements.map(el => el.href)")

                for url in page_urls:
                    urls_list.append(url)
            except Exception as e:
                print(f"Error downloading page {page_num}: {e}")

            page.wait_for_timeout(3000)

    return urls_list


def collect_data(urls_list, folder_path):
    with launch(headless=False) as browser:
        page = browser.new_page()

        result_list = []
        for url in urls_list[:2]:
            try:
                page.goto(url)
                page.wait_for_load_state('networkidle')
            except Exception as e:
                print(f"Failed to load page: {e}")

            try:
                page.wait_for_selector(
                    "h1.service-page-header [itemprop='name']", timeout=15000)
                raw_clinic_name = page.locator(
                    "h1.service-page-header [itemprop='name']").inner_text()
                clinic_name = ' '.join(
                    raw_clinic_name.split()) if raw_clinic_name else 'N/A'
            except Exception as e:
                print(f"Failed to load title: {e}")

            try:
                page.wait_for_selector('a.tel-phone', timeout=5000)
            except:
                print("No phone numbers were found on this page.")

            phone_elements = page.locator(
                'a.tel-phone').all()
            phone_list = []
            for element in phone_elements:
                href = element.get_attribute('href')
                if href:
                    clean_phone = href.replace('tel:', '').strip()
                    if clean_phone not in phone_list:
                        phone_list.append(clean_phone)

            if not phone_list:
                phone_list = ['N/A']

            address_locator = page.locator(
                "[itemprop='address']").first

            if page.locator("[itemprop='address']").count() > 0:
                raw_address = address_locator.inner_text()
                clinic_address = ' '.join(raw_address.split())
            else:
                clinic_address = 'N/A'

            website_locator = page.locator('.service-website-value a')

            if website_locator.count() > 0:
                raw_url = website_locator.get_attribute('href')

                if raw_url and 'to=' in raw_url:
                    parsed_url = urllib.parse.urlparse(raw_url)
                    query_params = urllib.parse.parse_qs(parsed_url.query)
                    website = query_params.get('to', [raw_url])[0]
                else:
                    website = raw_url if raw_url else 'N/A'
            else:
                website = 'N/A'

            social_elements = page.locator(
                '.service-description-social-list a').all()

            social_links = {}
            for element in social_elements:
                raw_url = element.get_attribute('href')

                if raw_url and 'to=' in raw_url:
                    parsed_url = urllib.parse.urlparse(raw_url)
                    query_params = urllib.parse.parse_qs(parsed_url.query)
                    clean_url = query_params.get('to', [raw_url])[0]

                    domain = urllib.parse.urlparse(
                        clean_url).netloc.replace('www', '')
                    platform_name = domain.split('.')[0]
                    if platform_name == 't':
                        platform_name = 'telegram'

                    social_links[platform_name] = clean_url

            rating_locator = page.locator('.service-rating.stars-view').first

            if rating_locator.count() > 0:
                clinic_rating = rating_locator.inner_text().strip()
            else:
                clinic_rating = 'N/A'

            reviews_locator = page.locator(
                '.service-rating.stars-view + span').first
            if reviews_locator.count() > 0:
                raw_reviews = reviews_locator.inner_text()
                clinic_reviews = ' '.join(raw_reviews.split())
            else:
                clinic_reviews = 'N/A'

            result_list.append(
                {
                    "clinic name": clinic_name,
                    "clinic url": url,
                    "clinic phone list": phone_list,
                    "clinic address": clinic_address,
                    "clinic site": website,
                    "social network": social_links if social_links else "not found",
                    "clinic rating": clinic_rating,
                    "clinic reviews": clinic_reviews,
                }
            )

            page.wait_for_timeout(3000)

        json_path = folder_path / 'result.json'

        with open(json_path, 'w', encoding='utf-8') as file:
            json.dump(result_list, file, indent=4, ensure_ascii=False)


def main():
    target_url = "https://zoon.ru/spb/medical/type/detskaya_klinika/"

    total_pages = get_page_count(url=target_url)

    folder = Path(__file__).resolve().parent.parent
    folder_path = folder / 'data'
    folder_path.mkdir(exist_ok=True)

    urls_list = get_all_urls(base_url=target_url, page_count=total_pages)

    collect_data(urls_list=urls_list, folder_path=folder_path)


if __name__ == '__main__':
    main()
