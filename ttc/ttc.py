#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
import time
from datetime import datetime
import base64
import re
import uuid
import random
from bs4 import BeautifulSoup

# --- ANSI Color Codes for Terminal Output ---
_Reset_ = '\033[0m'
_Bold_ = '\033[1m'

# --- Global Variables ---
CURRENT_COLOR_SCHEME = []
SETTINGS_FILE = "settings.json"
ACCOUNT_FILE = "account.txt"  # For TTC accounts
COOKIE_FILE = "cookie.txt"    # For FB cookies
REACTION_TYPES = {
    "LIKE": "1635855486666999", "LOVE": "1678524932434102", "CARE": "613557422527858",
    "HAHA": "115940658764963", "WOW": "478547315650144", "SAD": "908563459236466", "ANGRY": "444813342392137"
}

# --- Custom Exception for Stopping Tool ---
class StopToolException(Exception):
    pass

# ==============================================================================
# SECTION: TUONGTACCHEO API INTERACTION
# ==============================================================================

def login_ttc(username, password):
    login_url = "https://tuongtaccheo.com/login.php"
    login_data = {"username": username, "password": password, "submit": "ĐĂNG NHẬP"}
    session = requests.Session()
    try:
        response = session.post(login_url, data=login_data)
        response.raise_for_status()
        if "success" in response.text.lower():
            return session.cookies.get_dict(), username, password
    except requests.RequestException as e:
        print(f"{CURRENT_COLOR_SCHEME[0]}Lỗi khi đăng nhập TTC: {e}{_Reset_}")
    return None, None, None

def get_ttc_token(cookies):
    try:
        response = requests.get("https://tuongtaccheo.com/api/", cookies=cookies)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        token_input = soup.find('input', {'name': 'ttc_access_token'})
        return token_input.get('value') if token_input else None
    except requests.RequestException as e:
        print(f"{CURRENT_COLOR_SCHEME[0]}Lỗi khi lấy TTC token: {e}{_Reset_}")
    return None

def get_account_info(token):
    try:
        response = requests.post("https://tuongtaccheo.com/logintoken.php", data={"access_token": token})
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, json.JSONDecodeError):
        return {}

def _fetch_jobs_from_endpoint(url, cookies):
    headers = {"X-Requested-With": "XMLHttpRequest"}
    try:
        response = requests.get(url, headers=headers, cookies=cookies)
        response.raise_for_status()
        if response.text in ["0", "[]", ""]:
            return []
        jobs = response.json()
        # Filter out invalid jobs (non-dictionaries)
        valid_jobs = [job for job in jobs if isinstance(job, dict)]
        return valid_jobs
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"{CURRENT_COLOR_SCHEME[0]}Lỗi khi lấy jobs từ {url}: {e}{_Reset_}")
        return []

def get_vip_reaction_jobs(cookies):
    jobs = _fetch_jobs_from_endpoint("https://tuongtaccheo.com/kiemtien/camxucvipre/getpost.php", cookies)
    if jobs:
        return jobs
    return _fetch_jobs_from_endpoint("https://tuongtaccheo.com/kiemtien/camxucvipcheo/getpost.php", cookies)

def get_follow_jobs(cookies):
    return _fetch_jobs_from_endpoint("https://tuongtaccheo.com/kiemtien/subcheo/getpost.php", cookies)

def get_share_jobs(cookies):
    return _fetch_jobs_from_endpoint("https://tuongtaccheo.com/kiemtien/sharecheo/getpost.php", cookies)

def _claim_ttc_reward(claim_url, cookies, data):
    headers = {
        "accept": "*/*", "content-type": "application/x-www-form-urlencoded",
        "x-requested-with": "XMLHttpRequest", "origin": "https://tuongtaccheo.com",
        "referer": claim_url.replace("nhantien.php", ""),
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }
    try:
        response = requests.post(claim_url, headers=headers, cookies=cookies, data=data, timeout=15)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, json.JSONDecodeError):
        return None

def claim_reaction_reward(cookies, post_id, reaction_type):
    return _claim_ttc_reward("https://tuongtaccheo.com/kiemtien/camxucvipcheo/nhantien.php", cookies, {"id": post_id, "loaicx": reaction_type})

def claim_follow_reward(cookies, target_id):
    return _claim_ttc_reward("https://tuongtaccheo.com/kiemtien/subcheo/nhantien.php", cookies, {"id": target_id})

def claim_share_reward(cookies, post_id):
    return _claim_ttc_reward("https://tuongtaccheo.com/kiemtien/sharecheo/nhantien.php", cookies, {"id": post_id})

# ==============================================================================
# SECTION: FACEBOOK INTERACTION
# ==============================================================================

