#!/bin/bash

# 本地开发环境启动脚本

echo "🚀 启动Lever招聘数据爬虫本地开发环境..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 检查Docker Compose是否可用
if ! docker-compose version > /dev/null 2>&1; then
    echo "❌ Docker Compose不可用，请安装Docker Compose"
    exit 1
fi

echo "📦 构建并启动服务..."

# 停止现有服务
docker-compose down

# 构建并启动服务
docker-compose up -d --build

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 服务状态："
docker-compose ps

# 检查API健康状态
echo "🔍 检查API健康状态..."
if curl -s http://localhost:5000/health > /dev/null; then
    echo "✅ 后端API运行正常"
else
    echo "❌ 后端API启动失败，请检查日志："
    docker-compose logs backend-api
fi

# 检查MongoDB连接
echo "🔍 检查MongoDB连接..."
if curl -s http://localhost:8081 > /dev/null; then
    echo "✅ MongoDB管理界面可访问: http://localhost:8081"
    echo "   用户名: admin, 密码: password123"
else
    echo "❌ MongoDB管理界面不可访问"
fi

echo ""
echo "🎉 本地开发环境启动完成！"
echo ""
echo "📋 服务信息："
echo "   - 后端API: http://localhost:5000"
echo "   - MongoDB管理界面: http://localhost:8081"
echo "   - MongoDB连接: mongodb://admin:password123@localhost:27017/"
echo ""
echo "🔧 常用命令："
echo "   - 查看日志: docker-compose logs -f"
echo "   - 停止服务: docker-compose down"
echo "   - 重启服务: docker-compose restart"
echo "   - 测试爬虫: python test_scraper.py"
echo ""
echo "📚 API文档："
echo "   - 健康检查: GET http://localhost:5000/health"
echo "   - 获取职位: GET http://localhost:5000/api/jobs"
echo "   - 获取统计: GET http://localhost:5000/api/stats"
echo "" 