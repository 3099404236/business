#!/usr/bin/env python3
"""
招商银行久期缺口分析
基于重新定价缺口数据估算久期缺口，并分析其与利率变化的关系
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

# 重新定价缺口数据（单位：亿元）
# 数据来源：招商银行2019-2023年度报告
gap_data = {
    '年份': [2019, 2020, 2021, 2022, 2023],
    '3个月或以下': [-15239, -21908, -24288, -29356, -25839],
    '3个月至1年': [14516, 18873, 20081, 24052, 19554],
    '1年至5年': [1947, 3609, 3546, 2361, 2632],
    '5年以上': [4211, 5836, 8183, 11583, 13328]
}

# 利率数据
interest_rate_data = {
    '年份': [2019, 2020, 2021, 2022, 2023],
    '生息资产收益率': [4.38, 4.13, 3.98, 3.89, 3.76],
    '计息负债成本率': [1.90, 1.73, 1.59, 1.61, 1.73],
    '净利差': [2.48, 2.40, 2.39, 2.28, 2.03]
}

# 总资产数据（单位：亿元）- 从年报中提取
# 用于计算加权平均久期和久期缺口
total_assets = {
    2019: 73000,  # 约7.3万亿
    2020: 81000,  # 约8.1万亿
    2021: 89000,  # 约8.9万亿
    2022: 94000,  # 约9.4万亿
    2023: 100000  # 约10万亿
}

def calculate_duration_from_gap(gap_df, year):
    """
    基于重新定价缺口数据估算久期

    方法：
    1. 为每个期限段分配一个估计的修正久期（Modified Duration）
    2. 使用缺口数据反推资产和负债在各期限段的分布
    3. 计算加权平均久期

    期限段久期估计：
    - 3个月或以下：0.125年（约1.5个月）
    - 3个月至1年：0.625年（约7.5个月）
    - 1年至5年：3年（期限中点）
    - 5年以上：7年（保守估计，考虑到存款和长期贷款的特性）
    """

    # 各期限段的估计久期（单位：年）
    duration_estimates = {
        '3个月或以下': 0.125,
        '3个月至1年': 0.625,
        '1年至5年': 3.0,
        '5年以上': 7.0
    }

    # 获取该年份的数据
    year_data = gap_df[gap_df['年份'] == year].iloc[0]

    # 从缺口推算资产和负债
    # 缺口 = 资产 - 负债
    # 我们需要估算各期限段的资产和负债规模

    # 方法：基于总资产和缺口的比例关系估算
    # 这里使用简化假设：总缺口 = 净资产（股东权益）
    total_gap = sum([year_data[period] for period in duration_estimates.keys()])
    total_asset = total_assets[year]
    total_liability = total_asset - total_gap

    # 对于负缺口期限，负债 = 资产 + |缺口|
    # 对于正缺口期限，资产 = 负债 + 缺口

    asset_distribution = {}
    liability_distribution = {}

    # 简化处理：假设短期主要是负债主导，长期主要是资产主导
    # 根据银行特性调整
    for period in duration_estimates.keys():
        gap = year_data[period]

        if period == '3个月或以下':
            # 短期负债占优（存款为主）
            # 假设这个期限段的资产规模为总资产的30%
            asset = total_asset * 0.30
            liability = asset + abs(gap)
        elif period == '3个月至1年':
            # 中短期有正缺口，资产占优
            asset = total_asset * 0.25
            liability = asset - gap
        elif period == '1年至5年':
            # 中期
            asset = total_asset * 0.25
            liability = asset - gap
        else:  # 5年以上
            # 长期资产占优（长期贷款）
            asset = total_asset * 0.20
            liability = asset - gap

        asset_distribution[period] = max(0, asset)
        liability_distribution[period] = max(0, liability)

    # 计算加权平均久期
    total_weighted_duration_asset = 0
    total_weighted_duration_liability = 0
    total_asset_amount = sum(asset_distribution.values())
    total_liability_amount = sum(liability_distribution.values())

    duration_details = []

    for period in duration_estimates.keys():
        duration = duration_estimates[period]
        asset_amt = asset_distribution[period]
        liability_amt = liability_distribution[period]

        weighted_duration_asset = (asset_amt / total_asset_amount) * duration
        weighted_duration_liability = (liability_amt / total_liability_amount) * duration

        total_weighted_duration_asset += weighted_duration_asset
        total_weighted_duration_liability += weighted_duration_liability

        duration_details.append({
            '期限段': period,
            '估计久期': duration,
            '资产规模': asset_amt,
            '负债规模': liability_amt,
            '缺口': year_data[period]
        })

    # 久期缺口 = 资产久期 - (负债/资产) * 负债久期
    leverage_ratio = total_liability_amount / total_asset_amount
    duration_gap = total_weighted_duration_asset - leverage_ratio * total_weighted_duration_liability

    return {
        'year': year,
        'asset_duration': total_weighted_duration_asset,
        'liability_duration': total_weighted_duration_liability,
        'leverage_ratio': leverage_ratio,
        'duration_gap': duration_gap,
        'details': duration_details
    }


def main():
    print("="*70)
    print("招商银行2019-2023年久期缺口分析")
    print("="*70)
    print()

    # 创建数据框
    gap_df = pd.DataFrame(gap_data)
    rate_df = pd.DataFrame(interest_rate_data)

    print("【数据来源】")
    print("1. 重新定价缺口数据：招商银行2019-2023年度报告")
    print("2. 利率数据：招商银行2019-2023年度报告")
    print()

    # 计算每年的久期缺口
    duration_results = []

    for year in gap_df['年份']:
        result = calculate_duration_from_gap(gap_df, year)
        duration_results.append(result)

        print(f"\n【{year}年久期分析】")
        print(f"资产加权平均久期：{result['asset_duration']:.3f} 年")
        print(f"负债加权平均久期：{result['liability_duration']:.3f} 年")
        print(f"杠杆比率（负债/资产）：{result['leverage_ratio']:.3f}")
        print(f"久期缺口：{result['duration_gap']:.3f} 年")
        print()

        # 打印详细分布
        print("各期限段分布：")
        df_details = pd.DataFrame(result['details'])
        print(df_details.to_string(index=False))
        print()

    # 汇总分析
    print("\n" + "="*70)
    print("【久期缺口与利率变化趋势分析】")
    print("="*70)
    print()

    # 创建汇总表
    summary_data = {
        '年份': [r['year'] for r in duration_results],
        '资产久期': [f"{r['asset_duration']:.3f}" for r in duration_results],
        '负债久期': [f"{r['liability_duration']:.3f}" for r in duration_results],
        '久期缺口': [f"{r['duration_gap']:.3f}" for r in duration_results],
        '净利差(%)': rate_df['净利差'].tolist()
    }

    summary_df = pd.DataFrame(summary_data)
    print(summary_df.to_string(index=False))
    print()

    # 计算变化趋势
    print("\n【变化趋势分析】")
    print()

    duration_gaps = [r['duration_gap'] for r in duration_results]
    net_interest_margins = rate_df['净利差'].tolist()

    for i in range(1, len(duration_results)):
        year = duration_results[i]['year']
        prev_year = duration_results[i-1]['year']

        gap_change = duration_gaps[i] - duration_gaps[i-1]
        nim_change = net_interest_margins[i] - net_interest_margins[i-1]

        print(f"{prev_year}-{year}年：")
        print(f"  久期缺口变化：{gap_change:+.3f} 年 ({'扩大' if gap_change > 0 else '缩小'})")
        print(f"  净利差变化：{nim_change:+.2f}% ({abs(nim_change*100):+.0f} bp)")

        # 判断一致性
        # 久期缺口为正：资产久期 > 加权负债久期，利率上升有利，利率下降不利
        # 久期缺口为负：负债久期 > 加权资产久期，利率下降有利，利率上升不利

        if gap_change * nim_change < 0:
            consistency = "一致"
        else:
            consistency = "不一致"

        print(f"  趋势一致性：{consistency}")
        print()

    # 生成图表
    generate_charts(duration_results, rate_df)

    print("\n【分析结论】")
    print()
    print("1. 久期缺口特征：")
    if all(r['duration_gap'] > 0 for r in duration_results):
        print("   - 招商银行在2019-2023年期间久期缺口均为正值")
        print("   - 说明资产久期长于负债久期（经杠杆调整后）")
        print("   - 这意味着利率上升对银行不利，利率下降对银行有利")

    print()
    print("2. 与利率变化的关系：")
    print("   - 2019-2023年期间，市场利率整体呈下降趋势")
    print("   - 净利差从2.48%下降至2.03%，累计下降45bp")
    print("   - 久期缺口的变化反映了银行对利率风险的管理调整")

    print()
    print("3. 风险管理启示：")
    print("   - 正久期缺口使银行面临利率下行风险")
    print("   - 银行需要通过调整资产负债结构或使用衍生品对冲")
    print("   - 久期缺口管理是利率风险管理的重要工具")

    print()
    print("="*70)
    print("分析完成！图表已保存为 duration_gap_analysis.png")
    print("="*70)


def generate_charts(duration_results, rate_df):
    """生成分析图表"""

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('招商银行2019-2023年久期缺口与利率变化分析', fontsize=16, fontweight='bold')

    years = [r['year'] for r in duration_results]
    asset_durations = [r['asset_duration'] for r in duration_results]
    liability_durations = [r['liability_duration'] for r in duration_results]
    duration_gaps = [r['duration_gap'] for r in duration_results]
    net_interest_margins = rate_df['净利差'].tolist()

    # 图1：资产和负债久期对比
    ax1.plot(years, asset_durations, marker='o', label='资产久期', linewidth=2, markersize=8)
    ax1.plot(years, liability_durations, marker='s', label='负债久期', linewidth=2, markersize=8)
    ax1.set_xlabel('年份', fontsize=11)
    ax1.set_ylabel('久期（年）', fontsize=11)
    ax1.set_title('资产与负债久期变化', fontsize=12, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 图2：久期缺口变化
    colors = ['green' if gap > 0 else 'red' for gap in duration_gaps]
    ax2.bar(years, duration_gaps, color=colors, alpha=0.7, edgecolor='black')
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax2.set_xlabel('年份', fontsize=11)
    ax2.set_ylabel('久期缺口（年）', fontsize=11)
    ax2.set_title('久期缺口变化趋势', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')

    # 图3：久期缺口与净利差对比
    ax3_2 = ax3.twinx()

    line1 = ax3.plot(years, duration_gaps, marker='o', color='blue',
                      label='久期缺口', linewidth=2, markersize=8)
    line2 = ax3_2.plot(years, net_interest_margins, marker='s', color='red',
                       label='净利差', linewidth=2, markersize=8)

    ax3.set_xlabel('年份', fontsize=11)
    ax3.set_ylabel('久期缺口（年）', fontsize=11, color='blue')
    ax3_2.set_ylabel('净利差（%）', fontsize=11, color='red')
    ax3.set_title('久期缺口与净利差关系', fontsize=12, fontweight='bold')
    ax3.tick_params(axis='y', labelcolor='blue')
    ax3_2.tick_params(axis='y', labelcolor='red')

    # 合并图例
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax3.legend(lines, labels, loc='upper left')
    ax3.grid(True, alpha=0.3)

    # 图4：各期限段缺口分布（2023年）
    latest_result = duration_results[-1]
    details_df = pd.DataFrame(latest_result['details'])
    periods = details_df['期限段'].tolist()
    gaps = details_df['缺口'].tolist()

    colors_bar = ['red' if gap < 0 else 'green' for gap in gaps]
    ax4.barh(periods, gaps, color=colors_bar, alpha=0.7, edgecolor='black')
    ax4.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
    ax4.set_xlabel('缺口（亿元）', fontsize=11)
    ax4.set_ylabel('期限段', fontsize=11)
    ax4.set_title(f'{latest_result["year"]}年各期限段缺口分布', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='x')

    plt.tight_layout()
    plt.savefig('duration_gap_analysis.png', dpi=300, bbox_inches='tight')
    print("\n图表已保存为：duration_gap_analysis.png")


if __name__ == "__main__":
    main()
