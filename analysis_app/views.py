# analysis_app/views.py

from django.shortcuts import render
from django.http import JsonResponse
import requests
from bs4 import BeautifulSoup
import json

# মূল পেজটি রেন্ডার করার জন্য
def index(request):
    return render(request, 'analysis_app/index.html')

# ওয়েব স্ক্র্যাপিং এর জন্য ভিউ
def scrape_data_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            url = data.get('url')

            if not url:
                return JsonResponse({'error': 'URL পাওয়া যায়নি'}, status=400)

            # ওয়েবসাইট ব্লক করা এড়ানোর জন্য একটি বাস্তবসম্মত User-Agent ব্যবহার করা হচ্ছে
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status() # কোনো HTTP error থাকলে exception দেখাবে

            # HTML পার্স করা হচ্ছে
            soup = BeautifulSoup(response.text, 'html.parser')

            # সবচেয়ে বড় টেবিলটি খুঁজে বের করা হচ্ছে
            tables = soup.find_all('table')
            if not tables:
                return JsonResponse({'error': 'এই পেজে কোনো টেবিল পাওয়া যায়নি'}, status=400)

            largest_table = max(tables, key=lambda table: len(table.find_all('tr')))

            # টেবিলের হেডার ও ডেটা বের করা হচ্ছে
            headers = [th.get_text(strip=True).replace('[edit]', '') for th in largest_table.find_all('th')]
            scraped_data = []
            
            # tbody আছে কিনা তা পরীক্ষা করা হচ্ছে
            table_body = largest_table.find('tbody')
            if not table_body:
                table_body = largest_table # যদি tbody ট্যাগ না থাকে

            for row in table_body.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) > 0 and len(cells) >= len(headers):
                    row_data = {headers[i]: cell.get_text(strip=True).replace('[edit]', '') for i, cell in enumerate(cells) if i < len(headers)}
                    if any(row_data.values()): # খালি সারি বাদ দেওয়া হচ্ছে
                        scraped_data.append(row_data)

            if not scraped_data:
                # যদি হেডারগুলো প্রথম সারিতে 'td' হিসেবে থাকে
                if not headers and largest_table.find_all('tr'):
                    header_row = largest_table.find_all('tr')[0]
                    headers = [cell.get_text(strip=True) for cell in header_row.find_all('td')]
                    data_rows = largest_table.find_all('tr')[1:]
                    for row in data_rows:
                        cells = row.find_all('td')
                        row_data = {headers[i]: cell.get_text(strip=True) for i, cell in enumerate(cells) if i < len(headers)}
                        if any(row_data.values()):
                            scraped_data.append(row_data)

            if not scraped_data:
                 return JsonResponse({'error': 'টেবিল থেকে ডেটা বের করা সম্ভব হয়নি। টেবিলের গঠন ভিন্ন হতে পারে।'}, status=400)


            return JsonResponse({'data': scraped_data, 'headers': headers})

        except requests.exceptions.HTTPError as e:
            return JsonResponse({'error': f'স্ক্রেপিং ব্যর্থ হয়েছে: {e}'}, status=e.response.status_code)
        except requests.exceptions.RequestException as e:
            return JsonResponse({'error': f'নেটওয়ার্ক সমস্যা: {e}'}, status=500)
        except Exception as e:
            return JsonResponse({'error': f'একটি অপ্রত্যাশিত সমস্যা হয়েছে: {e}'}, status=500)

    return JsonResponse({'error': 'শুধুমাত্র POST অনুরোধ গ্রহণযোগ্য'}, status=405)