class FacebookAccount:
    def __init__(self, cookie_str):
        self.cookie = cookie_str
        self.name = None
        self.uid = None
        self.fb_dtsg = None
        self.is_valid = self._validate_and_fetch_details()

    def _validate_and_fetch_details(self):
        try:
            self.uid = re.search(r"c_user=(\d+)", self.cookie).group(1)
            headers = {
                'authority': 'www.facebook.com',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                'cookie': self.cookie,
                'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'none',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            }
            homepage_response = requests.get('https://www.facebook.com/', headers=headers, timeout=20)
            homepage_response.raise_for_status()
            homepage_text = homepage_response.text

            if 'login.php' in str(homepage_response.url) or "Đăng nhập Facebook" in homepage_text:
                return False

            fb_dtsg_match = re.search(r'"DTSGInitialData",\[\],{"token":"(.*?)"', homepage_text) or \
                            re.search(r'name="fb_dtsg" value="(.*?)"', homepage_text) or \
                            re.search(r'"async_get_token":"(.*?)"', homepage_text)
            if not fb_dtsg_match:
                return False
            self.fb_dtsg = fb_dtsg_match.group(1)

            name_match = re.search(r'"NAME":"(.*?)"', homepage_text)
            if name_match:
                self.name = name_match.group(1).encode('latin1').decode('unicode-escape')
            else:
                soup = BeautifulSoup(homepage_text, 'html.parser')
                title_tag = soup.find('title')
                if title_tag and title_tag.string not in ["Facebook", "Log in to Facebook"]:
                    self.name = title_tag.string
                else:
                    return False
            return True
        except (requests.RequestException, AttributeError):
            return False

class FacebookInteractor:
    def __init__(self, fb_account: FacebookAccount):
        self.account = fb_account
        self.base_headers = {
            "accept": "*/*", "accept-language": "en-US,en;q=0.9", "content-type": "application/x-www-form-urlencoded",
            "cookie": self.account.cookie, "origin": "https://www.facebook.com", "priority": "u=1, i",
            "sec-ch-ua": '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"', "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"', "sec-fetch-dest": "empty", "sec-fetch-mode": "cors", "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "x-fb-lsd": "SaEkSywP_uH8A3cpczP2RG"
        }

    def _handle_response(self, response, job_type):
        if response.text.startswith("for (;;);"):
            try:
                error_data = json.loads(response.text[9:])
                if error_data.get("error") == 1357001:
                    print(f"\n{CURRENT_COLOR_SCHEME[0]}{_Bold_}LỖI: Tài khoản {self.account.name} đã bị LOGOUT. Dừng tool.{_Reset_}")
                    self.account.is_valid = False
                    raise StopToolException("Account logged out")
                if "errors" in error_data and isinstance(error_data["errors"], list):
                    for error in error_data["errors"]:
                        if error.get("api_error_code") == 10 and "Tài khoản của bạn bị hạn chế" in error.get("summary", ""):
                            print(f"\n{CURRENT_COLOR_SCHEME[0]}{_Bold_}LỖI: Tài khoản {self.account.name} bị hạn chế khi làm job {job_type.upper()}.{_Reset_}")
                            raise StopToolException(f"{job_type} blocked")
            except json.JSONDecodeError:
                pass
        
        try:
            data = response.json()
            if "errors" in data and isinstance(data["errors"], list):
                for error in data["errors"]:
                    if error.get("api_error_code") == 10 and "Tài khoản của bạn bị hạn chế" in error.get("summary", ""):
                        print(f"\n{CURRENT_COLOR_SCHEME[0]}{_Bold_}LỖI: Tài khoản {self.account.name} bị hạn chế khi làm job {job_type.upper()}.{_Reset_}")
                        raise StopToolException(f"{job_type} blocked")
        except json.JSONDecodeError:
            pass
        
        if not response.ok:
            return False, None
        
        try:
            return True, response.json()
        except json.JSONDecodeError:
            return True, None

    def react_to_post(self, post_id, reaction_name):
        reaction_id = REACTION_TYPES.get(reaction_name.upper())
        if not reaction_id:
            return False
        
        variables = {
            "input": {
                "feedback_id": base64.b64encode(f"feedback:{post_id}".encode()).decode(),
                "feedback_reaction_id": reaction_id,
                "feedback_source": "NEWS_FEED",
                "actor_id": self.account.uid,
                "client_mutation_id": "1"
            }
        }
        data = {
            "av": self.account.uid,
            "__user": self.account.uid,
            "fb_dtsg": self.account.fb_dtsg,
            "fb_api_req_friendly_name": "CometUFIFeedbackReactMutation",
            "variables": json.dumps(variables),
            "doc_id": "9518016021660044"
        }
        
        try:
            response = requests.post("https://www.facebook.com/api/graphql/", headers=self.base_headers, data=data, timeout=15)
            is_ok, resp_json = self._handle_response(response, "reaction")
            if not is_ok:
                return False
            return resp_json is None or 'errors' not in resp_json
        except StopToolException:
            raise
        except requests.RequestException:
            return False

    def follow_user(self, target_id):
        if not target_id or not str(target_id).isdigit():
            print(f"{CURRENT_COLOR_SCHEME[0]}Lỗi: target_id không hợp lệ: {target_id}{_Reset_}")
            return False
        
        target_id = str(target_id)
        timestamp = int(time.time())
        session_id = str(uuid.uuid4())
        headers = {
            'accept': '*/*', 'accept-language': 'en-US,en;q=0.9', 'content-type': 'application/x-www-form-urlencoded',
            'cookie': self.account.cookie, 'origin': 'https://www.facebook.com', 'priority': 'u=1, i',
            'referer': f'https://www.facebook.com/profile.php?id={target_id}',
            'sec-ch-ua': '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"', 'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"', 'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'x-fb-lsd': 'luH3GY4liovr25K3-Kmxnz'
        }
        try:
            friend_headers = headers.copy()
            friend_headers.update({'x-fb-friendly-name': 'FriendingCometFriendRequestSendMutation'})
            friend_variables = {
                "input": {
                    "attribution_id_v2": f"ProfileCometContextualProfileRoot.react,comet.profile.contextual_profile,unexpected,{timestamp}710,151967,,,",
                    "friend_requestee_ids": [target_id],
                    "friending_channel": "PROFILE_BUTTON",
                    "warn_ack_for_ids": [],
                    "actor_id": self.account.uid,
                    "client_mutation_id": "7"
                },
                "scale": 1
            }
            friend_data = {
                "av": self.account.uid, "__user": self.account.uid, "__a": "1",
                "fb_dtsg": self.account.fb_dtsg, "variables": json.dumps(friend_variables),
                "doc_id": "9757269034400464"
            }
            
            friend_response = requests.post("https://www.facebook.com/api/graphql/", headers=friend_headers, data=friend_data)
            is_ok, friend_json = self._handle_response(friend_response, "follow")
            if is_ok and friend_json and not friend_json.get('errors'):
                return True

            follow_headers = headers.copy()
            follow_headers.update({'x-fb-friendly-name': 'CometUserFollowMutation'})
            follow_variables = {
                "input": {
                    "attribution_id_v2": f"ProfileCometTimelineListViewRoot.react,comet.profile.timeline.list,unexpected,{timestamp}313,397001,250100865708545,,",
                    "is_tracking_encrypted": False,
                    "subscribe_location": "PROFILE",
                    "subscribee_id": target_id,
                    "tracking": None,
                    "actor_id": self.account.uid,
                    "client_mutation_id": "11",
                    "session_id": session_id
                },
                "scale": 1
            }
            follow_data = {
                "av": self.account.uid, "__user": self.account.uid, "__a": "1",
                "fb_dtsg": self.account.fb_dtsg, "variables": json.dumps(follow_variables),
                "doc_id": "9831187040342850"
            }

            follow_response = requests.post("https://www.facebook.com/api/graphql/", headers=follow_headers, data=follow_data)
            is_ok, follow_json = self._handle_response(follow_response, "follow")
            return is_ok and follow_json and not follow_json.get('errors')
        
        except StopToolException:
            raise
        except Exception as e:
            print(f"{CURRENT_COLOR_SCHEME[0]}Lỗi khi thực hiện follow: {e}{_Reset_}")
            return False

    def share_post(self, post_id):
        headers = self.base_headers.copy()
        headers.update({'x-fb-friendly-name': 'ComposerStoryCreateMutation'})
        variables = {
            "input": {
                "composer_entry_point": "share_modal",
                "composer_source_surface": "feed_story",
                "composer_type": "share",
                "idempotence_token": f"{str(uuid.uuid4())}_FEED",
                "source": "WWW",
                "attachments": [{"link": {"share_scrape_data": json.dumps({"share_type": 22, "share_params": [str(post_id)]})}}],
                "audience": {"privacy": {"base_state": "EVERYONE"}},
                "actor_id": self.account.uid,
                "client_mutation_id": "7"
            }
        }
        data = {
            "av": self.account.uid, "__user": self.account.uid, "fb_dtsg": self.account.fb_dtsg,
            "variables": json.dumps(variables), "doc_id": "9502543119760740"
        }
        
        try:
            response = requests.post("https://www.facebook.com/api/graphql/", headers=headers, data=data, timeout=15)
            is_ok, resp_json = self._handle_response(response, "share")
            if not is_ok:
                return False
            return resp_json and resp_json.get('data', {}).get('story_create') is not None
        except StopToolException:
            raise
        except requests.RequestException:
            return False

# ==============================================================================
# SECTION: JOB PROCESSING & UTILITIES
# ==============================================================================

def extract_xu_from_message(message):
    if not isinstance(message, str):
        return "???"
    return re.search(r'cộng (\d+)', message).group(1) if re.search(r'cộng (\d+)', message) else "???"

def countdown_display(seconds):
    for i in range(int(seconds), 0, -1):
        print(f"{CURRENT_COLOR_SCHEME[2]}Chờ {i}s...{_Reset_}", end='\r')
        time.sleep(1)
    print(" " * 20, end='\r')

def process_job(job_type, job, ttc_cookies, interactor):
    if not isinstance(job, dict):
        print(f"{CURRENT_COLOR_SCHEME[0]}Cảnh báo: Dữ liệu job không hợp lệ cho {job_type.upper()}: {job}{_Reset_}")
        return 'ACTION_FAILED'

    now = datetime.now().strftime('%H:%M:%S')
    fb_name = interactor.account.name
    job_id_ttc = job.get('idpost') or job.get('id')
    
    fb_action_succeeded = False
    action_details = ""
    claim_function = None
    claim_args = []

    if job_type == "reaction":
        post_id_fb = job.get('idfb') or job_id_ttc
        reaction_type = job.get('loaicx')
        if not post_id_fb or not reaction_type:
            return 'ACTION_FAILED'
        action_details = f"REACTION:{reaction_type.upper()}|{post_id_fb}"
        fb_action_succeeded = interactor.react_to_post(post_id_fb, reaction_type)
        claim_function = claim_reaction_reward
        claim_args = [ttc_cookies, job_id_ttc, reaction_type]
    
    elif job_type == "follow":
        target_id_fb = job.get('idpost') or job.get('id')
        if not target_id_fb or not str(target_id_fb).isdigit():
            print(f"{CURRENT_COLOR_SCHEME[0]}Lỗi: ID người dùng không hợp lệ: {target_id_fb}{_Reset_}")
            return 'ACTION_FAILED'
        action_details = f"FOLLOW|{target_id_fb}"
        fb_action_succeeded = interactor.follow_user(target_id_fb)
        claim_function = claim_follow_reward
        claim_args = [ttc_cookies, target_id_fb]
        
    elif job_type == "share":
        post_id_fb = job.get('link', '').split('/posts/')[1].split('?')[0].strip('/') if '/posts/' in job.get('link','') else job_id_ttc
        action_details = f"SHARE|{post_id_fb}"
        fb_action_succeeded = interactor.share_post(post_id_fb)
        claim_function = claim_share_reward
        claim_args = [ttc_cookies, job_id_ttc]

    if not interactor.account.is_valid:
        return 'LOGGED_OUT'

    if fb_action_succeeded:
        if job_type == "share":
            time.sleep(2)
        else:
            time.sleep(random.uniform(2, 4))
        result = claim_function(*claim_args)

        if result and 'mess' in result:
            xu = extract_xu_from_message(result.get('mess', ''))
            print(f"{CURRENT_COLOR_SCHEME[1]}[{now}] {fb_name}|{action_details}|Thành công: +{xu} xu{_Reset_}")
            delay = random.uniform(*settings['DELAY_BETWEEN_JOBS'])
            print(f"{CURRENT_COLOR_SCHEME[2]}Chờ {delay:.2f}s trước khi chạy job tiếp theo...{_Reset_}")
            return 'SUCCESS'
        else:
            print(f"{CURRENT_COLOR_SCHEME[2]}[{now}] {fb_name}|{action_details}|Nhận thưởng thất bại.{_Reset_}")
            return 'ACTION_FAILED'
    
    else:
        print(f"{CURRENT_COLOR_SCHEME[0]}[{now}] {fb_name}|{action_details}|Hành động FB thất bại.{_Reset_}")
        return 'ACTION_FAILED'

# ==============================================================================
# SECTION: UI & MAIN EXECUTION
# ==============================================================================
def get_random_color_scheme():
    """Tạo bộ màu ngẫu nhiên hài hòa"""
    color_schemes = [
        ['\033[38;5;33m', '\033[38;5;39m', '\033[38;5;45m', '\033[38;5;51m'],
        ['\033[38;5;196m', '\033[38;5;202m', '\033[38;5;208m', '\033[38;5;214m'],
        ['\033[38;5;129m', '\033[38;5;135m', '\033[38;5;141m', '\033[38;5;147m'],
        ['\033[38;5;22m', '\033[38;5;28m', '\033[38;5;34m', '\033[38;5;40m'],
        ['\033[38;5;124m', '\033[38;5;160m', '\033[38;5;196m', '\033[38;5;202m'],
        ['\033[38;5;46m', '\033[38;5;82m', '\033[38;5;118m', '\033[38;5;154m'],
        ['\033[38;5;54m', '\033[38;5;90m', '\033[38;5;126m', '\033[38;5;162m'],
        ['\033[38;5;21m', '\033[38;5;27m', '\033[38;5;33m', '\033[38;5;39m'],
        ['\033[38;5;166m', '\033[38;5;172m', '\033[38;5;178m', '\033[38;5;184m'],
        ['\033[38;5;30m', '\033[38;5;36m', '\033[38;5;42m', '\033[38;5;48m']
    ]
    return random.choice(color_schemes)
def print_banner():
    global CURRENT_COLOR_SCHEME
    os.system('cls' if os.name == 'nt' else 'clear')
    color_schemes = [['\033[38;5;196m', '\033[38;5;46m', '\033[38;5;226m', '\033[38;5;21m'], ['\033[38;5;129m', '\033[38;5;82m', '\033[38;5;214m', '\033[38;5;51m']]
    CURRENT_COLOR_SCHEME = get_random_color_scheme()
    colors = CURRENT_COLOR_SCHEME
    print(f"""
{colors[3]}██╗  ██╗      {colors[2]}████████╗ ██████╗  ██████╗ ██╗     
{colors[3]}██║  ██║      {colors[2]}╚══██╔══╝██╔═══██╗██╔═══██╗██║     
{colors[2]}███████║█████╗{colors[1]}   ██║   ██║   ██║██║   ██║██║     
{colors[1]}██╔══██║╚════╝{colors[0]}   ██║   ██║   ██║██║   ██║██║     
{colors[1]}██║  ██║      {colors[0]}   ██║   ╚██████╔╝╚██████╔╝███████╗
{colors[0]}╚═╝  ╚═╝         ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝{_Reset_}
""")
    print(f"{colors[2]}                Copyright © H-Tool 2025 | Version 5.2 (Final){_Reset_}\n")

def print_section(title):
    print(f"\n{_Bold_}{CURRENT_COLOR_SCHEME[3]}>> {title.upper()} <<{_Reset_}")

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return None

def save_settings(s):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(s, f, indent=4)

def setup_settings():
    print_section("Thiết Lập Cấu Hình Chạy Tool")
    saved_settings = load_settings()
    if saved_settings:
        use_saved = input(f"{CURRENT_COLOR_SCHEME[2]}Tìm thấy cấu hình đã lưu, bạn có muốn sử dụng không? (y/n): {_Reset_}").lower()
        if use_saved == 'y':
            print(f"{CURRENT_COLOR_SCHEME[1]}Đã áp dụng cấu hình đã lưu.{_Reset_}")
            return saved_settings

    s = {}
    try:
        s['DELAY_BETWEEN_JOBS'] = (
            int(input(f"- Delay tối thiểu giữa các job (giây): ") or 5),
            int(input(f"- Delay tối đa giữa các job (giây): ") or 10)
        )
        s['JOBS_BEFORE_BREAK'] = int(input(f"- Sau bao nhiêu job thì nghỉ chống block: ") or 20)
        s['BREAK_TIME'] = int(input(f"- Thời gian nghỉ chống block (giây): ") or 300)
        s['JOBS_BEFORE_SWITCH'] = int(input(f"- Bao nhiêu job thì đổi tài khoản Facebook: ") or 15)
        
        save_choice = input(f"\n{CURRENT_COLOR_SCHEME[2]}Bạn có muốn lưu cấu hình này cho lần sau? (y/n): {_Reset_}").lower()
        if save_choice == 'y':
            save_settings(s)
            print(f"{CURRENT_COLOR_SCHEME[1]}Đã lưu cấu hình.{_Reset_}")
    except ValueError:
        print(f"{CURRENT_COLOR_SCHEME[0]}Nhập không hợp lệ, thoát.{_Reset_}")
        exit()
    return s

def load_ttc_accounts():
    accounts = []
    if os.path.exists(ACCOUNT_FILE):
        try:
            with open(ACCOUNT_FILE, 'r') as f:
                for line in f:
                    if line.strip():
                        parts = line.strip().split('|')
                        if len(parts) == 2:
                            username, password = parts
                            accounts.append((username, password))
        except Exception as e:
            print(f"{CURRENT_COLOR_SCHEME[0]}Lỗi khi đọc {ACCOUNT_FILE}: {e}{_Reset_}")
    return accounts

def save_ttc_account(username, password):
    with open(ACCOUNT_FILE, 'a') as f:
        f.write(f"{username}|{password}\n")

def select_ttc_accounts(saved_accounts):
    print_section("Chọn Tài Khoản TuongTacCheo")
    if not saved_accounts:
        return []
    for i, (username, _) in enumerate(saved_accounts):
        print(f"{i+1}. {username}")
    print("all. Chọn tất cả tài khoản trên.")
    
    choice = input(f"{CURRENT_COLOR_SCHEME[2]}Nhập lựa chọn (ví dụ: 1+2 hoặc all): {_Reset_}").lower()
    if choice == 'all':
        return saved_accounts
    try:
        selected_indices = [int(x.strip()) - 1 for x in choice.split('+')]
        return [saved_accounts[i] for i in selected_indices if 0 <= i < len(saved_accounts)]
    except (ValueError, IndexError):
        print(f"{CURRENT_COLOR_SCHEME[0]}Lựa chọn không hợp lệ, sẽ không chạy tài khoản nào.{_Reset_}")
        return []

def select_ttc_account_source():
    print_section("Chọn Nguồn Tài Khoản TuongTacCheo")
    print(f"1. Nhập tài khoản TTC mới.")
    print(f"2. Sử dụng tài khoản TTC đã lưu trong `{ACCOUNT_FILE}`.")
    choice = input(f"{CURRENT_COLOR_SCHEME[2]}Lựa chọn của bạn (1-2): {_Reset_}")
    return choice

def get_fb_cookies_menu():
    print_section("Chọn Nguồn Cung Cấp Cookie Facebook")
    print(f"1. Nhập cookie trực tiếp vào console.")
    print(f"2. Nhập cookie từ file (ví dụ: `new_cookies.txt`).")
    print(f"3. Sử dụng cookie đã lưu trong `{COOKIE_FILE}`.")
    choice = input(f"{CURRENT_COLOR_SCHEME[2]}Lựa chọn của bạn (1-3): {_Reset_}")
    
    cookies = []
    if choice == '1':
        print(f"{CURRENT_COLOR_SCHEME[2]}Nhập các cookie, mỗi cookie một dòng. Nhấn Enter trên dòng trống để kết thúc.{_Reset_}")
        while True:
            line = input()
            if not line: break
            cookies.append(line.strip())
    elif choice == '2':
        filename = input(f"{CURRENT_COLOR_SCHEME[2]}Nhập tên file chứa cookie: {_Reset_}")
        try:
            with open(filename, 'r') as f:
                cookies = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"{CURRENT_COLOR_SCHEME[0]}File '{filename}' không tồn tại.{_Reset_}")
            return []
    elif choice == '3':
        try:
            with open(COOKIE_FILE, 'r') as f:
                cookies = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"{CURRENT_COLOR_SCHEME[0]}File `{COOKIE_FILE}` không tồn tại.{_Reset_}")
            return []
    else:
        print(f"{CURRENT_COLOR_SCHEME[0]}Lựa chọn không hợp lệ.{_Reset_}")
        return []

    if cookies:
        with open(COOKIE_FILE, 'w') as f:
            f.write('\n'.join(cookies))
        print(f"{CURRENT_COLOR_SCHEME[1]}Đã lấy và lưu {len(cookies)} cookie vào {COOKIE_FILE}{_Reset_}")
    return cookies

