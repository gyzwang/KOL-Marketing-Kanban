import json
import subprocess
import sys
import time

BASE_TOKEN = "E4Aub48pUadmyBskPEjcML63nrh"
CURRENT_USER_ID = "ou_479eb700f115c4d306541aa6c2d11477"  # 郭召

def run_cli(cmd_args):
    """运行 lark-cli 并返回解析后的 JSON 结果"""
    full_cmd = ["lark-cli"] + cmd_args
    # print(f"Running: {' '.join(full_cmd)}")
    result = subprocess.run(full_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error executing command: {' '.join(full_cmd)}")
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"Failed to parse JSON output: {result.stdout}")
        return None

def get_tables():
    """获取多维表格中的所有数据表"""
    res = run_cli(["base", "+table-list", "--base-token", BASE_TOKEN])
    if res and res.get("ok"):
        return res["data"].get("items", [])
    return []

def create_table(name, fields=None):
    """创建数据表"""
    fields_arg = json.dumps(fields or [{"name": "名称", "type": "text"}])
    res = run_cli([
        "base", "+table-create", 
        "--base-token", BASE_TOKEN, 
        "--name", name, 
        "--fields", fields_arg
    ])
    if res and res.get("ok"):
        # 获取创建成功的 table_id
        time.sleep(1)  # 稍微等待同步
        tables = get_tables()
        for t in tables:
            if t["table_name"] == name:
                print(f"✅ 数据表创建成功: {name} ({t['table_id']})")
                return t["table_id"]
    print(f"❌ 数据表创建失败: {name}")
    return None

def create_field(table_id, name, field_type, options=None, multiple=None):
    """为数据表创建字段"""
    payload = {
        "name": name,
        "type": field_type
    }
    if options is not None:
        payload["options"] = [{"name": opt} for opt in options]
    if multiple is not None:
        payload["multiple"] = multiple
        
    res = run_cli([
        "base", "+field-create",
        "--base-token", BASE_TOKEN,
        "--table-id", table_id,
        "--json", json.dumps(payload)
    ])
    if res and res.get("ok"):
        print(f"  └─ 字段创建成功: {name} ({field_type})")
        return res["data"]["field"]["id"]
    else:
        print(f"  └─ ❌ 字段创建失败: {name}")
        return None

def create_view(table_id, name, view_type):
    """为数据表创建视图"""
    payload = {
        "name": name,
        "type": view_type
    }
    res = run_cli([
        "base", "+view-create",
        "--base-token", BASE_TOKEN,
        "--table-id", table_id,
        "--json", json.dumps(payload)
    ])
    if res and res.get("ok"):
        print(f"  └─ 视图创建成功: {name} ({view_type})")
        return True
    else:
        print(f"  └─ ❌ 视图创建失败: {name}")
        return False

def insert_record(table_id, record_data):
    """往数据表中插入记录"""
    res = run_cli([
        "base", "+record-upsert",
        "--base-token", BASE_TOKEN,
        "--table-id", table_id,
        "--json", json.dumps(record_data)
    ])
    return res and res.get("ok")

def delete_table(table_id):
    """删除数据表"""
    res = run_cli([
        "base", "+table-delete",
        "--yes",
        "--base-token", BASE_TOKEN,
        "--table-id", table_id
    ])
    return res and res.get("ok")

