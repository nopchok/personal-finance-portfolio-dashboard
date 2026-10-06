"""
Plotly Chart Generators with Minimal Light / Tailwind Theme
Clean palettes, smooth curves, soft gridlines, and high contrast typography.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict, Any

# Tailwind / Minimal Light theme color palette
PALETTE = [
    "#4F46E5",  # Indigo-600
    "#10B981",  # Emerald-500
    "#0284C7",  # Sky-600
    "#F59E0B",  # Amber-500
    "#8B5CF6",  # Violet-500
    "#E11D48",  # Rose-600
    "#0D9488",  # Teal-600
    "#EA580C",  # Orange-600
    "#64748B",  # Slate-500
]

CHART_LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Plus Jakarta Sans, Prompt, sans-serif", color="#64748B", size=12),
    margin=dict(l=20, r=20, t=35, b=20),
    hoverlabel=dict(
        bgcolor="#FFFFFF",
        bordercolor="#CBD5E1",
        font=dict(family="Plus Jakarta Sans, Prompt, sans-serif", color="#0F172A", size=12)
    )
)

def create_allocation_donut(df: pd.DataFrame, group_col: str = "category", val_col: str = "current_value", title: str = "สัดส่วนพอร์ตการลงทุน"):
    if df.empty or df[val_col].sum() == 0:
        fig = go.Figure()
        fig.add_annotation(text="ยังไม่มีข้อมูลสินทรัพย์", showarrow=False, font=dict(size=14, color="#94A3B8"))
        fig.update_layout(**CHART_LAYOUT_BASE, height=320)
        return fig

    grouped = df.groupby(group_col)[val_col].sum().reset_index()
    grouped = grouped[grouped[val_col] > 0].sort_values(by=val_col, ascending=False)
    
    total_val = grouped[val_col].sum()
    
    fig = go.Figure(data=[go.Pie(
        labels=grouped[group_col],
        values=grouped[val_col],
        hole=0.68,
        marker=dict(colors=PALETTE[:len(grouped)], line=dict(color="#FFFFFF", width=2)),
        textinfo="percent",
        textfont=dict(color="#FFFFFF", size=11, family="Plus Jakarta Sans"),
        hovertemplate="<b>%{label}</b><br>มูลค่า: ฿%{value:,.0f}<br>สัดส่วน: %{percent:.1%}<extra></extra>"
    )])

    fig.add_annotation(
        text=f"<span style='font-size:12px;color:#64748B;'>มูลค่ารวม</span><br><b style='font-size:18px;color:#0F172A;'>฿{total_val:,.0f}</b>",
        showarrow=False,
        x=0.5, y=0.5,
        font=dict(family="Plus Jakarta Sans, Prompt")
    )

    fig.update_layout(
        **CHART_LAYOUT_BASE,
        title=dict(text=title, font=dict(color="#0F172A", size=14, weight=700), x=0.02),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color="#64748B")
        ),
        height=340
    )
    return fig

def create_expense_donut(df: pd.DataFrame, group_col: str = "category", val_col: str = "estimated_amount", title: str = "สัดส่วนประมาณการรายจ่ายตามหมวดหมู่"):
    if df.empty or df[val_col].sum() == 0:
        fig = go.Figure()
        fig.add_annotation(text="ยังไม่มีข้อมูลรายจ่าย", showarrow=False, font=dict(size=14, color="#94A3B8"))
        fig.update_layout(**CHART_LAYOUT_BASE, height=320)
        return fig

    grouped = df.groupby(group_col)[val_col].sum().reset_index()
    grouped = grouped[grouped[val_col] > 0].sort_values(by=val_col, ascending=False)
    total_val = grouped[val_col].sum()
    
    fig = go.Figure(data=[go.Pie(
        labels=grouped[group_col],
        values=grouped[val_col],
        hole=0.68,
        marker=dict(colors=PALETTE[:len(grouped)], line=dict(color="#FFFFFF", width=2)),
        textinfo="percent",
        textfont=dict(color="#FFFFFF", size=11, family="Plus Jakarta Sans"),
        hovertemplate="<b>%{label}</b><br>ประมาณการ: ฿%{value:,.0f}/ด.<br>สัดส่วน: %{percent:.1%}<extra></extra>"
    )])

    fig.add_annotation(
        text=f"<span style='font-size:11px;color:#64748B;'>รายจ่ายรวม</span><br><b style='font-size:17px;color:#E11D48;'>฿{total_val:,.0f}</b>",
        showarrow=False,
        x=0.5, y=0.5,
        font=dict(family="Plus Jakarta Sans, Prompt")
    )

    fig.update_layout(
        **CHART_LAYOUT_BASE,
        title=dict(text=title, font=dict(color="#0F172A", size=14, weight=700), x=0.02),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color="#64748B")
        ),
        height=340
    )
    return fig

def create_income_donut(df: pd.DataFrame, group_col: str = "category", val_col: str = "estimated_amount", title: str = "สัดส่วนประมาณการรายได้ตามหมวดหมู่"):
    if df.empty or df[val_col].sum() == 0:
        fig = go.Figure()
        fig.add_annotation(text="ยังไม่มีข้อมูลรายได้", showarrow=False, font=dict(size=14, color="#94A3B8"))
        fig.update_layout(**CHART_LAYOUT_BASE, height=320)
        return fig

    grouped = df.groupby(group_col)[val_col].sum().reset_index()
    grouped = grouped[grouped[val_col] > 0].sort_values(by=val_col, ascending=False)
    total_val = grouped[val_col].sum()
    
    fig = go.Figure(data=[go.Pie(
        labels=grouped[group_col],
        values=grouped[val_col],
        hole=0.68,
        marker=dict(colors=PALETTE[:len(grouped)], line=dict(color="#FFFFFF", width=2)),
        textinfo="percent",
        textfont=dict(color="#FFFFFF", size=11, family="Plus Jakarta Sans"),
        hovertemplate="<b>%{label}</b><br>ประมาณการ: ฿%{value:,.0f}/ด.<br>สัดส่วน: %{percent:.1%}<extra></extra>"
    )])

    fig.add_annotation(
        text=f"<span style='font-size:11px;color:#64748B;'>รายได้รวม</span><br><b style='font-size:17px;color:#059669;'>฿{total_val:,.0f}</b>",
        showarrow=False,
        x=0.5, y=0.5,
        font=dict(family="Plus Jakarta Sans, Prompt")
    )

    fig.update_layout(
        **CHART_LAYOUT_BASE,
        title=dict(text=title, font=dict(color="#0F172A", size=14, weight=700), x=0.02),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color="#64748B")
        ),
        height=340
    )
    return fig

def create_target_vs_actual_chart(comparison_df: pd.DataFrame):
    if comparison_df.empty:
        fig = go.Figure()
        fig.update_layout(**CHART_LAYOUT_BASE, height=300)
        return fig

    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name="สัดส่วนปัจจุบัน (Actual)",
        x=comparison_df["category"],
        y=comparison_df["actual_pct"],
        marker_color="#4F46E5",
        hovertemplate="<b>%{x}</b><br>ปัจจุบัน: %{y:.1f}%<extra></extra>",
        width=0.35
    ))

    fig.add_trace(go.Bar(
        name="เป้าหมาย (Target)",
        x=comparison_df["category"],
        y=comparison_df["target_pct"],
        marker_color="#CBD5E1",
        hovertemplate="<b>%{x}</b><br>เป้าหมาย: %{y:.1f}%<extra></extra>",
        width=0.35
    ))

    fig.update_layout(
        **CHART_LAYOUT_BASE,
        title=dict(text="สัดส่วนปัจจุบัน vs สัดส่วนเป้าหมาย (Asset Allocation %)", font=dict(color="#0F172A", size=14, weight=700), x=0.02),
        barmode="group",
        bargap=0.25,
        bargroupgap=0.1,
        xaxis=dict(
            showgrid=False,
            color="#64748B",
            tickfont=dict(size=11)
        ),
        yaxis=dict(
            title="สัดส่วน (%)",
            showgrid=True,
            gridcolor="#F1F5F9",
            color="#64748B",
            ticksuffix="%"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#64748B")
        ),
        height=320
    )
    return fig

def create_cashflow_waterfall(income: float, fixed_exp: float, var_exp: float, savings: float):
    fig = go.Figure(go.Waterfall(
        name="Cash Flow",
        orientation="v",
        measure=["relative", "relative", "relative", "total"],
        x=["รายได้รวม (Income)", "ค่าใช้จ่ายคงที่ (Fixed)", "ประมาณการใช้จ่าย (Variable)", "เงินออม/ลงทุนสุทธิ (Savings)"],
        textposition="outside",
        text=[f"+฿{income:,.0f}", f"-฿{fixed_exp:,.0f}", f"-฿{var_exp:,.0f}", f"฿{savings:,.0f}"],
        y=[income, -fixed_exp, -var_exp, savings],
        connector={"line": {"color": "#CBD5E1", "dash": "dot"}},
        decreasing={"marker": {"color": "#E11D48"}},
        increasing={"marker": {"color": "#10B981"}},
        totals={"marker": {"color": "#4F46E5"}}
    ))

    fig.update_layout(
        **CHART_LAYOUT_BASE,
        title=dict(text="ผังกระแสเงินสดรายเดือน (Monthly Cash Flow Waterfall)", font=dict(color="#0F172A", size=14, weight=700), x=0.02),
        yaxis=dict(
            title="จำนวนเงิน (บาท)",
            showgrid=True,
            gridcolor="#F1F5F9",
            color="#64748B",
            tickprefix="฿"
        ),
        xaxis=dict(showgrid=False, color="#64748B"),
        height=340
    )
    return fig

def create_budget_rule_gauge(income: float, fixed_exp: float, var_exp: float, savings: float):
    if income <= 0:
        return go.Figure()
        
    needs_pct = (fixed_exp / income) * 100
    wants_pct = (var_exp / income) * 100
    savings_pct = (savings / income) * 100
    
    fig = go.Figure()

    # Actual Stacked Bar
    fig.add_trace(go.Bar(
        name="จำเป็น (Needs)",
        y=["สัดส่วนปัจจุบัน", "เกณฑ์มาตรฐาน (50/30/20)"],
        x=[needs_pct, 50],
        orientation="h",
        marker=dict(color="#0284C7"),
        text=[f"{needs_pct:.1f}%", "50%"],
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color="#FFFFFF", size=11, family="Plus Jakarta Sans")
    ))
    
    fig.add_trace(go.Bar(
        name="ใช้จ่ายตามใจ (Wants)",
        y=["สัดส่วนปัจจุบัน", "เกณฑ์มาตรฐาน (50/30/20)"],
        x=[wants_pct, 30],
        orientation="h",
        marker=dict(color="#F59E0B"),
        text=[f"{wants_pct:.1f}%", "30%"],
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color="#FFFFFF", size=11, family="Plus Jakarta Sans")
    ))
    
    fig.add_trace(go.Bar(
        name="เงินออม/ลงทุน (Savings)",
        y=["สัดส่วนปัจจุบัน", "เกณฑ์มาตรฐาน (50/30/20)"],
        x=[savings_pct, 20],
        orientation="h",
        marker=dict(color="#10B981"),
        text=[f"{savings_pct:.1f}%", "20%"],
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color="#FFFFFF", size=11, family="Plus Jakarta Sans")
    ))

    fig.update_layout(
        **CHART_LAYOUT_BASE,
        title=dict(text="การจัดสรรตามเกณฑ์ 50/30/20 Rule", font=dict(color="#0F172A", size=14, weight=700), x=0.02),
        barmode="stack",
        xaxis=dict(
            showgrid=False,
            range=[0, max(100, needs_pct + wants_pct + savings_pct)],
            ticksuffix="%",
            color="#64748B"
        ),
        yaxis=dict(showgrid=False, color="#64748B"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#64748B")
        ),
        height=220
    )
    return fig

def create_fire_projection_chart(current_nw: float, monthly_invest: float, years: int = 25, expected_return: float = 7.0, fire_target: float = 10000000):
    months = years * 12
    x_years = [i / 12 for i in range(months + 1)]
    
    def calc_future_values(annual_rate):
        r = annual_rate / 100 / 12
        values = []
        for m in range(months + 1):
            if r == 0:
                fv = current_nw + (monthly_invest * m)
            else:
                fv = current_nw * ((1 + r) ** m) + monthly_invest * (((1 + r) ** m - 1) / r)
            values.append(fv)
        return values

    val_cons = calc_future_values(max(1.0, expected_return - 2.5))
    val_mod = calc_future_values(expected_return)
    val_agg = calc_future_values(expected_return + 3.0)
    
    fig = go.Figure()
    
    # Aggressive
    fig.add_trace(go.Scatter(
        x=x_years,
        y=val_agg,
        mode="lines",
        name=f"ผลตอบแทนสูง ({expected_return + 3:.1f}%)",
        line=dict(color="#10B981", width=1.5, dash="dash"),
        hovertemplate="ปีที่ %{x:.1f}: ฿%{y:,.0f}<extra></extra>"
    ))

    # Moderate / Primary
    fig.add_trace(go.Scatter(
        x=x_years,
        y=val_mod,
        mode="lines",
        name=f"คาดการณ์หลัก ({expected_return:.1f}%)",
        line=dict(color="#4F46E5", width=3),
        fill="tozeroy",
        fillcolor="rgba(79, 70, 229, 0.08)",
        hovertemplate="ปีที่ %{x:.1f}: ฿%{y:,.0f}<extra></extra>"
    ))

    # Conservative
    fig.add_trace(go.Scatter(
        x=x_years,
        y=val_cons,
        mode="lines",
        name=f"แบบระมัดระวัง ({max(1.0, expected_return - 2.5):.1f}%)",
        line=dict(color="#F59E0B", width=1.5, dash="dot"),
        hovertemplate="ปีที่ %{x:.1f}: ฿%{y:,.0f}<extra></extra>"
    ))

    # Target FIRE line
    if fire_target > 0:
        fig.add_hline(
            y=fire_target,
            line_dash="dash",
            line_color="#E11D48",
            annotation_text=f"เป้าหมายอิสรภาพการเงิน ฿{fire_target:,.0f}",
            annotation_position="top left",
            annotation_font=dict(color="#E11D48", size=11)
        )

    fig.update_layout(
        **CHART_LAYOUT_BASE,
        title=dict(text=f"การเติบโตของพอร์ตและความมั่งคั่ง ({years} ปีข้างหน้า)", font=dict(color="#0F172A", size=14, weight=700), x=0.02),
        xaxis=dict(
            title="จำนวนปีนับจากปัจจุบัน (Years)",
            showgrid=True,
            gridcolor="#F1F5F9",
            color="#64748B"
        ),
        yaxis=dict(
            title="มูลค่าพอร์ต (บาท)",
            showgrid=True,
            gridcolor="#F1F5F9",
            color="#64748B",
            tickprefix="฿"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#64748B")
        ),
        height=380
    )
    return fig

def create_historical_trend_chart(snapshots: List[Dict[str, Any]]):
    if not snapshots:
        fig = go.Figure()
        fig.add_annotation(text="ยังไม่มีข้อมูลประวัติย้อนหลัง (บันทึก Snapshot รายเดือนได้ที่แท็บตั้งค่า)", showarrow=False, font=dict(size=13, color="#94A3B8"))
        fig.update_layout(**CHART_LAYOUT_BASE, height=280)
        return fig

    df = pd.DataFrame(snapshots)
    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="สินทรัพย์รวม (Assets)",
        x=df["snapshot_month"],
        y=df["total_assets"],
        marker_color="#10B981",
        hovertemplate="เดือน %{x}<br>สินทรัพย์: ฿%{y:,.0f}<extra></extra>"
    ))

    fig.add_trace(go.Bar(
        name="หนี้สินรวม (Debts)",
        x=df["snapshot_month"],
        y=df["total_debts"],
        marker_color="#E11D48",
        hovertemplate="เดือน %{x}<br>หนี้สิน: ฿%{y:,.0f}<extra></extra>"
    ))

    fig.add_trace(go.Scatter(
        name="Net Worth",
        x=df["snapshot_month"],
        y=df["net_worth"],
        mode="lines+markers",
        line=dict(color="#0284C7", width=3),
        marker=dict(size=7, color="#0284C7"),
        hovertemplate="เดือน %{x}<br>Net Worth: ฿%{y:,.0f}<extra></extra>"
    ))

    fig.update_layout(
        **CHART_LAYOUT_BASE,
        title=dict(text="ประวัติและแนวโน้มความมั่งคั่ง (Monthly Historical Trend)", font=dict(color="#0F172A", size=14, weight=700), x=0.02),
        barmode="group",
        xaxis=dict(showgrid=False, color="#64748B"),
        yaxis=dict(
            title="จำนวนเงิน (บาท)",
            showgrid=True,
            gridcolor="#F1F5F9",
            color="#64748B",
            tickprefix="฿"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#64748B")
        ),
        height=320
    )
    return fig
