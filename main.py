import os
import sys
import json
import time
import hashlib
import random
import requests
import string
from datetime import datetime, timedelta
from time import sleep

# API Endpoints
API_TOKEN = "703371951353e080dde13a50207e2ff7c3fc31fe88f765c17fa11d9fd1046528"
API_YEUMONEY = "https://yeumoney.com/QL_api.php"
API_KEY_SERVER = "https://cnc.subhatde.id.vn/api"
API_KEY_PAGE = "http://sublikevip.site/key.html"
API_NOTIFICATIONS = "https://cnc.subhatde.id.vn/apis/thongbao"
DEFAULT_KEY = "joonwuydeptrai"

def install_required_packages():
    flag_file = os.path.join(os.path.dirname(__file__), '.packages_installed')
    if os.path.exists(flag_file):
        return
        
    packages = [
        'requests',
        'beautifulsoup4',
        'colorama'
    ]
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
        'prompt': '\033[38;5;46m',      # Xanh lá sáng
        'label': '\033[38;5;51m',       # Cyan sáng  
        'name': '\033[38;5;159m',       # Cyan nhạt
        'website': '\033[38;5;214m',    # Cam vàng
        'phone': '\033[38;5;196m',      # Đỏ sáng
        'link': '\033[38;5;141m'        # Tím hồng
    }
    reset_color = '\033[0m'
    
    print(f"{info_colors['prompt']}~[●] ➤ {info_colors['label']}Admin: {info_colors['name']}Trần Văn Quang Huy{reset_color}")
    print(f"{info_colors['prompt']}~[●] ➤ {info_colors['label']}Website Bán Sub Giá Rẻ: {info_colors['website']}trumsubvip.site{reset_color}")
    print(f"{info_colors['prompt']}~[●] ➤ {info_colors['label']}Zalo Admin: {info_colors['phone']}0372065607{reset_color}")
    print(f"{info_colors['prompt']}~[●] ➤ {info_colors['label']}Box Zalo Thông Báo: {info_colors['link']}https://zalo.me/g/dqacsy523{reset_color}")
    print()

def get_notifications():
    """Fetch notifications from API"""
    try:
        response = requests.get(API_NOTIFICATIONS, timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"Debug - Error fetching notifications: {str(e)}")
        return []

