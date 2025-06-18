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
PRINT_PREFIX = "~( ! ) ➤ "

# --- Centralized URL Configuration ---
URLS = {
    "login_ttc": "https://tuongtaccheo.com/login.php",
    "get_ttc_token": "https://tuongtaccheo.com/api/",
    "get_account_info": "https://tuongtaccheo.com/logintoken.php",
    "config_ttc": "https://tuongtaccheo.com/caidat/",
    "set_main_account": "https://tuongtaccheo.com/cauhinh/datnick.php",
    "jobs": {
        "reaction": [
            {
                "fetch": "https://tuongtaccheo.com/kiemtien/camxucvipre/getpost.php",
                "claim": "https://tuongtaccheo.com/kiemtien/camxucvipre/nhantien.php",
                "source": "camxucvipre"
            },
            {
                "fetch": "https://tuongtaccheo.com/kiemtien/camxucvipcheo/getpost.php",
                "claim": "https://tuongtaccheo.com/kiemtien/camxucvipcheo/nhantien.php",
                "source": "camxucvipcheo"
            }
        ],
        "follow": {
            "fetch": "https://tuongtaccheo.com/kiemtien/subcheo/getpost.php",
            "claim": "https://tuongtaccheo.com/kiemtien/subcheo/nhantien.php",
            "source": "subcheo"
        },
        "share": {
            "fetch": "https://tuongtaccheo.com/kiemtien/sharecheo/getpost.php",
            "claim": "https://tuongtaccheo.com/kiemtien/sharecheo/nhantien.php",
            "source": "sharecheo"
        }
    },
    "facebook_api": "https://www.facebook.com/api/graphql/"
}

# --- Custom Exception for Stopping Tool ---
class StopToolException(Exception):
    pass

# --- Utility for Prefixed Printing ---
def print_with_prefix(message, message_type="info", end='\n'):
    if not message.strip() or message == "\n":  # Skip prefix for empty or newline-only messages
        print(message, end=end)
        return
    color = {
        "error": CURRENT_COLOR_SCHEME[0],  # Red for errors
        "success": CURRENT_COLOR_SCHEME[1],  # Green for success
        "info": CURRENT_COLOR_SCHEME[2]  # Blue for info
    }.get(message_type, CURRENT_COLOR_SCHEME[2])
    print(f"{color}{PRINT_PREFIX}{message}{_Reset_}", end=end)

# ==============================================================================
# SECTION: TUONGTACCHEO API INTERACTION
# ==============================================================================

def login_ttc(username, password):
    login_data = {"username": username, "password": password, "submit": "ĐĂNG NHẬP"}
    session = requests.Session()
    try:
        response = session.post(URLS["login_ttc"], data=login_data, timeout=10)
        response.raise_for_status()
        if "success" in response.text.lower():
            return session.cookies.get_dict(), username, password
    except requests.RequestException as e:
        print_with_prefix(f"Lỗi khi đăng nhập TTC: {e}", message_type="error")
    return None, None, None

def get_ttc_token(cookies):
    try:
        response = requests.get(URLS["get_ttc_token"], cookies=cookies, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        token_input = soup.find('input', {'name': 'ttc_access_token'})
        return token_input.get('value') if token_input else None
    except requests.RequestException as e:
        print_with_prefix(f"Lỗi khi lấy TTC token: {e}", message_type="error")
    return None

def get_account_info(token):
    try:
        response = requests.post(URLS["get_account_info"], data={"access_token": token}, timeout=10)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, json.JSONDecodeError) as e:
        print_with_prefix(f"Lỗi khi lấy thông tin tài khoản TTC: {e}", message_type="error")
        return {}

def set_main_account(cookies, fb_uid):
    headers = {
        "accept": "*/*",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://tuongtaccheo.com",
        "referer": "https://tuongtaccheo.com/cauhinh/facebook.php",
        "x-requested-with": "XMLHttpRequest",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    }
    data = {
        "iddat[]": fb_uid,
        "loai": "fb"
    }
    try:
        response = requests.post(URLS["set_main_account"], headers=headers, cookies=cookies, data=data, timeout=10)
        response.raise_for_status()
        if response.text.strip() == "1":
            print_with_prefix(f"Đã đặt nick chính thành công cho UID {fb_uid}", message_type="success")
            return True
        else:
            try:
                result = response.json()
                print_with_prefix(f"Lỗi khi đặt nick chính: {result.get('message', 'Phản hồi không rõ')}", message_type="error")
            except json.JSONDecodeError:
                print_with_prefix(f"Lỗi: Phản hồi đặt nick không hợp lệ: {response.text[:100]}", message_type="error")
            return False
    except requests.Timeout:
        print_with_prefix(f"Lỗi: Hết thời gian chờ khi đặt nick chính", message_type="error")
        return False
    except requests.HTTPError as e:
        print_with_prefix(f"Lỗi HTTP khi đặt nick chính: {e.response.status_code} - {e.response.text[:100]}", message_type="error")
        return False
    except requests.RequestException as e:
        print_with_prefix(f"Lỗi mạng khi đặt nick chính: {e}", message_type="error")
        return False

def _fetch_jobs_from_endpoint(url, cookies):
    headers = {"X-Requested-With": "XMLHttpRequest"}
    try:
        response = requests.get(url, headers=headers, cookies=cookies, timeout=10)
        response.raise_for_status()
        if response.text in ["0", "[]", ""]:
            return []
        jobs = response.json()
        valid_jobs = [job for job in jobs if isinstance(job, dict)]
        return valid_jobs
    except (requests.RequestException, json.JSONDecodeError) as e:
        print_with_prefix(f"Lỗi khi lấy jobs từ {url}: {e}", message_type="error")
        return []

