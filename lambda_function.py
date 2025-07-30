import json
import boto3
import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
import os
from utils.scraper_utils import LeverScraperUtils

class LeverJobScraper:
    def __init__(self):
        self.base_url = "https://jobs.lever.co"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # 澳大利亚关键词用于识别澳大利亚公司
        self.australian_keywords = [
            'australia', 'australian', 'sydney', 'melbourne', 'brisbane', 
            'perth', 'adelaide', 'canberra', 'darwin', 'hobart',
            'nsw', 'vic', 'qld', 'wa', 'sa', 'tas', 'nt', 'act'
        ]
        
        # 已知的澳大利亚公司列表
        self.known_australian_companies = [
            'atlassian', 'canva', 'afterpay', 'xero', 'wisetech', 
            'seek', 'carsales', 'realestate', 'domain', 'rea-group',
            'commonwealth-bank', 'anz', 'westpac', 'nab', 'macquarie',
            'telstra', 'optus', 'tpg', 'woolworths', 'coles',
            'bhp', 'rio-tinto', 'fortescue', 'woodside', 'origin',
            'qantas', 'virgin-australia', 'jetstar', 'flight-centre',
            'medibank', 'bupa', 'nib', 'ahm', 'hcf',
            'australian-super', 'rest', 'hostplus', 'united-super',
            'airtasker', 'hipages', 'service-seeking', 'oneflare',
            'prospa', 'societyone', 'ratesetter', 'money-me',
            'zip', 'humm', 'laybuy', 'klarna', 'affirm',
            'culture-amp', 'safetyculture', 'enboard', 'deputy',
            'myob', 'reckon', 'sage', 'intuit', 'wave',
            'square', 'stripe', 'paypal', 'adyen', 'braintree'
        ]

    def is_australian_company(self, company_name, company_path):
        """判断是否为澳大利亚公司"""
        if not company_name:
            return False
            
        company_lower = company_name.lower()
        company_path_lower = company_path.lower() if company_path else ""
        
        # 首先检查已知的澳大利亚公司列表
        for known_company in self.known_australian_companies:
            if known_company in company_lower or known_company in company_path_lower:
                return True
        
        # 然后检查关键词
        for keyword in self.australian_keywords:
            if keyword in company_lower or keyword in company_path_lower:
                return True
                
        return False

    def get_company_jobs(self, company_path):
        """获取指定公司的所有职位"""
        jobs = []
        try:
            url = f"{self.base_url}/{company_path}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            job_links = soup.find_all('a', href=re.compile(r'/job/'))
            
            for link in job_links:
                job_url = link.get('href')
                if job_url.startswith('/'):
                    job_url = f"{self.base_url}{job_url}"
                
                job_data = self.get_job_details(job_url, company_path)
                if job_data:
                    jobs.append(job_data)
                    time.sleep(1)  # 礼貌延迟
                    
        except Exception as e:
            print(f"获取公司 {company_path} 职位时出错: {str(e)}")
            
        return jobs

    def get_job_details(self, job_url, company_path):
        """获取职位详细信息"""
        try:
            response = self.session.get(job_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取职位信息
            job_title = self.extract_text(soup.find('h1')) or self.extract_text(soup.find('h2'))
            company_name = self.extract_text(soup.find('div', class_='company-name')) or company_path
            location = self.extract_text(soup.find('div', class_='location')) or self.extract_text(soup.find('span', class_='location'))
            
            # 提取部门信息
            department = self.extract_text(soup.find('div', class_='department')) or self.extract_text(soup.find('span', class_='department'))
            team = self.extract_text(soup.find('div', class_='team')) or self.extract_text(soup.find('span', class_='team'))
            
            # 提取职位描述
            description_elem = soup.find('div', class_='description') or soup.find('div', class_='content') or soup.find('div', class_='job-description')
            description = self.extract_text(description_elem) if description_elem else ""
            
            # 提取其他信息
            requirements = self.extract_text(soup.find('div', class_='requirements'))
            benefits = self.extract_text(soup.find('div', class_='benefits'))
            
            return {
                'job_title': job_title,
                'company_name': company_name,
                'company_path': company_path,
                'location': location,
                'department': department,
                'team': team,
                'description': description,
                'requirements': requirements,
                'benefits': benefits,
                'job_url': job_url,
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"获取职位详情时出错 {job_url}: {str(e)}")
            return None

    def extract_text(self, element):
        """安全提取文本内容"""
        if element:
            return element.get_text(strip=True)
        return ""

    def discover_companies(self):
        """发现所有公司"""
        companies = []
        
        # 首先添加已知的澳大利亚公司
        companies.extend(self.known_australian_companies)
        
        try:
            # 从主页获取公司列表
            response = self.session.get(self.base_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            company_links = soup.find_all('a', href=re.compile(r'^/[^/]+$'))
            
            for link in company_links:
                company_path = link.get('href', '').strip('/')
                if company_path and company_path not in companies:
                    companies.append(company_path)
                    
        except Exception as e:
            print(f"发现公司时出错: {str(e)}")
            
        return list(set(companies))  # 去重

def save_to_s3(data, bucket_name, key):
    """保存数据到S3作为数据湖"""
    try:
        s3_client = boto3.client('s3')
        
        # 将数据转换为JSON格式
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        
        # 上传到S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=json_data,
            ContentType='application/json'
        )
        
        print(f"数据已保存到S3: s3://{bucket_name}/{key}")
        return True
        
    except Exception as e:
        print(f"保存到S3时出错: {str(e)}")
        return False

def call_backend_api(job_data, api_endpoint):
    """调用后端API将数据发送到MongoDB"""
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {os.environ.get("API_TOKEN", "")}'
        }
        
        # 准备发送到API的数据
        api_payload = {
            'table': 'jobsprofiles',
            'data': job_data
        }
        
        response = requests.post(
            api_endpoint,
            json=api_payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"数据已成功发送到后端API: {len(job_data)} 条记录")
            return True
        else:
            print(f"API调用失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"调用后端API时出错: {str(e)}")
        return False

def lambda_handler(event, context):
    """Lambda函数主处理器"""
    try:
        # 获取环境变量
        s3_bucket = os.environ.get('S3_BUCKET_NAME', 'lever-jobs-data')
        api_endpoint = os.environ.get('BACKEND_API_ENDPOINT', '')
        
        # 初始化爬虫
        scraper = LeverJobScraper()
        
        # 发现公司
        companies = scraper.discover_companies()
        print(f"发现 {len(companies)} 家公司")
        
        # 限制处理的公司数量以避免超时
        companies = companies[:15]
        
        all_jobs = []
        australian_jobs = []
        
        # 爬取每个公司的职位
        for i, company in enumerate(companies):
            print(f"处理公司 {i+1}/{len(companies)}: {company}")
            
            jobs = scraper.get_company_jobs(company)
            all_jobs.extend(jobs)
            
            # 过滤澳大利亚职位
            for job in jobs:
                if scraper.is_australian_company(job.get('company_name', ''), job.get('company_path', '')):
                    australian_jobs.append(job)
            
            time.sleep(2)  # 礼貌延迟
        
        print(f"总共爬取到 {len(all_jobs)} 个职位，其中 {len(australian_jobs)} 个澳大利亚职位")
        
        # 保存原始数据到S3（数据湖）
        if all_jobs:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            raw_data_key = f"raw_data/jobs_{timestamp}.json"
            
            raw_data = {
                'scraped_at': datetime.now().isoformat(),
                'total_jobs': len(all_jobs),
                'australian_jobs': len(australian_jobs),
                'companies_processed': companies,
                'jobs': all_jobs
            }
            
            save_to_s3(raw_data, s3_bucket, raw_data_key)
        
        # 保存澳大利亚职位数据到S3
        if australian_jobs:
            australian_data_key = f"australian_jobs/jobs_{timestamp}.json"
            australian_data = {
                'scraped_at': datetime.now().isoformat(),
                'total_jobs': len(australian_jobs),
                'jobs': australian_jobs
            }
            
            save_to_s3(australian_data, s3_bucket, australian_data_key)
        
        # 调用后端API将数据发送到MongoDB
        if australian_jobs and api_endpoint:
            call_backend_api(australian_jobs, api_endpoint)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': '数据爬取完成',
                'total_jobs': len(all_jobs),
                'australian_jobs': len(australian_jobs),
                's3_raw_data_key': raw_data_key if all_jobs else None,
                's3_australian_data_key': australian_data_key if australian_jobs else None
            })
        }
        
    except Exception as e:
        print(f"Lambda函数执行出错: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        } 