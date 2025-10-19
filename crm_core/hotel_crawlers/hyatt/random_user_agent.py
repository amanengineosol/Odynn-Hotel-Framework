import random

def get_random_sec_ch_headers(user_agents: str) -> tuple:
    user_agent = user_agents
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