def get_vip_reaction_jobs(cookies):
    jobs = []
    for endpoint in URLS["jobs"]["reaction"]:
        fetched_jobs = _fetch_jobs_from_endpoint(endpoint["fetch"], cookies)
        if fetched_jobs:
            jobs.extend([{"job": job, "source": endpoint["source"]} for job in fetched_jobs])
        if jobs:
            break  # Stop after first successful fetch
    return jobs

def get_follow_jobs(cookies):
    fetched_jobs = _fetch_jobs_from_endpoint(URLS["jobs"]["follow"]["fetch"], cookies)
    return [{"job": job, "source": URLS["jobs"]["follow"]["source"]} for job in fetched_jobs]

def get_share_jobs(cookies):
    fetched_jobs = _fetch_jobs_from_endpoint(URLS["jobs"]["share"]["fetch"], cookies)
    return [{"job": job, "source": URLS["jobs"]["share"]["source"]} for job in fetched_jobs]

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
        try:
            return response.json()
        except json.JSONDecodeError:
            print_with_prefix(f"Lỗi: Phản hồi nhận thưởng không phải JSON hợp lệ: {response.text[:100]}", message_type="error")
            return None
    except requests.Timeout:
        print_with_prefix(f"Lỗi: Hết thời gian chờ khi nhận thưởng từ {claim_url}", message_type="error")
        return None
    except requests.HTTPError as e:
        print_with_prefix(f"Lỗi HTTP khi nhận thưởng: {e.response.status_code} - {e.response.text[:100]}", message_type="error")
        return None
    except requests.RequestException as e:
        print_with_prefix(f"Lỗi mạng khi nhận thưởng: {e}", message_type="error")
        return None

def claim_reaction_reward(cookies, post_id, reaction_type, source):
    claim_url = next(
        endpoint["claim"] for endpoint in URLS["jobs"]["reaction"] if endpoint["source"] == source
    )
    return _claim_ttc_reward(claim_url, cookies, {"id": post_id, "loaicx": reaction_type})

def claim_follow_reward(cookies, target_id):
    return _claim_ttc_reward(URLS["jobs"]["follow"]["claim"], cookies, {"id": target_id})

def claim_share_reward(cookies, post_id):
    return _claim_ttc_reward(URLS["jobs"]["share"]["claim"], cookies, {"id": post_id})

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
                print_with_prefix(f"Tài khoản FB không hợp lệ: Có vẻ đã bị logout.", message_type="error")
                return False

            fb_dtsg_match = re.search(r'"DTSGInitialData",\[\],{"token":"(.*?)"', homepage_text) or \
                            re.search(r'name="fb_dtsg" value="(.*?)"', homepage_text) or \
                            re.search(r'"async_get_token":"(.*?)"', homepage_text)
            if not fb_dtsg_match:
                print_with_prefix(f"Lỗi: Không tìm thấy fb_dtsg trong phản hồi.", message_type="error")
                return False
            self.fb_dtsg = fb_dtsg_match.group(1)

            user_id_match = re.search(r'"USER_ID":"(\d+)"', homepage_text)
            if not user_id_match or user_id_match.group(1) != self.uid:
                print_with_prefix(f"Lỗi: USER_ID không khớp hoặc không tìm thấy.", message_type="error")
                return False

            name_match = re.search(r'"NAME":"(.*?)"', homepage_text)
            if name_match:
                self.name = name_match.group(1).encode('latin1').decode('unicode-escape')
            else:
                soup = BeautifulSoup(homepage_text, 'html.parser')
                title_tag = soup.find('title')
                if not title_tag or title_tag.string in ["Facebook", "Log in to Facebook", ""]:
                    print_with_prefix(f"Lỗi: Không tìm thấy tên tài khoản FB.", message_type="error")
                    return False
                self.name = title_tag.string

            if not self.name or self.name.strip() in ["Facebook", "Log in to Facebook"]:
                print_with_prefix(f"Lỗi: Tên tài khoản FB không hợp lệ.", message_type="error")
                return False

            return True
        except (requests.RequestException, AttributeError) as e:
            print_with_prefix(f"Lỗi khi xác thực tài khoản FB: {e}", message_type="error")
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
        try:
            if response.text.startswith("for (;;);"):
                error_data = json.loads(response.text[9:])
                if error_data.get("error") == 1357001:
                    print_with_prefix(f"\n{_Bold_}LỖI: Tài khoản {self.account.name} đã bị LOGOUT.", message_type="error")
                    self.account.is_valid = False
                    raise StopToolException("Account logged out")
                if "errors" in error_data and isinstance(error_data["errors"], list):
                    for error in error_data["errors"]:
                        if error.get("api_error_code") == 10 and "Tài khoản của bạn bị hạn chế" in error.get("summary", ""):
                            print_with_prefix(f"\n{_Bold_}LỖI: Tài khoản {self.account.name} bị hạn chế khi làm job {job_type.upper()}.", message_type="error")
                            raise StopToolException(f"{job_type} blocked")
        except json.JSONDecodeError:
            print_with_prefix(f"Lỗi: Phản hồi FB không phải JSON hợp lệ: {response.text[:100]}", message_type="error")

        try:
            data = response.json()
            if "errors" in data and isinstance(data["errors"], list):
                for error in data["errors"]:
                    if error.get("api_error_code") == 10 and "Tài khoản của bạn bị hạn chế" in error.get("summary", ""):
                        print_with_prefix(f"\n{_Bold_}LỖI: Tài khoản {self.account.name} bị hạn chế khi làm job {job_type.upper()}.", message_type="error")
                        raise StopToolException(f"{job_type} blocked")
        except json.JSONDecodeError:
            pass

        if not response.ok:
            print_with_prefix(f"Lỗi: Phản hồi FB không thành công: {response.status_code} - {response.text[:100]}", message_type="error")
            return False, None

        return True, None

    def react_to_post(self, post_id, reaction_name):
        reaction_id = REACTION_TYPES.get(reaction_name.upper())
        if not reaction_id:
            print_with_prefix(f"Lỗi: Loại reaction không hợp lệ: {reaction_name}", message_type="error")
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
            response = requests.post(URLS["facebook_api"], headers=self.base_headers, data=data, timeout=15)
            is_ok, _ = self._handle_response(response, "reaction")
            if not isinstance(is_ok, bool):
                print_with_prefix(f"Lỗi: Giá trị is_ok không hợp lệ trong react_to_post: {is_ok}", message_type="error")
                return False
            if not is_ok:
                return False
            return True
        except StopToolException:
            raise
        except requests.RequestException as e:
            print_with_prefix(f"Lỗi khi thực hiện reaction: {e}", message_type="error")
            return False

    def follow_user(self, target_id):
        if not target_id or not str(target_id).isdigit():
            print_with_prefix(f"Lỗi: target_id không hợp lệ: {target_id}", message_type="error")
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

            friend_response = requests.post(URLS["facebook_api"], headers=friend_headers, data=friend_data, timeout=15)
            is_ok, friend_json = self._handle_response(friend_response, "follow")
            if not isinstance(is_ok, bool):
                print_with_prefix(f"Lỗi: Giá trị is_ok không hợp lệ trong follow_user (friend): {is_ok}", message_type="error")
                return False
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

            follow_response = requests.post(URLS["facebook_api"], headers=follow_headers, data=follow_data, timeout=15)
            is_ok, follow_json = self._handle_response(follow_response, "follow")
            if not isinstance(is_ok, bool):
                print_with_prefix(f"Lỗi: Giá trị is_ok không hợp lệ trong follow_user (follow): {is_ok}", message_type="error")
                return False
            if not is_ok or (follow_json and follow_json.get('errors')):
                print_with_prefix(f"Lỗi: Không thể follow user {target_id}: {follow_json}", message_type="error")
                return False
            return True
        except StopToolException:
            raise
        except requests.RequestException as e:
            print_with_prefix(f"Lỗi khi thực hiện follow: {e}", message_type="error")
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
            response = requests.post(URLS["facebook_api"], headers=headers, data=data, timeout=15)
            is_ok, _ = self._handle_response(response, "share")
            if not isinstance(is_ok, bool):
                print_with_prefix(f"Lỗi: Giá trị is_ok không hợp lệ trong share_post: {is_ok}", message_type="error")
                return False
            if is_ok:
                return True
            return False
        except StopToolException:
            raise
        except requests.RequestException as e:
            print_with_prefix(f"Lỗi khi thực hiện share: {e}", message_type="error")
            return False

