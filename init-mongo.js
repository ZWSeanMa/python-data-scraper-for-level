// MongoDB初始化脚本
// 创建数据库和集合

// 切换到jobscraper数据库
db = db.getSiblingDB('jobscraper');

// 创建jobsprofiles集合
db.createCollection('jobsprofiles');

// 创建索引以提高查询性能
db.jobsprofiles.createIndex({ "company_name": 1 });
db.jobsprofiles.createIndex({ "location": 1 });
db.jobsprofiles.createIndex({ "scraped_at": -1 });
db.jobsprofiles.createIndex({ "job_title": 1 });
db.jobsprofiles.createIndex({ "source": 1 });

// 创建复合索引
db.jobsprofiles.createIndex({ "company_name": 1, "scraped_at": -1 });
db.jobsprofiles.createIndex({ "location": 1, "scraped_at": -1 });

print('MongoDB初始化完成');
print('数据库: jobscraper');
print('集合: jobsprofiles');
print('索引已创建'); 