def select_accounts_to_run(valid_accounts):
    print_section("Chọn Tài Khoản Facebook Để Chạy")
    if not valid_accounts:
        return []
    for i, acc in enumerate(valid_accounts):
        print(f"{i+1}. {acc.name} (UID: {acc.uid})")
    print("all. Chạy tất cả các tài khoản trên.")
    
    choice = input(f"{CURRENT_COLOR_SCHEME[2]}Nhập lựa chọn (ví dụ: 1+3 hoặc all): {_Reset_}").lower()
    if choice == 'all':
        return valid_accounts
    try:
        selected_indices = [int(x.strip()) - 1 for x in choice.split('+')]
        return [valid_accounts[i] for i in selected_indices if 0 <= i < len(valid_accounts)]
    except (ValueError, IndexError):
        print(f"{CURRENT_COLOR_SCHEME[0]}Lựa chọn không hợp lệ, sẽ không chạy tài khoản nào.{_Reset_}")
        return []

def select_job_types():
    print_section("Chọn Loại Job Muốn Thực Hiện")
    print("1. Reaction (VIP)\n2. Follow\n3. Share")
    print("Nhập các số cách nhau bằng '+' (ví dụ: 1+2 để chạy Reaction và Follow, để trống để chạy tất cả)")
    choice = input(f"{CURRENT_COLOR_SCHEME[2]}Lựa chọn của bạn: {_Reset_}").strip()
    
    job_map = {"1": "reaction", "2": "follow", "3": "share"}
    selected = []
    if choice:
        for c in choice.split('+'):
            if c in job_map:
                selected.append(job_map[c])
    return selected if selected else ["reaction", "follow", "share"]

