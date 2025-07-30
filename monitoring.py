#!/usr/bin/env python3
"""
监控脚本 - 监控Lever爬虫执行状态和数据质量
"""

import boto3
import json
import time
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LeverScraperMonitor:
    """Lever爬虫监控器"""
    
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.lambda_client = boto3.client('lambda')
        self.s3_client = boto3.client('s3')
        self.dynamodb_client = boto3.client('dynamodb')
        
    def check_lambda_execution(self, function_name: str = 'lever-job-scraper') -> Dict:
        """检查Lambda函数执行状态"""
        try:
            # 获取最近的执行日志
            logs_client = boto3.client('logs')
            
            # 获取最近的日志流
            response = logs_client.describe_log_streams(
                logGroupName=f'/aws/lambda/{function_name}',
                orderBy='LastEventTime',
                descending=True,
                maxItems=5
            )
            
            execution_status = {
                'function_name': function_name,
                'last_execution': None,
                'success_count': 0,
                'error_count': 0,
                'execution_time': 0,
                'jobs_scraped': 0
            }
            
            for stream in response.get('logStreams', []):
                # 获取日志事件
                events_response = logs_client.get_log_events(
                    logGroupName=f'/aws/lambda/{function_name}',
                    logStreamName=stream['logStreamName'],
                    startTime=int((datetime.now() - timedelta(hours=24)).timestamp() * 1000),
                    endTime=int(datetime.now().timestamp() * 1000)
                )
                
                for event in events_response.get('events', []):
                    message = event['message']
                    
                    if '开始执行Lever招聘数据爬虫' in message:
                        execution_status['last_execution'] = datetime.fromtimestamp(event['timestamp'] / 1000)
                    
                    elif '爬虫执行成功' in message:
                        execution_status['success_count'] += 1
                        # 提取职位数量
                        if 'total_jobs' in message:
                            try:
                                import re
                                match = re.search(r'"total_jobs":\s*(\d+)', message)
                                if match:
                                    execution_status['jobs_scraped'] += int(match.group(1))
                            except:
                                pass
                    
                    elif 'Lambda函数执行失败' in message:
                        execution_status['error_count'] += 1
                    
                    elif '执行时间' in message:
                        try:
                            import re
                            match = re.search(r'执行时间:\s*(\d+\.?\d*)', message)
                            if match:
                                execution_status['execution_time'] = float(match.group(1))
                        except:
                            pass
            
            return execution_status
            
        except Exception as e:
            logger.error(f"检查Lambda执行状态失败: {str(e)}")
            return {'error': str(e)}
    
    def check_s3_data(self, bucket_name: str = 'lever-jobs-data') -> Dict:
        """检查S3数据存储状态"""
        try:
            # 列出最近的文件
            response = self.s3_client.list_objects_v2(
                Bucket=bucket_name,
                MaxKeys=10
            )
            
            s3_status = {
                'bucket_name': bucket_name,
                'total_files': 0,
                'latest_file': None,
                'total_size_mb': 0,
                'files_last_24h': 0
            }
            
            if 'Contents' in response:
                files = response['Contents']
                s3_status['total_files'] = len(files)
                
                # 按修改时间排序
                files.sort(key=lambda x: x['LastModified'], reverse=True)
                
                if files:
                    latest_file = files[0]
                    s3_status['latest_file'] = {
                        'key': latest_file['Key'],
                        'size_mb': latest_file['Size'] / (1024 * 1024),
                        'last_modified': latest_file['LastModified'].isoformat()
                    }
                    
                    # 计算总大小和最近24小时的文件数
                    cutoff_time = datetime.now(latest_file['LastModified'].tzinfo) - timedelta(hours=24)
                    
                    for file in files:
                        s3_status['total_size_mb'] += file['Size'] / (1024 * 1024)
                        if file['LastModified'] > cutoff_time:
                            s3_status['files_last_24h'] += 1
            
            return s3_status
            
        except Exception as e:
            logger.error(f"检查S3数据状态失败: {str(e)}")
            return {'error': str(e)}
    
    def check_dynamodb_data(self, table_name: str = 'lever-jobs') -> Dict:
        """检查DynamoDB数据状态"""
        try:
            # 获取表信息
            table_info = self.dynamodb_client.describe_table(TableName=table_name)
            
            # 扫描最近的数据
            response = self.dynamodb_client.scan(
                TableName=table_name,
                Select='COUNT'
            )
            
            dynamodb_status = {
                'table_name': table_name,
                'total_items': response.get('Count', 0),
                'scanned_count': response.get('ScannedCount', 0),
                'table_status': table_info['Table']['TableStatus'],
                'items_last_24h': 0
            }
            
            # 检查最近24小时的数据
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            # 扫描所有数据（注意：这可能需要分页处理）
            scan_response = self.dynamodb_client.scan(TableName=table_name)
            
            for item in scan_response.get('Items', []):
                if 'scraped_at' in item:
                    scraped_time_str = item['scraped_at']['S']
                    try:
                        scraped_time = datetime.fromisoformat(scraped_time_str.replace('Z', '+00:00'))
                        if scraped_time > cutoff_time:
                            dynamodb_status['items_last_24h'] += 1
                    except:
                        pass
            
            return dynamodb_status
            
        except Exception as e:
            logger.error(f"检查DynamoDB数据状态失败: {str(e)}")
            return {'error': str(e)}
    
    def check_data_quality(self, table_name: str = 'lever-jobs') -> Dict:
        """检查数据质量"""
        try:
            # 扫描数据进行分析
            response = self.dynamodb_client.scan(TableName=table_name, Limit=100)
            
            quality_metrics = {
                'total_samples': len(response.get('Items', [])),
                'complete_records': 0,
                'australian_jobs': 0,
                'avg_description_length': 0,
                'companies_with_jobs': set()
            }
            
            total_description_length = 0
            
            for item in response.get('Items', []):
                # 检查记录完整性
                required_fields = ['job_title', 'company_name', 'description']
                if all(field in item for field in required_fields):
                    quality_metrics['complete_records'] += 1
                
                # 检查澳洲职位
                if 'company_name' in item:
                    company_name = item['company_name']['S'].lower()
                    australian_keywords = ['australia', 'australian', 'sydney', 'melbourne', 'brisbane']
                    if any(keyword in company_name for keyword in australian_keywords):
                        quality_metrics['australian_jobs'] += 1
                
                # 统计描述长度
                if 'description' in item:
                    desc_length = len(item['description']['S'])
                    total_description_length += desc_length
                
                # 统计公司数量
                if 'company_name' in item:
                    quality_metrics['companies_with_jobs'].add(item['company_name']['S'])
            
            if quality_metrics['total_samples'] > 0:
                quality_metrics['avg_description_length'] = total_description_length / quality_metrics['total_samples']
                quality_metrics['companies_with_jobs'] = len(quality_metrics['companies_with_jobs'])
            
            return quality_metrics
            
        except Exception as e:
            logger.error(f"检查数据质量失败: {str(e)}")
            return {'error': str(e)}
    
    def generate_monitoring_report(self) -> str:
        """生成监控报告"""
        report = f"""# Lever爬虫监控报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🔍 Lambda函数状态

"""
        
        # Lambda执行状态
        lambda_status = self.check_lambda_execution()
        if 'error' not in lambda_status:
            report += f"- 函数名称: {lambda_status['function_name']}\n"
            report += f"- 最后执行: {lambda_status['last_execution']}\n"
            report += f"- 成功次数: {lambda_status['success_count']}\n"
            report += f"- 错误次数: {lambda_status['error_count']}\n"
            report += f"- 爬取职位数: {lambda_status['jobs_scraped']}\n"
        else:
            report += f"- Lambda状态检查失败: {lambda_status['error']}\n"
        
        report += "\n## 📦 S3存储状态\n\n"
        
        # S3状态
        s3_status = self.check_s3_data()
        if 'error' not in s3_status:
            report += f"- 存储桶: {s3_status['bucket_name']}\n"
            report += f"- 总文件数: {s3_status['total_files']}\n"
            report += f"- 总大小: {s3_status['total_size_mb']:.2f} MB\n"
            report += f"- 24小时内文件数: {s3_status['files_last_24h']}\n"
            if s3_status['latest_file']:
                report += f"- 最新文件: {s3_status['latest_file']['key']}\n"
                report += f"- 文件大小: {s3_status['latest_file']['size_mb']:.2f} MB\n"
        else:
            report += f"- S3状态检查失败: {s3_status['error']}\n"
        
        report += "\n## 🗄️ DynamoDB状态\n\n"
        
        # DynamoDB状态
        db_status = self.check_dynamodb_data()
        if 'error' not in db_status:
            report += f"- 表名: {db_status['table_name']}\n"
            report += f"- 总记录数: {db_status['total_items']}\n"
            report += f"- 表状态: {db_status['table_status']}\n"
            report += f"- 24小时内记录数: {db_status['items_last_24h']}\n"
        else:
            report += f"- DynamoDB状态检查失败: {db_status['error']}\n"
        
        report += "\n## 📊 数据质量指标\n\n"
        
        # 数据质量
        quality_metrics = self.check_data_quality()
        if 'error' not in quality_metrics:
            report += f"- 样本数量: {quality_metrics['total_samples']}\n"
            report += f"- 完整记录: {quality_metrics['complete_records']}\n"
            report += f"- 澳洲职位: {quality_metrics['australian_jobs']}\n"
            report += f"- 平均描述长度: {quality_metrics['avg_description_length']:.0f} 字符\n"
            report += f"- 涉及公司数: {quality_metrics['companies_with_jobs']}\n"
        else:
            report += f"- 数据质量检查失败: {quality_metrics['error']}\n"
        
        return report
    
    def send_alert(self, message: str, alert_type: str = 'info'):
        """发送告警（示例实现）"""
        # 这里可以集成SNS、Slack、邮件等告警方式
        logger.info(f"[{alert_type.upper()}] {message}")
        
        # 示例：发送到SNS
        try:
            sns_client = boto3.client('sns')
            topic_arn = 'arn:aws:sns:region:account:lever-scraper-alerts'  # 需要配置
            
            sns_client.publish(
                TopicArn=topic_arn,
                Message=message,
                Subject=f'Lever爬虫告警 - {alert_type.upper()}'
            )
        except Exception as e:
            logger.error(f"发送告警失败: {str(e)}")

def main():
    """主函数"""
    monitor = LeverScraperMonitor()
    
    print("🔍 开始监控检查...")
    
    # 生成监控报告
    report = monitor.generate_monitoring_report()
    
    # 保存报告
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'monitoring_report_{timestamp}.md'
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 监控报告已保存到: {filename}")
    print("\n" + "="*50)
    print(report)
    print("="*50)

if __name__ == "__main__":
    main() 