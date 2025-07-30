"""
爬虫工具函数
"""
import requests
from bs4 import BeautifulSoup
import re
import time
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class LeverScraperUtils:
    """Lever网站爬虫工具类"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def get_company_list_from_api(self) -> List[str]:
        """从Lever API获取公司列表"""
        companies = []
        try:
            # Lever可能使用API端点来获取公司列表
            api_url = "https://jobs.lever.co/api/companies"
            response = self.session.get(api_url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                companies = [company.get('slug', '') for company in data if company.get('slug')]
            else:
                # 如果API不可用，尝试从主页解析
                companies = self.get_companies_from_homepage()
                
        except Exception as e:
            logger.error(f"从API获取公司列表失败: {str(e)}")
            companies = self.get_companies_from_homepage()
            
        return companies
    
    def get_companies_from_homepage(self) -> List[str]:
        """从主页解析公司列表"""
        companies = []
        try:
            response = self.session.get("https://jobs.lever.co", timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 查找公司链接 - 根据Lever的实际网站结构调整
            company_links = soup.find_all('a', href=re.compile(r'^/[^/]+$'))
            
            for link in company_links:
                href = link.get('href', '')
                if href and href != '/':
                    company_slug = href.strip('/')
                    if company_slug and len(company_slug) > 1:
                        companies.append(company_slug)
                        
        except Exception as e:
            logger.error(f"从主页获取公司列表失败: {str(e)}")
            
        return list(set(companies))  # 去重
    
    def get_jobs_from_company_page(self, company_slug: str) -> List[Dict]:
        """从公司页面获取职位列表"""
        jobs = []
        try:
            url = f"https://jobs.lever.co/{company_slug}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 查找职位链接
            job_links = soup.find_all('a', href=re.compile(r'/job/'))
            
            for link in job_links:
                job_url = link.get('href')
                if job_url:
                    if job_url.startswith('/'):
                        job_url = f"https://jobs.lever.co{job_url}"
                    
                    job_data = self.extract_job_data(job_url)
                    if job_data:
                        jobs.append(job_data)
                        
                    # 添加延迟避免被限制
                    time.sleep(0.5)
                    
        except Exception as e:
            logger.error(f"获取公司 {company_slug} 职位失败: {str(e)}")
            
        return jobs
    
    def extract_job_data(self, job_url: str) -> Optional[Dict]:
        """提取职位详细信息"""
        try:
            response = self.session.get(job_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取职位信息 - 根据Lever的实际HTML结构调整
            job_title = self.extract_text(soup.find('h2', class_='posting-headline')) or \
                       self.extract_text(soup.find('h1', class_='posting-headline')) or \
                       self.extract_text(soup.find('h1'))
            
            company_name = self.extract_text(soup.find('a', class_='company-link')) or \
                          self.extract_text(soup.find('div', class_='company-name'))
            
            location = self.extract_text(soup.find('div', class_='posting-categories')) or \
                      self.extract_text(soup.find('div', class_='location'))
            
            # 提取职位描述
            description_elements = soup.find_all('div', class_='section page-centered')
            description = ""
            for element in description_elements:
                description += self.extract_text(element) + "\n"
            
            # 提取其他信息
            department = self.extract_text(soup.find('div', class_='department'))
            team = self.extract_text(soup.find('div', class_='team'))
            
            if not job_title or not company_name:
                return None
            
            job_data = {
                'job_title': job_title,
                'company_name': company_name,
                'location': location,
                'department': department,
                'team': team,
                'description': description.strip(),
                'job_url': job_url,
                'scraped_at': time.time()
            }
            
            return job_data
            
        except Exception as e:
            logger.error(f"提取职位数据失败 {job_url}: {str(e)}")
            return None
    
    def extract_text(self, element) -> str:
        """安全提取文本内容"""
        if element:
            return element.get_text(strip=True)
        return ""
    
    def is_australian_job(self, job_data: Dict) -> bool:
        """判断是否为澳洲职位"""
        if not job_data:
            return False
            
        text_to_check = f"{job_data.get('company_name', '')} {job_data.get('location', '')} {job_data.get('description', '')}".lower()
        
        australian_keywords = [
            'australia', 'australian', 'sydney', 'melbourne', 'brisbane', 
            'perth', 'adelaide', 'canberra', 'darwin', 'hobart',
            'nsw', 'vic', 'qld', 'wa', 'sa', 'tas', 'nt', 'act',
            'australia', 'australian', 'sydney', 'melbourne', 'brisbane', 
            'perth', 'adelaide', 'canberra', 'darwin', 'hobart',
            'nsw', 'vic', 'qld', 'wa', 'sa', 'tas', 'nt', 'act'
        ]
        
        return any(keyword in text_to_check for keyword in australian_keywords) 