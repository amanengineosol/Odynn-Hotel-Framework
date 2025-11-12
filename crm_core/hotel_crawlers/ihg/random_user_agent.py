import random

def get_random_sec_ch_headers(user_agents: list) -> dict:

    user_agent = random.choice(user_agents)
    ua = user_agent.lower()

    headers = {
        'user-agent': user_agent,
        'accept-encoding': 'gzip, deflate, br, zstd'
    }

    browser_family = "other"

    # Chrome (but not Edge)
    if "chrome" in ua and "edg" not in ua:
        version = user_agent.split("Chrome/")[1].split(".")[0]
        if "windows" in ua:
            platform = '"Windows"'
        elif "macintosh" in ua or "mac os" in ua:
            platform = '"macOS"'
        elif "linux" in ua:
            platform = '"Linux"'
        else:
            platform = '"Windows"'
        headers.update({
            'sec-ch-ua': f'"Not;A=Brand";v="99", "Google Chrome";v="{version}", "Chromium";v="{version}"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': platform,
        })
        browser_family = "chromium"

    # Edge (Chromium-based)
    elif "edg" in ua:
        version = user_agent.split("Edg/")[1].split(".")[0]
        if "windows" in ua:
            platform = '"Windows"'
        elif "macintosh" in ua or "mac os" in ua:
            platform = '"macOS"'
        elif "linux" in ua:
            platform = '"Linux"'
        else:
            platform = '"Unknown"'
        headers.update({
            'sec-ch-ua': f'"Not;A=Brand";v="99", "Microsoft Edge";v="{version}", "Chromium";v="{version}"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': platform,
        })
        browser_family = "chromium"

        # Firefox
    elif "firefox" in ua:
        browser_family = "firefox"

    # Safari
    elif "safari" in ua and "chrome" not in ua:
        browser_family = "webkit"

    return browser_family, headers


