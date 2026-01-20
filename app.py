"""
店铺业绩分析工具 - Web版本
使用Streamlit构建的Web界面
"""

import streamlit as st
import pandas as pd
import numpy as np
from shop_analyzer import ShopAnalyzer
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from datetime import datetime

# 页面配置
st.set_page_config(
    page_title="店铺业绩分析工具",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def load_data_from_upload(uploaded_file):
    """从上传的文件加载数据"""
    try:
        if uploaded_file.name.endswith('.xlsx') or uploaded_file.name.endswith('.xls'):
            df = pd.read_excel(uploaded_file)
            return df, None
        else:
            return None, "请上传Excel文件（.xlsx或.xls格式）"
    except Exception as e:
        return None, f"加载文件失败: {str(e)}"

def create_chart_product_performance(df, chart_type='bar'):
    """创建产品业绩图表"""
    if df is None or len(df) == 0:
        return None
    
    # 取前10名
    df_top = df.head(10).copy()
    df_top = df_top.reset_index()
    
    if '销售额' in df.columns:
        if chart_type == 'bar':
            fig = px.bar(
                df_top,
                x=df_top.columns[0],
                y='销售额',
                title='产品销售额TOP 10',
                labels={df_top.columns[0]: '产品', '销售额': '销售额（元）'},
                color='销售额',
                color_continuous_scale='Blues'
            )
        else:
            fig = px.pie(
                df_top,
                values='销售额',
                names=df_top.columns[0],
                title='产品销售额占比TOP 10'
            )
        fig.update_layout(height=400, showlegend=True)
        return fig
    return None

def create_comparison_chart(comparison_df):
    """创建对比图表"""
    if comparison_df is None or len(comparison_df) == 0:
        return None
    
    if '销售额变化' not in comparison_df.columns:
        return None
    
    # 取变化最大的前10个产品
    df_sorted = comparison_df.sort_values('销售额变化', ascending=False)
    df_top = df_sorted.head(10).copy()
    
    fig = go.Figure()
    
    # 添加增长的产品（绿色）
    growth = df_top[df_top['销售额变化'] > 0]
    if len(growth) > 0:
        fig.add_trace(go.Bar(
            x=growth['产品'],
            y=growth['销售额变化'],
            name='增长',
            marker_color='green'
        ))
    
    # 添加下降的产品（红色）
    decline = df_top[df_top['销售额变化'] < 0]
    if len(decline) > 0:
        fig.add_trace(go.Bar(
            x=decline['产品'],
            y=decline['销售额变化'],
            name='下降',
            marker_color='red'
        ))
    
    fig.update_layout(
        title='产品销售额变化TOP 10',
        xaxis_title='产品',
        yaxis_title='销售额变化（元）',
        height=400,
        barmode='group'
    )
    
    return fig

def export_to_excel_bytes(analyzer, comparison_df=None):
    """导出分析结果到Excel字节流"""
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # 产品业绩
        product_perf = analyzer.analyze_product_performance('product')
        if product_perf is not None:
            product_perf.to_excel(writer, sheet_name='产品业绩', index=True)
        
        # 产品+尺寸业绩
        product_size_perf = analyzer.analyze_product_performance('product_size')
        if product_size_perf is not None:
            product_size_perf.to_excel(writer, sheet_name='产品尺寸业绩', index=True)
        
        # 对比分析
        if comparison_df is not None:
            comparison_df.to_excel(writer, sheet_name='月度对比', index=False)
    
    output.seek(0)
    return output

def main():
    """主函数"""
    # 标题
    st.markdown('<div class="main-header">📊 店铺业绩分析工具</div>', unsafe_allow_html=True)
    
    # 侧边栏
    with st.sidebar:
        st.header("📋 功能选择")
        analysis_mode = st.radio(
            "选择分析模式",
            ["单文件分析", "月度对比分析"],
            help="单文件分析：分析单个Excel文件的业绩构成\n月度对比分析：对比两个月的业绩变化"
        )
        
        st.markdown("---")
        st.markdown("### 📖 使用说明")
        st.markdown("""
        1. 上传Excel文件（支持.xlsx和.xls格式）
        2. 工具会自动识别列名（产品、金额、数量等）
        3. 查看分析结果和图表
        4. 下载分析报告
        """)
        
        st.markdown("---")
        st.markdown("### 💡 提示")
        st.markdown("""
        Excel文件应包含以下列：
        - 产品/品名
        - 金额/销售额
        - 数量/销量
        - 尺寸/规格（可选）
        - 运费（可选）
        """)
    
    # 主内容区
    if analysis_mode == "单文件分析":
        st.header("📁 单文件分析")
        
        uploaded_file = st.file_uploader(
            "上传Excel文件",
            type=['xlsx', 'xls'],
            help="上传包含店铺业绩数据的Excel文件"
        )
        
        if uploaded_file is not None:
            # 加载数据
            df, error = load_data_from_upload(uploaded_file)
            
            if error:
                st.error(error)
            else:
                st.success(f"✓ 成功加载数据，共 {len(df)} 行，{len(df.columns)} 列")
                
                # 显示原始数据预览
                with st.expander("📊 数据预览", expanded=False):
                    st.dataframe(df.head(20), use_container_width=True)
                    st.caption(f"列名: {', '.join(df.columns.tolist())}")
                
                # 创建分析器
                try:
                    analyzer = ShopAnalyzer(df=df)
                    
                    # 显示检测到的列名
                    col_map = analyzer.detect_columns()
                    if col_map:
                        st.info(f"✓ 自动识别列名: {col_map}")
                    
                    # 分析结果标签页
                    tab1, tab2, tab3, tab4 = st.tabs(["📈 产品业绩", "📦 产品+尺寸", "📊 数据可视化", "💾 下载报告"])
                    
                    with tab1:
                        st.subheader("产品业绩分析")
                        product_perf = analyzer.analyze_product_performance('product')
                        
                        if product_perf is not None:
                            # 显示关键指标
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                if '销售额' in product_perf.columns:
                                    total_sales = product_perf['销售额'].sum()
                                    st.metric("总销售额", f"¥{total_sales:,.2f}")
                            with col2:
                                if '销量' in product_perf.columns:
                                    total_qty = product_perf['销量'].sum()
                                    st.metric("总销量", f"{total_qty:,.0f}")
                            with col3:
                                if '销售额' in product_perf.columns:
                                    top_product = product_perf.index[0]
                                    st.metric("销售额最高", top_product)
                            with col4:
                                if '销售额占比(%)' in product_perf.columns:
                                    top_ratio = product_perf['销售额占比(%)'].iloc[0]
                                    st.metric("最高占比", f"{top_ratio:.2f}%")
                            
                            # 显示数据表
                            st.dataframe(product_perf, use_container_width=True)
                            
                            # 显示TOP 5
                            st.subheader("销售额TOP 5")
                            top5 = product_perf.head(5)
                            for idx, (product, row) in enumerate(top5.iterrows(), 1):
                                sales = row.get('销售额', 0)
                                ratio = row.get('销售额占比(%)', 0)
                                st.write(f"{idx}. **{product}**: ¥{sales:,.2f} ({ratio:.2f}%)")
                        else:
                            st.warning("⚠ 无法进行产品业绩分析，请检查数据格式")
                    
                    with tab2:
                        st.subheader("产品+尺寸业绩分析")
                        product_size_perf = analyzer.analyze_product_performance('product_size')
                        
                        if product_size_perf is not None:
                            st.dataframe(product_size_perf, use_container_width=True)
                            
                            # 显示TOP 10
                            st.subheader("销售额TOP 10")
                            top10 = product_size_perf.head(10)
                            for idx, (item, row) in enumerate(top10.iterrows(), 1):
                                sales = row.get('销售额', 0)
                                ratio = row.get('销售额占比(%)', 0)
                                st.write(f"{idx}. **{item}**: ¥{sales:,.2f} ({ratio:.2f}%)")
                        else:
                            st.warning("⚠ 无法进行产品+尺寸业绩分析")
                    
                    with tab3:
                        st.subheader("数据可视化")
                        product_perf = analyzer.analyze_product_performance('product')
                        
                        if product_perf is not None:
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                chart_type = st.selectbox("选择图表类型", ["柱状图", "饼图"])
                                chart = create_chart_product_performance(
                                    product_perf,
                                    'pie' if chart_type == "饼图" else 'bar'
                                )
                                if chart:
                                    st.plotly_chart(chart, use_container_width=True)
                            
                            with col2:
                                st.subheader("销售额分布")
                                if '销售额占比(%)' in product_perf.columns:
                                    # 显示占比信息
                                    top3 = product_perf.head(3)
                                    for idx, (product, row) in enumerate(top3.iterrows(), 1):
                                        ratio = row.get('销售额占比(%)', 0)
                                        st.progress(ratio / 100, text=f"{product}: {ratio:.2f}%")
                    
                    with tab4:
                        st.subheader("下载分析报告")
                        st.write("点击下方按钮下载完整的分析报告（Excel格式）")
                        
                        excel_bytes = export_to_excel_bytes(analyzer)
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"店铺业绩分析_{timestamp}.xlsx"
                        
                        st.download_button(
                            label="📥 下载Excel报告",
                            data=excel_bytes,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                
                except Exception as e:
                    st.error(f"分析过程中出现错误: {str(e)}")
                    st.exception(e)
    
    else:  # 月度对比分析
        st.header("📊 月度对比分析")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("上月数据")
            month1_file = st.file_uploader(
                "上传上月Excel文件",
                type=['xlsx', 'xls'],
                key='month1'
            )
        
        with col2:
            st.subheader("本月数据")
            month2_file = st.file_uploader(
                "上传本月Excel文件",
                type=['xlsx', 'xls'],
                key='month2'
            )
        
        if month1_file is not None and month2_file is not None:
            # 加载两个文件
            df1, error1 = load_data_from_upload(month1_file)
            df2, error2 = load_data_from_upload(month2_file)
            
            if error1:
                st.error(f"上月文件错误: {error1}")
            elif error2:
                st.error(f"本月文件错误: {error2}")
            else:
                st.success(f"✓ 上月数据: {len(df1)} 行 | 本月数据: {len(df2)} 行")
                
                try:
                    # 创建分析器
                    analyzer1 = ShopAnalyzer(df=df1)
                    analyzer2 = ShopAnalyzer(df=df2)
                    
                    # 对比分析
                    comparison = analyzer1.compare_months(df1, df2)
                    
                    if comparison is not None:
                        # 关键指标
                        col1, col2, col3, col4 = st.columns(4)
                        
                        if '销售额变化' in comparison.columns:
                            total_change = comparison['销售额变化'].sum()
                            growth_count = len(comparison[comparison['销售额变化'] > 0])
                            decline_count = len(comparison[comparison['销售额变化'] < 0])
                            
                            with col1:
                                st.metric("总销售额变化", f"¥{total_change:,.2f}")
                            with col2:
                                st.metric("增长产品数", growth_count, delta=f"+{growth_count}")
                            with col3:
                                st.metric("下降产品数", decline_count, delta=f"-{decline_count}")
                            with col4:
                                if '销售额变化率(%)' in comparison.columns:
                                    avg_change = comparison['销售额变化率(%)'].mean()
                                    st.metric("平均变化率", f"{avg_change:.2f}%")
                        
                        # 标签页
                        tab1, tab2, tab3, tab4 = st.tabs(["📊 对比结果", "📈 增长产品", "📉 下降产品", "💾 下载报告"])
                        
                        with tab1:
                            st.subheader("完整对比结果")
                            st.dataframe(comparison, use_container_width=True)
                            
                            # 可视化
                            chart = create_comparison_chart(comparison)
                            if chart:
                                st.plotly_chart(chart, use_container_width=True)
                        
                        with tab2:
                            st.subheader("增长的产品")
                            if '销售额变化率(%)' in comparison.columns:
                                growth = comparison[comparison['销售额变化率(%)'] > 0].copy()
                                growth = growth.sort_values('销售额变化率(%)', ascending=False)
                                
                                if len(growth) > 0:
                                    st.dataframe(growth, use_container_width=True)
                                    
                                    # 显示增长TOP 5
                                    st.subheader("增长TOP 5")
                                    top5_growth = growth.head(5)
                                    for idx, row in top5_growth.iterrows():
                                        product = row['产品']
                                        change = row.get('销售额变化', 0)
                                        change_rate = row.get('销售额变化率(%)', 0)
                                        st.success(f"**{product}**: +¥{change:,.2f} (+{change_rate:.2f}%)")
                                else:
                                    st.info("本月没有增长的产品")
                        
                        with tab3:
                            st.subheader("下降的产品")
                            if '销售额变化率(%)' in comparison.columns:
                                decline = comparison[comparison['销售额变化率(%)'] < 0].copy()
                                decline = decline.sort_values('销售额变化率(%)')
                                
                                if len(decline) > 0:
                                    st.dataframe(decline, use_container_width=True)
                                    
                                    # 显示下降TOP 5
                                    st.subheader("下降TOP 5")
                                    top5_decline = decline.head(5)
                                    for idx, row in top5_decline.iterrows():
                                        product = row['产品']
                                        change = row.get('销售额变化', 0)
                                        change_rate = row.get('销售额变化率(%)', 0)
                                        st.error(f"**{product}**: ¥{change:,.2f} ({change_rate:.2f}%)")
                                else:
                                    st.success("✓ 本月没有下降的产品")
                        
                        with tab4:
                            st.subheader("下载对比报告")
                            excel_bytes = export_to_excel_bytes(analyzer1, comparison)
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            filename = f"月度对比分析_{timestamp}.xlsx"
                            
                            st.download_button(
                                label="📥 下载Excel报告",
                                data=excel_bytes,
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    else:
                        st.warning("⚠ 对比分析失败，请检查数据格式")
                
                except Exception as e:
                    st.error(f"分析过程中出现错误: {str(e)}")
                    st.exception(e)
    
    # 页脚
    st.markdown("---")
    st.markdown(
        '<div style="text-align: center; color: #666; padding: 1rem;">店铺业绩分析工具 v1.0 | Powered by Streamlit</div>',
        unsafe_allow_html=True
    )

if __name__ == '__main__':
    main()

