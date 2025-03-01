import os
import requests
from prettytable import PrettyTable
import json

def check_firecrawl_credits():
    api_keys_str = os.getenv("FIRECRAWL_API_KEY", "")
    
    if not api_keys_str:
        print("No Firecrawl API keys found in environment variables.")
        return
    
    api_keys = api_keys_str.split(";")
    
    table = PrettyTable()
    table.field_names = ["Key ID", "API Key (masked)", "Remaining Credits", "Status"]
    
    for idx, api_key in enumerate(api_keys):
        if not api_key.strip():
            continue
        
        masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
        
        try:
            response = requests.get(
                "https://api.firecrawl.dev/v1/team/credit-usage",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get("success"):
                remaining_credits = response_data.get("data", {}).get("remaining_credits", "N/A")
                status = "OK"
            else:
                remaining_credits = "Error"
                status = f"Failed: {response.status_code} - {response_data.get('message', 'Unknown error')}"
        
        except requests.RequestException as e:
            remaining_credits = "Error"
            status = f"Request failed: {str(e)}"
        except json.JSONDecodeError:
            remaining_credits = "Error"
            status = "Invalid JSON response"
        except Exception as e:
            remaining_credits = "Error"
            status = f"Unexpected error: {str(e)}"
        
        table.add_row([idx + 1, masked_key, remaining_credits, status])
    
    print("\n=== Firecrawl API Credit Usage ===")
    print(table)
    print(f"Total API keys checked: {len(api_keys)}")

if __name__ == "__main__":
    check_firecrawl_credits()