# --- Example Usage ---
# USER_AGENT = [
#     "Mozilla/5.0 (X11; CentOS Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.3851.19 Safari/537.36 Edg/139.0.3851.19",
#     "Mozilla/5.0 (X11; Linux Mint 20 x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.3485.94 Safari/537.36 Edg/140.0.3485.94",
#     #"Mozilla/5.0 (X11; Fedora 36 x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.2892.70 Safari/537.36 Edg/141.0.2892.70",
#     "Mozilla/5.0 (X11; Debian GNU/Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.4334.67 Safari/537.36 Edg/140.0.4334.67",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.4551.83 Safari/537.36 Edg/142.0.4551.83",
#     "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.4079.95 Safari/537.36 Edg/139.0.4079.95",
#     "Mozilla/5.0 (X11; CentOS Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.3552.64 Safari/537.36 Edg/138.0.3552.64",
#     "Mozilla/5.0 (X11; Linux Mint 20 x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.4690.88 Safari/537.36 Edg/142.0.4690.88",
#
#     "Mozilla/5.0 (X11; Linux Mint 20 x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.3.111.100 Safari/537.36 Edg/138.3.111.100",
#     "Mozilla/5.0 (X11; Fedora 36 x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.14.99.100 Safari/537.36 Edg/138.14.99.100",
#     "Mozilla/5.0 (X11; Debian GNU/Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.4.120.100 Safari/537.36 Edg/138.4.120.100",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.1.115.100 Safari/537.36 Edg/139.1.115.100",
#     "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.16.114.100 Safari/537.36 Edg/139.16.114.100",
#     "Mozilla/5.0 (X11; CentOS Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.17.89.100 Safari/537.36 Edg/139.17.89.100",
#     "Mozilla/5.0 (X11; Linux Mint 20 x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.18.84.100 Safari/537.36 Edg/139.18.84.100",
#     "Mozilla/5.0 (X11; Fedora 36 x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.9.77.100 Safari/537.36 Edg/139.9.77.100",
#     "Mozilla/5.0 (X11; Debian GNU/Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.3.90.100 Safari/537.36 Edg/139.3.90.100",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.19.78.100 Safari/537.36 Edg/140.19.78.100",
#     "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.1.100.100 Safari/537.36 Edg/140.1.100.100",
#     "Mozilla/5.0 (X11; CentOS Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.2.115.100 Safari/537.36 Edg/140.2.115.100",
#     "Mozilla/5.0 (X11; Linux Mint 20 x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.4.122.100 Safari/537.36 Edg/140.4.122.100",
#     "Mozilla/5.0 (X11; Fedora 36 x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.5.118.100 Safari/537.36 Edg/140.5.118.100",
#     "Mozilla/5.0 (X11; Debian GNU/Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.6.107.100 Safari/537.36 Edg/140.6.107.100",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.7.109.100 Safari/537.36 Edg/141.7.109.100",
#     "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.15.101.100 Safari/537.36 Edg/141.15.101.100",
#     "Mozilla/5.0 (X11; CentOS Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.12.106.100 Safari/537.36 Edg/141.12.106.100",
#     "Mozilla/5.0 (X11; Linux Mint 20 x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.10.89.100 Safari/537.36 Edg/141.10.89.100",
#     "Mozilla/5.0 (X11; Fedora 36 x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.3.92.100 Safari/537.36 Edg/141.3.92.100",
#     "Mozilla/5.0 (X11; Debian GNU/Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.1.87.100 Safari/537.36 Edg/141.1.87.100",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.7.113.100 Safari/537.36 Edg/142.7.113.100",
#     "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.15.99.100 Safari/537.36 Edg/142.15.99.100",
#     "Mozilla/5.0 (X11; CentOS Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.13.105.100 Safari/537.36 Edg/142.13.105.100",
#     "Mozilla/5.0 (X11; Linux Mint 20 x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.10.91.100 Safari/537.36 Edg/142.10.91.100",
#     "Mozilla/5.0 (X11; Fedora 36 x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.3.108.100 Safari/537.36 Edg/142.3.108.100",
#     "Mozilla/5.0 (X11; Debian GNU/Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.1.84.100 Safari/537.36 Edg/142.1.84.100",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.7.103.100 Safari/537.36 Edg/143.7.103.100",
#     "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.15.110.100 Safari/537.36 Edg/143.15.110.100",
#     "Mozilla/5.0 (X11; CentOS Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.12.93.100 Safari/537.36 Edg/143.12.93.100",
#     "Mozilla/5.0 (X11; Linux Mint 20 x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.9.120.100 Safari/537.36 Edg/143.9.120.100",
#     "Mozilla/5.0 (X11; Fedora 36 x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.3.125.100 Safari/537.36 Edg/143.3.125.100",
#     "Mozilla/5.0 (X11; Debian GNU/Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.1.117.100 Safari/537.36 Edg/143.1.117.100",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.7.98.100 Safari/537.36 Edg/144.7.98.100",
#     "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.15.105.100 Safari/537.36 Edg/144.15.105.100",
#     "Mozilla/5.0 (X11; CentOS Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.12.89.100 Safari/537.36 Edg/144.12.89.100",
#     "Mozilla/5.0 (X11; Linux Mint 20 x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.9.114.100 Safari/537.36 Edg/144.9.114.100",
#     "Mozilla/5.0 (X11; Fedora 36 x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.3.121.100 Safari/537.36 Edg/144.3.121.100",
#     "Mozilla/5.0 (X11; Debian GNU/Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.1.110.100 Safari/537.36 Edg/144.1.110.100",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.7.87.100 Safari/537.36 Edg/145.7.87.100",
#     "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.15.95.100 Safari/537.36 Edg/145.15.95.100",
#     "Mozilla/5.0 (X11; CentOS Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.12.99.100 Safari/537.36 Edg/145.12.99.100",
#     "Mozilla/5.0 (X11; Linux Mint 20 x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.9.115.100 Safari/537.36 Edg/145.9.115.100",
#     "Mozilla/5.0 (X11; Fedora 36 x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.3.123.100 Safari/537.36 Edg/145.3.123.100",
#     "Mozilla/5.0 (X11; Debian GNU/Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.1.130.100 Safari/537.36 Edg/145.1.130.100",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.4278.99 Safari/537.36 Edg/141.0.4278.99",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.3274.72 Safari/537.36 Edg/140.0.3274.72",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.2897.44 Safari/537.36 Edg/140.0.2897.44",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.4454.81 Safari/537.36 Edg/139.0.4454.81",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.3851.19 Safari/537.36 Edg/139.0.3851.19",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.3022.27 Safari/537.36 Edg/138.0.3022.27",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.3742.91 Safari/537.36 Edg/138.0.3742.91",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.2949.77 Safari/537.36 Edg/140.0.2949.77",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.3267.24 Safari/537.36 Edg/141.0.3267.24"
# ]
# USER_AGENT = [
#
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.3485.94 Safari/537.36 Edg/140.0.3485.94",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.4334.67 Safari/537.36 Edg/140.0.4334.67",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.3022.21 Safari/537.36 Edg/140.0.3022.21",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.4079.95 Safari/537.36 Edg/139.0.4079.95",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.2989.82 Safari/537.36 Edg/139.0.2989.82",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.4812.88 Safari/537.36 Edg/138.0.4812.88",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.3552.64 Safari/537.36 Edg/138.0.3552.64",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.2892.70 Safari/537.36 Edg/141.0.2892.70",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.3767.43 Safari/537.36 Edg/141.0.3767.43",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.1295.15 Safari/537.36 Edg/140.0.1295.15",
#      # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.3485.94 Safari/537.36 Edg/140.0.3485.94",
#      # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
#      # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0",
#      # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"
#     # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
#     # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"
# # ]
USER_AGENT = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.7204.169 Safari/537.36 OPR/142.0.7204.169",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:141.0) Gecko/20100101 Firefox/141.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"
]
# USER_AGENT = [
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
#     # "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
#     # "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
#     # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
#     # "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:141.0) Gecko/20100101 Firefox/141.0",
#     # "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0",
#     # "Mozilla/5.0 (X11; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0",
#     # "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0",
#     # "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Safari/605.1.15",
#     # "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"
# ]