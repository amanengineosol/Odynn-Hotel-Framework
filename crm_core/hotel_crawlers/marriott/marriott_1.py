import re
import json
import requests
import logging
from .proxy_manager import ProxyManager
from datetime import datetime, timedelta
from .random_user_agent import get_random_sec_ch_headers, USER_AGENT


# ---------------- Log configuration ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("marriott.log"),
        logging.StreamHandler()
    ]
)

# Log variable for access log
logger = logging.getLogger(__name__)

logger.info("Starting application...")

class ExtractMarriott:
    def __init__(self):
        self._proxy_fetcher = ProxyManager()
        browser_family, headers = get_random_sec_ch_headers(USER_AGENT)
        self._headers = headers
        self._sec_headers_flag = False
        if browser_family not in ("firefox", "webkit"):
            self._sec_headers_flag = True

    def get_search_data(self, hotel_id, check_in_date, check_out_date, guest_count):
        logger.info("Getting proxy IP for current session")
        _proxy_url = self._proxy_fetcher.fetch_proxy()
        if not _proxy_url:
            message = "Proxy url not retrieved from the server"
            # return self.build_response(success=False, data=message, status_code=101)

        proxies = {
            'http': _proxy_url,
            'https': _proxy_url
        }
        logger.info("Proxy url dict created for request")

        # ---------- Session Setup ----------
        session = requests.Session()
        session.proxies.update(proxies)
        session.headers.update(self._headers)
        # logger.info(f"Session Headers :: {session.headers}")

        logger.info("proxy & headers set in request session")

        logger.info("Setting up crawler to extract data")

        # Convert strings to datetime objects
        check_in = datetime.strptime(check_in_date, "%Y-%m-%d")
        check_out = datetime.strptime(check_out_date, "%Y-%m-%d")

        # Calculate length of stay in days
        length_of_stay = int((check_out - check_in).days)


        if not hotel_id or length_of_stay <=0 or guest_count <= 0:
            raise("hotel_id/no_of_stays/guest must have some values.")
            return

        current_date = datetime.today().strftime("%Y-%m-%d")
        next_day_date = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")

        check_in_dd = check_in.strftime("%d")
        check_in_mm = check_in.strftime("%m")
        check_in_yyyy = check_in.strftime("%Y")

        check_out_dd = check_out.strftime("%d")
        check_out_mm = check_out.strftime("%m")
        check_out_yyyy = check_out.strftime("%Y")

        hotel_name_original = hotel_id
        hotel_id = hotel_name_original.split('-')[0].upper()
        logger.info(f"Hotel Name : {hotel_id}")

        # ---- Retry mechanism ----
        int_count = 1
        for icount in range(3):
            is_all_requests_passed = True

            try:

                url = "https://www.marriott.com/mi/query/PhoenixBookProperty"

                payload = "{\"query\":\"query PhoenixBookProperty($propertyId: ID!) {\\n  property(id: $propertyId) {\\n    ... on Hotel {\\n      basicInformation {\\n        ... on HotelBasicInformation {\\n          descriptions {\\n            type {\\n              code\\n              __typename\\n            }\\n            text\\n            __typename\\n          }\\n          isAdultsOnly\\n          resort\\n          __typename\\n        }\\n        __typename\\n      }\\n      __typename\\n    }\\n    __typename\\n  }\\n}\\n\",\"variables\":{\"propertyId\":\"SWFHR\"}}"
                session.headers.update({
                    'host': 'www.marriott.com',
                    'accept': '*/*',
                    'accept-language': 'en-US',
                    'apollographql-client-name': 'phoenix_book',
                    'apollographql-client-version': '1',
                    'application-name': 'book',
                    'content-type': 'application/json',
                    'graphql-force-safelisting': 'true',
                    'graphql-operation-name': 'PhoenixBookProperty',
                    'graphql-operation-signature': '9f165424df22961c9a0d1664c26b9130e2fcf0318bc78c25972cc2e505455376',
                    'graphql-require-safelisting': 'true',
                    'origin': 'https://www.marriott.com',
                    'priority': 'u=1, i',
                    'referer': 'https://www.marriott.com/reservation/rateListMenu.mi',
                    'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
                    # 'sec-ch-ua-mobile': '?0',
                    # 'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    # 'traceparent': '00-82500F26885F2D817F0FAC0BC494864E-94F55A4BF85B8597-01',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
                    # 'x-dtpc': '6$36758541_438h3vKJPTIVKBRMCMUMUDFVHJRKICCHCKJPFR-0e0',
                    'x-request-id': '',
                    # 'Cookie': 'useRequestedLanguage=true; device-characteristics=brand_name=Chrome&model_name=141&marketing_name=Chrome+141&device_os=Windows+NT&device_os_version=10.0&mobile_browser=Chrome&mobile_browser_version=141&is_mobile=false&is_tablet=false; AKA_A2=A; akacd_phoenix=3939689309~rv=18~id=12a00c996a8d48fab88a1fb59b5528ce; bm_ss=ab8e18ef4e; MarriottOrigin=B; rxVisitor=1762236510500UJ89E67ONNQ6FV9I3G79IHLF0B79MMF3; dtSa=-; PIM-SESSION-ID=R3I23v8cqsHkefiT; dtPC=-14526$36510498_552h6vKJPTIVKBRMCMUMUDFVHJRKICCHCKJPFR-0e0; sessionID=BF24730B-B686-5ADE-BAEC-7EB2B046E5D9; MI_SITE=prod17; dtCookie=v_4_srv_6_sn_KAODCQ0URGOLLKUIORP8D969T26LJOM4_perc_100000_ol_0_mul_1_app-3A220110cf75551a30_0_rcs-3Acss_0; rxvt=1762238311614|1762236510502; authStateToken=; ak_bmsc=CA6BEAF696EB1F7F701E7F9051D0AD6B~000000000000000000000000000000~YAAQDWnDF96duTCaAQAAEzd7TR0sAIT2wvNKWQHSNJZoyjmQqBuU5BoXPQPqn3jfbwoZMJuFNNuWjKfVmKdVatKZ53dUjqfIGbtvbn/7NY/soz6Jjk8BSAYSbW9uOzWFEWJN+0w9AElmElei6KiV84mAlWpgGBzEBNiFpAbWKyQ7PiYznDJhPuarxnZjHDAbZSFM9Wd/DuNlpXAq++qYQyEOljlur8863doue2apCiczu/P46GFZeOkUcEklfz5floE5YpeQayPw8GGag799LSaLNZMSpJHQokir76eQSbqHwMtrekTR0/dLd0x+dcjRBz5ksJmnawkeV68HX32N7/ub1rNRBxHXiiZ9G2ibLSb7Eu54QJZNeP1gQluZrDeMarPyADV9NbdlTveVsS8=; s_loginState=unauthenticated; _cls_v=11429a02-91fc-4131-867e-60292ed66b29; _cls_s=563fb0e2-ed23-46c6-a0f6-ef96317d61c4:0; kndctr_664516D751E565010A490D4C_AdobeOrg_identity=CiY0NDgxNjI3Njc2MDAyNTY2OTAzMTgxODI4NTcyODQxNDEyMjcwOFITCMaG7eukMxABGAEqBElORDEwAPABxobt66Qz; kndctr_664516D751E565010A490D4C_AdobeOrg_cluster=ind1; mboxEdgeCluster=41; _fwb=119JflBf6ADPbianadt9FK9.1762236515448; rto=default; _yjsu_yjad=1762236516.efdf70ea-d2af-442e-beb0-8c3817a7f05a; kampyle_userid=d079-fbd9-bddc-93b2-015f-2250-9b2e-e83c; kampyleUserSession=1762236517658; kampyleUserSessionsCount=1; kampyleUserPercentile=68.47193075144122; _fbp=fb.1.1762236518490.231022811610500070; _gcl_au=1.1.1314795305.1762236519; _scid=NCYdRc4TdIRoadqCQwuPVVs72ccYzBms; jvxsync=v1yIQoiNd3om; __lt__cid=a87f94ed-05dc-4bdf-a8ec-ebc20b13b059; __lt__sid=364ea114-3bf18dee; _ScCbts=%5B%5D; _ga=GA1.1.2120643016.1762236520; _pin_unauth=dWlkPU1UYzFNemczTTJVdE1UVXhaUzAwWVRFMExUa3pNVFF0TlRjMVpUQmpPR1JoTWpsag; _yoid=43cb17b9-0006-42f0-a652-6fba98a7842f; _yosid=20a6f641-4acc-4cae-bd6c-a983a2ff1c5a; _sctr=1%7C1762194600000; JVMID=mi-interceptor-app-blue; akacd_phoenix-dtt=3939689359~rv=33~id=51eeb34004c88fd065a1d278c8c0c7e4; AMCVS_664516D751E565010A490D4C%40AdobeOrg=1; AMCV_664516D751E565010A490D4C%40AdobeOrg=-1124106680%7CMCMID%7C44816276760025669031818285728414122708%7CMCAAMLH-1762841362%7C12%7CMCAAMB-1762841362%7Cj8Odv6LonN4r3an7LhD3WZrU1bUpAkFkkiY1ncBR96t2PTI%7CMCOPTOUT-1762243762s%7CNONE%7CvVersion%7C5.2.0; x-mi-tag=NA; OptanonConsent=isGpcEnabled=0&datestamp=Tue+Nov+04+2025+11%3A39%3A25+GMT%2B0530+(India+Standard+Time)&version=202411.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=edbc3615-5624-4479-9419-7271007a4df1&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=1%3A1%2C3%3A1%2C4%3A1%2C6%3A1&AwaitingReconsent=false; kampyleSessionPageCounter=2; _uetsid=b5dd93e0b94411f0b9a70f621c46d7cf; _uetvid=b5dde8e0b94411f0b842a18eb4cbe35c; bm_lso=186B77BA39B1D08A10D13808AADDBA049F53FF693E4ABB6894DAE0D40F4738F5~YAAQDWnDF9GfuTCaAQAAN/h7TQV7mNI0kTitmEnavAV2omUQCNbUTGoowB2pDlouz0spkDNATodLppMpw4GH0f8HcyJE60sciwHW4+yJrkCEhdigKnFLGohFfMaS8vAIgzyH4LvjPLxeV/Tmm/cU/10JhG43+2lmsRLBexvUaeuS4fXdGJKBg0xAwwpeMA7ArVPsk/wy7ozviNi0g4DwwZBuMaonDZrwGAHDZdHt88iqj0uZqJUReVkx3tQnE6aC4xRKN1OflJrS5d/c2CUpEBX6UgpBZ5xPnTuGmySMwJKNBxPYtOkRfmLz3hdnM/qATLzEopdAPimYujpJ5TAyCK2lYdz5+LEmZ8jcMp/Hj0sJyYgiS3Zq4uIdvrbVaIvOZmIpr6M1TXKcFKMgvEmdjx6u6WVY5yjlEbBX/E4EbcjiG/PWR3vQZ66eXhB5tVWwMBWX6aVt7VXW0SC9PEwOBRE=^1762236566821; _scid_r=TaYdRc4TdIRoadqCQwuPVVs72ccYzBmsDvOclA; wcs_bt=s_199db929d7ed:1762236567; at_check=true; s_tbm=true; s_cc=true; aam_uuid=44921783985584242221827693920410799293; demdex=44921783985584242221827693920410799293; merchViewed=serpBannerhvmb010124|; s_sq=%5B%5BB%5D%5D; x_page_trace_id=/search/availabilityCalendar.mi~X~014919FB-A256-5222-84E8-6977A97517A2; _abck=B0CF753F61AEE99653453E75B15044B6~0~YAAQDWnDF8iluTCaAQAAFfh+TQ7IKWG+PShHJxliocIrvyIHjNceWXrV3XAK7GVOdTVKf6TSn/mHcA2HV6M8NXIhb1Qm0gap6l4OWfRrUoxaIO/OgZdfs32kWhtroGxt9dsCtUxM6NLVrqkDhwt/y/JF2IkOIgdcZTeTmlAqMSvxxCkQDr7ea6z/D0xKrA9ot9JW+/29nA2IW8mSuym9dwlAA78PbJl1BFD9jBwIRexW/9jiFFwT/DF1v4akhkPt+N1JLx1bT/wUI57jwYnAzpnbjvdS9vRBI4+ASuG1kPRcSOfKvznVmFgZpuGKnuuzXrqYRsJ7tTSbZ0o23oEmy3L4+AzHcYe1GCmCCxyb4p0eIei+DQRvcXfXTIEwWy6miXWLMNdcHZmTgHjHzFrk//a0oft2Ba0uTuhTW0RvAKB7mrKLnWqq7GPqrCR9C6aVD0BjTI7//49khse+qvMFx4lueOKfTe6C9FjiKY3YkdMzOb2iyDRLv2Q6yveFZxWGfn1QwKnvRHH84+WL9QozrZsRyrujK76CLUWFjGCyCU1eZUyKun0hx4VLxQCAIZlq9Er/z/qXp0rKxT0XyxH6hSpckJGTAe2Q/ZPO9pqsxDS/bTkZTweU0VLELbBPqvzMoiT+cPSNdd1gnQtx2DWqlZG2hr2I+RG9ZggWjYW4W1YCErFtS33r1bLADSIfpMz2yISwb0q5jkqTz1cE/hhkKHtKy4M78VH93OhUuGiSQ+neSn4TmDV3fwYyIFpreMF6mC6VGs0jxPDOQELQFhZGPhowt9QrOeZ2UsPEjFQRQvl+r9ghem4ECZYxOtdviI/rCAPsrTXxh+Jl2bMWD6EOoiAZoQ69wW3/a98WI1bfJpZdKZcROpXztTF9kVxe~-1~-1~1762240158~AAQAAAAE%2f%2f%2f%2f%2f0Q3cPNrdq6pUzYZ044KE6G1eLCJ+QG2sg0L78olU8TQ1ANehU9PnYH+0jFh%2fO6I0%2f5+Irj%2frJjvgtq%2fQ1T6z7A5ZWEP8K5k0V+X~-1; bm_s=YAAQDWnDF8mluTCaAQAAFfh+TQQocM6XZxrg8msasJbXyn/v3QN0dOc1RcOymUKneQ9Xn5536x/Ar0vc8LLVR+t+mp1qK8xc2N/DaEaghdEo0wr8wweKJ1OzXWvBUWqPOJpDLZlfiOPm1wsVxyNRM9adIsRkxoxyc62zE8GJuDEfw0mPUs2UuKRxtz0LmECjSDCV/6HuSPWnZ7raZUpVdndABmNQbYs5rPT4btMDLN7v1BYTGRhRvHMIafEgIq8TTpOxoIo1o9khkyXTSdzFS0X2gDNMtcigsyojC8Fx0q62sn3qlDsOwlSdrj10bAntgy3JjUQDIoZLPIrZPMlO1k6/MBDdRBPYdOmGiTmnH323HFmwZRMmV7+2t2ISmLGLmzX5L7GQX7AuPlj5/0YXQZcH/4cdt9aiyaVFLIl+yPa4lxJ9FaCslDstRfeXOljGVArW2sApwv8DLDL1KEAww3PJPrH7nBKS1VcbowWk0upVmOcJ1drbBhl37Xv50OvOnLby6b96B9HvWxTiaf99/min+63Pzjj7mk9tCF9RqB6rCe8z7FU8CCk2Y2rCo6TNm2PrY9S1El34Ew==; bm_so=2948D778AB5456395F7DCF08478E097F4E73E645FBF767E467C415CB18264ADD~YAAQDWnDF8qluTCaAQAAFfh+TQXPpayj07YsqxYdedAuBMs8it/6zzreGSOJpsE59yM+fptMFx/JaB5E3/topfXPlhKfgGtQKAW2SoDB0a4G1cKF0sA+q6xCGpEKy1dGtiHFoYXf92mGEYG+CdO1hi3pN0i0e9PVPzVJnkIWC0zvJewot69//ULx8uNt8qZGTl2h6ZIouUngZivUZK5EYY+FmKc5bfC2N/llEBTh0xARkTQjnKb0l+9OwklZlFLdrJHFAjc3EJV6Gh+6ek1OpGBexBRqeIVt2r6fSDTh3IAS+7LrZnCd+5H4U9ti7A+AQP4Ube6utPyrEMBCYd1Ah56uQNc3zFGKcbSqZK9NaTWwgnKQLqutpUrMmqV0MURtveEF/dNLeIMWr39YLw8fqyf/s3VE7lfEURqD1v7VEB7x3bEc0fDKRRgQm4B57wQqFPK7/p2hLHx1/bLm3iXZh04=; bm_sz=5EE67950119C229B0541866E8487A67E~YAAQDWnDF8uluTCaAQAAFfh+TR0OSVRGdmYwteyApUoO/0Mck/gbS0xXAvqTgrUW12MJ4GZ2X5bWEV8kRKPNMHFeUv7vyISRJWDzbkSRmA8JkfF2cCl4N4TNeZcGJsE0N71ViXDo+PofOuC3P9TdnJ9V3GIVQKBsqz/V6yAa4kbldFnE2dDmYoudnF0txmjYEcTKBOhmq+yU3R7Nnn9vA7p5z3FtwCXkhZe5CZHWXzfYsd9rLdZ1rfumncWe2kXwmWCIvC6jyc2WnL5WuYNxSgMP6ZxBpVHxe/T/OrgvBVGdsCPdslZsOGUROFKSFXCHAxN/pd9xLbgEeh4uzMJkn1XckAA5lzNTVsRJYjD6o5CrYq83DbB1KSA3kM2xKIcLOpbP+MVCoAdErJEj56FTQprRzoYv8Csvlkiv1sSZINgbpikuIrD7sbj84Q5+MQ==~4274244~4536114; _ga_1LXTBF5X2V=GS2.1.s1762236519$o1$g1$t1762236758$j60$l0$h0; Ddup=6f9802d8-b652-481e-90c7-bd62b6f2be85; mbox=session#44816276760025669031818285728414122708-faIhwd#1762238620|PC#44816276760025669031818285728414122708-faIhwd.41_0#1825481371; _abck=B0CF753F61AEE99653453E75B15044B6~-1~YAAQDWnDF2VeuzCaAQAAt88aTg7fOeJbBbHEZV+uY+ImtP7Ed+PL/XGl1QXHf6YV/EJMT4C9TjJLvkHPWOfygWTQZy0zKPnAlZrCrxfE8YxRU4rbgBWztvp9Kkb3yC6KFjD/6QQzxqf5KElaWldS7Yg82TVC1bFKYUj3foEiW1Ir+2KXnCMa2cnwM787w5JD3MhW0qTMv7cVXvqC34GStls+duTeCJ9rEl2Pn/mohuIUP3ACzLHWyzM8AZYrGPpbWStVAPtJ1SKps8C4vPvIM+KR8HyQ6+0PM7ty3+k4HrikLwazAYp0asyZZCdSWekibFqhXBqQaT/3gBqc0KrZtJZz1oOE1dWnR+sww4OibfSb12+JvlB/0hPRtGEONocF70UF8s85XcTqES3obdLOsxZhjRzzfCyTJ0giW8M+yeMFNEvVZBeNeAjOK0ePeXReXlLfkBKZwZl8usaCLVCCNvpHYODe7aDb1TNT0TaOwY4l1QChPGZfGwY10rQwomC2PsYP3QySCuMNkVH75Xn7ZCCPt9384BzXidHBvZfLUxbJbx0iuEgk36pmSKX28s8KpuW0/q3vahWnAwLzZ5ZySJClI6hvh6CnDvutqNpBKsMBysfwEjraAf2TEMCqTVXPJexdGJyP3QgCCcsI11mbfRCGXHjVa7oiGGLWjcc7o18YdHj7q9Q9qGfU/65C/Z8YG/LgCD1AS4hV5xtT1gJlac89Cu2Y/mPTIesYmXlEBsNUBpmVYmYw3parGiMlsxAtOL5ueGpt6Nil9Onkyfn90HF8smh9Yx4O4LG4pXOz2lFI8MMMhfyN1DGlDQIgm5OBQlCiC/V5bHhYU9l6CklwNpMUGzOiChnrgnvEeRZsLASzTwf0DW6E2jNdQirX~0~-1~1762240158~AAQAAAAE%2f%2f%2f%2f%2f0Q3cPNrdq6pUzYZ044KE6G1eLCJ+QG2sg0L78olU8TQ1ANehU9PnYH+0jFh%2fO6I0%2f5+Irj%2frJjvgtq%2fQ1T6z7A5ZWEP8K5k0V+X~-1; bm_s=YAAQDWnDFzRduzCaAQAA32caTgRC0+njTaalf4AeUCxIO8x0nshoSLDNF4SlgKr8IRSXPlSyEW7vQbHhOS+xifSFBqZSKoY4tLKOHEyTG8Nx9HNmypu0xdVHVJgW1WR1a+J71GuIyFvEWbKf7X3vtYMpaoQYfd6NMfuoMyrTgeGpolWxALnP4l2r2M1o2OB5ipB1VI86Dl5KdxKPNsrnoXynxSMcupTP40KNPIjexkby/HY5NBH8E7kL9zMQpvNm6PpJlyne2jJNrmRt1HTVEE68zjZlTrF1vxnnTLtlxZGMij5Zfvcy8RlROReilOZ2/dMOHIy6m3BGvk4kBjHdLPuRASCN9FTATwhi/lxw4IQalWWMSCO2TNd2X6tb4dhfBkpaFqe8dYHZrYJ6eV0BUkQMBj1B0xy99HGUPpJlLVqZ4eBySAWqC3RXaYCZFPHAcVZF+iWaQ9jd9xlW5nlZE+evxOeKS5V5YQrnr41WtyNbHBOoXAbxUJnTKc4bygiy/VAqA+X/0K8I94paZmTpnDjolj//RmDBzShURO+HVvupkoIryVLWypNLQ4rZ8yWyLsFsLECQHqwPVGBYVGFHZQ==; bm_so=C9482E4FA3FD0D807C78FAC91FD0BEECF05223D25B00FDBF8EF0F4BE51875D57~YAAQDWnDFy5rszCaAQAAoIOiSQUQqoJLBkg9CjJlMLEh2Q2vZRreOF48v1hxhnJH0xJf8oTjkZUZfVXskBNitDv/v4Q9IsEhYAD8Nub5ohM2COOZRu8NzKp7CsTdag0sB9e3h3JYHcxnxnM6BrE+LOhhsIXwwKFjYazgkYc6A5yjBj4m0OuLLLaSDvsZbZGYcRx0R+/Lh6G3d52i0xZTjUB1q5VAIhT8mm+OUJCYhgl3TbEzX4LKZvlPFy5/hL8oekSss4HsNiJrtVdFgRogJx1LOQtcfcCxx2kpjKzsfnmAXEE31WtAG9EXk5aE/jOHqapZTmLdg0sRQVxBm6fn9woo3FMr6GjfyghUhS1V1ajZTRTrMUuo1AI8q8EsD6KpmaeP3377lbjkGfLi+zUG0ZYZZpIq8chm2uJVCXHKjCAKuxP6UQF2gPW/9zh/02IzQsppdwEdg4XCZXsEX0zXLeA=; bm_sz=5EE67950119C229B0541866E8487A67E~YAAQDWnDF6GmuTCaAQAAv6F/TR0tR2YmgvEAkwfHKwTjKxSFk3yKJF1a+LfJp0Ap8fu5Hzb+yGERL9u8xrpzehOGpHuVEG0EjbasTYtWoQjrs1f/PUi9dn27fSBqhHwiNCJdjbcHbnFyS4LEKAkMS6rnk/yxFTkBl69xyXzv6GKCRJkzhAFHTsP0SCLAmFZU0NrgxpEl0TCzyTi6O32BJwicbdl66DsXL0iKDdtl5Y8Av+zQaVvBRo8nIZ/EFgk4dxM0ne8aWL5LwdtdNKGIyWhlp3QI5I46sLGHyHCHuimZ5lH1NL1jUJBI+wAtpEiI/8DJVZ5sw1uqeLrHEntxb6TGeV8Bu/i+KgUzrIx4NXhkp433GaeyNf0sQFH/aVsun9SPJwVPaKpXFEsHWUxvQ9sTPkatWOTOK5bf7QEfLM47IvE=~4274244~4536114; JVMID=mi-interceptor-app-blue; MI_Visitor=3AF17CDC-A9AC-52B9-96EE-E90A3EF5710E; device-characteristics=brand_name=Chrome&model_name=141&marketing_name=Chrome+141&device_os=Windows+NT&device_os_version=10.0&mobile_browser=Chrome&mobile_browser_version=141&is_mobile=false&is_tablet=false'
                })
                response = session.post(url, data=payload)
                #
                print(response.status_code)

                url = "https://www.marriott.com/mi/query/PhoenixBookSearchProductsByProperty"

                # payload = json.dumps({
                #     "operationName": "PhoenixBookSearchProductsByProperty",
                #     "variables": {
                #         "search": {
                #             "options": {
                #                 "startDate": f"{check_in_date}",
                #                 "endDate": f"{check_out_date}",
                #                 "quantity": 1,
                #                 "numberInParty": 1,
                #                 "childAges": [],
                #                 "productRoomType": [
                #                     "ALL"
                #                 ],
                #                 "productStatusType": [
                #                     "AVAILABLE"
                #                 ],
                #                 "rateRequestTypes": [
                #                     {
                #                         "value": "",
                #                         "type": "STANDARD"
                #                     },
                #                     {
                #                         "value": "",
                #                         "type": "PREPAY"
                #                     },
                #                     {
                #                         "value": "",
                #                         "type": "PACKAGES"
                #                     },
                #                     {
                #                         "value": "MRM",
                #                         "type": "CLUSTER"
                #                     },
                #                     {
                #                         "value": "",
                #                         "type": "REDEMPTION"
                #                     }
                #                 ],
                #                 "isErsProperty": False
                #             },
                #             "propertyId": f"{hotel_id}"
                #         },
                #         "offset": 0,
                #         "limit": 150
                #     },
                #     "query": "query PhoenixBookSearchProductsByProperty($search: ProductByPropertySearchInput, $offset: Int, $limit: Int) {\n  searchProductsByProperty(search: $search, offset: $offset, limit: $limit) {\n    edges {\n      node {\n        ... on HotelRoom {\n          availabilityAttributes {\n            rateCategory {\n              type {\n                code\n                __typename\n              }\n              value\n              __typename\n            }\n            isNearSellout\n            __typename\n          }\n          rates {\n            name\n            description\n            rateAmounts {\n              amount {\n                origin {\n                  amount\n                  currency\n                  valueDecimalPoint\n                  __typename\n                }\n                __typename\n              }\n              points\n              pointsSaved\n              pointsToPurchase\n              __typename\n            }\n            localizedDescription {\n              translatedText\n              sourceText\n              __typename\n            }\n            localizedName {\n              translatedText\n              sourceText\n              __typename\n            }\n            rateAmountsByMode {\n              averageNightlyRatePerUnit {\n                amount {\n                  origin {\n                    amount\n                    currency\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          basicInformation {\n            type\n            name\n            localizedName {\n              translatedText\n              __typename\n            }\n            description\n            localizedDescription {\n              translatedText\n              __typename\n            }\n            membersOnly\n            oldRates\n            representativeRoom\n            housingProtected\n            actualRoomsAvailable\n            depositRequired\n            roomsAvailable\n            roomsRequested\n            ratePlan {\n              ratePlanType\n              ratePlanCode\n              marketCode\n              __typename\n            }\n            freeCancellationUntil\n            __typename\n          }\n          roomAttributes {\n            attributes {\n              id\n              description\n              groupID\n              category {\n                code\n                description\n                __typename\n              }\n              accommodationCategory {\n                code\n                description\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          totalPricing {\n            quantity\n            rateAmountsByMode {\n              grandTotal {\n                amount {\n                  origin {\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              subtotalPerQuantity {\n                amount {\n                  origin {\n                    currency\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              totalMandatoryFeesPerQuantity {\n                amount {\n                  origin {\n                    currency\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          id\n          __typename\n        }\n        id\n        __typename\n      }\n      __typename\n    }\n    total\n    status {\n      ... on UserInputError {\n        httpStatus\n        messages {\n          user {\n            message\n            field\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      ... on DateRangeTooLongError {\n        httpStatus\n        messages {\n          user {\n            message\n            field\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"
                # })
                check = 'false'
                payload = json.dumps({
                    "operationName": "PhoenixBookSearchProductsByProperty",
                    "variables": {
                        "search": {
                            "options": {
                                "startDate": "2025-11-21",
                                "endDate": "2025-11-29",
                                "quantity": 1,
                                "numberInParty": 1,
                                "childAges": [],
                                "productRoomType": [
                                    "ALL"
                                ],
                                "productStatusType": [
                                    "AVAILABLE"
                                ],
                                "rateRequestTypes": [
                                    {
                                        "value": "",
                                        "type": "STANDARD"
                                    },
                                    {
                                        "value": "",
                                        "type": "PREPAY"
                                    },
                                    {
                                        "value": "",
                                        "type": "PACKAGES"
                                    },
                                    {
                                        "value": "MRM",
                                        "type": "CLUSTER"
                                    },
                                    {
                                        "value": "",
                                        "type": "REDEMPTION"
                                    }
                                ],
                                "isErsProperty": check
                            },
                            "propertyId": "SWFHR"
                        },
                        "offset": 0,
                        "limit": 150
                    },
                    "query": "query PhoenixBookSearchProductsByProperty($search: ProductByPropertySearchInput, $offset: Int, $limit: Int) {\n  searchProductsByProperty(search: $search, offset: $offset, limit: $limit) {\n    edges {\n      node {\n        ... on HotelRoom {\n          availabilityAttributes {\n            rateCategory {\n              type {\n                code\n                __typename\n              }\n              value\n              __typename\n            }\n            isNearSellout\n            __typename\n          }\n          rates {\n            name\n            description\n            rateAmounts {\n              amount {\n                origin {\n                  amount\n                  currency\n                  valueDecimalPoint\n                  __typename\n                }\n                __typename\n              }\n              points\n              pointsSaved\n              pointsToPurchase\n              __typename\n            }\n            localizedDescription {\n              translatedText\n              sourceText\n              __typename\n            }\n            localizedName {\n              translatedText\n              sourceText\n              __typename\n            }\n            rateAmountsByMode {\n              averageNightlyRatePerUnit {\n                amount {\n                  origin {\n                    amount\n                    currency\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          basicInformation {\n            type\n            name\n            localizedName {\n              translatedText\n              __typename\n            }\n            description\n            localizedDescription {\n              translatedText\n              __typename\n            }\n            membersOnly\n            oldRates\n            representativeRoom\n            housingProtected\n            actualRoomsAvailable\n            depositRequired\n            roomsAvailable\n            roomsRequested\n            ratePlan {\n              ratePlanType\n              ratePlanCode\n              marketCode\n              __typename\n            }\n            freeCancellationUntil\n            __typename\n          }\n          roomAttributes {\n            attributes {\n              id\n              description\n              groupID\n              category {\n                code\n                description\n                __typename\n              }\n              accommodationCategory {\n                code\n                description\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          totalPricing {\n            quantity\n            rateAmountsByMode {\n              grandTotal {\n                amount {\n                  origin {\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              subtotalPerQuantity {\n                amount {\n                  origin {\n                    currency\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              totalMandatoryFeesPerQuantity {\n                amount {\n                  origin {\n                    currency\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          id\n          __typename\n        }\n        id\n        __typename\n      }\n      __typename\n    }\n    total\n    status {\n      ... on UserInputError {\n        httpStatus\n        messages {\n          user {\n            message\n            field\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      ... on DateRangeTooLongError {\n        httpStatus\n        messages {\n          user {\n            message\n            field\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"
                })
                # session.headers.pop('traceparent')
                # session.headers.update({
                #     # 'host': 'www.marriott.com',
                #     'content-length': '5190',
                #     # 'application-name': 'book',
                #     # 'x-request-id': '',
                #     # 'sec-ch-ua-platform': '"Windows"',
                #     'graphql-operation-name': 'PhoenixBookSearchProductsByProperty',
                #     'x-dtpc': '6$36758541_438h5vKJPTIVKBRMCMUMUDFVHJRKICCHCKJPFR-0e0',
                #     # 'traceparent': '00-916AE5B5A7E6DCA1E754F9FBE6A00D55-87A64169B3E0C2ED-01',
                #     'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
                #     # 'sec-ch-ua-mobile': '?0',
                #     'graphql-force-safelisting': 'true',
                #     # 'accept': '*/*',
                #     'apollographql-client-version': '1',
                #     'content-type': 'application/json',
                #     'apollographql-client-name': 'phoenix_book',
                #     'graphql-require-safelisting': 'true',
                #     'accept-language': 'en-US',
                #     'graphql-operation-signature': 'a1079a703a2d21d82c0c65e4337271c3029c69028c6189830f30882170075756',
                #     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
                #     'origin': 'https://www.marriott.com',
                #     'sec-fetch-site': 'same-origin',
                #     'sec-fetch-mode': 'cors',
                #     'sec-fetch-dest': 'empty',
                #     'referer': 'https://www.marriott.com/reservation/rateListMenu.mi',
                #     # 'accept-encoding': 'gzip, deflate, br, zstd',
                #     # 'priority': 'u=1, i',
                #     # 'cookie': 'useRequestedLanguage=true; device-characteristics=brand_name=Chrome&model_name=141&marketing_name=Chrome+141&device_os=Windows+NT&device_os_version=10.0&mobile_browser=Chrome&mobile_browser_version=141&is_mobile=false&is_tablet=false; AKA_A2=A; akacd_phoenix=3939689309~rv=18~id=12a00c996a8d48fab88a1fb59b5528ce; bm_ss=ab8e18ef4e; MarriottOrigin=B; rxVisitor=1762236510500UJ89E67ONNQ6FV9I3G79IHLF0B79MMF3; dtSa=-; PIM-SESSION-ID=R3I23v8cqsHkefiT; dtPC=-14526$36510498_552h6vKJPTIVKBRMCMUMUDFVHJRKICCHCKJPFR-0e0; sessionID=BF24730B-B686-5ADE-BAEC-7EB2B046E5D9; MI_SITE=prod17; dtCookie=v_4_srv_6_sn_KAODCQ0URGOLLKUIORP8D969T26LJOM4_perc_100000_ol_0_mul_1_app-3A220110cf75551a30_0_rcs-3Acss_0; rxvt=1762238311614|1762236510502; authStateToken=; ak_bmsc=CA6BEAF696EB1F7F701E7F9051D0AD6B~000000000000000000000000000000~YAAQDWnDF96duTCaAQAAEzd7TR0sAIT2wvNKWQHSNJZoyjmQqBuU5BoXPQPqn3jfbwoZMJuFNNuWjKfVmKdVatKZ53dUjqfIGbtvbn/7NY/soz6Jjk8BSAYSbW9uOzWFEWJN+0w9AElmElei6KiV84mAlWpgGBzEBNiFpAbWKyQ7PiYznDJhPuarxnZjHDAbZSFM9Wd/DuNlpXAq++qYQyEOljlur8863doue2apCiczu/P46GFZeOkUcEklfz5floE5YpeQayPw8GGag799LSaLNZMSpJHQokir76eQSbqHwMtrekTR0/dLd0x+dcjRBz5ksJmnawkeV68HX32N7/ub1rNRBxHXiiZ9G2ibLSb7Eu54QJZNeP1gQluZrDeMarPyADV9NbdlTveVsS8=; s_loginState=unauthenticated; _cls_v=11429a02-91fc-4131-867e-60292ed66b29; _cls_s=563fb0e2-ed23-46c6-a0f6-ef96317d61c4:0; kndctr_664516D751E565010A490D4C_AdobeOrg_identity=CiY0NDgxNjI3Njc2MDAyNTY2OTAzMTgxODI4NTcyODQxNDEyMjcwOFITCMaG7eukMxABGAEqBElORDEwAPABxobt66Qz; kndctr_664516D751E565010A490D4C_AdobeOrg_cluster=ind1; mboxEdgeCluster=41; _fwb=119JflBf6ADPbianadt9FK9.1762236515448; rto=default; _yjsu_yjad=1762236516.efdf70ea-d2af-442e-beb0-8c3817a7f05a; kampyle_userid=d079-fbd9-bddc-93b2-015f-2250-9b2e-e83c; kampyleUserSession=1762236517658; kampyleUserSessionsCount=1; kampyleUserPercentile=68.47193075144122; _fbp=fb.1.1762236518490.231022811610500070; _gcl_au=1.1.1314795305.1762236519; _scid=NCYdRc4TdIRoadqCQwuPVVs72ccYzBms; jvxsync=v1yIQoiNd3om; __lt__cid=a87f94ed-05dc-4bdf-a8ec-ebc20b13b059; __lt__sid=364ea114-3bf18dee; _ScCbts=%5B%5D; _ga=GA1.1.2120643016.1762236520; _pin_unauth=dWlkPU1UYzFNemczTTJVdE1UVXhaUzAwWVRFMExUa3pNVFF0TlRjMVpUQmpPR1JoTWpsag; _yoid=43cb17b9-0006-42f0-a652-6fba98a7842f; _yosid=20a6f641-4acc-4cae-bd6c-a983a2ff1c5a; _sctr=1%7C1762194600000; JVMID=mi-interceptor-app-blue; akacd_phoenix-dtt=3939689359~rv=33~id=51eeb34004c88fd065a1d278c8c0c7e4; AMCVS_664516D751E565010A490D4C%40AdobeOrg=1; AMCV_664516D751E565010A490D4C%40AdobeOrg=-1124106680%7CMCMID%7C44816276760025669031818285728414122708%7CMCAAMLH-1762841362%7C12%7CMCAAMB-1762841362%7Cj8Odv6LonN4r3an7LhD3WZrU1bUpAkFkkiY1ncBR96t2PTI%7CMCOPTOUT-1762243762s%7CNONE%7CvVersion%7C5.2.0; x-mi-tag=NA; OptanonConsent=isGpcEnabled=0&datestamp=Tue+Nov+04+2025+11%3A39%3A25+GMT%2B0530+(India+Standard+Time)&version=202411.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=edbc3615-5624-4479-9419-7271007a4df1&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=1%3A1%2C3%3A1%2C4%3A1%2C6%3A1&AwaitingReconsent=false; kampyleSessionPageCounter=2; _uetsid=b5dd93e0b94411f0b9a70f621c46d7cf; _uetvid=b5dde8e0b94411f0b842a18eb4cbe35c; bm_lso=186B77BA39B1D08A10D13808AADDBA049F53FF693E4ABB6894DAE0D40F4738F5~YAAQDWnDF9GfuTCaAQAAN/h7TQV7mNI0kTitmEnavAV2omUQCNbUTGoowB2pDlouz0spkDNATodLppMpw4GH0f8HcyJE60sciwHW4+yJrkCEhdigKnFLGohFfMaS8vAIgzyH4LvjPLxeV/Tmm/cU/10JhG43+2lmsRLBexvUaeuS4fXdGJKBg0xAwwpeMA7ArVPsk/wy7ozviNi0g4DwwZBuMaonDZrwGAHDZdHt88iqj0uZqJUReVkx3tQnE6aC4xRKN1OflJrS5d/c2CUpEBX6UgpBZ5xPnTuGmySMwJKNBxPYtOkRfmLz3hdnM/qATLzEopdAPimYujpJ5TAyCK2lYdz5+LEmZ8jcMp/Hj0sJyYgiS3Zq4uIdvrbVaIvOZmIpr6M1TXKcFKMgvEmdjx6u6WVY5yjlEbBX/E4EbcjiG/PWR3vQZ66eXhB5tVWwMBWX6aVt7VXW0SC9PEwOBRE=^1762236566821; _scid_r=TaYdRc4TdIRoadqCQwuPVVs72ccYzBmsDvOclA; wcs_bt=s_199db929d7ed:1762236567; at_check=true; s_tbm=true; s_cc=true; aam_uuid=44921783985584242221827693920410799293; demdex=44921783985584242221827693920410799293; merchViewed=serpBannerhvmb010124|; s_sq=%5B%5BB%5D%5D; x_page_trace_id=/search/availabilityCalendar.mi~X~014919FB-A256-5222-84E8-6977A97517A2; _abck=B0CF753F61AEE99653453E75B15044B6~0~YAAQDWnDF8iluTCaAQAAFfh+TQ7IKWG+PShHJxliocIrvyIHjNceWXrV3XAK7GVOdTVKf6TSn/mHcA2HV6M8NXIhb1Qm0gap6l4OWfRrUoxaIO/OgZdfs32kWhtroGxt9dsCtUxM6NLVrqkDhwt/y/JF2IkOIgdcZTeTmlAqMSvxxCkQDr7ea6z/D0xKrA9ot9JW+/29nA2IW8mSuym9dwlAA78PbJl1BFD9jBwIRexW/9jiFFwT/DF1v4akhkPt+N1JLx1bT/wUI57jwYnAzpnbjvdS9vRBI4+ASuG1kPRcSOfKvznVmFgZpuGKnuuzXrqYRsJ7tTSbZ0o23oEmy3L4+AzHcYe1GCmCCxyb4p0eIei+DQRvcXfXTIEwWy6miXWLMNdcHZmTgHjHzFrk//a0oft2Ba0uTuhTW0RvAKB7mrKLnWqq7GPqrCR9C6aVD0BjTI7//49khse+qvMFx4lueOKfTe6C9FjiKY3YkdMzOb2iyDRLv2Q6yveFZxWGfn1QwKnvRHH84+WL9QozrZsRyrujK76CLUWFjGCyCU1eZUyKun0hx4VLxQCAIZlq9Er/z/qXp0rKxT0XyxH6hSpckJGTAe2Q/ZPO9pqsxDS/bTkZTweU0VLELbBPqvzMoiT+cPSNdd1gnQtx2DWqlZG2hr2I+RG9ZggWjYW4W1YCErFtS33r1bLADSIfpMz2yISwb0q5jkqTz1cE/hhkKHtKy4M78VH93OhUuGiSQ+neSn4TmDV3fwYyIFpreMF6mC6VGs0jxPDOQELQFhZGPhowt9QrOeZ2UsPEjFQRQvl+r9ghem4ECZYxOtdviI/rCAPsrTXxh+Jl2bMWD6EOoiAZoQ69wW3/a98WI1bfJpZdKZcROpXztTF9kVxe~-1~-1~1762240158~AAQAAAAE%2f%2f%2f%2f%2f0Q3cPNrdq6pUzYZ044KE6G1eLCJ+QG2sg0L78olU8TQ1ANehU9PnYH+0jFh%2fO6I0%2f5+Irj%2frJjvgtq%2fQ1T6z7A5ZWEP8K5k0V+X~-1; bm_s=YAAQDWnDF8mluTCaAQAAFfh+TQQocM6XZxrg8msasJbXyn/v3QN0dOc1RcOymUKneQ9Xn5536x/Ar0vc8LLVR+t+mp1qK8xc2N/DaEaghdEo0wr8wweKJ1OzXWvBUWqPOJpDLZlfiOPm1wsVxyNRM9adIsRkxoxyc62zE8GJuDEfw0mPUs2UuKRxtz0LmECjSDCV/6HuSPWnZ7raZUpVdndABmNQbYs5rPT4btMDLN7v1BYTGRhRvHMIafEgIq8TTpOxoIo1o9khkyXTSdzFS0X2gDNMtcigsyojC8Fx0q62sn3qlDsOwlSdrj10bAntgy3JjUQDIoZLPIrZPMlO1k6/MBDdRBPYdOmGiTmnH323HFmwZRMmV7+2t2ISmLGLmzX5L7GQX7AuPlj5/0YXQZcH/4cdt9aiyaVFLIl+yPa4lxJ9FaCslDstRfeXOljGVArW2sApwv8DLDL1KEAww3PJPrH7nBKS1VcbowWk0upVmOcJ1drbBhl37Xv50OvOnLby6b96B9HvWxTiaf99/min+63Pzjj7mk9tCF9RqB6rCe8z7FU8CCk2Y2rCo6TNm2PrY9S1El34Ew==; bm_so=2948D778AB5456395F7DCF08478E097F4E73E645FBF767E467C415CB18264ADD~YAAQDWnDF8qluTCaAQAAFfh+TQXPpayj07YsqxYdedAuBMs8it/6zzreGSOJpsE59yM+fptMFx/JaB5E3/topfXPlhKfgGtQKAW2SoDB0a4G1cKF0sA+q6xCGpEKy1dGtiHFoYXf92mGEYG+CdO1hi3pN0i0e9PVPzVJnkIWC0zvJewot69//ULx8uNt8qZGTl2h6ZIouUngZivUZK5EYY+FmKc5bfC2N/llEBTh0xARkTQjnKb0l+9OwklZlFLdrJHFAjc3EJV6Gh+6ek1OpGBexBRqeIVt2r6fSDTh3IAS+7LrZnCd+5H4U9ti7A+AQP4Ube6utPyrEMBCYd1Ah56uQNc3zFGKcbSqZK9NaTWwgnKQLqutpUrMmqV0MURtveEF/dNLeIMWr39YLw8fqyf/s3VE7lfEURqD1v7VEB7x3bEc0fDKRRgQm4B57wQqFPK7/p2hLHx1/bLm3iXZh04=; bm_sz=5EE67950119C229B0541866E8487A67E~YAAQDWnDF8uluTCaAQAAFfh+TR0OSVRGdmYwteyApUoO/0Mck/gbS0xXAvqTgrUW12MJ4GZ2X5bWEV8kRKPNMHFeUv7vyISRJWDzbkSRmA8JkfF2cCl4N4TNeZcGJsE0N71ViXDo+PofOuC3P9TdnJ9V3GIVQKBsqz/V6yAa4kbldFnE2dDmYoudnF0txmjYEcTKBOhmq+yU3R7Nnn9vA7p5z3FtwCXkhZe5CZHWXzfYsd9rLdZ1rfumncWe2kXwmWCIvC6jyc2WnL5WuYNxSgMP6ZxBpVHxe/T/OrgvBVGdsCPdslZsOGUROFKSFXCHAxN/pd9xLbgEeh4uzMJkn1XckAA5lzNTVsRJYjD6o5CrYq83DbB1KSA3kM2xKIcLOpbP+MVCoAdErJEj56FTQprRzoYv8Csvlkiv1sSZINgbpikuIrD7sbj84Q5+MQ==~4274244~4536114; _ga_1LXTBF5X2V=GS2.1.s1762236519$o1$g1$t1762236758$j60$l0$h0; Ddup=6f9802d8-b652-481e-90c7-bd62b6f2be85; mbox=session#44816276760025669031818285728414122708-faIhwd#1762238620|PC#44816276760025669031818285728414122708-faIhwd.41_0#1825481371'
                #     # 'cookie': 'useRequestedLanguage=true; device-characteristics=brand_name=Chrome&model_name=141&marketing_name=Chrome+141&device_os=Windows+NT&device_os_version=10.0&mobile_browser=Chrome&mobile_browser_version=141&is_mobile=false&is_tablet=false; AKA_A2=A; akacd_phoenix=3939614826~rv=38~id=9a875ff8ca0b7ffbbf95ec19ff88f855; bm_ss=ab8e18ef4e; MarriottOrigin=B; dtSa=-; PIM-SESSION-ID=txfFAVoatZhuvcwD; dtPC=-29510$562027889_620h6vUTKONPHOPHJBWFVPFSFNAFGNQFUAKORP-0e0; sessionID=283B489B-C0F1-5E96-9987-3282FBDFD1B8; MI_SITE=prod17; dtCookie=v_4_srv_6_sn_EIJ4M148EU4188LSGNRCO076DGEAG8LK_perc_100000_ol_0_mul_1_app-3A220110cf75551a30_0_rcs-3Acss_0; rxvt=1762163828931|1762162027894; authStateToken=; ak_bmsc=9B016CB8BE425D8B79A1E5960F85A8F6~000000000000000000000000000000~YAAQDWnDF8AgsjCaAQAAULMKSR3LEY8GAJm5MHl4qWrgsKxPUw0jklDEjY74TOmlTW29IlZ3fDkVmb72CGGg3VzZQwskrrc/poZuaNAYFMFRVvL7twTLoGOvkX2tZo1eup85JQARXsxPrePijm1mjSxElRUzTieEClFQ+dRTM6FHkYT+6+PNDtfuQwdjLoQn3Vx0FJph99Qt15nFeWQOeQu5MtbcooR94lj8wTwKrOJIhIJMme2M/IfLccINtXg37diw0L/Zz8U7Lsvlez50gUT/hJaNzXM6/NzuCpSItC9ExhyUPX4rncbqOUUgklZMB9kDEO0sfWFPJrS05A0pO8baE6Np2c47IKG6KAhMdHCs6MQHxgQzWLq9cXdGgL2XxLfKZDkqBtz3IdFrezI=; s_loginState=unauthenticated; _cls_v=b2850aa1-4f9f-46a9-bc62-403aa7eb4676; _cls_s=f84882fc-901a-4246-9b59-7c6db0d2c23c:0; kndctr_664516D751E565010A490D4C_AdobeOrg_identity=CiYyNTMyNzQwNzk3NDU2MTQwMjU1MzI5MjUyNjQxNDU3Mzc4ODk1NVITCPv1qsikMxABGAEqBElORDEwAPAB%2D%5FWqyKQz; kndctr_664516D751E565010A490D4C_AdobeOrg_cluster=ind1; mboxEdgeCluster=41; _fwb=53Askl5RBzhnuQqFAPIRlf.1762162031468; rto=default; _yjsu_yjad=1762162032.4f3c0803-16cb-404f-9006-f654d7a30f8d; _fbp=fb.1.1762162032936.972361057892895196; kampyle_userid=0e08-3c12-351c-ed4b-af07-ff0b-1cf2-04b1; kampyleUserSession=1762162033079; kampyleUserSessionsCount=1; kampyleUserPercentile=74.58942712717389; __lt__cid=6fbc0ce3-00b0-4323-bb39-b6fba8e3a778; __lt__sid=5319f3b9-9efebfa8; _scid=tZBAzBk-bihtbWD82qODhbylDE5vdnWQ; jvxsync=v1tGjmsv6gOv; _ScCbts=%5B%5D; _ga=GA1.1.1883530285.1762162035; _yoid=d0e82a52-1d7f-47b3-a8ce-48205d0e5321; _yosid=a3065403-a25e-4e4b-b606-87871ad54c96; JVMID=mi-interceptor-app-blue; akacd_phoenix-dtt=3939614835~rv=24~id=f0ecde6165dd2ce5175ce0f7ad9df522; bm_sc=4~1~830552331~YAAQDWnDFwYhsjCaAQAAH9EKSQXIMOJn0EhLccFig/qWhfuTPCoJuCn9gQGejxn6qTr2gofZ4RL0GlzzsWTWUg/Mn0OYkaOcIXmT/kF/TRQiDIA4ZgWHjffsch2uWxXuxtutDxV+cWKRN4FCs0FS95xq7czuFqsM1DQb+z+C8hTyJmLRBc5jqrhHeaZcKY5crGUzE2Uz/GzxjEH7lEoPOIBqQz/ns7HhhU11gDeZCWuzPKMdukXRLMWBp1z28ZaVldQIL4p/SOhVVpD48/9zgxM1bE5ng6pegNWFrKpmuwPrXIl4cCteEf2t18nUwo/6UqqgTLIig2Jnv5nEXvTORt239OHkJN4pPV/qWGZD7xEwHlyIiXSfbtxLCqd6zebUvNqwJkXFydpM0KlH9+OhOxekaytU9EET+3El82EqUE+aeI31KHCPSG32+Lno74zX7cmIe2DCqjmuuMLTuRnFVgqEa5pzj9i+3ja6TDxbwdXKdt4tUEf+BBAv2wT0KyjRCda5e9QvR/SAu51w8PpBXTxzyKkZLHVjtXtgqXOzsScYrIPpPrDSSt5mEFHgG67aTLb8lclXAnlPD88um29ThEPlWEQ/vDRNZc2hYtkn0CHDUTVVWnaEMsMlyBOJhsMW7qxixkKDADyQiruBfCV16lnZSMLaovoIvhQAw1X7yteQzz9cGAyXgYT1Pb+Wsvec6jaUfkB5XR11cjVVJ3KDNpWLU0BKgoibp40U2A7XpMx7tcS3I7gt7/dQXicg9D+qHj46gct1pKdAy+FvqLzmz6HXEUB4q39lVJzIKiTWTR+Sl2/LG3+uwB2p4PmBicOVTFoE6UjC2srXFQ3IE3MopzmjRkvC+fXWrNQem5smr6GvKGV+BPBVeMQOs/BKNptyOnKbiubDkQCcY6xycFL2q6yNT/KtKv4Az+JgquXTq3r5jP8BUxrFTLaHuDRRy9jZv8XnFfq0UoCcEbLPrYvPtSQR71zFs5YZXDNO7GFLJ9vR67CUwTrvudNBZF4fti00d51NMHumkKrJj57N2ZMPSSP+7Vnf3SUNvEj/plHTPmar0PzC5FgnUgDuEISn5RcADQEt7vN0Gs8n1BLZeIsxtLVhR/MEcFRI0AnEPOxVfMMcNa4yefLawWOQ4zX8jb4mBau3F1n8tbjoLZ+WbJPCxJHv8M4HUvhRCIsK4lOa93rx3C2GO9YU//L6udNlCz5ME/1txdJNk73OVWLhOJ392FhmudZVZjQOzmMZyPZJ+oIp0XoqvGr9E8tDspz01Sx7BqquVoVkueSNL3R+C3plX0vCBMi6V8L8wTAZ9YYk4nk44hGzAinKE7U9bTgCrmc4JkXMma/TBnSnpxanlqHyY3/R4JMp6cGr0FyO6nZcDq24LhDRPHMswrDBqT8+gHH/5BVX2ExefQqGYrJEgmYl/DF3tCbPyUinOulUi4+IJ3NanbbzqWkrZ4DdsrWcEJ/3RxjCTkNeyjW6s7gmA6V72z28y9xXIRoJP70mQEIgDiALIbiFw/fMkFb4Jtd0AJpMn3Q4FIQw9aqWz/d3LASJc4jwgbKiEQ6mqYk39uv6KWGL6Hys30AhZ+L9RBHI4u/YyIqb2ghTrxG4saI7lokHbzYDcC7au8C8FdDEewkvuZMDXlVOwyc8mFfFH88onJrAEBkY9L9153JtlPUqUORMTBmflam4vqbX51h/177bmdOW8dBKY0G1nur0YDBtggtbUlj6XRygInj4yc/FXBJiLB3qyG8=; at_check=true; _gcl_au=1.1.1842475900.1762162040; _pin_unauth=dWlkPU5UbGlaRFV4TmpBdFpqYzFNUzAwT1RNNExXRm1NV1V0TkdZeU1qUTNNak5qTmpVNA; _sctr=1%7C1762108200000; AMCVS_664516D751E565010A490D4C%40AdobeOrg=1; AMCV_664516D751E565010A490D4C%40AdobeOrg=-1124106680%7CMCMID%7C25327407974561402553292526414573788955%7CMCAAMLH-1762766846%7C12%7CMCAAMB-1762766846%7Cj8Odv6LonN4r3an7LhD3WZrU1bUpAkFkkiY1ncBR96t2PTI%7CMCOPTOUT-1762169246s%7CNONE%7CvVersion%7C5.2.0; s_tbm=true; s_cc=true; aam_uuid=25401780980238278943303385412163178866; demdex=25401780980238278943303385412163178866; x_page_trace_id=/search/findHotels.mi~X~4CE6864C-DB00-5889-96D7-E9C3B5EC2C34; bm_so=A8979BD7A17BB8989C228F936B9E00A809212E53FA4281BE7A0EFD1734B2B58F~YAAQDWnDF/8hsjCaAQAAsXELSQWq3LTBygYuB1eDgA6vhMJhNlgTh/ahqPw4lrNC3eTlKLxMvsse38ZfnxRZ4JwXBr7UDZojJK2CVFnPRxcKN/H06VPq7UpAK6fZyiBCPj5m6lBuWxXuan+jmnOs7Ff4cmyxStktikEpg0HZBRWiccANHTRLoeKQSXf3aVXdh+mw0GLr4Rz9QQIOQsfAWsOvHYLiqd/YDHDoxHYl9WMZIvA6pNORyBxEBPeuJpX8xxIW1Iz62l3foxYjP8HplohFHZFlJk8Mx0QIzkjMClFbnlcwB7syhDQm1kWyhu8UanXeoBHUvsycNtboLpuwH4GDKKIr7XQBc0taLLmppkMkfjJWycN6gCV0Dr9oZ1d9B+uiMFppcxCotlPsCw7LajT6gZHpjaxOvCr8C7qjSsgRMLgY2onVH8SsmHbe1KSwhHatW1f5/BVb7K1ZRgDxvkA=; x-mi-tag=NA; kampyleSessionPageCounter=3; _uetsid=4bd95c10b89711f0951c05517e4a0c1b; _uetvid=4bd987f0b89711f0b5aa75dbf3a347e1; bm_lso=A8979BD7A17BB8989C228F936B9E00A809212E53FA4281BE7A0EFD1734B2B58F~YAAQDWnDF/8hsjCaAQAAsXELSQWq3LTBygYuB1eDgA6vhMJhNlgTh/ahqPw4lrNC3eTlKLxMvsse38ZfnxRZ4JwXBr7UDZojJK2CVFnPRxcKN/H06VPq7UpAK6fZyiBCPj5m6lBuWxXuan+jmnOs7Ff4cmyxStktikEpg0HZBRWiccANHTRLoeKQSXf3aVXdh+mw0GLr4Rz9QQIOQsfAWsOvHYLiqd/YDHDoxHYl9WMZIvA6pNORyBxEBPeuJpX8xxIW1Iz62l3foxYjP8HplohFHZFlJk8Mx0QIzkjMClFbnlcwB7syhDQm1kWyhu8UanXeoBHUvsycNtboLpuwH4GDKKIr7XQBc0taLLmppkMkfjJWycN6gCV0Dr9oZ1d9B+uiMFppcxCotlPsCw7LajT6gZHpjaxOvCr8C7qjSsgRMLgY2onVH8SsmHbe1KSwhHatW1f5/BVb7K1ZRgDxvkA=^1762162080575; _scid_r=zxBAzBk-bihtbWD82qODhbylDE5vdnWQlZuQxQ; wcs_bt=s_199db929d7ed:1762162081; OptanonConsent=isGpcEnabled=0&datestamp=Mon+Nov+03+2025+14%3A58%3A01+GMT%2B0530+(India+Standard+Time)&version=202411.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=e4f0388c-c649-451a-b65e-9bb7af749550&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=1%3A1%2C3%3A1%2C4%3A1%2C6%3A1&AwaitingReconsent=false; merchViewed=hpHero-undefined|hpBanner-|advSearchBanner-MER_GLB0005L9X_GLE000D16M_GLF000T3RY|serpBannerhvmb010124|; s_sq=%5B%5BB%5D%5D; _abck=AB3EE59BA38D71D22E516DE5984072E1~0~YAAQDWnDF3wisjCaAQAAGbILSQ4/Ehcs9pZiG04ty1mi6I02xuPbbiKH9Q9cpTIuIu50jqgqgGO1ByBg5Ou22gbvxjwNyXqGENU60sBLmAMex9lBVvW1t3PTmr7M9EWc7Ug4CYeG8oa8Q515Xe/nQITzhX1tzlb6+Nj3g2t4SjC1+N4scFOSAx5pOy3uDIB3qvbfBulRYIXPRNxZCs4i68vvBwoGKLS/y4tLyy55SSAzcys43/moKoKEZvniKMduy+DIstsU2cFfmBp8z4M+Y5ig2H15Mw6ePgCbRLZ7PBHllmT65hVforNfIW6S1TYVYZyFV4t60Jirygkpkp1FCjunij2lkIUOyosAfoPiomyUAmMWUldOIFNJEIhrVwp8UdBxdWfkWPcKjf5JkFssQ0r3U5qb/urmdPVZcfStgDkWtNIWLw9U1anjJNvExBAjWY0akqLWIVqTQv60xnO6R8LYCfnCDWzg/EFfuPMnpPSLz21SLb+Sb+Pvs35ketBvYh++2BVXV8EMp8AQ2OoGsD54177laSZmzPEBho18L1pDI07uDRNZ1dGZXgjfR8rk/1AWDo/VPR9FHuu2r5aqlQUeD4gC4FpOtYNK1KXbYi9SmTdIeGcYOt1YWrg9TiJ0+tcodj9ci3ZclxyQwJ8rLMFQOd5/P8tfWtXvNTuVIIvW3LZMnoCA7aZe+sTKdUuMuwFso/kDa3ANwQ7sg78weUjR8cqvkdTSgWGVXlxCrP4OmS3nh67PpNj4Tn7vtkOMWjl3n+k4ki2J2VrfqHVEcutAgEhP7c/3LPe6qf+3LG2N4J7HSycP5IuxVSgcnUHgY/aThbE2JM6xHmIRYL67a64gMrpa+yd410DqAOMoW6KG+Kybqo7G+QJUTg==~-1~-1~1762165675~AAQAAAAE%2f%2f%2f%2f%2f34b4M0zOelFMIq3haxzVoIjSRuZzWreXK2o+mGD%2f2gkWLpo2DPweINpB95GftmWuHC30eRgUiZjPhKOT1FaqbsVLvvBtiel1ZjY~-1; bm_s=YAAQDWnDF30isjCaAQAAGbILSQS4e+fhF5NjpLA6yvqcKu0FG36oKEhc53V/Loyu550yZWSY7tnia3tv1Pw9xcvdtr1TvJygisGHO3XMDAh8xjOcvFQVTif1+cl0qegpSBaFs6PygmbK4EjNBGht7/34QLclD7LuqswMLBOl2XHBHYxMBxYuRTHmvaDjFSOw6oonlsXkKXpanBjNBZJRQs4mrMiNlRaGIUN5jfYhFeeiR2OyoYfW6wrvITVBg9Bwdo6ELC8rhfjS++VEARy35lq0WxDLsqDxzXhTOBdBrNEF7ln5rxdWrGyO94urYXSo/bBiCTPgXcxwqvc3YiV3fg18da7z7j8fhcezc7/d1yC8p6ml0Rj+Np6Rd9Jx8BzWDz2YRdnVtFhbUL7AjqJ9A+xCZD+XnNxdC3DLa0kX2F77kKHKFOH+tmG0gF0Ee/Ii04WNK50VCrxGUT8wfTPt0Uz3i3q1xoVfBf5PvXQmA8ZmR2gJrqmg0xDcCgXqPMfIhGEeMs5lDoMBMMXBEID6LJJkNAYmOH09z929UjMPfNFyJl+Pz+DNB18HAvGfcmzPPQ/JQXpEblyO+A==; bm_sz=AF266690FE46EAED160FC659BC8314E1~YAAQDWnDF34isjCaAQAAGbILSR0S7QE4UL/DHUXTVZUpp8TfO/Sz5yS8Cemk0Y6rxDr2jv1HsfjrNdCtLfyCcdXVaNr6wK1ccbxe/BcDsRyAj5g5O/cMJ7rQwaT2gahWNDVe7a6FLBlYg/dKOflJbIVdCzWOo94sFAVyVfsk7mGGqsqS3bwoJHWT4aBCYrYpBk9luyPwK8im+YYt29nLlcX1uFE0z6a3GvFKHWx79WLDKAcfCKC37i2aNFUKiXqVJW56CTuzkibfrnVlfP27Fu1vs/ReiUgtCoehjxF4yjv3W2i2wKK2AFKtv0yU0jv5/kz8XNqF1d0GMkyFBYjONB+nBb24A+Ejt8Bs0iJxLwUqsZKSMWqoZVasRDnQHhpNBLHv9A1EgAGEWm7sZ+1wDT7NHmsmS8/k1PSZWoTygnLTXl7RTImlyBCPZdYYIm42/4+eBlj9Z6UZ44xl3LzcRQ==~4536116~4536133; _ga_1LXTBF5X2V=GS2.1.s1762162034$o1$g1$t1762162094$j60$l0$h0; Ddup=06fa8593-7cbe-4ca3-9708-8377c53fddb0; mbox=session#25327407974561402553292526414573788955-XNXjBN#1762163956|PC#25327407974561402553292526414573788955-XNXjBN.41_0#1825406886; _abck=27073CA09FFBD04249C03138C9D83786~-1~YAAQDWnDF/HEEOiZAQAAH+N08Q7LzdBqNxvu0yhLwJMQwA1TxakR1H7uRkAYgYs/Lc+aAy6tc+f0XJyoJzl7DaHjYJL0rKQLalMEpork56BdVM1Qv4wk06oudnM+QVBjjAyWpLvBdhPdb7aYnInrxrEkPBM+k1zejSl/csqr6GT5tY6xv7IY6w9aD2D8sR8CjnVU0CMvZ5GKT1K4+WWviVwY4qV8HwYuoMrjPQ/ti+MKEwBtE3PilJSEwOE16TrtmKSGiH7UB2QsuDeHsGMbMN8ZdOoObBJa2lix2NbPdF3ubv3s3f7ZQ+LMtF3htDTfKffM0UIwFEyzHMD4feMk8CC+XoAt1oKbggXw7DkNy7uRP1VVtMAsZPWqhXXJADPJSrSGMIlApZe2cnmnq9bSNsVaRsA6G8SzUtL5WPY15tNyUR8kyqLzKlyBeVoQVM8H7VOBl9gxUiUt5fdNM27cNE5jE5jbFTSk037WxmahOtjzYLKkoY6dPt20aUWTZ+iKcbecpg7DvrYcnOIwsYFj48St5/Z/hYQelN0HvneT/dLTuMgh4/bemgAoLvQIgVtlFKjsO+woHan5vZ/7l0dvRc3fj5Yb9Cd4h+/BXrdKtoib8PRoPZaxg2Z/IvzxQP6dnGWF~0~-1~1760688859~AAQAAAAE%2f%2f%2f%2f%2f%2f+XwhtCu8g3JZ09tSBSv7qKr2LntrNtwZfKYBwSbeNP80PRiCW7ejY%2fLuuhDt6m2RBrnf6oSXJx0xbOZiUpP1rxanT9qpbNrEok~-1; bm_s=YAAQDWnDFxTmEOiZAQAABD998QQvAYiLIHztpBxob724mzMV0q0sH/7VzWWLqXaR1RHsxddWAMWRTHh213xeEfuGtROCLYtK0LgB1MVcQjTa8DrnALH88R31K9df14ebRYnYKhHVbb0YHZh9L4CnOwu4mgCUSFcldSWqZlqiCMcqYuk7HSc8fwi6y/P1RxUie0q3UyTabk4jGJZF2tADE0UqQclqcfBA3T1uusNYwco5F9xpNZ3RC85uKjyMan0LVo/eUNCeLAXXR1xlZ9fCHu99VQ2JWT2g9lR6XVoIsv281JPkYTrIqLxeaJHRGscuFCH+RpK0W3E1Ogdzj2zwW3ULZMICUUvBxtBnFNSD4bgLwm24iBrIP7T5NFel8h/Oj4zoDRv+3szfAaoqLrbx931L0C0ykw8a9Qz5LoIcmVQlKoA=; JVMID=mi-interceptor-app-green; MI_SITE=prod17; MI_Visitor=3AF17CDC-A9AC-52B9-96EE-E90A3EF5710E; device-characteristics=brand_name=Chrome&model_name=141&marketing_name=Chrome+141&device_os=Windows+NT&device_os_version=10.0&mobile_browser=Chrome&mobile_browser_version=141&is_mobile=false&is_tablet=false; x-mi-tag=NA'
                # })
                session.headers.update({
                    'host': 'www.marriott.com',
                    'content-length': '5190',
                    'application-name': 'book',
                    'x-request-id': '',
                    'sec-ch-ua-platform': '"Windows"',
                    'graphql-operation-name': 'PhoenixBookSearchProductsByProperty',
                    # 'x-dtpc': '1$43166847_262h5vCSFLRWSLEJSCPHNDTIHJIACCIPFKPFCA-0e0',
                    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
                    'sec-ch-ua-mobile': '?0',
                    'graphql-force-safelisting': 'true',
                    'accept': '*/*',
                    'apollographql-client-version': '1',
                    'content-type': 'application/json',
                    'apollographql-client-name': 'phoenix_book',
                    'graphql-require-safelisting': 'true',
                    'accept-language': 'en-US',
                    'graphql-operation-signature': 'a1079a703a2d21d82c0c65e4337271c3029c69028c6189830f30882170075756',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
                    'origin': 'https://www.marriott.com',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-dest': 'empty',
                    'referer': 'https://www.marriott.com/reservation/rateListMenu.mi',
                    'accept-encoding': 'gzip, deflate, br, zstd',
                    'priority': 'u=1, i',
                    'cookie': 'useRequestedLanguage=true; device-characteristics=brand_name=Chrome&model_name=142&marketing_name=Chrome+142&device_os=Windows+NT&device_os_version=10.0&mobile_browser=Chrome&mobile_browser_version=142&is_mobile=false&is_tablet=false; AKA_A2=A; akacd_phoenix=3940895835~rv=34~id=5bef2c02b577c0d02986faea39662090; bm_ss=ab8e18ef4e; MarriottOrigin=B; PIM-SESSION-ID=vehoYGsHyFS06FiJ; dtSa=-; ak_bmsc=CC6D156FCF3CD329A5EF7105C90D192F~000000000000000000000000000000~YAAQzfUwF3H3JYuaAQAASV5llR3QkhleqmqPIevV1sOa5AXlMHNsyvWwqLbCvnkatzoqGGjv5QFOVfTHuoJKnip7QMiIpMcnMCUDlzn3+CzWaUIamJrGulvlsaLP+nejd+ipIKVvs7QIxxu6TL6aMqU7mJXw6XlMAwJBCkwA6wAdYa69lfsWjyTEXcwrnZxre9wOTDbIoXEIpium+ZdusKNCoJA4gCCEQ/Hjvp1/RqgOzrd9WLT6SRJFAY3kpk2/kTlscU71FDESI20B/oANRNuZmmlCcb1i0CUqID8WJwhCcgpf/1kao4zrxRwHBj4A02vFGXUkFOftDaSkHvaGl5YDEg9QUASGtPxKNQsGupjSDaDUTTwuGz3l6ZNNqP/p4uE66mTdkAI0OU16EPk=; MI_SITE=prod17; authStateToken=; s_loginState=unauthenticated; JVMID=mi-interceptor-app-green; akacd_phoenix-dtt=3940895953~rv=83~id=ab728e8505eb2502bb340651ecf39c96; bm_so=344B3C6A3510E1AA5D70ABC2D6438006D6A23C9131F8BB83122A927B4EE4BB1E~YAAQzfUwF0moJouaAQAAziJnlQVkCu0iyjHgec9zy/TpNpbSJPfAOpHGore6EGS/wMPxueHfBX+a99fdStzf2X22ClxLjQICe7crvdck9+8sc23HI5yvREWglF+i0wknkLO/gb701G3kPtAG5v+33lU+flenjpUJBN5mYLD5dGATZmWC2fDh3EIa2xEOnEJjWFtFO10JeuvAqC90mnEeKFWwECJBBT06PE7rjizuYNxqGzfpQD1iYZ7OPgjOXqUyoeVg7LZMQ1YWRHLoYxylx76iCvbOPOq3azzlKVJtGrSSHrxNMF/japIzN1ux14yw72D3qVtF+lEQ1t/WaP3PQ2z43TrEouA748aXpCWbSVeNG0C5qEjmxcbIPM/dsZscuEyIrrHPWm8kJ2+LA2XGIKok22AP6ocBVAAvMwlixvJgnpk9Cm3XMvye27zZfnLgUVW/3ul++7dkb/hFNVyoyQ==;  bm_lso=344B3C6A3510E1AA5D70ABC2D6438006D6A23C9131F8BB83122A927B4EE4BB1E~YAAQzfUwF0moJouaAQAAziJnlQVkCu0iyjHgec9zy/TpNpbSJPfAOpHGore6EGS/wMPxueHfBX+a99fdStzf2X22ClxLjQICe7crvdck9+8sc23HI5yvREWglF+i0wknkLO/gb701G3kPtAG5v+33lU+flenjpUJBN5mYLD5dGATZmWC2fDh3EIa2xEOnEJjWFtFO10JeuvAqC90mnEeKFWwECJBBT06PE7rjizuYNxqGzfpQD1iYZ7OPgjOXqUyoeVg7LZMQ1YWRHLoYxylx76iCvbOPOq3azzlKVJtGrSSHrxNMF/japIzN1ux14yw72D3qVtF+lEQ1t/WaP3PQ2z43TrEouA748aXpCWbSVeNG0C5qEjmxcbIPM/dsZscuEyIrrHPWm8kJ2+LA2XGIKok22AP6ocBVAAvMwlixvJgnpk9Cm3XMvye27zZfnLgUVW/3ul++7dkb/hFNVyoyQ==^1763443156605; ScCbts=%5B%5D; s_tbm=true; s_cc=true; at_check=true; s_sq=%5B%5BB%5D%5D; _abck=EDC8F4D256B9412527950F3CFCA8E7F6~0~YAAQzfUwF37BJouaAQAAhFNnlQ448XL/R20hVwRq2TAL28oUY+7BE7WWB1D15PoG/WZD4LqCVjJDDpnYs3qqpmdQ6u/+ug+snW0khle7Fx+mOvXkEwzqyLfLnf24jkoEvpv97oznze2nSIbveBLymZSOJazHAA/Sk8kTbq2N97sRbpPgIE5188jYgadBgjMn2uSK1Daen1H3ewVxnLy2pnHHnvvRBQ75i+HJx8sObppye+mkD5CEAUmFAX0aefHvFVzvukw3i3AWOuTXFOVx9XOXr2DyGvGRY1X9qheEbaT+8X5bM33Pf0YXtPpG+FY0CspBp2+Jhile4tApyptAZJD6UQHGbSS5KbJFdPmlrnw1o6ZMytlD99pg8dYvU1SgMc+mBh0yGlFU9nW0ghz6XzLoHyAl9TIPdmh7b8ky1p0ERE+j8zDnWZO79zidPUPqBv+uhDk07VXlqgaKuel84mkm14wR6NJBvgNqC+J9usfaQfiuDVSuxd8682mVd6hVIMhcejprba2acSfLKZ7dBeoT8isolK3y3iUeDKa5qAxIe0CfymqgUq5AP4nBSecXQdpgkfVpJrWQI6KdeLPfMmrgAgvcDhBlG1V6C9DGbDs6R2BO0EX6GGEeh1ds4urfRXDEO6GqVbWNIJP143CyuI4U4OTLLh9o/LavHpLZqHliyAWt3xCN8gy2ySas7ZnCuOnAen66EzHKHAeV2QNO8x6Mxw4cedL/Bizak+/P9t/BN1UbFLz8sQx8zWjYAR+rK+nRQHBFVNPoFz17pDlPvfPbwRuZlQQI26VtdKpnLwIyGg4DLHGsJ+lLYy1d4Mr0fLJoqNc/bu4YR5gTrdvEXkPPHmCzyEoKk/6uEdj+rcRr5krYl7FRcG3h82TSHUlHJuQzUEq24I/enZbtGxh0+uI7NK1iBFc=~-1~-1~1763446755~AAQAAAAE%2f%2f%2f%2f%2f+7wJLz+WsUKkpBDIdt7sPkaa3xCUBC+SjnNl8psP+9YhioAI7iScU7PuC4jlhAk40ad9CLlu1WMe2hWxSYir8cp6IXwlvS0VtQG~-1; bm_s=YAAQzfUwF3/BJouaAQAAhFNnlQSyndDdRWbS+Wv6vF5MnUQS/fAAus7X9gj/ph0I4TPaCUWRb6Vb5HSUsrXh94zKzid7AV08jQXjXQQ0Si0E1odpbelOUAmNpRclVc+/MwTfOmGI+yF5qzaaHyY1vQXbPh9ihy7Fy5+F7wNc0pBejYq7VQlsj8hsAMtcN9gjm6E3q4cJq8nalijh/k3tZTeWxJ/nYYf79fbmPe8ee3eTlbBMbmYaJ246DiBd7sodJLvFi+WYdc1FVfwdSgGnCnaN8LBz7BVczPvVFpI2Lz62NARAVwutayG3zjHqlc7oIUzfQKx/2LHxGptkU5hp4eFrFnvlmelPMdObg0ObmdD4UGoFBroMuQbCqjrzjtPrNIt1Hhefw32pgtcnKxdPN6VJBd4DW/XXgvAMAQy3aaEUiBE8C5/gTSmzhcZ4Mvc73v4BxNb2Dbtq2R//tw91jgxWf7EB/bhVPU+z1XKOpZcCAuUDSMTXCNGfgUSdntAR/N0oxXS6Z+lvJmIg6AXKzShblbEmf4ogfvfZqCXUb7reREQLBQObrRK6olWFZyAc8pmNpob+1X8=; bm_sz=57B734F5DEEE8CD99ABEC851B1AEAEC5~YAAQzfUwF4DBJouaAQAAhFNnlR3WyG2GLpLITiDxGRqyz2zgpM4+TXIj3Kb8g6HHvaPpO2m+wMLtGNBshp3H3Z/Fc2NBStLdxsD9Nud7NoVKn6plsETkm+24KgtNl89cKf9/zpFrIsULVLE+kiAPNDTJDxJoFmgpxJo93KDXV+RrdEZqif4+HoFnCs2WSQHcCn8RK3ZbOna3mObSYa/V8PG1I+I1ojPtK5AXLYh8g2EfFaG2cgIUcPlfME/o1QEMYgOvuQSDIdXjhYPH1AFgGhtXQOWTiYkVePLWK2djgYRF+XswG9kT3feishxd5cc90XzhC4cMXNQE/jUOHXrWRQHlKJTwNOkAH8Tocq0Ei/b6859dpidjtfXN3D8GNBJF34fBdxTfWcWgfyh7d9+Uke0Jr41i2BRGB/Nsrgx39wtD1g==~4273974~3162438; _abck=B0CF753F61AEE99653453E75B15044B6~-1~YAAQDWnDF+VxuzCaAQAAiUkgTg4HY2kvIY65Sg06KnacmEKvZ4sDCu8e+YtU89aDN4Idp4BXeKOMD2rG7xtpiPy/aqQP1XUTS4vgXm8QaJ5miU7JWeXCheuD7AMD8qbbInO5+z6xbIcaCQQbFdODNDJIAQV2f+8nYDDayItf/Dv0jZ52kTSitCr9vQg0gSU+UnNQ4wsAizYHZ0EoDqJxfjomTS8kaP7+WC7C6yC5wag6/6K1f41vFuaSXcu+xxkUQSMnllDOCIHQX6WJXLsSXgGg/ESRJLemoy/F+B50rUhiPru+jkfMqfHenZ7Bpff87/txX7JeAZ880bH2hYwnFueZOAlUnVn80JwQM1gHdyx0gBXipfSU0myr2v3z9XGzdi/7naEYiXn59g6/W3k905BxZvyCAO3OXXR1b7KQYlQfO9YozwMbps/X6B0nEOUYcqsjGtdFP+xt0jIra/hA/OOT5txJAwaauTUyjnSVds6o345xxPVai316p15KvB+yF/P5SMeQcloQaa2cySQEKQ17FW9FvRUOFypobV2Ea8rDGKx5uYh7+x7thiBK1scOqkMq9e8WJPrEElXt0+KRa8CWeyy8pkJiXOvcDGUlW6ZVbJpEHjbVf1SBr6i1+v+L0B5zBiFuYDP2BBVs8/ZpsrrVUZXoI/Hpot0okAw8azAc1gx83n09n0a0P2d1j2ocBPovYz5JXfImbO+uVsTnsxaJ08JKalhO1EvYwk+UaPMsOqZjWnDxFv+UdPUItywfKdB11Xr0OMWHuNZj7L+4xgRb++avK6/9AAhjmDriwPXmRFKPLEncz3FB9317BFk6rhgdA8hteWnnXJZUbLHOG+NXDlXBuMS3gjUUS6DjjsWDQPIUj9orbTgzDPQ6~0~-1~1762240158~AAQAAAAE%2f%2f%2f%2f%2f0Q3cPNrdq6pUzYZ044KE6G1eLCJ+QG2sg0L78olU8TQ1ANehU9PnYH+0jFh%2fO6I0%2f5+Irj%2frJjvgtq%2fQ1T6z7A5ZWEP8K5k0V+X~-1; bm_s=YAAQv/UwF7iJHIWaAQAAAc/ekQS0vRteFOum+9maCvcZYCqq5imlX8bxVs+43WL8pBUzl+qcnCh2UmDmXN31nDhYP4ra8Y9Ipw3ryKuDlr/HnJW3s2lt8bDz6XewKBqVB8GL63sKcEaLewIuQktubUiWyFSiWsp2gSnraRKNHmJgOSfN3nTHsZ0v/YLCXpefxPJKwR8lCu+jr0+hPlrpriqvnarjD+AHzwUepBHaXC/gRYhYKkAurz80NUBHjsALDly84TxgxCpHbICIGdEy8PPqQy1AJs6OLyhKcRgxg83KBhYxYBsEhkIZEOon+wM2hMS2C1YlJDGNkZhz6bimuTyL6xKH4glkBt3Ditzpc7gS56TzBmGVTYVbpaoYW3avhxR9bZ0Urf1b/zu4eH/YRhIZymcl09mH1lETUafpnQG+8ausRw=='
                })
                logger.info(f"Session Headers: {session.headers}")

                resp10 = session.post(url, data=payload)

                logger.info(f"10 - Promotional_Rate_Page Status: {resp10.status_code}")
                logger.info(f"10 - Promotional_Rate_Page Content: {resp10.text[:1000]}")
                if "\"Invalid Property Code\"" in resp10.text:
                    logging.error("Property Code is invalid.")
                    return ("Property Code is invalid.")
                if '"code":"standard"' in resp10.text and '"code":"redemption"' not in resp10.text:
                    logging.error("There are no redemption rates available for the dates you selected.")
                    return("There are no redemption rates available for the dates you selected.")

                text_resp = resp10.text
                file_path = f"marriott_{hotel_id}_{check_in_date}_{check_out_date}_response.json"

                logger.info(f"Saving API Response at Path:- {file_path}")
                json_data = {}

                try:
                    json_data = json.loads(text_resp)
                except json.JSONDecodeError:
                    logger.info("Response is not valid JSON")
                    json_data = {"raw_response": text_resp}

                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=4, ensure_ascii=False)

                int_count += 1

            except Exception as ex:
                logging.error(f"Exception occurred: {ex}")
                is_all_requests_passed = False
            finally:
                logger.info("Closing application...")

            if is_all_requests_passed:
                break

        return json_data

