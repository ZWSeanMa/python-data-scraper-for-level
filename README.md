# Lever招聘数据爬虫 - ELT架构

这是一个基于AWS Lambda的Python数据爬虫项目，用于从Lever招聘网站爬取澳大利亚公司的职位信息，并采用ELT（Extract, Load, Transform）架构进行数据处理。

## 项目概述

### 架构设计
- **Extract**: AWS Lambda从Lever网站爬取原始职位数据
- **Load**: 将原始数据加载到AWS S3作为数据湖
- **Transform**: 通过后端API对数据进行转换和清洗
- **Final Load**: 将处理后的数据存储到MongoDB的`jobsprofiles`表

### 技术栈
- **Python 3.9**: 主要编程语言
- **AWS Lambda**: 无服务器计算服务
- **AWS S3**: 数据湖存储
- **AWS EventBridge**: 定时触发
- **MongoDB**: 最终数据存储
- **Flask**: 后端API框架
- **BeautifulSoup4**: HTML解析
- **Requests**: HTTP请求库

## 项目结构

```
python-data-scraper-for-level/
├── lambda_function.py          # Lambda主函数
├── deployment.yaml            # AWS SAM部署模板
├── samconfig.toml            # SAM配置文件
├── requirements.txt           # Python依赖
├── backend_api_example.py    # 后端API示例
├── Dockerfile                # Docker配置
├── docker-compose.yml        # 本地开发环境
├── init-mongo.js            # MongoDB初始化脚本
├── test_scraper.py          # 本地测试脚本
├── data_analysis.py         # 数据分析脚本
├── monitoring.py            # 监控脚本
├── deploy.sh               # 部署脚本
├── utils/
│   └── scraper_utils.py    # 爬虫工具类
└── README.md               # 项目文档
```

## 快速开始

### 1. 环境准备

确保已安装以下工具：
- AWS CLI
- AWS SAM CLI
- Docker & Docker Compose
- Python 3.9+

### 2. 本地开发环境

启动本地开发环境（包含MongoDB和后端API）：

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend-api
```

### 3. 测试爬虫

```bash
# 运行本地测试
python test_scraper.py

# 测试特定公司
python test_scraper.py --company atlassian
```

### 4. 部署到AWS

```bash
# 运行部署脚本
./deploy.sh

# 或手动部署
sam build
sam deploy --guided
```

## 数据流程

### 1. 数据提取 (Extract)
- Lambda函数从`https://jobs.lever.co/`爬取职位数据
- 识别澳大利亚公司（基于关键词和已知公司列表）
- 提取职位标题、公司名称、地点、描述等信息

### 2. 数据加载 (Load)
- 原始数据保存到S3数据湖
- 文件路径格式：`raw_data/jobs_YYYYMMDD_HHMMSS.json`
- 澳大利亚职位数据：`australian_jobs/jobs_YYYYMMDD_HHMMSS.json`

### 3. 数据转换 (Transform)
- 后端API接收Lambda发送的数据
- 数据清洗和格式转换
- 添加元数据（时间戳、来源等）

### 4. 最终加载 (Final Load)
- 转换后的数据存储到MongoDB
- 表名：`jobsprofiles`
- 包含索引优化查询性能

## 配置说明

### 环境变量

#### Lambda函数
- `S3_BUCKET_NAME`: S3存储桶名称
- `BACKEND_API_ENDPOINT`: 后端API端点
- `API_TOKEN`: API认证令牌（可选）

#### 后端API
- `MONGO_URI`: MongoDB连接字符串
- `DB_NAME`: 数据库名称
- `COLLECTION_NAME`: 集合名称

### AWS资源

#### S3存储桶
- 名称：`lever-jobs-data`
- 版本控制：启用
- 生命周期：365天后自动删除

#### Lambda函数
- 运行时：Python 3.9
- 超时：900秒
- 内存：512MB
- 触发器：EventBridge（每日执行）

## API接口

### 后端API端点

#### POST /api/jobs
接收Lambda发送的职位数据

**请求格式：**
```json
{
  "table": "jobsprofiles",
  "data": [
    {
      "job_title": "Software Engineer",
      "company_name": "Atlassian",
      "location": "Sydney, Australia",
      "description": "...",
      "job_url": "https://jobs.lever.co/...",
      "scraped_at": "2024-01-01T10:00:00"
    }
  ]
}
```

#### GET /api/jobs
获取存储的职位数据

**查询参数：**
- `limit`: 返回记录数（默认50）
- `skip`: 跳过记录数（默认0）
- `company`: 按公司名称过滤
- `location`: 按地点过滤

#### GET /api/stats
获取数据统计信息

#### GET /health
健康检查

## 监控和分析

### 监控脚本
```bash
# 运行监控脚本
python monitoring.py
```

监控内容包括：
- Lambda执行状态
- S3数据存储情况
- 数据质量检查
- 错误报告

### 数据分析
```bash
# 运行数据分析
python data_analysis.py
```

分析内容包括：
- 职位分布统计
- 公司分布分析
- 地点分布分析
- 可视化图表生成

## 开发指南

### 本地测试
1. 启动本地环境：`docker-compose up -d`
2. 运行测试：`python test_scraper.py`
3. 检查API：`curl http://localhost:5000/health`

### 调试技巧
- 查看Lambda日志：AWS CloudWatch
- 查看API日志：`docker-compose logs backend-api`
- 查看MongoDB数据：访问 `http://localhost:8081`

### 扩展功能
- 添加更多数据源
- 实现数据去重
- 添加数据质量检查
- 实现实时通知

## 安全注意事项

1. **API认证**: 在生产环境中添加适当的认证机制
2. **数据加密**: 确保敏感数据在传输和存储时加密
3. **访问控制**: 限制对S3和MongoDB的访问权限
4. **速率限制**: 避免对目标网站造成过大压力

## 故障排除

### 常见问题

1. **Lambda超时**
   - 减少处理的公司数量
   - 增加Lambda内存配置
   - 优化网络请求

2. **API连接失败**
   - 检查网络连接
   - 验证API端点配置
   - 检查认证信息

3. **MongoDB连接问题**
   - 验证连接字符串
   - 检查网络权限
   - 确认数据库服务状态

### 日志查看
```bash
# Lambda日志
aws logs tail /aws/lambda/lever-job-scraper

# API日志
docker-compose logs backend-api

# MongoDB日志
docker-compose logs mongodb
```

## 重要说明

1. **合规性**: 确保遵守目标网站的robots.txt和使用条款
2. **性能**: 添加适当的延迟避免对目标网站造成压力
3. **数据质量**: 定期检查数据完整性和准确性
4. **备份**: 定期备份MongoDB数据
5. **更新**: 定期更新依赖包和安全补丁

## 许可证

本项目仅供学习和研究使用，请遵守相关法律法规和网站使用条款。