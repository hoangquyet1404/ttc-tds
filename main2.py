import os
import sys
import json
import time
import hashlib
import random
import requests
import string
import threading
import queue
from datetime import datetime, timedelta
from time import sleep

API_TOKEN = "703371951353e080dde13a50207e2ff7c3fc31fe88f765c17fa11d9fd1046528"
API_YEUMONEY = "https://yeumoney.com/QL_api.php"
API_KEY_SERVER = "http://103.149.252.133:2000/api"
API_KEY_PAGE = "http://sublikevip.site/key.html"
API_NOTIFICATIONS = "http://103.149.252.133:2000/apis/thongbao"
DEFAULT_KEY = "joonwuydeptrai"

HEADERS = {
    "key": "anhyeuem"
}
def install_required_packages():
    flag_file = os.path.join(os.path.dirname(__file__), '.packages_installed')
    if os.path.exists(flag_file):
        return
        
    packages = ['requests', 'beautifulsoup4', 'colorama','bs4','colorama','termcolor']
    for package in packages:
        os.system(f'pip install {package}')
    with open(flag_file, 'w') as f:
        f.write('1')

def init_colors():
    try:
        from colorama import init, Fore, Back, Style
        init(autoreset=True)
        return Fore, Back, Style
    except ImportError:
        class Colors:
            RED = '\033[91m'
            GREEN = '\033[92m'
            YELLOW = '\033[93m'
            BLUE = '\033[94m'
            MAGENTA = '\033[95m'
            CYAN = '\033[96m'
            WHITE = '\033[97m'
            ORANGE = '\033[38;5;208m'
            BRIGHT_GREEN = '\033[38;5;46m'
            BRIGHT_RED = '\033[38;5;196m'
            BRIGHT_YELLOW = '\033[38;5;226m'
            BRIGHT_CYAN = '\033[38;5;51m'
            RESET = '\033[0m'
            BOLD = '\033[1m'
            DIM = '\033[2m'
        return Colors, None, Colors

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

def show_logo():
    Fore, Back, Style = init_colors()
    os.system('cls' if os.name == 'nt' else 'clear')
    colors = get_random_color_scheme()
    reset_color = '\033[0m'
    print(f"""
{colors[0]}██╗  ██╗      {colors[1]}████████╗ ██████╗  ██████╗ ██╗     
{colors[0]}██║  ██║      {colors[1]}╚══██╔══╝██╔═══██╗██╔═══██╗██║     
{colors[1]}███████║█████╗{colors[2]}   ██║   ██║   ██║██║   ██║██║     
{colors[2]}██╔══██║╚════╝{colors[3]}   ██║   ██║   ██║██║   ██║██║     
{colors[2]}██║  ██║      {colors[3]}   ██║   ╚██████╔╝╚██████╔╝███████╗
{colors[3]}╚═╝  ╚═╝         ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝{reset_color}
""")
    copyright_colors = ['\033[38;5;220m', '\033[38;5;226m', '\033[38;5;214m', '\033[38;5;208m']
    copyright_color = random.choice(copyright_colors)
    print(f"{copyright_color}                Copyright © H-Tool 2025 | Version 4.0{reset_color}")
    print()

def show_user_info():
    Fore, Back, Style = init_colors()
    info_colors = {
        'prompt': '\033[38;5;46m',
        'label': '\033[38;5;51m',
        'name': '\033[38;5;159m',
        'website': '\033[38;5;214m',
        'phone': '\033[38;5;196m',
        'link': '\033[38;5;141m'
    }
    reset_color = '\033[0m'
    
    print(f"{info_colors['prompt']}~[●] ➤ {info_colors['label']}Admin: {info_colors['name']}Trần Văn Quang Huy{reset_color}")
    print(f"{info_colors['prompt']}~[●] ➤ {info_colors['label']}Website Bán Sub Giá Rẻ: {info_colors['website']}trumsubvip.site{reset_color}")
    print(f"{info_colors['prompt']}~[●] ➤ {info_colors['label']}Zalo Admin: {info_colors['phone']}0372065607{reset_color}")
    print(f"{info_colors['prompt']}~[●] ➤ {info_colors['label']}Box Zalo: {info_colors['link']}https://zalo.me/g/dqacsy523{reset_color}")
    print()

