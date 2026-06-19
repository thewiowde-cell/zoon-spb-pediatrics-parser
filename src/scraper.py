import re
import math
import json
import random
import urllib.parse
from pathlib import Path
from cloakbrowser import launch


def normalize(phone_str):
    digits = re.sub(r'\D', '', phone_str)
    if phone_str.startswith('+'):
        return '+' + digits
    if digits.startswith('8') and len(digits) == 11:
        return '+7' + digits[1:]
    return digits


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

            page.wait_for_timeout(random.uniform(2000, 4000))

    return urls_list


def collect_data(urls_list, folder_path):
    with launch(headless=False) as browser:
        page = browser.new_page()
        page.route(
            "**/*.{png,jpg,jpeg,gif,webp,svg,woff,woff2,mp4}", lambda route: route.abort())

        result_list = []
        for url in urls_list[:5]:
            try:
                print(f"Processing: {url}")
                page.goto(url, timeout=20000)
                page.wait_for_load_state('networkidle', timeout=15000)

                clinic_name = 'N/A'
                try:
                    name_loc = page.locator(
                        "h1.service-page-header--text, h1[data-uitest='org-name']").first
                    if name_loc.count() > 0:
                        raw_name = name_loc.inner_text()
                        clinic_name = ' '.join(raw_name.split())
                except Exception as e:
                    print(f"Failed to load title: {e}")

                phone_list = ['N/A']
                try:
                    temp_phone_list = []
                    normalized_phones = set()

                    hidden_phone_loc = page.locator(
                        '[class*="js-phone"][data-number]')
                    if hidden_phone_loc.count() > 0:
                        raw_number = hidden_phone_loc.first.get_attribute(
                            'data-number')
                        if raw_number:
                            clean_phone = raw_number.replace(
                                '\xa0', ' ').replace('&nbsp;', ' ').strip()
                            norm = normalize(clean_phone)
                            if norm not in normalized_phones:
                                normalized_phones.add(norm)
                                temp_phone_list.append(clean_phone)

                    phone_elements = page.locator(
                        '.service-description a[href^="tel:"]').all()
                    for element in phone_elements:
                        href = element.get_attribute('href')
                        if href:
                            raw_phone = href.replace('tel:', '').strip()
                            link_text = element.inner_text().strip()
                            display_phone = link_text if link_text and 'Показать' not in link_text else raw_phone

                            norm = normalize(raw_phone)
                            if norm not in normalized_phones:
                                normalized_phones.add(norm)
                                temp_phone_list.append(display_phone)

                    if temp_phone_list:
                        phone_list = temp_phone_list
                except Exception as e:
                    print(f"Phone parsing error: {e}")

                clinic_address = 'N/A'
                try:
                    address_locator = page.locator(
                        "[itemprop='address']").first
                    if address_locator.count() > 0:
                        raw_address = address_locator.inner_text()
                        clinic_address = ' '.join(raw_address.split())
                except:
                    pass

                website = 'N/A'
                try:
                    website_locator = page.locator(
                        '.service-website-value a')
                    if website_locator.count() > 0:
                        raw_url = website_locator.get_attribute('href')
                        if raw_url and 'to=' in raw_url:
                            parsed_url = urllib.parse.urlparse(raw_url)
                            query_params = urllib.parse.parse_qs(
                                parsed_url.query)
                            clean_url = query_params.get('to', [raw_url])[0]
                        else:
                            clean_url = raw_url

                        if '?' in clean_url:
                            clean_url = clean_url.split('?')[0]

                        website = clean_url.strip()
                except Exception as e:
                    print(f"Error getting site: {e}")

                social_links = {}
                try:
                    page.wait_for_timeout(1000)

                    social_elements = page.locator(
                        'a[href*="t.me"], a[href*="vk.com"], a[href*="wa.me"], a[href*="whatsapp"], '
                        'a[class*="social"], a[id*="messenger"], #social-messengers a, .js-service-social'
                    ).all()

                    for element in social_elements:
                        raw_url = element.get_attribute('href')
                        if not raw_url:
                            continue

                        if 'to=' in raw_url:
                            parsed_url = urllib.parse.urlparse(raw_url)
                            query_params = urllib.parse.parse_qs(
                                parsed_url.query)
                            to_param = query_params.get('to')
                            clean_url = to_param[0] if to_param else raw_url
                        else:
                            clean_url = raw_url

                        clean_url = urllib.parse.unquote(clean_url)
                        if '?' in clean_url:
                            clean_url = clean_url.split('?')[0]

                        clean_url = clean_url.strip().rstrip('/')

                        if not clean_url or clean_url.startswith(('javascript:', '#', 'tel:')) or 'zoon.ru' in clean_url:
                            continue

                        if 't.me' in clean_url or 'telegram' in clean_url:
                            platform_key = 'telegram'
                        elif 'vk.com' in clean_url or 'vkontakte' in clean_url:
                            platform_key = 'vk'
                        elif 'wa.me' in clean_url or 'whatsapp' in clean_url:
                            platform_key = 'whatsapp'
                        else:
                            parsed_domain = urllib.parse.urlparse(
                                clean_url).netloc.lower()
                            domain_parts = [p for p in parsed_domain.split(
                                '.') if p not in ('www', 'm', 'api')]
                            platform_key = domain_parts[0] if domain_parts else 'other'

                        if platform_key not in social_links:
                            social_links[platform_key] = clean_url
                        else:
                            pass

                except Exception as e:
                    print(
                        f"Error when collecting social media data in isolation: {e}")

                clinic_rating = 'N/A'
                clinic_reviews = 'N/A'
                try:
                    rating_locator = page.locator(
                        'div.z-text--16.z-text--default.z-text--bold').first
                    if rating_locator.count() > 0:
                        clinic_rating = rating_locator.inner_text().strip()
                    else:
                        clinic_rating = page.locator(
                            'div.z-text--bold').filter(has_text=re.compile(r'^\d+[.,]\d$')).first.inner_text().strip()

                    reviews_locator = page.locator(
                        'span:has-text("оценок"), span:has-text("отзыв")').first
                    if reviews_locator.count() > 0:
                        clinic_reviews = reviews_locator.inner_text().strip()
                except Exception as e:
                    print(f"Rating error: {e}")

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

            except Exception as e:
                print(f"Error processing {url}: {e}")
                result_list.append(
                    {"clinic url": url, "status": f"failed: {str(e)}"})

            page.wait_for_timeout(random.uniform(3000, 7000))

        json_path = folder_path / 'result.json'
        with open(json_path, 'w', encoding='utf-8') as file:
            json.dump(result_list, file, indent=4, ensure_ascii=False)

        print(f"{len(result_list)} records saved")


def main():
    target_url = "https://zoon.ru/spb/medical/type/detskaya_klinika/"

    total_pages = get_page_count(url=target_url)

    folder = Path(__file__).resolve().parent.parent
    folder_path = folder / 'data'
    folder_path.mkdir(exist_ok=True)

    urls_list = get_all_urls(
        base_url=target_url, page_count=total_pages)

    collect_data(urls_list=urls_list, folder_path=folder_path)


if __name__ == '__main__':
    main()
