"""
后端API示例实现
用于接收Lambda发送的职位数据并存储到MongoDB的jobsprofiles表
"""

from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# MongoDB连接配置
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = os.environ.get('DB_NAME', 'jobscraper')
COLLECTION_NAME = os.environ.get('COLLECTION_NAME', 'jobsprofiles')

# 初始化MongoDB连接
try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    logger.info(f"成功连接到MongoDB: {DB_NAME}.{COLLECTION_NAME}")
except Exception as e:
    logger.error(f"MongoDB连接失败: {str(e)}")
    client = None
    db = None
    collection = None

def transform_job_data(job_data):
    """
    转换职位数据格式，添加必要的字段
    """
    transformed_jobs = []
    
    for job in job_data:
        # 生成唯一ID
        job_id = f"{job.get('company_name', 'unknown')}_{job.get('job_title', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 转换数据格式
        transformed_job = {
            'job_id': job_id,
            'job_title': job.get('job_title', ''),
            'company_name': job.get('company_name', ''),
            'company_path': job.get('company_path', ''),
            'location': job.get('location', ''),
            'department': job.get('department', ''),
            'team': job.get('team', ''),
            'description': job.get('description', ''),
            'requirements': job.get('requirements', ''),
            'benefits': job.get('benefits', ''),
            'job_url': job.get('job_url', ''),
            'source': 'lever',
            'scraped_at': job.get('scraped_at', datetime.now().isoformat()),
            'processed_at': datetime.now().isoformat(),
            'country': 'Australia',
            'status': 'active'
        }
        
        # 添加地理位置信息
        if job.get('location'):
            location_lower = job['location'].lower()
            if any(city in location_lower for city in ['sydney', 'melbourne', 'brisbane', 'perth', 'adelaide']):
                transformed_job['city'] = next(city for city in ['sydney', 'melbourne', 'brisbane', 'perth', 'adelaide'] 
                                            if city in location_lower)
        
        transformed_jobs.append(transformed_job)
    
    return transformed_jobs

@app.route('/api/jobs', methods=['POST'])
def receive_jobs():
    """
    接收Lambda发送的职位数据并存储到MongoDB
    """
    try:
        # 验证请求
        if not request.is_json:
            return jsonify({'error': '请求必须是JSON格式'}), 400
        
        data = request.get_json()
        
        # 验证数据格式
        if 'table' not in data or 'data' not in data:
            return jsonify({'error': '缺少必要的字段: table, data'}), 400
        
        if data['table'] != 'jobsprofiles':
            return jsonify({'error': '不支持的表名'}), 400
        
        job_data = data['data']
        if not isinstance(job_data, list):
            return jsonify({'error': 'data字段必须是数组'}), 400
        
        logger.info(f"接收到 {len(job_data)} 条职位数据")
        
        # 检查MongoDB连接
        if not collection:
            return jsonify({'error': 'MongoDB连接失败'}), 500
        
        # 转换数据
        transformed_jobs = transform_job_data(job_data)
        
        # 存储到MongoDB
        result = collection.insert_many(transformed_jobs)
        
        logger.info(f"成功存储 {len(result.inserted_ids)} 条记录到MongoDB")
        
        return jsonify({
            'success': True,
            'message': f'成功存储 {len(result.inserted_ids)} 条记录',
            'inserted_count': len(result.inserted_ids),
            'collection': COLLECTION_NAME
        }), 200
        
    except Exception as e:
        logger.error(f"处理请求时出错: {str(e)}")
        return jsonify({'error': f'服务器内部错误: {str(e)}'}), 500

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """
    获取存储的职位数据
    """
    try:
        if not collection:
            return jsonify({'error': 'MongoDB连接失败'}), 500
        
        # 获取查询参数
        limit = request.args.get('limit', 50, type=int)
        skip = request.args.get('skip', 0, type=int)
        company = request.args.get('company', '')
        location = request.args.get('location', '')
        
        # 构建查询条件
        query = {}
        if company:
            query['company_name'] = {'$regex': company, '$options': 'i'}
        if location:
            query['location'] = {'$regex': location, '$options': 'i'}
        
        # 查询数据
        jobs = list(collection.find(query, {'_id': 0}).skip(skip).limit(limit).sort('scraped_at', -1))
        
        return jsonify({
            'success': True,
            'data': jobs,
            'count': len(jobs),
            'total': collection.count_documents(query)
        }), 200
        
    except Exception as e:
        logger.error(f"获取数据时出错: {str(e)}")
        return jsonify({'error': f'服务器内部错误: {str(e)}'}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    获取数据统计信息
    """
    try:
        if not collection:
            return jsonify({'error': 'MongoDB连接失败'}), 500
        
        # 获取基本统计信息
        total_jobs = collection.count_documents({})
        total_companies = len(collection.distinct('company_name'))
        total_locations = len(collection.distinct('location'))
        
        # 获取最近的数据
        latest_job = collection.find_one({}, sort=[('scraped_at', -1)])
        latest_scrape = latest_job.get('scraped_at') if latest_job else None
        
        # 按公司统计
        company_stats = list(collection.aggregate([
            {'$group': {'_id': '$company_name', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]))
        
        # 按位置统计
        location_stats = list(collection.aggregate([
            {'$group': {'_id': '$location', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]))
        
        return jsonify({
            'success': True,
            'stats': {
                'total_jobs': total_jobs,
                'total_companies': total_companies,
                'total_locations': total_locations,
                'latest_scrape': latest_scrape,
                'top_companies': company_stats,
                'top_locations': location_stats
            }
        }), 200
        
    except Exception as e:
        logger.error(f"获取统计信息时出错: {str(e)}")
        return jsonify({'error': f'服务器内部错误: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    健康检查端点
    """
    try:
        if collection:
            # 测试数据库连接
            collection.find_one()
            db_status = 'connected'
        else:
            db_status = 'disconnected'
        
        return jsonify({
            'status': 'healthy',
            'database': db_status,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    # 在生产环境中，应该使用WSGI服务器如gunicorn
    app.run(host='0.0.0.0', port=5000, debug=False) 