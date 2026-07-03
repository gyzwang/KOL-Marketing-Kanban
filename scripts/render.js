const GIST_RAW_URL = "https://gist.githubusercontent.com/gyzwang/1a7c428ee04656882a416398851f4deb/raw/data.json";

document.addEventListener("DOMContentLoaded", () => {
    // 1. 初始化导航切换
    initNavigation();
    
    // 2. 载入并渲染数据
    loadDashboardData();
});

function loadDashboardData() {
    const syncTimeLabel = document.getElementById("sync-time-label");
    if (syncTimeLabel) {
        syncTimeLabel.innerText = "⏳ 正在同步云端...";
    }
    
    const timestamp = new Date().getTime();
    fetch(`${GIST_RAW_URL}?t=${timestamp}`)
        .then(res => {
            if (!res.ok) throw new Error("Gist load failed");
            return res.json();
        })
        .then(data => {
            renderDashboard(data);
        })
        .catch(err => {
            console.error("无法拉取 Gist 数据，尝试本地缓存: ", err);
            if (window.KOL_DATA) {
                renderDashboard(window.KOL_DATA);
            } else {
                if (syncTimeLabel) syncTimeLabel.innerText = "❌ 加载失败";
            }
        });
}

/* ==========================================================================
   🔗 导航路由切换
   ========================================================================== */
function initNavigation() {
    const menuItems = document.querySelectorAll(".menu-item");
    const tabContents = document.querySelectorAll(".tab-content");
    const pageTitle = document.getElementById("page-main-title");
    const pageSubtitle = document.getElementById("page-subtitle");
    
    const subtitles = {
        "dashboard-tab": "达人营销项目核心运营数据大盘",
        "kanban-tab": "敏捷协作与进度风险预警看板",
        "material-tab": "达人送审物料剪辑、优化及发布状态流",
        "kol-tab": "对接达人档案、建联进度与交付历史",
        "budget-tab": "预算消耗追踪与目标动作双向校验中心"
    };
    
    menuItems.forEach(item => {
        item.addEventListener("click", () => {
            const targetTabId = item.getAttribute("data-tab");
            
            // 切换菜单激活状态
            menuItems.forEach(i => i.classList.remove("active"));
            item.classList.add("active");
            
            // 切换内容页签激活状态
            tabContents.forEach(content => content.classList.remove("active"));
            document.getElementById(targetTabId).classList.add("active");
            
            // 更新标题和副标题
            pageTitle.innerText = item.querySelector("span").innerText;
            pageSubtitle.innerText = subtitles[targetTabId] || "";
        });
    });
}

/* ==========================================================================
   📊 主渲染管线
   ========================================================================== */
function renderDashboard(data) {
    // 填充上次更新时间
    document.getElementById("sync-time-label").innerText = data.last_updated || "未知";
    
    // 渲染各页签
    renderConsole(data);
    renderKanban(data);
    renderMaterials(data);
    renderKOLs(data);
    renderBudget(data);
}

/* ==========================================================================
   1. 仪表盘大盘 (Console rendering)
   ========================================================================== */