if __name__ =="__main__":
    crawl = ExtractMarriott()
    data = crawl.get_search_data(
        hotel_id="swfhr-inn at bellefield hyde park",
        check_in_date="2025-11-21",
        check_out_date="2025-11-29",
        guest_count=1,
    )
    if data:
        print("API data fetched successfully")
    else:
        print("API data could not be fetched with current cookies")


# import requests
# import json
#
# url = "https://www.marriott.com/mi/query/PhoenixBookSearchProductsByProperty"
#
# payload = json.dumps({
#   "operationName": "PhoenixBookSearchProductsByProperty",
#   "variables": {
#     "search": {
#       "options": {
#         "startDate": "2025-11-21",
#         "endDate": "2025-11-29",
#         "quantity": 1,
#         "numberInParty": 1,
#         "childAges": [],
#         "productRoomType": [
#           "ALL"
#         ],
#         "productStatusType": [
#           "AVAILABLE"
#         ],
#         "rateRequestTypes": [
#           {
#             "value": "",
#             "type": "STANDARD"
#           },
#           {
#             "value": "",
#             "type": "PREPAY"
#           },
#           {
#             "value": "",
#             "type": "PACKAGES"
#           },
#           {
#             "value": "MRM",
#             "type": "CLUSTER"
#           },
#           {
#             "value": "",
#             "type": "REDEMPTION"
#           }
#         ],
#         "isErsProperty": False
#       },
#       "propertyId": "SWFHR"
#     },
#     "offset": 0,
#     "limit": 150
#   },
#   "query": "query PhoenixBookSearchProductsByProperty($search: ProductByPropertySearchInput, $offset: Int, $limit: Int) {\n  searchProductsByProperty(search: $search, offset: $offset, limit: $limit) {\n    edges {\n      node {\n        ... on HotelRoom {\n          availabilityAttributes {\n            rateCategory {\n              type {\n                code\n                __typename\n              }\n              value\n              __typename\n            }\n            isNearSellout\n            __typename\n          }\n          rates {\n            name\n            description\n            rateAmounts {\n              amount {\n                origin {\n                  amount\n                  currency\n                  valueDecimalPoint\n                  __typename\n                }\n                __typename\n              }\n              points\n              pointsSaved\n              pointsToPurchase\n              __typename\n            }\n            localizedDescription {\n              translatedText\n              sourceText\n              __typename\n            }\n            localizedName {\n              translatedText\n              sourceText\n              __typename\n            }\n            rateAmountsByMode {\n              averageNightlyRatePerUnit {\n                amount {\n                  origin {\n                    amount\n                    currency\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          basicInformation {\n            type\n            name\n            localizedName {\n              translatedText\n              __typename\n            }\n            description\n            localizedDescription {\n              translatedText\n              __typename\n            }\n            membersOnly\n            oldRates\n            representativeRoom\n            housingProtected\n            actualRoomsAvailable\n            depositRequired\n            roomsAvailable\n            roomsRequested\n            ratePlan {\n              ratePlanType\n              ratePlanCode\n              marketCode\n              __typename\n            }\n            freeCancellationUntil\n            __typename\n          }\n          roomAttributes {\n            attributes {\n              id\n              description\n              groupID\n              category {\n                code\n                description\n                __typename\n              }\n              accommodationCategory {\n                code\n                description\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          totalPricing {\n            quantity\n            rateAmountsByMode {\n              grandTotal {\n                amount {\n                  origin {\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              subtotalPerQuantity {\n                amount {\n                  origin {\n                    currency\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              totalMandatoryFeesPerQuantity {\n                amount {\n                  origin {\n                    currency\n                    value: amount\n                    valueDecimalPoint\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          id\n          __typename\n        }\n        id\n        __typename\n      }\n      __typename\n    }\n    total\n    status {\n      ... on UserInputError {\n        httpStatus\n        messages {\n          user {\n            message\n            field\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      ... on DateRangeTooLongError {\n        httpStatus\n        messages {\n          user {\n            message\n            field\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"
# })
# # headers = {
#   # 'host': 'www.marriott.com',
#   # 'content-length': '5190',
#   # 'application-name': 'book',
#   # 'x-request-id': '',
#   # 'sec-ch-ua-platform': '"Windows"',
#   # 'graphql-operation-name': 'PhoenixBookSearchProductsByProperty',
#   # 'x-dtpc': '1$43166847_262h5vCSFLRWSLEJSCPHNDTIHJIACCIPFKPFCA-0e0',
#   # 'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
#   # 'sec-ch-ua-mobile': '?0',
#   # 'graphql-force-safelisting': 'true',
#   # 'accept': '*/*',
#   # 'apollographql-client-version': '1',
#   # 'content-type': 'application/json',
#   # 'apollographql-client-name': 'phoenix_book',
#   # 'graphql-require-safelisting': 'true',
#   # 'accept-language': 'en-US',
#   # 'graphql-operation-signature': 'a1079a703a2d21d82c0c65e4337271c3029c69028c6189830f30882170075756',
#   # 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
#   # 'origin': 'https://www.marriott.com',
#   # 'sec-fetch-site': 'same-origin',
#   # 'sec-fetch-mode': 'cors',
#   # 'sec-fetch-dest': 'empty',
#   # 'referer': 'https://www.marriott.com/reservation/rateListMenu.mi',
#   # 'accept-encoding': 'gzip, deflate, br, zstd',
#   # 'priority': 'u=1, i',
#   # 'cookie': 'useRequestedLanguage=true; device-characteristics=brand_name=Chrome&model_name=142&marketing_name=Chrome+142&device_os=Windows+NT&device_os_version=10.0&mobile_browser=Chrome&mobile_browser_version=142&is_mobile=false&is_tablet=false; AKA_A2=A; akacd_phoenix=3940895835~rv=34~id=5bef2c02b577c0d02986faea39662090; bm_ss=ab8e18ef4e; MarriottOrigin=B; PIM-SESSION-ID=vehoYGsHyFS06FiJ; rxVisitor=1763443035254J67J6HTHUMHMCSQ6N6CUOHLDUQCBQKRA; dtPC=-32041$43035250_676h1vCSFLRWSLEJSCPHNDTIHJIACCIPFKPFCA-0e0; dtSa=-; dtCookie=v_4_srv_1_sn_HUC448R7ILPIC7C80RJ13IVDAVTSA3LI_perc_100000_ol_0_mul_1_app-3A220110cf75551a30_0_rcs-3Acss_0; ak_bmsc=CC6D156FCF3CD329A5EF7105C90D192F~000000000000000000000000000000~YAAQzfUwF3H3JYuaAQAASV5llR3QkhleqmqPIevV1sOa5AXlMHNsyvWwqLbCvnkatzoqGGjv5QFOVfTHuoJKnip7QMiIpMcnMCUDlzn3+CzWaUIamJrGulvlsaLP+nejd+ipIKVvs7QIxxu6TL6aMqU7mJXw6XlMAwJBCkwA6wAdYa69lfsWjyTEXcwrnZxre9wOTDbIoXEIpium+ZdusKNCoJA4gCCEQ/Hjvp1/RqgOzrd9WLT6SRJFAY3kpk2/kTlscU71FDESI20B/oANRNuZmmlCcb1i0CUqID8WJwhCcgpf/1kao4zrxRwHBj4A02vFGXUkFOftDaSkHvaGl5YDEg9QUASGtPxKNQsGupjSDaDUTTwuGz3l6ZNNqP/p4uE66mTdkAI0OU16EPk=; sessionID=4D6871B2-F4E7-5EEA-A701-6D5469418077; MI_SITE=prod17; rxvt=1763444868281|1763443035255; authStateToken=; s_loginState=unauthenticated; x_page_trace_id=/search/findHotels.mi~X~2AE25FBA-C522-58E5-B155-6B87A93967C9; JVMID=mi-interceptor-app-green; akacd_phoenix-dtt=3940895953~rv=83~id=ab728e8505eb2502bb340651ecf39c96; bm_so=344B3C6A3510E1AA5D70ABC2D6438006D6A23C9131F8BB83122A927B4EE4BB1E~YAAQzfUwF0moJouaAQAAziJnlQVkCu0iyjHgec9zy/TpNpbSJPfAOpHGore6EGS/wMPxueHfBX+a99fdStzf2X22ClxLjQICe7crvdck9+8sc23HI5yvREWglF+i0wknkLO/gb701G3kPtAG5v+33lU+flenjpUJBN5mYLD5dGATZmWC2fDh3EIa2xEOnEJjWFtFO10JeuvAqC90mnEeKFWwECJBBT06PE7rjizuYNxqGzfpQD1iYZ7OPgjOXqUyoeVg7LZMQ1YWRHLoYxylx76iCvbOPOq3azzlKVJtGrSSHrxNMF/japIzN1ux14yw72D3qVtF+lEQ1t/WaP3PQ2z43TrEouA748aXpCWbSVeNG0C5qEjmxcbIPM/dsZscuEyIrrHPWm8kJ2+LA2XGIKok22AP6ocBVAAvMwlixvJgnpk9Cm3XMvye27zZfnLgUVW/3ul++7dkb/hFNVyoyQ==; AMCVS_664516D751E565010A490D4C%40AdobeOrg=1; AMCV_664516D751E565010A490D4C%40AdobeOrg=-1124106680%7CMCMID%7C44578361389366657883013487034263617020%7CMCAAMLH-1764047954%7C12%7CMCAAMB-1764047954%7C6G1ynYcLPuiQxYZrsz_pkqfLG9yMXBpb2zX5dvJdYQJzPXImdj0y%7CMCOPTOUT-1763450354s%7CNONE%7CvVersion%7C5.2.0; _fbp=fb.1.1763443155561.987461994260091981; x-mi-tag=NA; kndctr_664516D751E565010A490D4C_AdobeOrg_identity=CiY0NDU3ODM2MTM4OTM2NjY1Nzg4MzAxMzQ4NzAzNDI2MzYxNzAyMFIRCMPWnKupMxgBKgRJTkQxMAPwAcPWnKupMw%3D%3D; kndctr_664516D751E565010A490D4C_AdobeOrg_cluster=ind1; _ga=GA1.1.234707069.1763443156; bm_lso=344B3C6A3510E1AA5D70ABC2D6438006D6A23C9131F8BB83122A927B4EE4BB1E~YAAQzfUwF0moJouaAQAAziJnlQVkCu0iyjHgec9zy/TpNpbSJPfAOpHGore6EGS/wMPxueHfBX+a99fdStzf2X22ClxLjQICe7crvdck9+8sc23HI5yvREWglF+i0wknkLO/gb701G3kPtAG5v+33lU+flenjpUJBN5mYLD5dGATZmWC2fDh3EIa2xEOnEJjWFtFO10JeuvAqC90mnEeKFWwECJBBT06PE7rjizuYNxqGzfpQD1iYZ7OPgjOXqUyoeVg7LZMQ1YWRHLoYxylx76iCvbOPOq3azzlKVJtGrSSHrxNMF/japIzN1ux14yw72D3qVtF+lEQ1t/WaP3PQ2z43TrEouA748aXpCWbSVeNG0C5qEjmxcbIPM/dsZscuEyIrrHPWm8kJ2+LA2XGIKok22AP6ocBVAAvMwlixvJgnpk9Cm3XMvye27zZfnLgUVW/3ul++7dkb/hFNVyoyQ==^1763443156605; kampyle_userid=57a6-8986-8abe-3772-b2d2-48a3-15b9-ecda; kampyleUserSession=1763443156733; kampyleUserSessionsCount=1; kampyleUserPercentile=78.71079668921675; kampyleSessionPageCounter=1; _fwb=195Ff11vZCN4rbKP8m9WBLR.1763443156873; _gcl_au=1.1.1721151131.1763443157; wcs_bt=s_199db929d7ed:1763443157; _uetsid=2121b530c43e11f0b0119b8b2984e37b; _uetvid=2121c570c43e11f0af81c95af70c02ab; _yjsu_yjad=1763443157.1e33c843-9a3a-4714-a9d5-bd0b38f92890; __lt__cid=49e54739-419e-4aa7-aa41-eae441d079b6; __lt__sid=9b5216e6-de3daf8d; _cls_v=954dea03-f519-4ad7-9296-69cbf34ebe9a; _cls_s=0f56f2a3-69b2-4ffb-b99d-b79cc4944484:0; jvxsync=v2SnMAmogZA6; _yoid=4ef5a982-aa14-408f-bdc8-987312eaef7d; _yosid=a40b792f-1cca-40e7-9c91-ec47a7739602; rto=default; _scid=86uSiOlrJ4Dm4EzwMvawdiKwXgqLAJdt; _scid_r=86uSiOlrJ4Dm4EzwMvawdiKwXgqLAJdt; _pin_unauth=dWlkPU9UUXpPVFpqWVRBdE5XUTVNaTAwWXpCbExUZ3lNekV0WVRGaFlqSmxOemRoT1dWaQ; _ScCbts=%5B%5D; s_tbm=true; s_cc=true; aam_uuid=44484201298313402453005188128709571477; demdex=44484201298313402453005188128709571477; at_check=true; _sctr=1%7C1763404200000; merchViewed=serpBannerhvmb010124|; OptanonConsent=isGpcEnabled=0&datestamp=Tue+Nov+18+2025+10%3A49%3A23+GMT%2B0530+(India+Standard+Time)&version=202411.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=83a26dbb-d568-43c8-9d8f-d95917f54257&interactionCount=1&isAnonUser=1&landingPath=https%3A%2F%2Fwww.marriott.com%2Fsearch%2FfindHotels.mi%3FfromToDate_submit%3D11%2F29%2F2025%26fromDate%3D11%2F21%2F2025%26toDate%3D11%2F29%2F2025%26toDateDefaultFormat%3D11%2F29%2F2025%26fromDateDefaultFormat%3D11%2F21%2F2025%26flexibleDateSearch%3Dfalse%26t-start%3D11%2F21%2F2025%26t-end%3D11%2F29%2F2025%26lengthOfStay%3D8%26childrenCountBox%3D0+Children+Per+Room%26childrenCount%3D0%26clusterCode%3Dnone%26useRewardsPoints%3Dtrue%26isAdvanceSearch%3Dfalse%26recordsPerPage%3D20%26destinationAddress.type%3DHotel+Name%26destinationAddress.latitude%3D41.7445662%26isInternalSearch%3Dtrue%26vsInitialRequest%3Dfalse%26searchType%3DInCity%26destinationAddress.stateProvinceDisplayName%3DNY%26countryName%3DUS%26destinationAddress.stateProvince%3DNY%26searchRadius%3D50%26singleSearchAutoSuggest%3DUnmatched%26destinationAddress.placeId%3DChIJx9DS7uo33YkRNff4hWhXhFo%26for-hotels-nearme%3DNear%26destinationAddress.country%3DUS%26destinationAddress.address%3D25+Old+Vineyard+Pl%2C+Hyde+Park%2C+NY+12538%2C+USA%26collapseAccordian%3Dis-hidden%26singleSearch%3Dtrue%26destinationAddress.secondaryText%3DOld+Vineyard+Place%2C+Hyde+Park%2C+NY%2C+USA%26destinationAddress.city%3DHyde+Park%26destinationAddress.mainText%3DInn+at+Bellefield+%2F+Hyde+Park%26isTransient%3Dtrue%26destinationAddress.longitude%3D-73.9302708%26initialRequest%3Dfalse%26flexibleDateSearchRateDisplay%3Dfalse%26isSearch%3Dtrue%26isRateCalendar%3Dfalse%26destinationAddress.destination%3DInn+at+Bellefield+%2F+Hyde+Park%2C+Old+Vineyard+Place%2C+Hyde+Park%2C+NY%2C+USA%26isHideFlexibleDateCalendar%3Dfalse%26roomCountBox%3D1+Room%26roomCount%3D1%26guestCountBox%3D1+Adult+Per+Room%26numAdultsPerRoom%3D1%26deviceType%3Ddesktop-web%26view%3Dlist&groups=1%3A1%2C3%3A1%2C4%3A1%2C6%3A1; s_sq=%5B%5BB%5D%5D; _abck=EDC8F4D256B9412527950F3CFCA8E7F6~0~YAAQzfUwF37BJouaAQAAhFNnlQ448XL/R20hVwRq2TAL28oUY+7BE7WWB1D15PoG/WZD4LqCVjJDDpnYs3qqpmdQ6u/+ug+snW0khle7Fx+mOvXkEwzqyLfLnf24jkoEvpv97oznze2nSIbveBLymZSOJazHAA/Sk8kTbq2N97sRbpPgIE5188jYgadBgjMn2uSK1Daen1H3ewVxnLy2pnHHnvvRBQ75i+HJx8sObppye+mkD5CEAUmFAX0aefHvFVzvukw3i3AWOuTXFOVx9XOXr2DyGvGRY1X9qheEbaT+8X5bM33Pf0YXtPpG+FY0CspBp2+Jhile4tApyptAZJD6UQHGbSS5KbJFdPmlrnw1o6ZMytlD99pg8dYvU1SgMc+mBh0yGlFU9nW0ghz6XzLoHyAl9TIPdmh7b8ky1p0ERE+j8zDnWZO79zidPUPqBv+uhDk07VXlqgaKuel84mkm14wR6NJBvgNqC+J9usfaQfiuDVSuxd8682mVd6hVIMhcejprba2acSfLKZ7dBeoT8isolK3y3iUeDKa5qAxIe0CfymqgUq5AP4nBSecXQdpgkfVpJrWQI6KdeLPfMmrgAgvcDhBlG1V6C9DGbDs6R2BO0EX6GGEeh1ds4urfRXDEO6GqVbWNIJP143CyuI4U4OTLLh9o/LavHpLZqHliyAWt3xCN8gy2ySas7ZnCuOnAen66EzHKHAeV2QNO8x6Mxw4cedL/Bizak+/P9t/BN1UbFLz8sQx8zWjYAR+rK+nRQHBFVNPoFz17pDlPvfPbwRuZlQQI26VtdKpnLwIyGg4DLHGsJ+lLYy1d4Mr0fLJoqNc/bu4YR5gTrdvEXkPPHmCzyEoKk/6uEdj+rcRr5krYl7FRcG3h82TSHUlHJuQzUEq24I/enZbtGxh0+uI7NK1iBFc=~-1~-1~1763446755~AAQAAAAE%2f%2f%2f%2f%2f+7wJLz+WsUKkpBDIdt7sPkaa3xCUBC+SjnNl8psP+9YhioAI7iScU7PuC4jlhAk40ad9CLlu1WMe2hWxSYir8cp6IXwlvS0VtQG~-1; bm_s=YAAQzfUwF3/BJouaAQAAhFNnlQSyndDdRWbS+Wv6vF5MnUQS/fAAus7X9gj/ph0I4TPaCUWRb6Vb5HSUsrXh94zKzid7AV08jQXjXQQ0Si0E1odpbelOUAmNpRclVc+/MwTfOmGI+yF5qzaaHyY1vQXbPh9ihy7Fy5+F7wNc0pBejYq7VQlsj8hsAMtcN9gjm6E3q4cJq8nalijh/k3tZTeWxJ/nYYf79fbmPe8ee3eTlbBMbmYaJ246DiBd7sodJLvFi+WYdc1FVfwdSgGnCnaN8LBz7BVczPvVFpI2Lz62NARAVwutayG3zjHqlc7oIUzfQKx/2LHxGptkU5hp4eFrFnvlmelPMdObg0ObmdD4UGoFBroMuQbCqjrzjtPrNIt1Hhefw32pgtcnKxdPN6VJBd4DW/XXgvAMAQy3aaEUiBE8C5/gTSmzhcZ4Mvc73v4BxNb2Dbtq2R//tw91jgxWf7EB/bhVPU+z1XKOpZcCAuUDSMTXCNGfgUSdntAR/N0oxXS6Z+lvJmIg6AXKzShblbEmf4ogfvfZqCXUb7reREQLBQObrRK6olWFZyAc8pmNpob+1X8=; bm_sz=57B734F5DEEE8CD99ABEC851B1AEAEC5~YAAQzfUwF4DBJouaAQAAhFNnlR3WyG2GLpLITiDxGRqyz2zgpM4+TXIj3Kb8g6HHvaPpO2m+wMLtGNBshp3H3Z/Fc2NBStLdxsD9Nud7NoVKn6plsETkm+24KgtNl89cKf9/zpFrIsULVLE+kiAPNDTJDxJoFmgpxJo93KDXV+RrdEZqif4+HoFnCs2WSQHcCn8RK3ZbOna3mObSYa/V8PG1I+I1ojPtK5AXLYh8g2EfFaG2cgIUcPlfME/o1QEMYgOvuQSDIdXjhYPH1AFgGhtXQOWTiYkVePLWK2djgYRF+XswG9kT3feishxd5cc90XzhC4cMXNQE/jUOHXrWRQHlKJTwNOkAH8Tocq0Ei/b6859dpidjtfXN3D8GNBJF34fBdxTfWcWgfyh7d9+Uke0Jr41i2BRGB/Nsrgx39wtD1g==~4273974~3162438; _ga_1LXTBF5X2V=GS2.1.s1763443156$o1$g1$t1763443166$j50$l0$h0; Ddup=52a4251d-10fe-4a53-afc3-f654e19b3036; mbox=session#29f430a08060429b8290c963da309c25#1763445028|PC#29f430a08060429b8290c963da309c25.41_0#1826687962; _abck=B0CF753F61AEE99653453E75B15044B6~-1~YAAQDWnDF+VxuzCaAQAAiUkgTg4HY2kvIY65Sg06KnacmEKvZ4sDCu8e+YtU89aDN4Idp4BXeKOMD2rG7xtpiPy/aqQP1XUTS4vgXm8QaJ5miU7JWeXCheuD7AMD8qbbInO5+z6xbIcaCQQbFdODNDJIAQV2f+8nYDDayItf/Dv0jZ52kTSitCr9vQg0gSU+UnNQ4wsAizYHZ0EoDqJxfjomTS8kaP7+WC7C6yC5wag6/6K1f41vFuaSXcu+xxkUQSMnllDOCIHQX6WJXLsSXgGg/ESRJLemoy/F+B50rUhiPru+jkfMqfHenZ7Bpff87/txX7JeAZ880bH2hYwnFueZOAlUnVn80JwQM1gHdyx0gBXipfSU0myr2v3z9XGzdi/7naEYiXn59g6/W3k905BxZvyCAO3OXXR1b7KQYlQfO9YozwMbps/X6B0nEOUYcqsjGtdFP+xt0jIra/hA/OOT5txJAwaauTUyjnSVds6o345xxPVai316p15KvB+yF/P5SMeQcloQaa2cySQEKQ17FW9FvRUOFypobV2Ea8rDGKx5uYh7+x7thiBK1scOqkMq9e8WJPrEElXt0+KRa8CWeyy8pkJiXOvcDGUlW6ZVbJpEHjbVf1SBr6i1+v+L0B5zBiFuYDP2BBVs8/ZpsrrVUZXoI/Hpot0okAw8azAc1gx83n09n0a0P2d1j2ocBPovYz5JXfImbO+uVsTnsxaJ08JKalhO1EvYwk+UaPMsOqZjWnDxFv+UdPUItywfKdB11Xr0OMWHuNZj7L+4xgRb++avK6/9AAhjmDriwPXmRFKPLEncz3FB9317BFk6rhgdA8hteWnnXJZUbLHOG+NXDlXBuMS3gjUUS6DjjsWDQPIUj9orbTgzDPQ6~0~-1~1762240158~AAQAAAAE%2f%2f%2f%2f%2f0Q3cPNrdq6pUzYZ044KE6G1eLCJ+QG2sg0L78olU8TQ1ANehU9PnYH+0jFh%2fO6I0%2f5+Irj%2frJjvgtq%2fQ1T6z7A5ZWEP8K5k0V+X~-1; bm_s=YAAQv/UwF7iJHIWaAQAAAc/ekQS0vRteFOum+9maCvcZYCqq5imlX8bxVs+43WL8pBUzl+qcnCh2UmDmXN31nDhYP4ra8Y9Ipw3ryKuDlr/HnJW3s2lt8bDz6XewKBqVB8GL63sKcEaLewIuQktubUiWyFSiWsp2gSnraRKNHmJgOSfN3nTHsZ0v/YLCXpefxPJKwR8lCu+jr0+hPlrpriqvnarjD+AHzwUepBHaXC/gRYhYKkAurz80NUBHjsALDly84TxgxCpHbICIGdEy8PPqQy1AJs6OLyhKcRgxg83KBhYxYBsEhkIZEOon+wM2hMS2C1YlJDGNkZhz6bimuTyL6xKH4glkBt3Ditzpc7gS56TzBmGVTYVbpaoYW3avhxR9bZ0Urf1b/zu4eH/YRhIZymcl09mH1lETUafpnQG+8ausRw==; JVMID=mi-interceptor-app-blue; MI_Visitor=3AF17CDC-A9AC-52B9-96EE-E90A3EF5710E'
# # }
#
# response = requests.request("POST", url, headers=headers, data=payload)
#
# print(response.text)