# ==============================================================================
# SECTION: JOB PROCESSING & UTILITIES
# ==============================================================================

def extract_xu_from_message(message):
    if not isinstance(message, str):
        return "???"
    return re.search(r'cộng (\d+)', message).group(1) if re.search(r'cộng (\d+)', message) else "???"

def countdown_display(seconds):
    print_with_prefix(f"--------Chờ {int(seconds)} giây nghỉ chống block------------", message_type="info")
    for i in range(int(seconds), 0, -1):
        print_with_prefix(f"Chờ {i}s...", message_type="info", end='\r')
        time.sleep(1)
    print(" " * 50, end='\r')

def handle_main_account_config_error(ttc_username):
    print_with_prefix(f"\n{_Bold_}LỖI: Tài khoản TTC {ttc_username} cần cấu hình nick chính trước khi nhận xu!", message_type="error")
    print_with_prefix(f"Vui lòng truy cập {URLS['config_ttc']} để cấu hình nick chính cho tài khoản {ttc_username}.", message_type="info")
    input(f"{CURRENT_COLOR_SCHEME[2]}{PRINT_PREFIX}Nhấn Enter sau khi hoàn tất cấu hình nick chính...{_Reset_}")

def process_job(job_type, job, ttc_cookies, interactor, ttc_username):
    if not isinstance(job, dict) or "job" not in job:
        print_with_prefix(f"Cảnh báo: Dữ liệu job không hợp lệ cho {job_type.upper()}: {job}", message_type="error")
        return 'ACTION_FAILED'

    if not interactor.account.is_valid:
        print_with_prefix(f"Tài khoản {interactor.account.name} không còn hợp lệ, có thể đã bị logout.", message_type="error")
        return 'LOGGED_OUT'

    actual_job = job["job"]
    job_source = job.get("source", URLS["jobs"][job_type]["source"] if job_type != "reaction" else "camxucvipcheo")
    now = datetime.now().strftime('%H:%M:%S')
    fb_name = interactor.account.name
    job_id_ttc = actual_job.get('idpost') or actual_job.get('id')

    fb_action_succeeded = False
    action_details = ""
    claim_function = None
    claim_args = []

    try:
        if job_type == "reaction":
            post_id_fb = actual_job.get('idfb') or job_id_ttc
            reaction_type = actual_job.get('loaicx')
            if not post_id_fb or not reaction_type:
                print_with_prefix(f"Lỗi: Thiếu post_id hoặc reaction_type cho job REACTION: {actual_job}", message_type="error")
                return 'ACTION_FAILED'
            action_details = f"REACTION:{reaction_type.upper()}|{post_id_fb}"
            fb_action_succeeded = interactor.react_to_post(post_id_fb, reaction_type)
            claim_function = claim_reaction_reward
            claim_args = [ttc_cookies, job_id_ttc, reaction_type, job_source]

        elif job_type == "follow":
            target_id_fb = actual_job.get('idpost') or actual_job.get('id')
            if not target_id_fb or not str(target_id_fb).isdigit():
                print_with_prefix(f"Lỗi: ID người dùng không hợp lệ cho job FOLLOW: {target_id_fb}", message_type="error")
                return 'ACTION_FAILED'
            action_details = f"FOLLOW|{target_id_fb}"
            fb_action_succeeded = interactor.follow_user(target_id_fb)
            claim_function = claim_follow_reward
            claim_args = [ttc_cookies, target_id_fb]

        elif job_type == "share":
            post_id_fb = actual_job.get('link', '').split('/posts/')[1].split('?')[0].strip('/') if '/posts/' in actual_job.get('link','') else job_id_ttc
            if not post_id_fb:
                print_with_prefix(f"Lỗi: Không thể lấy post_id cho job SHARE: {actual_job}", message_type="error")
                return 'ACTION_FAILED'
            action_details = f"SHARE|{post_id_fb}"
            fb_action_succeeded = interactor.share_post(post_id_fb)
            claim_function = claim_share_reward
            claim_args = [ttc_cookies, job_id_ttc]

        if not interactor.account.is_valid:
            print_with_prefix(f"Tài khoản {fb_name} không còn hợp lệ, có thể đã bị logout.", message_type="error")
            return 'LOGGED_OUT'

        if fb_action_succeeded:
            delay = 3 if job_type == "share" else 2
            # print_with_prefix(f"Chờ {delay}s sau khi thực hiện {job_type.upper()}...", message_type="info")
            time.sleep(delay)
            result = claim_function(*claim_args)

            if result is None:
                print_with_prefix(f"[{now}] {fb_name}|{action_details}|Nhận thưởng thất bại: Phản hồi API TTC không hợp lệ.", message_type="error")
                return 'ACTION_FAILED'

            if isinstance(result, dict):
                if result.get('error') == "Cần cấu hình đặt lại nick chính!":
                    print_with_prefix(f"[{now}] {fb_name}|{action_details}|Yêu cầu cấu hình nick chính. Đang thử tự động đặt...", message_type="error")
                    time.sleep(2)
                    if set_main_account(ttc_cookies, interactor.account.uid):
                        time.sleep(2)
                        result = claim_function(*claim_args)
                    else:
                        handle_main_account_config_error(ttc_username)
                        time.sleep(2)
                        result = claim_function(*claim_args)

                    if result is None:
                        print_with_prefix(f"[{now}] {fb_name}|{action_details}|Nhận thưởng thất bại sau khi cấu hình: Phản hồi API TTC không hợp lệ.", message_type="error")
                        return 'ACTION_FAILED'

                if result.get('mess'):
                    xu = extract_xu_from_message(result.get('mess'))
                    print_with_prefix(f"[{now}] {fb_name}|{action_details}|Thành công: +{xu} xu", message_type="success")
                    delay = random.uniform(*settings['DELAY_BETWEEN_JOBS'])
                    print_with_prefix(f"Chờ {delay:.2f}s trước khi chạy job tiếp theo...", message_type="info")
                    time.sleep(delay)
                    return 'SUCCESS'
                else:
                    print_with_prefix(f"[{now}] {fb_name}|{action_details}|Nhận thưởng thất bại: {result}", message_type="error")
                    return 'ACTION_FAILED'
            else:
                print_with_prefix(f"[{now}] {fb_name}|{action_details}|Nhận thưởng thất bại: Phản hồi không hợp lệ {result}", message_type="error")
                return 'ACTION_FAILED'

        else:
            print_with_prefix(f"[{now}] {fb_name}|{action_details}|Hành động FB thất bại.", message_type="error")
            return 'ACTION_FAILED'

    except StopToolException as e:
        if str(e) == "Account logged out":
            print_with_prefix(f"Tài khoản {fb_name} đã bị logout.", message_type="error")
            return 'LOGGED_OUT'
        raise

