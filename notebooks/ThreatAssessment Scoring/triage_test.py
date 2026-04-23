import pandas as pd, requests, warnings, time
warnings.filterwarnings('ignore')

HEADERS = {'User-Agent': 'HTOC-ThreatIntel-Triage/1.0'}

df = pd.read_excel(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\Threat_Assessment_Scores.xlsx', sheet_name='PRISM Scores')
test_ips = df[df['Indicator Type'] == 'Address']['Indicator'].head(10).tolist()
print('Test IPs:', test_ips)

payload = [{'query': ip, 'fields': 'status,country,isp,org,as,hosting,proxy,query'} for ip in test_ips]
resp = requests.post('http://ip-api.com/batch', json=payload, headers=HEADERS, timeout=15)
print('Status:', resp.status_code)
for r in resp.json():
    line = "  {:<20} | {:<35} | proxy={} | hosting={} | country={}".format(
        r.get('query','?'), r.get('isp','?'), r.get('proxy'), r.get('hosting'), r.get('country')
    )
    print(line)