function renderConsole(data) {
    const tasks = data.tasks || [];
    const kols = data.kols || [];
    const budgets = data.budgets || [];
    const materials = data.materials || [];
    
    // 计算任务指标
    const activeTasks = tasks.filter(t => t["任务状态"] !== "已完成").length;
    const overdueTasks = tasks.filter(t => t["任务状态"] === "已延期").length;
    
    document.getElementById("dashboard-active-tasks").innerText = activeTasks;
    document.getElementById("dashboard-overdue-tasks").innerText = overdueTasks;
    document.getElementById("dashboard-kols-count").innerText = kols.length;
    
    // 计算预算消耗率
    let totalBudget = 0;
    let totalSpent = 0;
    budgets.forEach(b => {
        totalBudget += Number(b["预算金额"] || 0);
        totalSpent += Number(b["实际花费"] || 0);
    });
    const budgetPct = totalBudget > 0 ? Math.round((totalSpent / totalBudget) * 100) : 0;
    document.getElementById("dashboard-budget-ratio").innerText = `${budgetPct}%`;
    
    // 渲染流水线负荷进度条
    const stages = ["待接收素材", "素材已到", "剪辑中", "封面优化中", "标题优化中", "待审核", "已发布"];
    const stageCounts = {};
    stages.forEach(s => stageCounts[s] = 0);
    
    materials.forEach(m => {
        const s = m["物料状态"];
        if (stageCounts[s] !== undefined) {
            stageCounts[s]++;
        }
    });
    
    const pipelineList = document.getElementById("dashboard-pipeline-list");
    pipelineList.innerHTML = "";
    
    stages.forEach(stage => {
        const count = stageCounts[stage];
        const pct = materials.length > 0 ? (count / materials.length) * 100 : 0;
        
        const stepHTML = `
            <div class="pipeline-step-item">
                <div class="step-label">
                    <span>${stage}</span>
                    <strong>${count} 个物料 (${Math.round(pct)}%)</strong>
                </div>
                <div class="step-bar-bg">
                    <div class="step-bar-fill" style="width: ${pct}%"></div>
                </div>
            </div>
        `;
        pipelineList.innerHTML += stepHTML;
    });
    
    // 渲染高危拦截与延期风险列表
    const riskList = document.getElementById("dashboard-risk-list");
    riskList.innerHTML = "";
    
    let riskCount = 0;
    
    // 1. 抓取延期任务
    tasks.forEach(t => {
        if (t["任务状态"] === "已延期") {
            riskCount++;
            const riskHTML = `
                <div class="risk-item">
                    <div class="risk-title">
                        <i class="fa-solid fa-triangle-exclamation"></i>
                        <span>任务延期: ${t["任务标题"]}</span>
                    </div>
                    <div class="risk-desc">${t["备注"] || "未填写延期说明，需尽快推进。"}</div>
                    <div class="risk-meta">
                        <span>负责人: ${getAssigneesText(t["负责人"])}</span>
                        <span>延期天数: ${t["延期天数"] || 1} 天</span>
                    </div>
                </div>
            `;
            riskList.innerHTML += riskHTML;
        }
    });
    
    // 2. 抓取物料中的异常问题
    materials.forEach(m => {
        if (m["问题备注"] && m["物料状态"] !== "已发布") {
            riskCount++;
            const riskHTML = `
                <div class="risk-item">
                    <div class="risk-title">
                        <i class="fa-solid fa-triangle-exclamation" style="color:#ef4444;"></i>
                        <span>物料异常: ${m["物料名称"]}</span>
                    </div>
                    <div class="risk-desc">${m["问题备注"]}</div>
                    <div class="risk-meta">
                        <span>关联达人: ${m["关联达人"] || "无"}</span>
                        <span>当前环节: ${m["物料状态"]}</span>
                    </div>
                </div>
            `;
            riskList.innerHTML += riskHTML;
        }
    });
    
    if (riskCount === 0) {
        riskList.innerHTML = `
            <div style="text-align:center;padding:40px 0;color:var(--text-muted);">
                <i class="fa-regular fa-circle-check" style="font-size:32px;margin-bottom:10px;display:block;color:var(--success);"></i>
                暂无运行异常或延期风险
            </div>
        `;
    }
}

/* ==========================================================================
   2. 任务看板 (Kanban rendering)
   ========================================================================== */
function renderKanban(data) {
    const tasks = data.tasks || [];
    
    const colTodo = document.getElementById("col-todo");
    const colDoing = document.getElementById("col-doing");
    const colReview = document.getElementById("col-review");
    const colDone = document.getElementById("col-done");
    
    colTodo.innerHTML = "";
    colDoing.innerHTML = "";
    colReview.innerHTML = "";
    colDone.innerHTML = "";
    
    let countTodo = 0, countDoing = 0, countReview = 0, countDone = 0;
    
    tasks.forEach(t => {
        const state = t["任务状态"];
        const priorityClass = (t["优先级"] || "").split("-")[0].toLowerCase(); // p0, p1, p2, p3
        const isOverdue = state === "已延期";
        
        const cardHTML = `
            <div class="kanban-card ${isOverdue ? 'overdue' : ''}">
                <div class="card-header">
                    <span class="tag-module">${t["所属模块"] || "未分类"}</span>
                    <span class="tag-priority ${priorityClass}">${t["优先级"] || "P2-中"}</span>
                </div>
                <div class="card-title">${t["任务标题"]}</div>
                ${t["备注"] ? `<div style="font-size:11px;color:var(--text-secondary);background:rgba(255,255,255,0.02);padding:6px;border-radius:6px;margin-top:4px;">${t["备注"]}</div>` : ''}
                <div class="card-meta">
                    <div class="card-assignee">
                        <div class="assignee-avatar">${getAssigneeInitials(t["负责人"])}</div>
                        <span>${getAssigneesText(t["负责人"])}</span>
                    </div>
                    ${isOverdue ? `<span class="overdue-badge">延期 ${t["延期天数"] || 1}天</span>` : `<span>截止: ${formatDate(t["截止日期"])}</span>`}
                </div>
            </div>
        `;
        
        if (state === "待处理") {
            colTodo.innerHTML += cardHTML;
            countTodo++;
        } else if (state === "进行中") {
            colDoing.innerHTML += cardHTML;
            countDoing++;
        } else if (state === "待审核") {
            colReview.innerHTML += cardHTML;
            countReview++;
        } else {
            // 已完成 / 已延期 放入最后一列
            colDone.innerHTML += cardHTML;
            countDone++;
        }
    });
    
    document.getElementById("count-todo").innerText = countTodo;
    document.getElementById("count-doing").innerText = countDoing;
    document.getElementById("count-review").innerText = countReview;
    document.getElementById("count-done").innerText = countDone;
}