def main():
    print("🚀 开始自动化搭建达人营销运营看板...")
    
    # 1. 检查已有的表格
    existing_tables = get_tables()
    print(f"当前已存在的数据表: {[t['table_name'] for t in existing_tables]}")
    
    # 为避免重名冲突，先删除旧表的逻辑（如果已存在）
    for t in existing_tables:
        if t["table_name"] in ["📋 任务看板", "📦 物料管理", "👤 达人管理", "💰 预算管控"]:
            print(f"发现已有数据表 '{t['table_name']}'，正在清理重置...")
            delete_table(t["table_id"])
            time.sleep(0.5)

    # ------------------ 1. 创建 👤 达人管理 ------------------
    # 以“达人名称”为主键
    kol_fields = [{"name": "达人名称", "type": "text"}]
    kol_table_id = create_table("👤 达人管理", kol_fields)
    
    if kol_table_id:
        create_field(kol_table_id, "平台", "select", ["抖音", "快手", "小红书", "B站", "微博", "其他"])
        create_field(kol_table_id, "粉丝量", "number")
        create_field(kol_table_id, "合作状态", "select", ["待联系", "沟通中", "已签约", "执行中", "已结束"])
        create_field(kol_table_id, "合作类型", "select", ["纯佣", "置换", "付费", "混合"])
        create_field(kol_table_id, "合作费用", "number")
        create_field(kol_table_id, "内容方向", "text")
        create_field(kol_table_id, "联系方式", "text")
        create_field(kol_table_id, "对接人", "user", multiple=True)
        create_field(kol_table_id, "沟通记录", "text")
        create_field(kol_table_id, "已交付物料数", "number")
        create_field(kol_table_id, "备注", "text")
        
        # 创建看板视图
        create_view(kol_table_id, "合作状态看板", "kanban")
        
        # 插入达人数据
        kol_samples = [
            {
                "达人名称": "小红书美妆达人A", "平台": "小红书", "粉丝量": 120000, 
                "合作状态": "已签约", "合作类型": "付费", "合作费用": 3000, 
                "内容方向": "美妆/穿搭", "联系方式": "wx_123456", 
                "对接人": [{"id": CURRENT_USER_ID}], "沟通记录": "已付定金，正在筹备素材", "已交付物料数": 0
            },
            {
                "达人名称": "抖音美食博主B", "平台": "抖音", "粉丝量": 550000, 
                "合作状态": "执行中", "合作类型": "混合", "合作费用": 5000, 
                "内容方向": "美食探店", "联系方式": "13800138000", 
                "对接人": [{"id": CURRENT_USER_ID}], "沟通记录": "第一期视频已发，效果极佳", "已交付物料数": 1
            },
            {
                "达人名称": "B站数码UP主C", "平台": "B站", "粉丝量": 80000, 
                "合作状态": "沟通中", "合作类型": "置换", "合作费用": 0, 
                "内容方向": "数码测评", "联系方式": "upc@bilibili.com", 
                "对接人": [{"id": CURRENT_USER_ID}], "沟通记录": "已寄送样品，等待拍摄素材反馈", "已交付物料数": 0
            }
        ]
        for item in kol_samples:
            insert_record(kol_table_id, item)
            
    # ------------------ 2. 创建 📦 物料管理 ------------------
    mat_fields = [{"name": "物料名称", "type": "text"}]
    mat_table_id = create_table("📦 物料管理", mat_fields)
    
    if mat_table_id:
        create_field(mat_table_id, "关联达人", "text")
        create_field(mat_table_id, "物料状态", "select", [
            "待接收素材", "素材已到", "剪辑中", "封面优化中", "标题优化中", "待审核", "已发布"
        ])
        create_field(mat_table_id, "当前环节负责人", "user", multiple=True)
        create_field(mat_table_id, "素材接收日期", "datetime")
        create_field(mat_table_id, "计划发布日期", "datetime")
        create_field(mat_table_id, "剪辑完成", "checkbox")
        create_field(mat_table_id, "封面完成", "checkbox")
        create_field(mat_table_id, "标题简介完成", "checkbox")
        create_field(mat_table_id, "审核通过", "checkbox")
        create_field(mat_table_id, "问题备注", "text")
        create_field(mat_table_id, "发布链接", "text")
        
        # 创建看板与甘特图视图
        create_view(mat_table_id, "物料状态流水线", "kanban")
        create_view(mat_table_id, "发布甘特图", "gantt")
        
        # 插入物料数据
        mat_samples = [
            {
                "物料名称": "小红书美妆测评v1", "关联达人": "小红书美妆达人A", 
                "物料状态": "待接收素材", "当前环节负责人": [{"id": CURRENT_USER_ID}],
                "计划发布日期": int(time.time() * 1000) + 86400 * 5 * 1000, # 5天后
                "剪辑完成": False, "封面完成": False, "标题简介完成": False, "审核通过": False
            },
            {
                "物料名称": "探店视频精剪版", "关联达人": "抖音美食博主B", 
                "物料状态": "剪辑中", "当前环节负责人": [{"id": CURRENT_USER_ID}],
                "素材接收日期": int(time.time() * 1000) - 86400 * 2 * 1000, # 2天前
                "计划发布日期": int(time.time() * 1000) + 86400 * 2 * 1000, # 2天后
                "剪辑完成": False, "封面完成": False, "标题简介完成": False, "审核通过": False
            },
            {
                "物料名称": "数码新品测评01", "关联达人": "B站数码UP主C", 
                "物料状态": "待审核", "当前环节负责人": [{"id": CURRENT_USER_ID}],
                "素材接收日期": int(time.time() * 1000) - 86400 * 4 * 1000, 
                "计划发布日期": int(time.time() * 1000) + 86400 * 1 * 1000, 
                "剪辑完成": True, "封面完成": True, "标题简介完成": True, "审核通过": False,
                "问题备注": "视频后半段音频音量偏小，需要重新调音后再审核。"
            }
        ]
        for item in mat_samples:
            insert_record(mat_table_id, item)

    # ------------------ 3. 创建 📋 任务看板 ------------------
    task_fields = [{"name": "任务标题", "type": "text"}]
    task_table_id = create_table("📋 任务看板", task_fields)
    
    if task_table_id:
        create_field(task_table_id, "所属模块", "select", ["达人沟通", "达人管理", "物料管理", "运营推广"])
        create_field(task_table_id, "任务状态", "select", ["待处理", "进行中", "待审核", "已完成", "已延期"])
        create_field(task_table_id, "优先级", "select", ["P0-紧急", "P1-高", "P2-中", "P3-低"])
        create_field(task_table_id, "负责人", "user", multiple=True)
        create_field(task_table_id, "截止日期", "datetime")
        create_field(task_table_id, "延期天数", "number")
        create_field(task_table_id, "关联达人", "text")
        create_field(task_table_id, "备注", "text")
        
        # 创建看板视图
        create_view(task_table_id, "任务进度看板", "kanban")
        create_view(task_table_id, "任务甘特图", "gantt")
        
        # 插入任务数据
        task_samples = [
            {
                "任务标题": "与美妆达人A沟通确定脚本方向", "所属模块": "达人沟通", 
                "任务状态": "进行中", "优先级": "P1-高", "负责人": [{"id": CURRENT_USER_ID}],
                "截止日期": int(time.time() * 1000) + 86400 * 1 * 1000, 
                "延期天数": 0, "关联达人": "小红书美妆达人A"
            },
            {
                "任务标题": "美食博主B视频初剪", "所属模块": "物料管理", 
                "任务状态": "已延期", "优先级": "P0-紧急", "负责人": [{"id": CURRENT_USER_ID}],
                "截止日期": int(time.time() * 1000) - 86400 * 2 * 1000, 
                "延期天数": 2, "关联达人": "抖音美食博主B", "备注": "因达人素材提交延迟导致整体排期延后"
            },
            {
                "任务标题": "数码UP主C新品测评文案优化", "所属模块": "物料管理", 
                "任务状态": "待审核", "优先级": "P2-中", "负责人": [{"id": CURRENT_USER_ID}],
                "截止日期": int(time.time() * 1000) + 86400 * 2 * 1000, 
                "延期天数": 0, "关联达人": "B站数码UP主C"
            }
        ]
        for item in task_samples:
            insert_record(task_table_id, item)

    # ------------------ 4. 创建 💰 预算管控 ------------------
    budget_fields = [{"name": "费用项目", "type": "text"}]
    budget_table_id = create_table("💰 预算管控", budget_fields)
    
    if budget_table_id:
        create_field(budget_table_id, "费用类别", "select", ["达人费用", "物料制作", "话费", "差旅", "平台投放", "其他"])
        create_field(budget_table_id, "预算金额", "number")
        create_field(budget_table_id, "实际花费", "number")
        create_field(budget_table_id, "消耗率", "number")
        create_field(budget_table_id, "关联目标", "text")
        create_field(budget_table_id, "目标指标", "text")
        create_field(budget_table_id, "对应动作", "text")
        create_field(budget_table_id, "预警状态", "select", ["正常", "⚠️黄色预警(≥80%)", "🔴红色预警(≥95%)", "🚨已超支"])
        create_field(budget_table_id, "负责人", "user", multiple=True)
        create_field(budget_table_id, "备注", "text")
        
        # 创建看板视图
        create_view(budget_table_id, "预算状态预警", "kanban")
        
        # 插入预算数据
        budget_samples = [
            {
                "费用项目": "美食博主B置换与差旅补给", "费用类别": "差旅", 
                "预算金额": 1000, "实际花费": 980, "消耗率": 0.98,
                "关联目标": "同框近景视频发布", "目标指标": "单期播放量≥10万",
                "对应动作": "实地跟拍与后期包装", "预警状态": "🔴红色预警(≥95%)",
                "负责人": [{"id": CURRENT_USER_ID}], "备注": "由于包含随行话费补贴及打车发票，几乎达到预算上限"
            },
            {
                "费用项目": "小红书美妆达人A签约款", "费用类别": "达人费用", 
                "预算金额": 3000, "实际花费": 1500, "消耗率": 0.50,
                "关联目标": "引流加粉转化", "目标指标": "粉丝新增门槛1万",
                "对应动作": "美妆专栏推荐与口红置换", "预警状态": "正常",
                "负责人": [{"id": CURRENT_USER_ID}], "备注": "首笔款（50%定金）已付，尾款待交付发布后结算"
            },
            {
                "费用项目": "天台直播运营卡充值与话费", "费用类别": "话费", 
                "预算金额": 200, "实际花费": 240, "消耗率": 1.20,
                "关联目标": "直播过程网速保障", "目标指标": "直播不掉线",
                "对应动作": "流量包叠加充值", "预警状态": "🚨已超支",
                "负责人": [{"id": CURRENT_USER_ID}], "备注": "由于户外直播流量耗费超预期，电话费与叠加包产生超支情况"
            }
        ]
        for item in budget_samples:
            insert_record(budget_table_id, item)

    # ------------------ 5. 清理初始默认表格 ------------------
    # 查找默认表格的 ID 并删除（我们前面知道它的名称改为了“任务看板”，但是我们重新创建了“📋 任务看板”）
    # 再次读取当前的所有表格
    tables = get_tables()
    for t in tables:
        if t["table_name"] == "数据表" or t["table_name"] == "任务看板":
            print(f"正在清理默认初始表格 '{t['table_name']}' ({t['table_id']})...")
            delete_table(t["table_id"])
            time.sleep(0.5)

    print("\n🎉 看板搭建完成！")
    print(f"🔗 飞书多维表格链接: https://my.feishu.cn/base/{BASE_TOKEN}")

if __name__ == "__main__":
    main()
