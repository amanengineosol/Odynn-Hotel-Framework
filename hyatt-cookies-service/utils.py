from ua import user_agent

def get_browser_and_ua(browser:str = 'chrome', ua:str = None):

    try:
        ua= user_agent[browser]
        return ua
    except KeyError:
        return "wrong browser passed as argument"

chrome_ua = get_browser_and_ua('lala')
print(chrome_ua)