/* ==========================================================================
   3. 物料流水线 (Material rendering)
   ========================================================================== */
function renderMaterials(data) {
    const materials = data.materials || [];
    
    // 物料状态分组映射
    const cols = {
        "待接收素材": document.getElementById("m-col-1"),
        "素材已到": document.getElementById("m-col-2"),
        "剪辑中": document.getElementById("m-col-2"),  // 剪辑中归类在第二列
        "封面优化中": document.getElementById("m-col-3"),
        "标题优化中": document.getElementById("m-col-3"), // 标题优化归类在第三列
        "待审核": document.getElementById("m-col-4"),
        "已发布": document.getElementById("m-col-5")
    };
    
    // 清空列
    Object.values(cols).forEach(col => {
        if(col) col.innerHTML = "";
    });
    
    const counts = { 1:0, 2:0, 3:0, 4:0, 5:0 };
    
    materials.forEach(m => {
        const state = m["物料状态"];
        
        // 判定复选框激活
        const clipOk = m["剪辑完成"] === true;
        const coverOk = m["封面完成"] === true;
        const textOk = m["标题简介完成"] === true;
        const auditOk = m["审核通过"] === true;
        
        const cardHTML = `
            <div class="material-card">
                <div class="material-title">${m["物料名称"]}</div>
                <div class="material-kol">
                    <i class="fa-regular fa-user"></i>
                    <span>${m["关联达人"] || "未绑定达人"}</span>
                </div>
                <div class="checks-grid">
                    <span class="check-dot ${clipOk ? 'checked' : ''}">剪辑</span>
                    <span class="check-dot ${coverOk ? 'checked' : ''}">封面</span>
                    <span class="check-dot ${textOk ? 'checked' : ''}">文案</span>
                    <span class="check-dot ${auditOk ? 'checked' : ''}">审核</span>
                </div>
                ${m["问题备注"] ? `<div style="font-size:10px;color:#fca5a5;margin-top:6px;line-height:1.3;"><i class="fa-solid fa-circle-info" style="margin-right:4px;"></i>${m["问题备注"]}</div>` : ''}
                <div class="card-meta">
                    <span>${getAssigneesText(m["当前环节负责人"])}</span>
                    <span style="font-size:10px;color:var(--text-muted);">${m["计划发布日期"] ? '发: ' + formatDate(m["计划发布日期"]) : ''}</span>
                </div>
            </div>
        `;
        
        if (state === "待接收素材") {
            cols["待接收素材"].innerHTML += cardHTML;
            counts[1]++;
        } else if (state === "素材已到" || state === "剪辑中") {
            cols["素材已到"].innerHTML += cardHTML;
            counts[2]++;
        } else if (state === "封面优化中" || state === "标题优化中") {
            cols["封面优化中"].innerHTML += cardHTML;
            counts[3]++;
        } else if (state === "待审核") {
            cols["待审核"].innerHTML += cardHTML;
            counts[4]++;
        } else if (state === "已发布") {
            cols["已发布"].innerHTML += cardHTML;
            counts[5]++;
        }
    });
    
    // 更新计数
    for (let i = 1; i <= 5; i++) {
        document.getElementById(`m-count-${i}`).innerText = counts[i];
    }
}

/* ==========================================================================
   4. 达人库列表 (KOL table rendering)
   ========================================================================== */
function renderKOLs(data) {
    const kols = data.kols || [];
    const tbody = document.getElementById("kol-table-body");
    tbody.innerHTML = "";
    
    kols.forEach(k => {
        // 解析平台
        const platform = Array.isArray(k["平台"]) ? k["平台"][0] : k["平台"] || "其他";
        const state = Array.isArray(k["合作状态"]) ? k["合作状态"][0] : k["合作状态"] || "沟通中";
        
        const rowHTML = `
            <tr>
                <td style="font-weight:600;color:#fff;">${k["达人名称"]}</td>
                <td><span class="tag-platform ${platform}">${platform}</span></td>
                <td style="font-family:'Outfit';">${formatFans(k["粉丝量"])}</td>
                <td>${getAssigneesText(k["对接人"])}</td>
                <td>${k["合作类型"] || "未指定"}</td>
                <td><span class="status-badge ${state}">${state}</span></td>
                <td style="font-family:'Outfit';text-align:center;">${k["已交付物料数"] || 0}</td>
                <td style="max-width:300px;font-size:12px;color:var(--text-secondary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="${k["沟通记录"] || ''}">
                    ${k["沟通记录"] || "-"}
                </td>
            </tr>
        `;
        tbody.innerHTML += rowHTML;
    });
}