def get_notifications():
    try:
        response = requests.get(API_NOTIFICATIONS, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def show_notifications():
    Fore, Back, Style = init_colors()
    notif_colors = {
        'header': '\033[48;5;220m\033[30m',
        'prompt': '\033[38;5;82m',
        'date': '\033[38;5;87m',
        'text': '\033[38;5;255m',
        'error': '\033[38;5;203m'
    }
    reset_color = '\033[0m'
    
    print(f"{notif_colors['header']}[THÔNG BÁO]{reset_color}")
    
    notifications = get_notifications()
    if not notifications:
        print(f"{notif_colors['error']}~(!) ➤ Không thể tải thông báo{reset_color}")
    else:
        for notif in notifications:
            print(f"{notif_colors['prompt']}~(!) ➤ {notif_colors['date']}{notif['date']} {notif_colors['text']}{notif['message']}{reset_color}")
    
    print()

def get_machine_id():
    machine_id = ""
    if os.name == 'nt':
        import wmi
        c = wmi.WMI()
        system_info = c.Win32_ComputerSystemProduct()[0]
        machine_id = system_info.UUID
    else:
        with open('/etc/machine-id', 'r') as f:
            machine_id = f.read().strip()
    return hashlib.md5(machine_id.encode()).hexdigest()

def load_key_data():
    key_file = os.path.join(os.path.dirname(__file__), 'key.txt')
    if os.path.exists(key_file):
        try:
            with open(key_file, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

def save_key_data(key_data):
    key_file = os.path.join(os.path.dirname(__file__), 'key.txt')
    try:
        data = {
            'id': key_data['id'],
            'key': key_data['key'],
            'machine_id': key_data['machine_id']
        }
        with open(key_file, 'w') as f:
            json.dump(data, f)
        return True
    except:
        return False

def generate_random_key():
    return ''.join(random.choices(string.digits, k=6))

def get_final_redirect_url(url):
    try:
        response = requests.get(url, allow_redirects=False)
        if response.status_code == 302:
            return response.headers['Location']
    except:
        pass
    return None

def generate_and_save_key():
    key = ''.join(random.choices(string.digits, k=6))
    try:
        data = {
            'key': key,
            'machine_id': get_machine_id(),
            'device_info': os.environ.get('COMPUTERNAME', 'Unknown Device'),
            'used': False,
            'expires_at': (datetime.now() + timedelta(days=1)).isoformat()
        }
        
        response = requests.post(f'{API_KEY_SERVER}/data', json=data, headers=HEADERS)
        if response.status_code == 200:
            return response.json()['data']
        return None
    except:
        return None

def get_bypass_link():
    try:
        key = generate_random_key()
        target_url = f"http://sublikevip.site/index.html?key={key}"
        shorten_api = f"https://yeumoney.com/QL_api.php?token=703371951353e080dde13a50207e2ff7c3fc31fe88f765c17fa11d9fd1046528&format=json&url={target_url}"
        
        shorten_response = requests.get(shorten_api, timeout=10)
        if shorten_response.status_code == 200:
            shorten_data = shorten_response.json()
            if shorten_data.get('status') == 'success':
                bypass_link = shorten_data['shortenedUrl']
                
                data = {
                    'key': key,
                    'machine_id': get_machine_id(),
                    'device_info': os.environ.get('COMPUTERNAME', 'Unknown Device'),
                    'used': False,
                    'expires_at': (datetime.now() + timedelta(days=1)).isoformat()
                }
                
                server_response = requests.post(f'{API_KEY_SERVER}/data', json=data, headers=HEADERS, timeout=10)
                if server_response.status_code != 200:
                    return "Lỗi kết nối, vui lòng thử lại", None
                    
                return bypass_link, {'id': server_response.json().get('data', {}).get('id')}
                
        return "Lỗi kết nối, vui lòng thử lại", None
        
    except requests.Timeout:
        return "Lỗi kết nối, vui lòng thử lại", None
    except requests.ConnectionError:
        return "Lỗi kết nối, vui lòng thử lại", None
    except:
        return "Lỗi kết nối, vui lòng thử lại", None

def check_key_with_server(key):
    if key == DEFAULT_KEY:
        return True, {
            'key': DEFAULT_KEY,
            'machine_id': get_machine_id(),
            'id': 'default',
            'expires_at': '2099-12-31T23:59:59.999Z'
        }, None
        
    try:
        response = requests.get(f'{API_KEY_SERVER}/data', headers=HEADERS, timeout=10)
        if response.status_code == 200:
            keys_data = response.json()
            key_entry = next((k for k in keys_data if k.get('key') == key), None)
            
            if key_entry:
                current_machine = get_machine_id()
                if key_entry.get('used', False):
                    if key_entry.get('machine_id') == current_machine:
                        return True, key_entry, None
                    return False, None, "Key đã được sử dụng bởi thiết bị khác"
                return True, key_entry, None
                
            return False, None, "Key không tồn tại"
            
    except:
        return False, None, "Lỗi kết nối, vui lòng thử lại"

def mark_key_as_used(key_id):
    if key_id == DEFAULT_KEY:
        return True
        
    try:
        get_response = requests.get(f'{API_KEY_SERVER}/data', headers=HEADERS, timeout=10)
        if get_response.status_code == 200:
            keys_data = get_response.json()
            key_entry = next((k for k in keys_data if k.get('key') == key_id), None)
            
            if key_entry:
                data = {
                    'key': key_entry['key'],
                    'machine_id': get_machine_id(),
                    'device_info': os.environ.get('COMPUTERNAME', 'Unknown Device'),
                    'used': True,
                    'expires_at': key_entry['expires_at'],
                    'timestamp': datetime.now().isoformat()
                }
                response = requests.put(f'{API_KEY_SERVER}/data/{key_entry["key"]}', json=data, headers=HEADERS)
                return response.status_code == 200
                
        return False
    except:
        return False

def delete_key_from_server(key):
    try:
        response = requests.delete(f'{API_KEY_SERVER}/data/{key}', headers=HEADERS, timeout=10)
        return response.status_code == 200
    except:
        return False

def show_warning():
    Fore, Back, Style = init_colors()
    
    valid, key_data = check_key_validity()
    if isinstance(key_data, dict):
        print(f"{Back.GREEN}{Fore.BLACK}[KEY STATUS]{Fore.RESET}{Back.RESET}")
        print(f"{Fore.GREEN}~(!) ➤ {Fore.CYAN}Key: ****{key_data.get('key', '???')[-2:]}")
        print(f"{Fore.GREEN}~(!) ➤ {Fore.CYAN}Thời hạn còn lại: {Fore.YELLOW}{key_data.get('remaining_time', 'Không xác định')}{Fore.RESET}")
    else:
        print(f"{Back.RED}{Fore.WHITE}[WARNING]{Fore.RESET}{Back.RESET} {Fore.RED}{key_data}{Fore.RESET}")
        if "hết hạn" in str(key_data):
            if not activate_key():
                sys.exit(1)
    print()

def show_tools():
    Fore, Back, Style = init_colors()
    tool_colors = {
        'title': '\033[38;5;220m',
        'prompt': '\033[38;5;40m',
        'text': '\033[38;5;231m',
        'border': '\033[38;5;245m'
    }
    reset_color = '\033[0m'
    
    print(f"{tool_colors['title']}[CÔNG CỤ]{reset_color}")
    print(f"{tool_colors['border']}══════════════════════════════════════{reset_color}")
    print(f"{tool_colors['prompt']}~[1] ➤ {tool_colors['text']}Tool Trao Đổi Sub{reset_color}")
    print(f"{tool_colors['prompt']}~[2] ➤ {tool_colors['text']}Tool Tương Tác Chéo{reset_color}")
    print(f"{tool_colors['border']}══════════════════════════════════════{reset_color}")
    print()

def show_menu():
    Fore, Back, Style = init_colors()
    menu_colors = {
        'title': '\033[38;5;87m',
        'option': '\033[38;5;118m',
        'exit': '\033[38;5;203m',
        'prompt': '\033[38;5;46m',
        'input': '\033[38;5;226m'
    }
    reset_color = '\033[0m'
    
    print(f"{menu_colors['title']}Chọn công cụ:{reset_color}")
    print(f"{menu_colors['option']}[1] Trao đổi sub{reset_color}")
    print(f"{menu_colors['option']}[2] Tương tác chéo{reset_color}")
    print(f"{menu_colors['exit']}[0] Thoát{reset_color}")
    print()
    
    print(f"{menu_colors['prompt']}~(!) ➤ {menu_colors['input']}Nhấp Số 8===D: {reset_color}", end="")

def execute_tool_in_thread(script_content, result_queue, timeout=300):
    """Run tool in separate thread with timeout and isolated context"""
    Fore, Back, Style = init_colors()
    exec_colors = {
        'loading': '\033[38;5;214m',
        'success': '\033[38;5;82m',
        'info': '\033[38;5;159m',
        'error': '\033[38;5;196m'
    }
    reset_color = '\033[0m'
    
    print(f"{exec_colors['loading']}🚀 Đang khởi chạy ...{reset_color}")
    print(f"{exec_colors['info']} Tool được cung cấp bởi TrumSubVip.site{reset_color}")
    print(f"{exec_colors['info']}Nhấn Ctrl+C để dừng tool hoặc đợi tối đa {timeout} giây.{reset_color}")
    
    def run_tool():
        try:
            # Create isolated globals for the tool
            tool_globals = {'__name__': '__main__'}
            # Redirect print to avoid cluttering main console
            tool_globals['print'] = lambda *args, **kwargs: sys.stdout.write(f"{' '.join(map(str, args))}\n")
            exec(script_content, tool_globals)
            result_queue.put(("success", f" completed successfully"))
        except KeyboardInterrupt:
            result_queue.put(("interrupt", f"stopped by user"))
        except Exception as e:
            result_queue.put(("error", f"Lỗi khi chạy : {str(e)}"))
    
    # Start tool in a new thread
    tool_thread = threading.Thread(target=run_tool, daemon=True)
    tool_thread.start()
    
    # Wait for thread to finish or timeout
    try:
        tool_thread.join(timeout)
        if tool_thread.is_alive():
            result_queue.put(("timeout", f" timed out after {timeout} seconds"))
    except KeyboardInterrupt:
        result_queue.put(("interrupt", f"stopped by user"))
    
    # Get result from queue
    try:
        status, message = result_queue.get_nowait()
        if status == "success":
            print(f"{exec_colors['success']}✅ {message}{reset_color}")
        elif status == "interrupt":
            print(f"{exec_colors['info']}⏹ {message}{reset_color}")
        else:
            print(f"{exec_colors['error']}✗ {message}{reset_color}")
    except queue.Empty:
        print(f"{exec_colors['error']}✗ No result from{reset_color}")
    
    print(f"{exec_colors['info']}Nhấn Enter để quay lại menu.{reset_color}")
    try:
        input()
    except KeyboardInterrupt:
        pass

def fetch_and_run_tool(url):
    """Fetch tool script and run in thread with timeout"""
    Fore, Back, _ = init_colors()
    exec_colors = {
        'error': '\033[38;5;196m',
        'loading': '\033[38;5;214m'
    }
    reset_color = '\033[0m'
    
    try:
        print(f"{exec_colors['loading']}Đang tải ..{reset_color}")
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            result_queue = queue.Queue()
            execute_tool_in_thread(response.text, result_queue)
            return True
        else:
            print(f"{exec_colors['error']}✗ Lỗi kết nối, vui lòng thử lại{reset_color}")
            return False
    except:
        print(f"{exec_colors['error']}✗ Lỗi kết nối, vui lòng thử lại{reset_color}")
        return False

def activate_key():
    Fore, Back, Style = init_colors()
    show_logo()
    show_user_info()
    
    bypass_link, _ = get_bypass_link()
    print(f"\n{Fore.YELLOW}--- Vượt link để lấy key nhé! ---{Fore.RESET}")
    print(f"{Fore.CYAN}Link vượt hôm nay: {Fore.YELLOW}{bypass_link}{Fore.RESET}")
    print()
    
    while True:
        print(f"{Fore.CYAN}Nhập key để kích hoạt (Enter để thử lại, 'exit' để thoát):")
        key = input(f"{Fore.YELLOW}>>> {Fore.RESET}").strip()
        
        if key.lower() == 'exit':
            return False
        
        if not key:
            continue
            
        try:
            valid, key_entry, error_msg = check_key_with_server(key)
            if valid and key_entry:
                if mark_key_as_used(key_entry['key']):
                    if save_key_data(key_entry):
                        print(f"{Fore.GREEN}Kích hoạt key thành công!{Fore.RESET}")
                        return True
                    else:
                        print(f"{Fore.RED}Lỗi khi lưu key!{Fore.RESET}")
                else:
                    print(f"{Fore.RED}Lỗi khi kích hoạt key!{Fore.RESET}")
            else:
                print(f"{Fore.RED}{error_msg}{Fore.RESET}")
        except:
            print(f"{Fore.RED}Lỗi kết nối, vui lòng thử lại{Fore.RESET}")
        
        print()

def get_remaining_time(server_expires_at, local_expires_at):
    try:
        server_time = datetime.fromisoformat(server_expires_at.replace('Z', '+00:00'))
        local_time = datetime.fromisoformat(local_expires_at.replace('Z', '+00:00'))
        
        remaining = server_time - local_time
        
        if remaining.total_seconds() <= 0:
            return "Đã hết hạn"
            
        days = remaining.days
        hours = int((remaining.seconds % 86400) / 3600)
        minutes = int((remaining.seconds % 3600) / 60)
        
        if days > 0:
            return f"{days} ngày {hours} giờ {minutes} phút"
        elif hours > 0:
            return f"{hours} giờ {minutes} phút"
        else:
            return f"{minutes} phút"
            
    except:
        return "Không xác định"

def check_key_validity():
    key_data = load_key_data()
    if not key_data:
        return False, "Chưa có key"
        
    if key_data['key'] == DEFAULT_KEY:
        return True, {
            'key': DEFAULT_KEY,
            'id': 'default',
            'machine_id': get_machine_id(),
            'remaining_time': 'Không giới hạn'
        }
    
    try:
        response = requests.get(f'{API_KEY_SERVER}/data', headers=HEADERS, timeout=10)
        if response.status_code == 200:
            keys_data = response.json()
            key_entry = next((k for k in keys_data if k.get('key') == key_data['key']), None)
            
            if not key_entry:
                return False, "Key không hợp lệ"
            if key_entry.get('machine_id') != get_machine_id():
                return False, "Key không thuộc về thiết bị này"
            try:
                expires_at = datetime.fromisoformat(key_entry['expires_at'].replace('Z', '+00:00'))
                now = datetime.now(expires_at.tzinfo)
                
                if now > expires_at:
                    if delete_key_from_server(key_entry['key']):
                        return False, "Key đã hết hạn"
                    return False, "Key đã hết hạn"
                    
                remaining = expires_at - now
                days = remaining.days
                hours = int((remaining.seconds % 86400) / 3600)
                minutes = int((remaining.seconds % 3600) / 60)
                
                if days > 0:
                    key_entry['remaining_time'] = f"{days} ngày {hours} giờ {minutes} phút"
                elif hours > 0:
                    key_entry['remaining_time'] = f"{hours} giờ {minutes} phút"
                else:
                    key_entry['remaining_time'] = f"{minutes} phút"
                    
                return True, key_entry
                
            except:
                return False, "Lỗi kiểm tra thời hạn"
            
    except:
        return False, "Lỗi kết nối, vui lòng thử lại"

def main():
    try:
        Fore, Back, Style = init_colors()
        install_required_packages()
        notifs = get_notifications()
        key_data = load_key_data()
        if key_data:
            valid, _, error_msg = check_key_with_server(key_data['key'])
            if not valid:
                print(f"Key invalid: {error_msg}")
                os.remove(os.path.join(os.path.dirname(__file__), 'key.txt'))
                if not activate_key():
                    print("Key activation failed")
                    sys.exit(1)
        else:
            print("No key found, activating new key...")
            if not activate_key():
                print("Key activation failed")
                sys.exit(1)

        print("Initialization complete, starting main loop...")
        
        while True:
            show_logo()
            show_user_info()
            show_notifications()
            show_warning()
            # show_tools()
            show_menu()
            
            choice = input().strip()
            
            if choice == "1":
                url = "https://raw.githubusercontent.com/hoangquyet1404/ttc-tds/master/tds/tpy.py"
                fetch_and_run_tool(url)
            
            elif choice == "2":
                url = "https://raw.githubusercontent.com/hoangquyet1404/ttc-tds/master/ttc/ttc.py"
                fetch_and_run_tool(url)
            
            elif choice == "0":
                print(f"{Fore.GREEN}✅ Cảm ơn bạn đã sử dụng H-Tool!{Fore.RESET}")
                print(f"{Fore.CYAN}🌐 Ghé thăm TrumSubVip.site để mua thêm dịch vụ!{Fore.RESET}")
                print(f"{Fore.MAGENTA}👋 Hẹn gặp lại!{Fore.RESET}")
                sys.exit()
            
            else:
                print(f"{Fore.RED}❌ Lựa chọn không hợp lệ!{Fore.RESET}")
                sleep(2)
    except:
        print("Critical error: Lỗi kết nối, vui lòng thử lại")
        raise

if __name__ == "__main__":
    main()