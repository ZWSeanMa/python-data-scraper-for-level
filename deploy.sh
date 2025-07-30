#!/bin/bash

# Lever招聘数据爬虫部署脚本

set -e

echo "🚀 开始部署Lever招聘数据爬虫..."

# 检查AWS CLI是否安装
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI未安装，请先安装AWS CLI"
    exit 1
fi

# 检查SAM CLI是否安装
if ! command -v sam &> /dev/null; then
    echo "❌ AWS SAM CLI未安装，请先安装SAM CLI"
    exit 1
fi

# 检查Python依赖
echo "📦 安装Python依赖..."
pip install -r requirements.txt

# 构建项目
echo "🔨 构建SAM项目..."
sam build

# 部署到AWS
echo "☁️ 部署到AWS..."
sam deploy --guided

echo "✅ 部署完成！"
echo ""
echo "📋 部署信息："
echo "- Lambda函数: lever-job-scraper"
echo "- S3存储桶: lever-jobs-data"
echo "- DynamoDB表: lever-jobs"
echo ""
echo "🔗 查看CloudFormation堆栈: https://console.aws.amazon.com/cloudformation"
echo "🔗 查看Lambda函数: https://console.aws.amazon.com/lambda"
echo "🔗 查看S3存储桶: https://console.aws.amazon.com/s3"
echo "🔗 查看DynamoDB表: https://console.aws.amazon.com/dynamodb" 