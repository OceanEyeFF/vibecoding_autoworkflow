# AW-Kernel 时间戳工具 (Windows PowerShell)
# 生成 ISO 8601 UTC 时间戳，用于日志记录
(Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