# ==============================================================================
# SECTION: UI & MAIN EXECUTION
# ==============================================================================

def get_random_color_scheme():
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
    print_with_prefix(f"Copyright © H-Tool 2025 | Version 5.2 (Final)\n", message_type="info")

def print_section(title):
    print_with_prefix(f"\n{_Bold_}>> {title.upper()} <<", message_type="info")

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print_with_prefix(f"Lỗi khi đọc file cài đặt: {e}", message_type="error")
            return None
    return None

def save_settings(s):
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(s, f, indent=4)
    except Exception as e:
        print_with_prefix(f"Lỗi khi lưu file cài đặt: {e}", message_type="error")

def setup_settings():
    print_section("Thiết Lập Cấu Hình Chạy Tool")
    saved_settings = load_settings()
    if saved_settings:
        use_saved = input(f"{CURRENT_COLOR_SCHEME[2]}{PRINT_PREFIX}Tìm thấy cấu hình đã lưu, bạn có muốn sử dụng không? (y/n): {_Reset_}").lower()
        if use_saved == 'y':
            print_with_prefix(f"Đã áp dụng cấu hình đã lưu.", message_type="success")
            return saved_settings

    s = {}
    try:
        s['DELAY_BETWEEN_JOBS'] = (
            int(input(f"{CURRENT_COLOR_SCHEME[2]}{PRINT_PREFIX}- Delay tối thiểu giữa các job (giây): {_Reset_}") or 5),
            int(input(f"{CURRENT_COLOR_SCHEME[2]}{PRINT_PREFIX}- Delay tối đa giữa các job (giây): {_Reset_}") or 10)
        )
        s['JOBS_BEFORE_BREAK'] = int(input(f"{CURRENT_COLOR_SCHEME[2]}{PRINT_PREFIX}- Sau bao nhiêu job thì nghỉ chống block: {_Reset_}") or 20)
        s['BREAK_TIME'] = int(input(f"{CURRENT_COLOR_SCHEME[2]}{PRINT_PREFIX}- Thời gian nghỉ chống block (giây): {_Reset_}") or 300)
        s['JOBS_BEFORE_SWITCH'] = int(input(f"{CURRENT_COLOR_SCHEME[2]}{PRINT_PREFIX}- Bao nhiêu job thì đổi tài khoản Facebook: {_Reset_}") or 15)

        save_choice = input(f"\n{CURRENT_COLOR_SCHEME[2]}{PRINT_PREFIX}Bạn có muốn lưu cấu hình này cho lần sau? (y/n): {_Reset_}").lower()
        if save_choice == 'y':
            save_settings(s)
            print_with_prefix(f"Đã lưu cấu hình.", message_type="success")
    except ValueError:
        print_with_prefix(f"Nhập không hợp lệ, sử dụng cấu hình mặc định.", message_type="error")
        s = {
            'DELAY_BETWEEN_JOBS': (5, 10),
            'JOBS_BEFORE_BREAK': 20,
            'BREAK_TIME': 300,
            'JOBS_BEFORE_SWITCH': 15
        }
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
            print_with_prefix(f"Lỗi khi đọc {ACCOUNT_FILE}: {e}", message_type="error")
    return accounts