/* ==========================================================================
   5. 预算与目标动作中心 (Budget rendering)
   ========================================================================== */
function renderBudget(data) {
    const budgets = data.budgets || [];
    
    let totalBudget = 0;
    let totalSpent = 0;
    
    const mappingList = document.getElementById("budget-mapping-list");
    mappingList.innerHTML = "";
    
    budgets.forEach(b => {
        const budget = Number(b["预算金额"] || 0);
        const spent = Number(b["实际花费"] || 0);
        totalBudget += budget;
        totalSpent += spent;
        
        const pct = budget > 0 ? Math.round((spent / budget) * 100) : 0;
        
        // 判定预警级别
        let warningText = "正常";
        let warningClass = "normal";
        
        if (pct >= 100) {
            warningText = "🚨已超支";
            warningClass = "overrun";
        } else if (pct >= 95) {
            warningText = "🔴红色预警(≥95%)";
            warningClass = "red";
        } else if (pct >= 80) {
            warningText = "⚠️黄色预警(≥80%)";
            warningClass = "yellow";
        }
        
        const cardHTML = `
            <div class="mapping-card">
                <div class="mapping-row-1">
                    <span class="mapping-target">🎯 目标: ${b["关联目标"] || "未绑定目标"}</span>
                    <span class="mapping-kpi">${b["目标指标"] || "常规监测"}</span>
                </div>
                <div class="mapping-action">
                    <i class="fa-solid fa-angles-right" style="color:var(--primary);"></i>
                    <span>动作: ${b["对应动作"] || "日常运营推进"}</span>
                </div>
                <div style="font-size:12px;color:var(--text-muted);">
                    费用项目: <strong>${b["费用项目"]}</strong> (${b["费用类别"] || "其他"})
                </div>
                <div class="mapping-costs">
                    <div class="cost-group">
                        <div class="cost-item"><span>预算:</span><strong>¥${budget.toLocaleString()}</strong></div>
                        <div class="cost-item"><span>实际:</span><strong>¥${spent.toLocaleString()}</strong></div>
                        <div class="cost-item"><span>消耗:</span><strong style="color:${pct >= 100 ? 'var(--danger)' : '#fff'}">${pct}%</strong></div>
                    </div>
                    <span class="warning-badge ${warningClass}">${warningText}</span>
                </div>
            </div>
        `;
        mappingList.innerHTML += cardHTML;
    });
    
    // 更新左侧环形进度表
    const totalPct = totalBudget > 0 ? Math.round((totalSpent / totalBudget) * 100) : 0;
    document.getElementById("budget-gauge-pct").innerText = `${totalPct}%`;
    document.getElementById("budget-ratio-label").innerText = `¥${totalSpent.toLocaleString()} / ¥${totalBudget.toLocaleString()}`;
    
    // svg 进度渲染
    const circle = document.getElementById("budget-gauge-fill");
    if(circle) {
        // 周长是 2 * pi * r = 2 * 3.14159 * 70 = 439.8 ≈ 440
        const strokeDashoffset = 440 - (440 * Math.min(totalPct, 100)) / 100;
        circle.style.strokeDashoffset = strokeDashoffset;
        
        // 超支预警颜色替换
        if (totalPct >= 100) {
            circle.style.stroke = "var(--danger)";
        } else if (totalPct >= 80) {
            circle.style.stroke = "var(--warning)";
        } else {
            circle.style.stroke = "url(#primaryGrad)";
        }
    }
}

/* ==========================================================================
   🧮 辅助工具函数 (Helper functions)
   ========================================================================== */
function formatDate(timePayload) {
    if (!timePayload) return "-";
    try {
        const date = new Date(Number(timePayload));
        if (isNaN(date.getTime())) return "-";
        return `${date.getMonth() + 1}/${date.getDate()}`;
    } catch(e) {
        return "-";
    }
}

function formatFans(num) {
    if (!num) return "-";
    const n = Number(num);
    if (n >= 10000) {
        return `${(n / 10000).toFixed(1)}W`;
    }
    return n.toLocaleString();
}

function getAssigneesText(assignees) {
    if (!assignees) return "无";
    if (Array.isArray(assignees)) {
        return assignees.map(a => a.name || "未知").join(", ");
    }
    return assignees.name || String(assignees);
}

function getAssigneeInitials(assignees) {
    if (!assignees || !Array.isArray(assignees) || assignees.length === 0) return "无";
    const name = assignees[0].name || "无";
    return name.charAt(0);
}
