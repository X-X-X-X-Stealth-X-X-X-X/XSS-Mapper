import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import os
# Built by Infiltrator, github : X-X-X-X-Stealth-X-X-X-X
xss_params = set()
visited = set()
params_found = set()
MAX_DEPTH = 3
fragment_params = set()

HEADERS = {
    'User-Agent': 'True_Crawler/1.0 (Infiltrator)'
}

def extract_params_from_url(url):
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    output = []

    if qs:
        for k in qs.keys():
            output.append(f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{k}=<INJECT>")


    if parsed.fragment:
        frag = parsed.fragment
        if '=' in frag:
            parts = frag.split('&')
            for f in parts:
                if '=' in f:
                    name = f.split('=')[0]
                    output.append(f"{parsed.scheme}://{parsed.netloc}{parsed.path}#{name}=<INJECT>")
                    fragment_params.add(name)
        else:
            output.append(f"{parsed.scheme}://{parsed.netloc}{parsed.path}#{frag}=<INJECT>")
            fragment_params.add(frag.strip())

    return output


def extract_parameters(url):
    parsed = urlparse(url)

    query_params = parse_qs(parsed.query)
    for param in query_params:
        xss_params.add(param)

    if parsed.fragment:
        frag = parsed.fragment
        if '=' in frag:
            frag_params = frag.split('&')
            for f in frag_params:
                if '=' in f:
                    name = f.split('=')[0]
                    fragment_params.add(name)
        else:
            fragment_params.add(frag.strip())


def extract_links(url, base):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(base, href)
            if is_same_domain(full_url, base):
                if full_url not in visited:
                    visited.add(full_url)
                    extract_links(full_url, base)

                extract_parameters(full_url)

    except Exception as e:
        print(f"Error: {e}")


def crawl(url, base_url, depth=0):
    if depth > MAX_DEPTH or url in visited:
        return
    visited.add(url)

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            return

        soup = BeautifulSoup(res.text, "html.parser")

        for a in soup.find_all('a', href=True):
            href = urljoin(base_url, a['href'])
            if is_same_domain(href, base_url):
                if "?" in href or "#" in href:
                    param_links = extract_params_from_url(href)
                    for p in param_links:
                        params_found.add(p)
                crawl(href, base_url, depth + 1)

        for form in soup.find_all('form'):
            action = form.get('action') or ''
            full_url = urljoin(base_url, action)
            inputs = form.find_all('input')
            for input_tag in inputs:
                name = input_tag.get('name')
                if name:
                    final = f"{full_url}?{name}=<INJECT>"
                    if is_same_domain(full_url, base_url):
                        params_found.add(final)

    except Exception as e:
        print(f"Error on {url}: {e}")


def is_same_domain(url, base_url):
    return urlparse(url).netloc == urlparse(base_url).netloc


def save_results():
    if not os.path.exists("xss_spider"):
        os.makedirs("xss_spider")
    name = input(" Enter a name for this scan (e.g., 'my_scan'): ").strip()
    folder = f"xss_spider/{name}"
    os.makedirs(folder, exist_ok=True)

    with open(f"{folder}/{name}.txt", "w") as f:
        for p in sorted(params_found):
            f.write(p + "\n")

    print(f"\n💾 Found {len(params_found)} injection points saved to {folder}/{name}.txt")
    if fragment_params:
        print(f"🧨 Fragment Parameters Found: {', '.join(sorted(fragment_params))}")


if __name__ == "__main__":
    start_url = input(" Enter target URL (https://example.com): ").strip()
    print(f"\n🕷 Starting deep XSS parameter crawl on: {start_url}")
    crawl(start_url, start_url)
    save_results()
    print("\n  Now test these with your payloads ")