def save_ttc_account(username, password):
    try:
        with open(ACCOUNT_FILE, 'a') as f:
            f.write(f"{username}|{password}\n")
    except Exception as e:
        print_with_prefix(f"Lỗi khi lưu tài khoản TTC: {e}", message_type="error")

def select_ttc_accounts(saved_accounts):
    print_section("Chọn Tài Khoản TuongTacCheo")
    if not saved_accounts:
        return []
    for i, (username, _) in enumerate(saved_accounts):
        print_with_prefix(f"{i+1}. {username}", message_type="info")
    print_with_prefix("all. Chọn tất cả tài khoản trên.", message_type="info")

    choice = input(f"{CURRENT_COLOR_SCHEME[2]}{PRINT_PREFIX}Nhập lựa chọn (ví dụ: 1+2 hoặc all): {_Reset_}").lower()
    if choice == 'all':
        return saved_accounts
    try:
        selected_indices = [int(x.strip()) - 1 for x in choice.split('+')]
        return [saved_accounts[i] for i in selected_indices if 0 <= i < len(saved_accounts)]
    except (ValueError, IndexError):
        print_with_prefix(f"Lựa chọn không hợp lệ, sẽ không chạy tài khoản nào.", message_type="error")
        return []

def select_ttc_account_source():
    print_section("Chọn Nguồn Tài Khoản TuongTacCheo")
    print_with_prefix(f"1. Nhập tài khoản TTC mới.", message_type="info")
    print_with_prefix(f"2. Sử dụng tài khoản TTC đã lưu trong `{ACCOUNT_FILE}`.", message_type="info")
    choice = input(f"{CURRENT_COLOR_SCHEME[2]}{PRINT_PREFIX}Lựa chọn của bạn (1-2): {_Reset_}")
    return choice

def get_fb_cookies_menu():
    print_section("Chọn Nguồn Cung Cấp Cookie Facebook")
    print_with_prefix(f"1. Nhập cookie trực tiếp vào console.", message_type="info")
    print_with_prefix(f"2. Nhập cookie từ file (ví dụ: `new_cookies.txt`).", message_type="info")
    print_with_prefix(f"3. Sử dụng cookie đã lưu trong `{COOKIE_FILE}`.", message_type="info")
    choice = input(f"{CURRENT_COLOR_SCHEME[2]}{PRINT_PREFIX}Lựa chọn của bạn (1-3): {_Reset_}")

    cookies = []
    if choice == '1':
        print_with_prefix(f"Nhập các cookie, mỗi cookie một dòng. Nhấn Enter trên dòng trống để kết thúc.", message_type="info")
        while True:
            line = input()
            if not line:
                break
            cookies.append(line.strip())
    elif choice == '2':
        filename = input(f"{CURRENT_COLOR_SCHEME[2]}{PRINT_PREFIX}Nhập tên file chứa cookie: {_Reset_}")
        try:
            with open(filename, 'r') as f:
                cookies = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print_with_prefix(f"File '{filename}' không tồn tại.", message_type="error")
            return []
    elif choice == '3':
        try:
            with open(COOKIE_FILE, 'r') as f:
                cookies = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print_with_prefix(f"File `{COOKIE_FILE}` không tồn tại.", message_type="error")
            return []
    else:
        print_with_prefix(f"Lựa chọn không hợp lệ.", message_type="error")
        return []

    if cookies:
        try:
            with open(COOKIE_FILE, 'w') as f:
                f.write('\n'.join(cookies))
            print_with_prefix(f"Đã lấy và lưu {len(cookies)} cookie vào {COOKIE_FILE}", message_type="success")
        except Exception as e:
            print_with_prefix(f"Lỗi khi lưu cookie: {e}", message_type="error")
    return cookies