def show_notifications():
    """Show notifications from API"""
    Fore, Back, Style = init_colors()
    notif_colors = {
        'header': '\033[48;5;220m\033[30m',  # Nền vàng, chữ đen
        'prompt': '\033[38;5;82m',           # Xanh lá neon
        'date': '\033[38;5;87m',             # Cyan pastel
        'text': '\033[38;5;255m',            # Trắng sáng
        'error': '\033[38;5;203m'            # Hồng đỏ
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
    """Get unique machine identifier"""
    machine_id = ""
    if os.name == 'nt':  # Windows
        import wmi
        c = wmi.WMI()
        system_info = c.Win32_ComputerSystemProduct()[0]
        machine_id = system_info.UUID
    else:  # Linux/Mac
        with open('/etc/machine-id', 'r') as f:
            machine_id = f.read().strip()
    return hashlib.md5(machine_id.encode()).hexdigest()

def load_key_data():
    """Load saved key data"""
    key_file = os.path.join(os.path.dirname(__file__), 'key.txt')
    if os.path.exists(key_file):
        try:
            with open(key_file, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

def save_key_data(key_data):
    """Save key data with correct ID format"""
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
    except Exception as e:
        print(f"Debug - Error saving key: {str(e)}")
        return False

def generate_random_key():
    """Generate random 6-digit key"""
    return ''.join(random.choices(string.digits, k=6))

def get_final_redirect_url(url):
    """Follow redirects and get final URL"""
    try:
        response = requests.get(url, allow_redirects=False)
        if response.status_code == 302:
            return response.headers['Location']
    except:
        pass
    return None

def generate_and_save_key():
    """Generate random key and save to server"""
    key = ''.join(random.choices(string.digits, k=6))
    try:
        data = {
            'key': key,
            'machine_id': get_machine_id(),
            'device_info': os.environ.get('COMPUTERNAME', 'Unknown Device'),
            'used': False,
            'expires_at': (datetime.now() + timedelta(days=1)).isoformat()
        }
        
        response = requests.post(f'{API_KEY_SERVER}/data', json=data)
        if response.status_code == 200:
            return response.json()['data']
        return None
    except:
        return None

def get_bypass_link():
    """Get daily bypass link with generated key"""
    try:
        # Generate new key
        key = generate_random_key()
        
        # Use link4m.co API for URL shortening
        target_url = f"http://sublikevip.site/index.html?key={key}"
        shorten_api = f"https://link4m.co/api-shorten/v2?api=672ed4b6da03836a1b72eb7a&url={target_url}"
        
        # Get shortened URL
        shorten_response = requests.get(shorten_api, timeout=10)
        if shorten_response.status_code == 200:
            shorten_data = shorten_response.json()
            if shorten_data.get('status') == 'success':
                bypass_link = shorten_data['shortenedUrl']
                
                # Save key to server
                data = {
                    'key': key,
                    'machine_id': get_machine_id(),
                    'device_info': os.environ.get('COMPUTERNAME', 'Unknown Device'),
                    'used': False,
                    'expires_at': (datetime.now() + timedelta(days=1)).isoformat()
                }
                
                server_response = requests.post(f'{API_KEY_SERVER}/data', json=data, timeout=10)
                if server_response.status_code != 200:
                    return "Lỗi khi kết nối máy chủ", None
                    
                return bypass_link, {'id': server_response.json().get('data', {}).get('id')}
                
        return "Không thể tạo link vượt", None
        
    except requests.Timeout:
        return "Máy chủ không phản hồi, vui lòng thử lại", None
    except requests.ConnectionError: 
        return "Không thể kết nối đến máy chủ", None
    except Exception as e:
        return f"Lỗi: {str(e)}", None

def check_key_with_server(key):
    """Check key validity with API server"""
    # Check default key first
    if key == DEFAULT_KEY:
        return True, {
            'key': DEFAULT_KEY,
            'machine_id': get_machine_id(),
            'id': 'default',
            'expires_at': '2099-12-31T23:59:59.999Z'  # Basically never expires
        }, None
        
    try:
        response = requests.get(f'{API_KEY_SERVER}/data', timeout=10)
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
            
    except requests.Timeout:
        return False, None, "Máy chủ không phản hồi"
    except Exception as e:
        print(f"Debug - Error checking key: {str(e)}")
        return False, None, f"Lỗi: {str(e)}"

def mark_key_as_used(key_id):
    """Mark key as used via PUT request"""
    # Skip server check for default key
    if key_id == DEFAULT_KEY:
        return True
        
    try:
        get_response = requests.get(f'{API_KEY_SERVER}/data', timeout=10)
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
                response = requests.put(f'{API_KEY_SERVER}/data/{key_entry["key"]}', json=data)
                # print(f"Debug - PUT Response: {response.status_code}") 
                return response.status_code == 200
                
        return False
    except Exception as e:
        # print(f"Debug - Error marking key as used: {str(e)}")  
        return False

def delete_key_from_server(key):
    """Delete expired key from server"""
    try:
        response = requests.delete(f'{API_KEY_SERVER}/data/{key}', timeout=10)
        return response.status_code == 200
    except Exception as e:
        # print(f"Debug - Error deleting key: {str(e)}")
        return False

def show_warning():
    """Show key status with safe attribute access"""
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
        'title': '\033[38;5;220m',      # Vàng đậm
        'prompt': '\033[38;5;40m',      # Xanh lá sáng
        'text': '\033[38;5;231m',       # Trắng
        'border': '\033[38;5;245m'      # Xám sáng
    }
    reset_color = '\033[0m'
    

def show_menu():
    Fore, Back, Style = init_colors()
    menu_colors = {
        'title': '\033[38;5;87m',       # Cyan nhạt
        'option': '\033[38;5;118m',     # Xanh lá lime
        'exit': '\033[38;5;203m',       # Hồng đỏ
        'prompt': '\033[38;5;46m',      # Xanh lá neon
        'input': '\033[38;5;226m'       # Vàng sáng
    }
    reset_color = '\033[0m'
    
    print(f"{menu_colors['title']}Chọn công cụ:{reset_color}")
    print(f"{menu_colors['option']}[1] Trao đổi sub{reset_color}")
    print(f"{menu_colors['option']}[2] Tương tác chéo{reset_color}")
    print(f"{menu_colors['exit']}[0] Thoát{reset_color}")
    print()
    
    print(f"{menu_colors['prompt']}~(!) ➤ {menu_colors['input']}Nhấp Số 8===D: {reset_color}", end="")

def execute_tool(url):
    Fore, Back, Style = init_colors()
    exec_colors = {
        'loading': '\033[38;5;214m',    # Cam
        'success': '\033[38;5;82m',     # Xanh lá neon
        'info': '\033[38;5;159m',       # Cyan nhạt
        'error': '\033[38;5;196m'       # Đỏ sáng
    }
    reset_color = '\033[0m'
    
    try:
        import requests
        response = requests.get(url)
        if response.status_code == 200:
            print(f"{exec_colors['info']} Tool được cung cấp bởi TrumSubVip.site{reset_color}")
            # Create a global scope dictionary
            global_scope = {}
            exec(response.text, global_scope)
            if 'main' in global_scope:
                global_scope['main']()
            return True
        else:
            print(f"{exec_colors['error']}✗ Lỗi tải tool! Status code: {response.status_code}{reset_color}")
            return False
    except Exception as e:
        print(f"{exec_colors['error']}✗ Lỗi: {str(e)}{reset_color}")
        return False

def activate_key():
    """Activate new key"""
    Fore, Back, Style = init_colors()
    show_logo()
    show_user_info()
    
    bypass_link, _ = get_bypass_link()
    print(f"{Fore.CYAN}Link vượt hôm nay: {Fore.YELLOW}{bypass_link}{Fore.RESET}")
    print()
    
    while True:
        print(f"{Fore.CYAN}Nhập key để kích hoạt tool (nhấn Enter để thử lại, nhập 'exit' để thoát):")
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
        except Exception as e:
            print(f"{Fore.RED}Lỗi: Vui lòng thử lại{Fore.RESET}")
            print(f"Debug - Error: {str(e)}")
        
        print()

def get_remaining_time(server_expires_at, local_expires_at):
    """Calculate time between server and local expiration"""
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
            
    except Exception as e:
        print(f"Debug - Time parse error: {str(e)}")
        return "Không xác định"

def check_key_validity():
    """Verify saved key against server"""
    key_data = load_key_data()
    if not key_data:
        return False, "Chưa có key"
        
    # Special handling for default key
    if key_data['key'] == DEFAULT_KEY:
        return True, {
            'key': DEFAULT_KEY,
            'id': 'default',
            'machine_id': get_machine_id(),
            'remaining_time': 'Không giới hạn'
        }
    
    try:
        response = requests.get(f'{API_KEY_SERVER}/data', timeout=10)
        if response.status_code == 200:
            keys_data = response.json()
            key_entry = next((k for k in keys_data 
                if k.get('key') == key_data['key']), None)
            
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
                
            except Exception as e:
                print(f"Debug - Time parse error: {str(e)}")
                return False, "Lỗi kiểm tra thời hạn"
            
    except Exception as e:
        return False, f"Lỗi kết nối: {str(e)}"

def main():
    """Main entry point with debug logging"""
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
            show_tools()
            show_menu()
            
            choice = input().strip()
            
            if choice == "1":
                # print(f"{main_colors['launch']}🚀 Khởi chạy Tool Trao Đổi Sub - TrumSubVip...{reset_color}")
                url = "https://raw.githubusercontent.com/hoangquyet1404/ttc/refs/heads/master/tpy.py"
                execute_tool(url)
            
            elif choice == "2":
                # print(f"{main_colors['launch']}⚡ Khởi chạy Tool Tương Tác Chéo - TrumSubVip...{reset_color}")
                url = "https://raw.githubusercontent.com/hoangquyet1404/ttc/refs/heads/master/ttc.py"
                execute_tool(url)
            
            elif choice == "0":
                print(f"{main_colors['success']}✅ Cảm ơn bạn đã sử dụng H-Tool!{reset_color}")
                print(f"{main_colors['info']}🌐 Ghé thăm TrumSubVip.site để mua thêm dịch vụ!{reset_color}")
                print(f"{main_colors['goodbye']}👋 Hẹn gặp lại!{reset_color}")
                sys.exit()
            
            else:
                print(f"{main_colors['error']}❌ Lựa chọn không hợp lệ!{reset_color}")
                sleep(2)
    except Exception as e:
        print(f"Critical error: {str(e)}")
        print("Debug info:")
        print(f"Python version: {sys.version}")
        print(f"Working directory: {os.getcwd()}")
        raise

if __name__ == "__main__":
    main()