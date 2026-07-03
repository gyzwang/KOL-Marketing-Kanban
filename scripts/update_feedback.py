import json
import subprocess
import time

BASE_TOKEN = "E4Aub48pUadmyBskPEjcML63nrh"
CURRENT_USER_ID = "ou_479eb700f115c4d306541aa6c2d11477"  # 郭召

# 数据表 ID
KOL_TABLE_ID = "tblhv1jMCaVmeXXe"     # 👤 达人管理
TASK_TABLE_ID = "tblxj1B7MGMgU7Dj"    # 📋 任务看板
MAT_TABLE_ID = "tbligeEr1TQzKBau"     # 📦 物料管理

def run_cli(cmd_args):
    """运行 lark-cli 并返回解析后的 JSON 结果"""
    full_cmd = ["lark-cli"] + cmd_args
    result = subprocess.run(full_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error executing command: {' '.join(full_cmd)}")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None

def insert_record(table_id, record_data):
    """往数据表中插入记录"""
    res = run_cli([
        "base", "+record-upsert",
        "--base-token", BASE_TOKEN,
        "--table-id", table_id,
        "--json", json.dumps(record_data)
    ])
    if res and res.get("ok"):
        print(f"✅ 成功向表 {table_id} 插入记录: {list(record_data.values())[0]}")
        return True
    else:
        print(f"❌ 向表 {table_id} 插入记录失败")
        return False

def main():
    print("🚀 开始同步学员沟通情况反馈至飞书多维表格...")
    
    # 1. 插入学员沟通记录到 👤 达人管理
    students = [
        {
            "达人名称": "扎西云旦",
            "平台": "抖音",
            "合作状态": "执行中",
            "沟通记录": "正常节奏素材持续更新中",
            "对接人": [{"id": CURRENT_USER_ID}]
        },
        {
            "达人名称": "格桑次仁",
            "平台": "抖音",
            "合作状态": "执行中",
            "沟通记录": "正常节奏素材持续更新中",
            "对接人": [{"id": CURRENT_USER_ID}]
        },
        {
            "达人名称": "周家松",
            "平台": "抖音",
            "合作状态": "执行中",
            "沟通记录": "抖音素材库持续更新中",
            "对接人": [{"id": CURRENT_USER_ID}]
        },
        {
            "达人名称": "洛桑旦巴",
            "平台": "抖音",
            "合作状态": "执行中",
            "沟通记录": "因为爷爷手术上周开始联系不上，现有素材还可更新3-4条",
            "对接人": [{"id": CURRENT_USER_ID}],
            "备注": "⚠️ 存在断更延期风险，目前失联"
        }
    ]
    
    for student in students:
        insert_record(KOL_TABLE_ID, student)
        time.sleep(0.5)
        
    # 2. 洛桑旦巴失联，触发 📋 任务看板 延期预警任务
    tomorrow_ms = int(time.time() * 1000) + 86400 * 1000
    mat_warning_task = {
        "任务标题": "【延期预警】洛桑旦巴沟通状态跟进与素材盘点",
        "所属模块": "达人沟通",
        "任务状态": "已延期",
        "优先级": "P0-紧急",
        "负责人": [{"id": CURRENT_USER_ID}],
        "截止日期": tomorrow_ms,
        "延期天数": 1,
        "关联达人": "洛桑旦巴",
        "备注": "因为爷爷手术上周开始联系不上，现有素材还可更新3-4条。需密切关注并尝试建联。"
    }
    insert_record(TASK_TABLE_ID, mat_warning_task)
    
    # 3. 洛桑旦巴素材断更风险，录入 📦 物料管理 跟踪
    mat_warning_item = {
        "物料名称": "洛桑旦巴-后续素材包",
        "关联达人": "洛桑旦巴",
        "物料状态": "待接收素材",
        "当前环节负责人": [{"id": CURRENT_USER_ID}],
        "剪辑完成": False,
        "封面完成": False,
        "标题简介完成": False,
        "审核通过": False,
        "问题备注": "⚠️ 达人因家人手术失联，现有素材仅够3-4条，后续素材交付面临中断风险。"
    }
    insert_record(MAT_TABLE_ID, mat_warning_item)
    
    print("\n🎉 学员沟通情况反馈同步完成！")

if __name__ == "__main__":
    main()
