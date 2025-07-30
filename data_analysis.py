#!/usr/bin/env python3
"""
数据分析脚本 - 分析Lever爬取的职位数据
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import boto3
from collections import Counter
import re

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class JobDataAnalyzer:
    """职位数据分析器"""
    
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.dynamodb_client = boto3.client('dynamodb')
        
    def load_data_from_s3(self, bucket_name: str, key: str) -> list:
        """从S3加载数据"""
        try:
            response = self.s3_client.get_object(Bucket=bucket_name, Key=key)
            data = json.loads(response['Body'].read().decode('utf-8'))
            return data
        except Exception as e:
            print(f"从S3加载数据失败: {str(e)}")
            return []
    
    def load_data_from_dynamodb(self, table_name: str) -> list:
        """从DynamoDB加载数据"""
        try:
            response = self.dynamodb_client.scan(TableName=table_name)
            items = response.get('Items', [])
            
            # 转换DynamoDB格式为普通字典
            data = []
            for item in items:
                job_data = {}
                for key, value_dict in item.items():
                    if 'S' in value_dict:
                        job_data[key] = value_dict['S']
                    elif 'N' in value_dict:
                        job_data[key] = float(value_dict['N'])
                data.append(job_data)
            
            return data
        except Exception as e:
            print(f"从DynamoDB加载数据失败: {str(e)}")
            return []
    
    def analyze_jobs(self, jobs_data: list) -> dict:
        """分析职位数据"""
        if not jobs_data:
            return {}
        
        df = pd.DataFrame(jobs_data)
        
        analysis = {
            'total_jobs': len(df),
            'unique_companies': df['company_name'].nunique(),
            'job_titles': df['job_title'].value_counts().head(10).to_dict(),
            'companies': df['company_name'].value_counts().head(10).to_dict(),
            'locations': self.extract_locations(df),
            'departments': df['department'].value_counts().head(10).to_dict(),
            'teams': df['team'].value_counts().head(10).to_dict(),
            'scraped_dates': df['scraped_at'].value_counts().head(5).to_dict()
        }
        
        return analysis
    
    def extract_locations(self, df: pd.DataFrame) -> dict:
        """提取和统计地点信息"""
        locations = []
        for location in df['location'].dropna():
            # 提取澳洲城市
            australian_cities = ['sydney', 'melbourne', 'brisbane', 'perth', 'adelaide', 'canberra', 'darwin', 'hobart']
            location_lower = location.lower()
            
            for city in australian_cities:
                if city in location_lower:
                    locations.append(city.title())
                    break
            else:
                # 如果没有找到澳洲城市，保留原始地点
                if location.strip():
                    locations.append(location.strip())
        
        return Counter(locations).most_common(10)
    
    def create_visualizations(self, analysis: dict, output_dir: str = 'analysis_output'):
        """创建可视化图表"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. 公司职位数量分布
        if analysis.get('companies'):
            plt.figure(figsize=(12, 8))
            companies = list(analysis['companies'].keys())[:10]
            counts = list(analysis['companies'].values())[:10]
            
            plt.barh(companies, counts)
            plt.title('澳洲公司职位数量分布 (Top 10)')
            plt.xlabel('职位数量')
            plt.ylabel('公司名称')
            plt.tight_layout()
            plt.savefig(f'{output_dir}/companies_distribution.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        # 2. 职位类型分布
        if analysis.get('job_titles'):
            plt.figure(figsize=(12, 8))
            titles = list(analysis['job_titles'].keys())[:10]
            counts = list(analysis['job_titles'].values())[:10]
            
            plt.barh(titles, counts)
            plt.title('职位类型分布 (Top 10)')
            plt.xlabel('数量')
            plt.ylabel('职位类型')
            plt.tight_layout()
            plt.savefig(f'{output_dir}/job_titles_distribution.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        # 3. 地点分布
        if analysis.get('locations'):
            plt.figure(figsize=(10, 8))
            locations = [loc[0] for loc in analysis['locations'][:8]]
            counts = [loc[1] for loc in analysis['locations'][:8]]
            
            plt.pie(counts, labels=locations, autopct='%1.1f%%', startangle=90)
            plt.title('澳洲城市职位分布')
            plt.axis('equal')
            plt.savefig(f'{output_dir}/locations_distribution.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        # 4. 部门分布
        if analysis.get('departments'):
            plt.figure(figsize=(12, 8))
            departments = list(analysis['departments'].keys())[:10]
            counts = list(analysis['departments'].values())[:10]
            
            plt.barh(departments, counts)
            plt.title('部门分布 (Top 10)')
            plt.xlabel('数量')
            plt.ylabel('部门')
            plt.tight_layout()
            plt.savefig(f'{output_dir}/departments_distribution.png', dpi=300, bbox_inches='tight')
            plt.close()
    
    def generate_report(self, analysis: dict, output_file: str = 'analysis_report.md'):
        """生成分析报告"""
        report = f"""# Lever澳洲职位数据分析报告

## 📊 数据概览

- **总职位数量**: {analysis.get('total_jobs', 0)}
- **涉及公司数量**: {analysis.get('unique_companies', 0)}

## 🏢 公司分布 (Top 10)

"""
        
        if analysis.get('companies'):
            for i, (company, count) in enumerate(analysis['companies'].items(), 1):
                report += f"{i}. {company}: {count} 个职位\n"
        
        report += "\n## 💼 职位类型分布 (Top 10)\n\n"
        
        if analysis.get('job_titles'):
            for i, (title, count) in enumerate(analysis['job_titles'].items(), 1):
                report += f"{i}. {title}: {count} 个\n"
        
        report += "\n## 🌏 地点分布\n\n"
        
        if analysis.get('locations'):
            for location, count in analysis['locations']:
                report += f"- {location}: {count} 个职位\n"
        
        report += "\n## 🏛️ 部门分布 (Top 10)\n\n"
        
        if analysis.get('departments'):
            for i, (dept, count) in enumerate(analysis['departments'].items(), 1):
                report += f"{i}. {dept}: {count} 个职位\n"
        
        report += f"\n## 📅 数据更新时间\n\n"
        
        if analysis.get('scraped_dates'):
            for date, count in list(analysis['scraped_dates'].items())[:5]:
                report += f"- {date}: {count} 个职位\n"
        
        report += f"\n---\n\n*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"分析报告已保存到: {output_file}")

def main():
    """主函数"""
    analyzer = JobDataAnalyzer()
    
    # 从本地文件加载数据（如果有的话）
    try:
        with open('test_results_*.json', 'r', encoding='utf-8') as f:
            jobs_data = json.load(f)
    except FileNotFoundError:
        print("未找到本地数据文件，请先运行测试脚本")
        return
    
    # 分析数据
    print("🔍 开始分析职位数据...")
    analysis = analyzer.analyze_jobs(jobs_data)
    
    if analysis:
        # 生成可视化
        print("📊 生成可视化图表...")
        analyzer.create_visualizations(analysis)
        
        # 生成报告
        print("📝 生成分析报告...")
        analyzer.generate_report(analysis)
        
        print("✅ 数据分析完成！")
        print(f"- 总职位数: {analysis.get('total_jobs', 0)}")
        print(f"- 涉及公司: {analysis.get('unique_companies', 0)}")
        print("- 可视化图表已保存到 analysis_output/ 目录")
        print("- 分析报告已保存到 analysis_report.md")
    else:
        print("❌ 没有数据可供分析")

if __name__ == "__main__":
    main() 