def main():
    print_banner()
    
    account_source = select_ttc_account_source()
    ttc_accounts_to_use = []

    if account_source == '1':
        username = input(f"{CURRENT_COLOR_SCHEME[2]}Nhập username TuongTacCheo: {_Reset_}")
        password = input(f"{CURRENT_COLOR_SCHEME[2]}Nhập password TuongTacCheo: {_Reset_}")
        ttc_cookies, _, _ = login_ttc(username, password)
        if ttc_cookies:
            save_ttc_account(username, password)
            print(f"{CURRENT_COLOR_SCHEME[1]}Đã lưu tài khoản TTC {username} vào {ACCOUNT_FILE}{_Reset_}")
            ttc_accounts_to_use = [(username, password, ttc_cookies)]
        else:
            print(f"{CURRENT_COLOR_SCHEME[0]}Đăng nhập TTC thất bại. Thoát tool.{_Reset_}")
            return
    
    elif account_source == '2':
        saved_accounts = load_ttc_accounts()
        if not saved_accounts:
            print(f"{CURRENT_COLOR_SCHEME[0]}Không tìm thấy tài khoản TTC đã lưu trong {ACCOUNT_FILE}. Thoát tool.{_Reset_}")
            return
        
        selected_accounts = select_ttc_accounts(saved_accounts)
        if not selected_accounts:
            print(f"{CURRENT_COLOR_SCHEME[0]}Không có tài khoản TTC nào được chọn. Thoát tool.{_Reset_}")
            return
        
        print_section("Đang kiểm tra các tài khoản TTC đã chọn")
        for username, password in selected_accounts:
            print(f"Đang kiểm tra tài khoản {username}...", end='')
            ttc_cookies, _, _ = login_ttc(username, password)
            if ttc_cookies:
                ttc_accounts_to_use.append((username, password, ttc_cookies))
                print(f"\r{CURRENT_COLOR_SCHEME[1]} -> Tài khoản {username}: Đăng nhập thành công{_Reset_}")
            else:
                print(f"\r{CURRENT_COLOR_SCHEME[0]} -> Tài khoản {username}: Đăng nhập thất bại{_Reset_}")

    if not ttc_accounts_to_use:
        print(f"{CURRENT_COLOR_SCHEME[0]}Không có tài khoản TTC nào hợp lệ để chạy. Thoát tool.{_Reset_}")
        return

    raw_cookies = get_fb_cookies_menu()
    if not raw_cookies:
        print(f"{CURRENT_COLOR_SCHEME[0]}Không có cookie Facebook nào được cung cấp. Thoát tool.{_Reset_}")
        return

    print_section("Đang kiểm tra các tài khoản Facebook")
    all_fb_accounts = []
    for i, cookie_str in enumerate(raw_cookies):
        print(f"Đang kiểm tra cookie #{i+1}...", end='')
        fb_account = FacebookAccount(cookie_str)
        if fb_account.is_valid:
            all_fb_accounts.append(fb_account)
            print(f"\r{CURRENT_COLOR_SCHEME[1]} -> Cookie #{i+1}: Hợp lệ - {fb_account.name}{_Reset_}")
        else:
            print(f"\r{CURRENT_COLOR_SCHEME[0]} -> Cookie #{i+1}: KHÔNG HỢP LỆ (Die hoặc Logout){_Reset_}")

    if not all_fb_accounts:
        print(f"{CURRENT_COLOR_SCHEME[0]}Không có tài khoản Facebook nào hợp lệ để chạy.{_Reset_}")
        return

    accounts_to_run = select_accounts_to_run(all_fb_accounts)
    if not accounts_to_run:
        print(f"{CURRENT_COLOR_SCHEME[0]}Không có tài khoản Facebook nào được chọn để chạy. Thoát tool.{_Reset_}")
        return
    print(f"{CURRENT_COLOR_SCHEME[1]}Sẵn sàng chạy với {len(accounts_to_run)} tài khoản Facebook.{_Reset_}")

    global settings
    settings = setup_settings()
    selected_job_types = select_job_types()
    print(f"{CURRENT_COLOR_SCHEME[1]}Các loại job sẽ chạy: {', '.join(s.upper() for s in selected_job_types)}{_Reset_}")

    print_section("Bắt đầu thực hiện Job")
    counters = {'per_account': {acc.uid: 0 for acc in accounts_to_run}, 'since_break': 0}
    current_account_index = 0
    blocked_jobs_per_account = {acc.uid: set() for acc in accounts_to_run}
    ttc_account_index = 0

    try:
        while accounts_to_run and ttc_accounts_to_use:
            if ttc_account_index >= len(ttc_accounts_to_use):
                ttc_account_index = 0
            ttc_username, _, ttc_cookies = ttc_accounts_to_use[ttc_account_index]
            print(f"\n{_Bold_}{CURRENT_COLOR_SCHEME[3]}Đang dùng TTC: {ttc_username}{_Reset_}")

            if current_account_index >= len(accounts_to_run):
                current_account_index = 0
            
            current_account = accounts_to_run[current_account_index]
            blocked_jobs = blocked_jobs_per_account[current_account.uid]
            available_jobs = [jt for jt in selected_job_types if jt not in blocked_jobs]
            
            if not available_jobs:
                print(f"\n{CURRENT_COLOR_SCHEME[0]}Tài khoản {current_account.name} đã bị khóa tất cả các loại job. Chuyển tài khoản...{_Reset_}")
                accounts_to_run.pop(current_account_index)
                current_account_index -= 1
                continue

            if counters['per_account'].get(current_account.uid, 0) >= settings['JOBS_BEFORE_SWITCH']:
                print(f"\n{CURRENT_COLOR_SCHEME[3]}Tài khoản {current_account.name} đã đạt giới hạn. Chuyển...{_Reset_}")
                counters['per_account'][current_account.uid] = 0
                # Do NOT clear blocked_jobs to prevent retrying blocked job types
                current_account_index = (current_account_index + 1) % len(accounts_to_run)
                continue

            print(f"\n{_Bold_}{CURRENT_COLOR_SCHEME[3]}Đang dùng FB: {current_account.name} (Jobs: {counters['per_account'].get(current_account.uid, 0)}/{settings['JOBS_BEFORE_SWITCH']}){_Reset_}")
            interactor = FacebookInteractor(current_account)
            
            job_found_in_cycle = False
            jobs_to_process = available_jobs.copy()
            random.shuffle(jobs_to_process)

            while jobs_to_process:
                job_type = jobs_to_process[0]
                fetcher = globals()[f"get_{'vip_' if job_type == 'reaction' else ''}{job_type}_jobs"]
                jobs = fetcher(ttc_cookies)
                print(f"{CURRENT_COLOR_SCHEME[2]}Đã lấy {len(jobs)} job {job_type.upper()}{_Reset_}")
                
                if jobs:
                    job_found_in_cycle = True
                    for job in jobs:
                        try:
                            status = process_job(job_type, job, ttc_cookies, interactor)
                        except StopToolException as e:
                            if str(e).endswith("blocked"):
                                blocked_jobs.add(job_type)
                                jobs_to_process.remove(job_type)
                                available_jobs = [jt for jt in selected_job_types if jt not in blocked_jobs]
                                if not available_jobs:
                                    print(f"\n{CURRENT_COLOR_SCHEME[0]}Tài khoản {current_account.name} đã bị khóa tất cả các loại job. Chuyển tài khoản...{_Reset_}")
                                    accounts_to_run.pop(current_account_index)
                                    current_account_index -= 1
                                    break
                                break
                            raise
                        
                        if status == 'LOGGED_OUT':
                            print(f"{CURRENT_COLOR_SCHEME[0]}Đã loại bỏ TK {current_account.name}. Còn lại: {len(accounts_to_run)} TK{_Reset_}")
                            accounts_to_run.pop(current_account_index)
                            current_account_index -= 1
                            break
                        
                        if status == 'SUCCESS':
                            counters['per_account'][current_account.uid] += 1
                            counters['since_break'] += 1
                            if counters['since_break'] >= settings['JOBS_BEFORE_BREAK']:
                                print(f"\n{CURRENT_COLOR_SCHEME[2]}Đạt mốc {counters['since_break']} jobs. Nghỉ chống block...{_Reset_}")
                                countdown_display(settings['BREAK_TIME'])
                                counters['since_break'] = 0
                        
                        if not current_account.is_valid or counters['per_account'].get(current_account.uid, 0) >= settings['JOBS_BEFORE_SWITCH']:
                            break
                    if not current_account.is_valid or not accounts_to_run or not jobs_to_process:
                        break
                jobs_to_process.pop(0)
                if not current_account.is_valid or not accounts_to_run:
                    break
            
            current_account_index += 1
            if not job_found_in_cycle and current_account.is_valid and accounts_to_run:
                print(f"\n{CURRENT_COLOR_SCHEME[2]}Không tìm thấy job nào. Chờ 30 giây rồi thử lại...{_Reset_}")
                time.sleep(30)
            ttc_account_index += 1

    except StopToolException:
        print(f"\n{CURRENT_COLOR_SCHEME[0]}{_Bold_}Tool đã dừng do lỗi tài khoản. Tạm biệt!{_Reset_}")
    except KeyboardInterrupt:
        print(f"\n{CURRENT_COLOR_SCHEME[2]}Đã dừng bởi người dùng. Tạm biệt!{_Reset_}")
    except Exception as e:
        print(f"\n{CURRENT_COLOR_SCHEME[0]}{_Bold_}Lỗi nghiêm trọng: {e}{_Reset_}")

if __name__ == "__main__":
    main()