def select_accounts_to_run(valid_accounts, ttc_cookies, ttc_username):
    print_section("Chọn Tài Khoản Facebook Để Chạy")
    if not valid_accounts:
        return []
    for i, acc in enumerate(valid_accounts):
        print_with_prefix(f"{i+1}. {acc.name} (UID: {acc.uid})", message_type="info")
    print_with_prefix("all. Chạy tất cả các tài khoản trên.", message_type="info")

    choice = input(f"{CURRENT_COLOR_SCHEME[2]}{PRINT_PREFIX}Nhập lựa chọn (ví dụ: 1+3 hoặc all): {_Reset_}").lower()
    if choice == 'all':
        selected_accounts = valid_accounts
    else:
        try:
            selected_indices = [int(x.strip()) - 1 for x in choice.split('+')]
            selected_accounts = [valid_accounts[i] for i in selected_indices if 0 <= i < len(valid_accounts)]
        except (ValueError, IndexError):
            print_with_prefix(f"Lựa chọn không hợp lệ, sẽ không chạy tài khoản nào.", message_type="error")
            return []

    for acc in selected_accounts:
        print_with_prefix(f"Đang đặt nick chính cho {acc.name} (UID: {acc.uid})...", message_type="info")
        time.sleep(2)
        if not set_main_account(ttc_cookies, acc.uid):
            print_with_prefix(f"Không thể đặt nick chính cho {acc.name}. Vui lòng cấu hình thủ công hoặc kiểm tra lại.", message_type="error")
            handle_main_account_config_error(ttc_username)
    return selected_accounts

