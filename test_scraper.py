#!/usr/bin/env python3
"""
本地测试脚本 - 测试Lever爬虫功能
"""

import sys
import os
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.scraper_utils import LeverScraperUtils

def test_scraper():
    """测试爬虫功能"""
    print("🧪 开始测试Lever爬虫...")
    
    # 初始化爬虫工具
    scraper = LeverScraperUtils()
    
    # 测试获取公司列表
    print("📋 测试获取公司列表...")
    companies = scraper.get_company_list_from_api()
    print(f"发现 {len(companies)} 个公司")
    
    if companies:
        # 测试前3个公司
        test_companies = companies[:3]
        print(f"测试公司: {test_companies}")
        
        all_jobs = []
        
        for company in test_companies:
            print(f"\n🏢 测试公司: {company}")
            jobs = scraper.get_jobs_from_company_page(company)
            print(f"获取到 {len(jobs)} 个职位")
            
            # 过滤澳洲职位
            australian_jobs = [job for job in jobs if scraper.is_australian_job(job)]
            print(f"其中 {len(australian_jobs)} 个澳洲职位")
            
            all_jobs.extend(australian_jobs)
            
            # 显示前2个职位详情
            for i, job in enumerate(australian_jobs[:2]):
                print(f"\n职位 {i+1}:")
                print(f"  标题: {job.get('job_title', 'N/A')}")
                print(f"  公司: {job.get('company_name', 'N/A')}")
                print(f"  地点: {job.get('location', 'N/A')}")
                print(f"  URL: {job.get('job_url', 'N/A')}")
        
        # 保存测试结果
        if all_jobs:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"test_results_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(all_jobs, f, ensure_ascii=False, indent=2)
            
            print(f"\n✅ 测试完成！结果已保存到: {filename}")
            print(f"总共获取到 {len(all_jobs)} 个澳洲职位")
        else:
            print("\n⚠️ 未获取到任何澳洲职位")
    else:
        print("❌ 未获取到公司列表")

def test_specific_company(company_slug: str):
    """测试特定公司"""
    print(f"🧪 测试特定公司: {company_slug}")
    
    scraper = LeverScraperUtils()
    jobs = scraper.get_jobs_from_company_page(company_slug)
    
    print(f"获取到 {len(jobs)} 个职位")
    
    australian_jobs = [job for job in jobs if scraper.is_australian_job(job)]
    print(f"其中 {len(australian_jobs)} 个澳洲职位")
    
    for i, job in enumerate(australian_jobs):
        print(f"\n职位 {i+1}:")
        print(f"  标题: {job.get('job_title', 'N/A')}")
        print(f"  公司: {job.get('company_name', 'N/A')}")
        print(f"  地点: {job.get('location', 'N/A')}")
        print(f"  部门: {job.get('department', 'N/A')}")
        print(f"  团队: {job.get('team', 'N/A')}")
        print(f"  URL: {job.get('job_url', 'N/A')}")
        print(f"  描述: {job.get('description', 'N/A')[:200]}...")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 测试特定公司
        company_slug = sys.argv[1]
        test_specific_company(company_slug)
    else:
        # 运行完整测试
        test_scraper() 