# WordPress XML-RPC Bruteforce Tool

A tool designed to test WordPress sites for XML-RPC vulnerabilities by attempting to brute force user credentials through the XML-RPC interface.

## Description

This tool tests WordPress installations for XML-RPC authentication vulnerabilities. It can perform standard brute force attacks or use system.multicall to test multiple passwords in a single request, potentially bypassing some rate-limiting protections.

## Features

- Checks if XML-RPC is enabled on the target WordPress site
- Tests single username/password or lists of credentials
- Supports system.multicall for faster testing and potential rate limit bypass
- Configurable delay between requests
- Colorized output for better readability

## Installation

```bash
git clone https://github.com/AnkhCorp/xmlrpc-brute.git
cd xmlrpc-brute
pip install -r requirements.txt
```

## Usage

```bash
python3 xmlrpc-brute.py -t <target_url> -u <username> -P <password_list>
```

### Options

| Option | Long Form | Description |
|--------|-----------|-------------|
| `-t` | `--target` | Target URL (e.g., https://example.com/) |
| `-u` | `--username` | Single username to test |
| `-U` | `--userlist` | File containing list of usernames |
| `-p` | `--password` | Single password to test |
| `-P` | `--passlist` | File containing list of passwords |
| `-d` | `--delay` | Delay between requests in seconds (default: 1.0) |
| `-m` | `--multicall` | Use system.multicall to test multiple passwords at once |
| `-b` | `--batch` | Batch size for multicall (default: 3) |
| `--max-passwords` | | Maximum number of passwords to test (0 = no limit) |

### Examples

Test a single username with a password list:
```bash
python3 xmlrpc-brute.py -t http://example.com/wordpress -u admin -P wordlist.txt
```

Test multiple usernames with a password list using multicall:
```bash
python3 xmlrpc-brute.py -t http://example.com/wordpress -U userlist.txt -P wordlist.txt -m
```

Test with a 2-second delay between requests and limit to 1000 passwords:
```bash
python3 xmlrpc-brute.py -t http://example.com/wordpress -u admin -P rockyou.txt -d 2 --max-passwords 1000
```

## Legal Disclaimer

This tool is provided for educational and testing purposes only. Only use this tool on systems you own or have explicit permission to test. Unauthorized access to computer systems is illegal and unethical.

## License

This project is licensed under the MIT License - see the LICENSE file for details.