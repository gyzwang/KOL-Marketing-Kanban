import json
import subprocess
import os

BASE_TOKEN = "E4Aub48pUadmyBskPEjcML63nrh"

# 数据表 ID
KOL_TABLE_ID = "tblhv1jMCaVmeXXe"     # 👤 达人管理
TASK_TABLE_ID = "tblxj1B7MGMgU7Dj"    # 📋 任务看板
MAT_TABLE_ID = "tbligeEr1TQzKBau"     # 📦 物料管理
BUDGET_TABLE_ID = "tblpYwoTY9dH5lX9"  # 💰 预算管控

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

def fetch_table_records(table_id):
    """抓取数据表数据并转换为字典列表"""
    res = run_cli([
        "base", "+record-list",
        "--base-token", BASE_TOKEN,
        "--table-id", table_id,
        "--limit", "100"  # 获取足够的数据
    ])
    if not res or not res.get("ok"):
        print(f"❌ 无法拉取表数据: {table_id}")
        return []
    
    data_payload = res.get("data", {})
    rows = data_payload.get("data", [])
    fields = data_payload.get("fields", [])
    record_ids = data_payload.get("record_id_list", [])
    
    records = []
    for i, row in enumerate(rows):
        # 组装字典
        item = {"id": record_ids[i]}
        for field_name, value in zip(fields, row):
            item[field_name] = value
        records.append(item)
    return records

def main():
    print("⏳ 正在从飞书多维表格抓取最新数据...")
    
    kols = fetch_table_records(KOL_TABLE_ID)
    materials = fetch_table_records(MAT_TABLE_ID)
    tasks = fetch_table_records(TASK_TABLE_ID)
    budgets = fetch_table_records(BUDGET_TABLE_ID)
    
    print(f"📊 抓取完成: 达人 {len(kols)} 位, 物料 {len(materials)} 个, 任务 {len(tasks)} 项, 预算 {len(budgets)} 项。")
    
    # 构造要写入 data.js 的数据结构
    data_content = {
        "kols": kols,
        "materials": materials,
        "tasks": tasks,
        "budgets": budgets,
        "last_updated": time_str()
    }
    
    # 确保 scripts 目录存在
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
    
    data_js_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.js")
    with open(data_js_path, "w", encoding="utf-8") as f:
        f.write(f"// 飞书同步数据 - 自动生成，请勿手动修改\n")
        f.write(f"window.KOL_DATA = {json.dumps(data_content, ensure_ascii=False, indent=2)};\n")
    print(f"💾 本地 JS 缓存已保存: {data_js_path}")
    
    # 写入 JSON 缓存用于上传
    data_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")
    with open(data_json_path, "w", encoding="utf-8") as f:
        json.dump(data_content, f, ensure_ascii=False, indent=2)
    print(f"💾 本地 JSON 缓存已保存: {data_json_path}")
    
    # 上传到 GitHub Gist
    print("⏳ 正在将最新数据上传到 GitHub Gist 云端...")
    gist_id = "1a7c428ee04656882a416398851f4deb"
    upload_res = subprocess.run([
        "gh", "gist", "edit", gist_id,
        "--filename", "data.json", data_json_path
    ], capture_output=True, text=True)
    if upload_res.returncode == 0:
        print("✅ 成功同步最新数据到 GitHub Gist 云端！")
    else:
        print("❌ 无法上传到 Gist:")
        print(upload_res.stderr)
        
    print(f"💾 缓存更新完成时间: {data_content['last_updated']}")

def time_str():
    import datetime
    # 使用本地时间格式化
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if __name__ == "__main__":
    main()