def select_job_types():
    print_section("Chọn Loại Job Muốn Thực Hiện")
    print_with_prefix("1. Reaction (ví dụ: Like, Love...)", message_type="info")
    print_with_prefix("2. Follow", message_type="info")
    print_with_prefix("3. Share", message_type="info")
    print_with_prefix("Nhập các số cách nhau bằng '+' (ví dụ: 1+2 để chạy Reaction và Follow, để trống để chạy tất cả)", message_type="info")
    choice = input(f"{CURRENT_COLOR_SCHEME[2]}{PRINT_PREFIX}Lựa chọn của bạn: {_Reset_}").strip()

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
        username = input(f"{CURRENT_COLOR_SCHEME[2]}{PRINT_PREFIX}Nhập username TuongTacCheo: {_Reset_}")
        password = input(f"{CURRENT_COLOR_SCHEME[2]}{PRINT_PREFIX}Nhập password TuongTacCheo: {_Reset_}")
        ttc_cookies, _, _ = login_ttc(username, password)
        if ttc_cookies:
            save_ttc_account(username, password)
            print_with_prefix(f"Đã lưu tài khoản TTC {username} vào {ACCOUNT_FILE}", message_type="success")
            ttc_accounts_to_use = [(username, password, ttc_cookies)]
        else:
            print_with_prefix(f"Đăng nhập TTC thất bại. Vui lòng thử lại sau.", message_type="error")
            return

    elif account_source == '2':
        saved_accounts = load_ttc_accounts()
        if not saved_accounts:
            print_with_prefix(f"Không tìm thấy tài khoản TTC đã lưu trong {ACCOUNT_FILE}. Vui lòng nhập tài khoản mới.", message_type="error")
            return

        selected_accounts = select_ttc_accounts(saved_accounts)
        if not selected_accounts:
            print_with_prefix(f"Không có tài khoản TTC nào được chọn. Vui lòng thử lại.", message_type="error")
            return

        print_section("Đang kiểm tra các tài khoản TTC đã chọn")
        for username, password in selected_accounts:
            print_with_prefix(f"Đang kiểm tra tài khoản {username}...", message_type="info", end='')
            ttc_cookies, _, _ = login_ttc(username, password)
            if ttc_cookies:
                ttc_accounts_to_use.append((username, password, ttc_cookies))
                print_with_prefix(f"\r -> Tài khoản {username}: Đăng nhập thành công", message_type="success")
            else:
                print_with_prefix(f"\r -> Tài khoản {username}: Đăng nhập thất bại", message_type="error")

    if not ttc_accounts_to_use:
        print_with_prefix(f"Không có tài khoản TTC nào hợp lệ để chạy. Vui lòng thử lại.", message_type="error")
        return

    global settings
    settings = setup_settings()

    while True:
        raw_cookies = get_fb_cookies_menu()
        if not raw_cookies:
            retry = input(f"{CURRENT_COLOR_SCHEME[2]}{PRINT_PREFIX}Không có cookie Facebook nào được cung cấp. Thử lại? (y/n): {_Reset_}").lower()
            if retry != 'y':
                print_with_prefix(f"Không có cookie để chạy. Thoát tool.", message_type="error")
                return
            continue

        print_section("Đang kiểm tra các tài khoản Facebook")
        all_fb_accounts = []
        for i, cookie_str in enumerate(raw_cookies):
            print_with_prefix(f"Đang kiểm tra cookie #{i+1}...", message_type="info", end='')
            fb_account = FacebookAccount(cookie_str)
            if fb_account.is_valid:
                all_fb_accounts.append(fb_account)
                print_with_prefix(f"\r -> Cookie #{i+1}: Hợp lệ - {fb_account.name}", message_type="success")
            else:
                print_with_prefix(f"\r -> Cookie #{i+1}: KHÔNG HỢP LỆ (Die hoặc Logout). Bỏ qua cookie này.", message_type="error")

        if not all_fb_accounts:
            print_with_prefix(f"Cảnh báo: Không có tài khoản Facebook nào hợp lệ. Vui lòng cung cấp cookie mới.", message_type="error")
            retry = input(f"{CURRENT_COLOR_SCHEME[2]}{PRINT_PREFIX}Thử lại với cookie mới? (y/n): {_Reset_}").lower()
            if retry != 'y':
                print_with_prefix(f"Không có tài khoản Facebook hợp lệ để chạy. Thoát tool.", message_type="error")
                return
            continue

        ttc_username, _, ttc_cookies = ttc_accounts_to_use[0]
        accounts_to_run = select_accounts_to_run(all_fb_accounts, ttc_cookies, ttc_username)
        if not accounts_to_run:
            print_with_prefix(f"Cảnh báo: Không có tài khoản Facebook nào được chọn.", message_type="error")
            retry = input(f"{CURRENT_COLOR_SCHEME[2]}{PRINT_PREFIX}Thử lại với cookie mới? (y/n): {_Reset_}").lower()
            if retry != 'y':
                print_with_prefix(f"Không có tài khoản được chọn để chạy. Thoát tool.", message_type="error")
                return
            continue

        print_with_prefix(f"Sẵn sàng chạy với {len(accounts_to_run)} tài khoản Facebook.", message_type="success")
        break

    selected_job_types = select_job_types()
    print_with_prefix(f"Các loại job sẽ chạy: {', '.join(s.upper() for s in selected_job_types)}", message_type="success")

    print_section("Bắt đầu thực hiện Job")
    counters = {'per_account': {acc.uid: 0 for acc in accounts_to_run}, 'since_break': 0}
    current_account_index = 0
    blocked_jobs_per_account = {acc.uid: set() for acc in accounts_to_run}
    ttc_account_index = 0

    while True:
        try:
            while accounts_to_run and ttc_accounts_to_use:
                if ttc_account_index >= len(ttc_accounts_to_use):
                    ttc_account_index = 0
                ttc_username, _, ttc_cookies = ttc_accounts_to_use[ttc_account_index]
                print_with_prefix(f"\n{_Bold_}Đang dùng TTC: {ttc_username}", message_type="info")

                if current_account_index >= len(accounts_to_run):
                    current_account_index = 0

                current_account = accounts_to_run[current_account_index]
                if not current_account.is_valid:
                    print_with_prefix(f"Tài khoản {current_account.name} không hợp lệ, bỏ qua...", message_type="error")
                    accounts_to_run.pop(current_account_index)
                    current_account_index -= 1
                    time.sleep(2)
                    continue

                blocked_jobs = blocked_jobs_per_account[current_account.uid]
                available_jobs = [jt for jt in selected_job_types if jt not in blocked_jobs]

                if not available_jobs:
                    print_with_prefix(f"\nTài khoản {current_account.name} đã bị khóa tất cả các loại job. Chuyển tài khoản...", message_type="error")
                    time.sleep(2)
                    accounts_to_run.pop(current_account_index)
                    current_account_index -= 1
                    continue

                if counters['per_account'].get(current_account.uid, 0) >= settings['JOBS_BEFORE_SWITCH']:
                    print_with_prefix(f"\nTài khoản {current_account.name} đã đạt giới hạn. Chuyển...", message_type="info")
                    counters['per_account'][current_account.uid] = 0
                    current_account_index = (current_account_index + 1) % len(accounts_to_run)
                    time.sleep(2)
                    continue

                print_with_prefix(f"\nĐang đặt nick chính cho {current_account.name} (UID: {current_account.uid})...", message_type="info")
                time.sleep(2)
                if not set_main_account(ttc_cookies, current_account.uid):
                    print_with_prefix(f"Không thể đặt nick chính cho {current_account.name}. Yêu cầu cấu hình thủ công.", message_type="error")
                    handle_main_account_config_error(ttc_username)

                print_with_prefix(f"\n{_Bold_}Đang dùng FB: {current_account.name} (Jobs: {counters['per_account'].get(current_account.uid, 0)}/{settings['JOBS_BEFORE_SWITCH']})", message_type="info")
                interactor = FacebookInteractor(current_account)

                job_found_in_cycle = False
                jobs_to_process = available_jobs.copy()
                random.shuffle(jobs_to_process)

                while jobs_to_process:
                    job_type = jobs_to_process[0]
                    if not current_account.is_valid:
                        print_with_prefix(f"Tài khoản {current_account.name} không hợp lệ, bỏ qua job {job_type.upper()}...", message_type="error")
                        break

                    fetcher = globals()[f"get_{'vip_' if job_type == 'reaction' else ''}{job_type}_jobs"]
                    try:
                        jobs = fetcher(ttc_cookies)
                        print_with_prefix(f"Đã lấy {len(jobs)} job {job_type.upper()}", message_type="info")
                    except Exception as e:
                        print_with_prefix(f"Lỗi khi lấy job {job_type.upper()}: {e}", message_type="error")
                        jobs = []

                    if jobs:
                        job_found_in_cycle = True
                        for job in jobs:
                            if not current_account.is_valid:
                                print_with_prefix(f"Tài khoản {current_account.name} không hợp lệ, bỏ qua job {job_type.upper()}...", message_type="error")
                                break

                            try:
                                status = process_job(job_type, job, ttc_cookies, interactor, ttc_username)
                            except StopToolException as e:
                                if str(e).endswith("blocked"):
                                    print_with_prefix(f"Job {job_type.upper()} bị khóa cho tài khoản {current_account.name}.", message_type="error")
                                    blocked_jobs.add(job_type)
                                    jobs_to_process.remove(job_type)
                                    available_jobs = [jt for jt in selected_job_types if jt not in blocked_jobs]
                                    if not available_jobs:
                                        print_with_prefix(f"\nTài khoản {current_account.name} đã bị khóa tất cả các loại job. Chuyển tài khoản...", message_type="error")
                                        time.sleep(2)
                                        accounts_to_run.pop(current_account_index)
                                        current_account_index -= 1
                                        break
                                    time.sleep(2)
                                    break
                                elif str(e) == "Account logged out":
                                    print_with_prefix(f"Tài khoản {current_account.name} đã bị logout. Bỏ qua và tiếp tục với tài khoản khác...", message_type="error")
                                    time.sleep(2)
                                    accounts_to_run.pop(current_account_index)
                                    current_account_index -= 1
                                    break
                                raise

                            if status == 'LOGGED_OUT':
                                print_with_prefix(f"Tài khoản {current_account.name} đã bị logout. Bỏ qua và tiếp tục với tài khoản khác...", message_type="error")
                                time.sleep(2)
                                accounts_to_run.pop(current_account_index)
                                current_account_index -= 1
                                if not accounts_to_run:
                                    print_with_prefix(f"Lỗi: Tất cả các tài khoản Facebook đã bị logout hoặc không hợp lệ. Yêu cầu nhập cookie mới.", message_type="error")
                                    while True:
                                        raw_cookies = get_fb_cookies_menu()
                                        if not raw_cookies:
                                            retry = input(f"{CURRENT_COLOR_SCHEME[2]}{PRINT_PREFIX}Không có cookie Facebook nào được cung cấp. Thử lại? (y/n): {_Reset_}").lower()
                                            if retry != 'y':
                                                print_with_prefix(f"Không có cookie để chạy. Thoát tool.", message_type="error")
                                                return
                                            continue

                                        print_section("Đang kiểm tra các tài khoản Facebook")
                                        new_accounts = []
                                        for i, cookie_str in enumerate(raw_cookies):
                                            print_with_prefix(f"Đang kiểm tra cookie #{i+1}...", message_type="info", end='')
                                            fb_account = FacebookAccount(cookie_str)
                                            if fb_account.is_valid:
                                                new_accounts.append(fb_account)
                                                print_with_prefix(f"\r -> Cookie #{i+1}: Hợp lệ - {fb_account.name}", message_type="success")
                                            else:
                                                print_with_prefix(f"\r -> Cookie #{i+1}: KHÔNG HỢP LỆ (Die hoặc Logout). Bỏ qua cookie này.", message_type="error")

                                        if not new_accounts:
                                            print_with_prefix(f"Cảnh báo: Không có tài khoản Facebook nào hợp lệ. Vui lòng cung cấp cookie mới.", message_type="error")
                                            retry = input(f"{CURRENT_COLOR_SCHEME[2]}{PRINT_PREFIX}Thử lại với cookie mới? (y/n): {_Reset_}").lower()
                                            if retry != 'y':
                                                print_with_prefix(f"Không có tài khoản Facebook hợp lệ để chạy. Thoát tool.", message_type="error")
                                                return
                                            continue

                                        accounts_to_run.extend(new_accounts)
                                        accounts_to_run = select_accounts_to_run(new_accounts, ttc_cookies, ttc_username)
                                        if accounts_to_run:
                                            counters['per_account'].update({acc.uid: 0 for acc in accounts_to_run})
                                            blocked_jobs_per_account.update({acc.uid: set() for acc in accounts_to_run})
                                            current_account_index = 0
                                            print_with_prefix(f"Sẵn sàng chạy lại với {len(accounts_to_run)} tài khoản Facebook.", message_type="success")
                                            break
                                continue

                            if status == 'SUCCESS':
                                counters['per_account'][current_account.uid] += 1
                                counters['since_break'] += 1
                                if counters['since_break'] >= settings['JOBS_BEFORE_BREAK']:
                                    print_with_prefix(f"\nĐạt mốc {counters['since_break']} jobs. Nghỉ để chống block...", message_type="info")
                                    countdown_display(settings['BREAK_TIME'])
                                    counters['since_break'] = 0

                            if not current_account.is_valid or counters['per_account'].get(current_account.uid, 0) >= settings['JOBS_BEFORE_SWITCH']:
                                break
                        if not current_account.is_valid or not accounts_to_run or not jobs_to_process:
                            break
                    jobs_to_process.pop(0)
                    time.sleep(2)
                    if not current_account.is_valid or not accounts_to_run:
                        break

                if not accounts_to_run:
                    print_with_prefix(f"Tất cả các tài khoản Facebook đã bị logout hoặc không hợp lệ. Yêu cầu nhập cookie mới.", message_type="error")
                    break

                current_account_index += 1
                if not job_found_in_cycle and current_account.is_valid and accounts_to_run:
                    print_with_prefix(f"\nKhông tìm thấy job nào để chạy. Chờ 30 giây rồi thử lại.", message_type="info")
                    time.sleep(30)
                ttc_account_index += 1

        except StopToolException as e:
            if str(e) != "Account logged out":
                print_with_prefix(f"\nLỗi: Tool đã dừng: {e}. Tạm biệt!", message_type="error")
                return
        except KeyboardInterrupt:
            print_with_prefix(f"\nĐã dừng bởi người dùng. Tạm biệt.", message_type="info")
            return
        except Exception as e:
            print_with_prefix(f"\nLỗi nghiêm trọng: {e}", message_type="error")
            return

if __name__ == "__main__":
    main()