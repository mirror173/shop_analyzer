"""
店铺业绩分析工具 - 网页版
使用Streamlit创建交互式分析界面
安装: pip install streamlit pandas numpy matplotlib seaborn plotly openpyxl
运行: streamlit run shop_analyzer_web.py
部署: 可部署到Streamlit Cloud, Hugging Face Spaces或GitHub Pages
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
import warnings
warnings.filterwarnings('ignore')

# 设置页面配置
st.set_page_config(
    page_title="店铺业绩分析系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #1E40AF;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #E5E7EB;
    }
    .metric-card {
        background-color: #F8FAFC;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .success-text {
        color: #10B981;
        font-weight: bold;
    }
    .warning-text {
        color: #F59E0B;
        font-weight: bold;
    }
    .danger-text {
        color: #EF4444;
        font-weight: bold;
    }
    .info-text {
        color: #3B82F6;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class ShopPerformanceAnalyzer:
    """店铺业绩分析器"""
    
    def __init__(self, data):
        self.data = data
        self.processed_data = None
        self.current_month = None
        self.previous_month = None
        
    def preprocess_data(self):
        """数据预处理"""
        # 创建数据副本
        df = self.data.copy()
        
        # 重命名列，统一处理
        column_mapping = {
            '订单编号': 'order_id',
            '交易编号': 'transaction_id',
            '状态': 'status',
            '付款时间': 'payment_time',
            '付款方式': 'payment_method',
            '订单原始总金额': 'original_order_amount',
            '订单总金额': 'order_amount',
            '原始商品总金额': 'original_product_amount',
            '商品总金额': 'product_amount',
            '商品销售单价': 'unit_price',
            '商品数量': 'quantity',
            '运费收入': 'shipping_fee',
            '订单核算金额（人民币）': 'accounting_amount',
            'SKU总数量': 'sku_total',
            'SKU明细': 'sku_details',
            'SKU': 'sku',
            '商品中文名称': 'product_name',
            '店铺名': 'shop_name',
            '平台': 'platform',
            '店长': 'shop_manager',
            '物流渠道': 'logistics_channel',
            '仓库': 'warehouse',
            '中文代码': 'chinese_code',
            '商品目录': 'product_category',
            '日期': 'date',
            '是否补单': 'is_replenishment',
            '是否一单': 'is_single_order',
            '是否无效': 'is_invalid',
            '订单实付金额（人民币）': 'actual_payment',
            '发货情况': 'delivery_status',
            '月份': 'month',
            '国家': 'country',
            '店铺类目': 'shop_category',
            '商品金额': 'product_value',
            '一级品类': 'category_level1',
            '二级品类': 'category_level2',
            '三级品类': 'category_level3',
            '新品年月': 'new_product_date',
            '合规': 'compliance'
        }
        
        # 只重命名存在的列
        existing_columns = {k: v for k, v in column_mapping.items() if k in df.columns}
        df.rename(columns=existing_columns, inplace=True)
        
        # 处理日期列
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df['month'] = df['date'].dt.strftime('%Y-%m')
            df['year_month'] = df['date'].dt.strftime('%Y%m').astype(int)
            df['week'] = df['date'].dt.isocalendar().week
            df['day'] = df['date'].dt.day
            df['weekday'] = df['date'].dt.weekday
        
        # 数值列处理
        numeric_columns = ['product_amount', 'unit_price', 'quantity', 'shipping_fee', 
                          'order_amount', 'actual_payment', 'accounting_amount']
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 计算衍生指标
        if 'product_amount' in df.columns and 'quantity' in df.columns:
            # 如果商品总金额为0但单价和数量都有，则重新计算
            mask = (df['product_amount'] == 0) & (df['unit_price'] > 0) & (df['quantity'] > 0)
            df.loc[mask, 'product_amount'] = df.loc[mask, 'unit_price'] * df.loc[mask, 'quantity']
        
        # 计算运费占比
        if 'product_amount' in df.columns and 'shipping_fee' in df.columns:
            df['shipping_ratio'] = np.where(
                df['product_amount'] > 0,
                df['shipping_fee'] / df['product_amount'] * 100,
                0
            )
        
        # 计算净收入（减去运费）
        if 'product_amount' in df.columns and 'shipping_fee' in df.columns:
            df['net_amount'] = df['product_amount'] - df['shipping_fee']
        
        # 提取尺寸信息（如果SKU中包含尺寸）
        if 'sku' in df.columns:
            df['extracted_size'] = df['sku'].apply(self._extract_size)
        
        self.processed_data = df
        
        # 确定月份
        if 'year_month' in df.columns:
            months = sorted(df['year_month'].unique(), reverse=True)
            if len(months) >= 2:
                self.current_month = months[0]
                self.previous_month = months[1]
        
        return df
    
    def _extract_size(self, sku):
        """从SKU中提取尺寸信息"""
        if pd.isna(sku):
            return "未知"
        
        sku_str = str(sku).upper()
        
        # 常见尺寸模式
        size_patterns = [
            ('XXXL', '3XL'), ('XXL', '2XL'), ('XL', 'XL'),
            ('L', 'L'), ('M', 'M'), ('S', 'S'), ('XS', 'XS'),
            ('XXS', '2XS')
        ]
        
        # 检查英文尺寸
        for pattern, size in size_patterns:
            if pattern in sku_str:
                return size
        
        # 检查数字尺寸
        import re
        numbers = re.findall(r'\b(2[0-9]|3[0-9]|4[0-6])\b', sku_str)
        if numbers:
            return f"码{numbers[0]}"
        
        # 检查尺寸代码
        size_codes = ['160', '165', '170', '175', '180', '185', '190']
        for code in size_codes:
            if code in sku_str:
                return f"身高{code}"
        
        return "标准"
    
    def get_summary_metrics(self):
        """获取汇总指标"""
        if self.processed_data is None:
            return {}
        
        df = self.processed_data
        
        metrics = {
            '总销售额': df['product_amount'].sum(),
            '总销量': df['quantity'].sum(),
            '总订单数': df['order_id'].nunique(),
            '平均客单价': df['product_amount'].sum() / df['order_id'].nunique() if df['order_id'].nunique() > 0 else 0,
            '总运费': df['shipping_fee'].sum(),
            '运费占比': df['shipping_fee'].sum() / df['product_amount'].sum() * 100 if df['product_amount'].sum() > 0 else 0,
            '产品数量': df['product_name'].nunique(),
            'SKU数量': df['sku'].nunique() if 'sku' in df.columns else 0,
            '平均单价': df['product_amount'].sum() / df['quantity'].sum() if df['quantity'].sum() > 0 else 0,
            '净收入': df['net_amount'].sum() if 'net_amount' in df.columns else df['product_amount'].sum()
        }
        
        return metrics
    
    def analyze_products(self, top_n=20):
        """产品分析"""
        if self.processed_data is None:
            return pd.DataFrame()
        
        df = self.processed_data
        
        # 按产品汇总
        product_summary = df.groupby('product_name').agg({
            'quantity': 'sum',
            'product_amount': 'sum',
            'shipping_fee': 'sum',
            'order_id': 'nunique',
            'unit_price': 'mean'
        }).reset_index()
        
        # 计算指标
        product_summary['avg_unit_price'] = product_summary['product_amount'] / product_summary['quantity']
        product_summary['avg_order_value'] = product_summary['product_amount'] / product_summary['order_id']
        product_summary['shipping_ratio'] = product_summary['shipping_fee'] / product_summary['product_amount'] * 100
        
        # 重命名列
        product_summary.columns = ['产品名称', '总销量', '总销售额', '总运费', '订单数', '平均单价', '实际平均单价', '平均订单金额', '运费占比']
        
        # 排序
        product_summary = product_summary.sort_values('总销售额', ascending=False)
        
        return product_summary
    
    def analyze_monthly_comparison(self):
        """月度对比分析"""
        if self.processed_data is None or self.previous_month is None:
            return None, None, None
        
        df = self.processed_data
        
        # 筛选当前月和上月数据
        current_data = df[df['year_month'] == self.current_month]
        previous_data = df[df['year_month'] == self.previous_month]
        
        # 当前月产品汇总
        current_products = current_data.groupby('product_name').agg({
            'product_amount': 'sum',
            'quantity': 'sum'
        }).reset_index()
        current_products.columns = ['产品名称', '本月销售额', '本月销量']
        
        # 上月产品汇总
        previous_products = previous_data.groupby('product_name').agg({
            'product_amount': 'sum',
            'quantity': 'sum'
        }).reset_index()
        previous_products.columns = ['产品名称', '上月销售额', '上月销量']
        
        # 合并对比
        product_comparison = pd.merge(
            current_products, 
            previous_products, 
            on='产品名称', 
            how='outer'
        ).fillna(0)
        
        # 计算增长
        product_comparison['销售额增长'] = product_comparison['本月销售额'] - product_comparison['上月销售额']
        product_comparison['销售额增长率'] = np.where(
            product_comparison['上月销售额'] > 0,
            (product_comparison['销售额增长'] / product_comparison['上月销售额'] * 100),
            float('inf')
        )
        
        # 月度总体统计
        monthly_stats = pd.DataFrame({
            '指标': ['总销售额', '总销量', '订单数', '平均客单价'],
            '本月': [
                current_data['product_amount'].sum(),
                current_data['quantity'].sum(),
                current_data['order_id'].nunique(),
                current_data['product_amount'].sum() / current_data['order_id'].nunique() if current_data['order_id'].nunique() > 0 else 0
            ],
            '上月': [
                previous_data['product_amount'].sum(),
                previous_data['quantity'].sum(),
                previous_data['order_id'].nunique(),
                previous_data['product_amount'].sum() / previous_data['order_id'].nunique() if previous_data['order_id'].nunique() > 0 else 0
            ]
        })
        
        # 计算增长率
        monthly_stats['增长率'] = ((monthly_stats['本月'] - monthly_stats['上月']) / monthly_stats['上月'] * 100).round(2)
        
        return product_comparison, monthly_stats, current_data
    
    def analyze_categories(self):
        """品类分析"""
        if self.processed_data is None:
            return pd.DataFrame()
        
        df = self.processed_data
        
        # 确定使用哪个品类列
        category_col = None
        for col in ['category_level1', 'category_level2', 'category_level3', 'shop_category']:
            if col in df.columns and df[col].notna().sum() > 0:
                category_col = col
                break
        
        if category_col is None:
            return pd.DataFrame()
        
        # 品类汇总
        category_summary = df.groupby(category_col).agg({
            'product_amount': 'sum',
            'quantity': 'sum',
            'order_id': 'nunique',
            'product_name': 'nunique'
        }).reset_index()
        
        # 计算指标
        total_sales = category_summary['product_amount'].sum()
        category_summary['销售额占比'] = (category_summary['product_amount'] / total_sales * 100).round(2)
        category_summary['平均单价'] = (category_summary['product_amount'] / category_summary['quantity']).round(2)
        category_summary['平均订单金额'] = (category_summary['product_amount'] / category_summary['order_id']).round(2)
        
        # 排序
        category_summary = category_summary.sort_values('product_amount', ascending=False)
        
        return category_summary, category_col
    
    def analyze_shipping(self):
        """运费分析"""
        if self.processed_data is None:
            return pd.DataFrame()
        
        df = self.processed_data
        
        # 运费总体统计
        shipping_stats = {
            '总运费收入': df['shipping_fee'].sum(),
            '平均每单运费': df['shipping_fee'].mean(),
            '运费占比': df['shipping_fee'].sum() / df['product_amount'].sum() * 100 if df['product_amount'].sum() > 0 else 0,
            '有运费订单数': (df['shipping_fee'] > 0).sum(),
            '总订单数': len(df)
        }
        
        # 运费分布
        shipping_bins = pd.cut(df['shipping_fee'], 
                              bins=[-0.01, 0.01, 10, 20, 50, 100, float('inf')],
                              labels=['免运费', '0-10元', '10-20元', '20-50元', '50-100元', '100元以上'])
        
        shipping_dist = shipping_bins.value_counts().sort_index()
        
        return shipping_stats, shipping_dist
    
    def analyze_size_performance(self):
        """尺寸分析（如果提取了尺寸）"""
        if self.processed_data is None or 'extracted_size' not in self.processed_data.columns:
            return pd.DataFrame()
        
        df = self.processed_data
        
        size_summary = df.groupby('extracted_size').agg({
            'product_amount': 'sum',
            'quantity': 'sum',
            'product_name': 'nunique'
        }).reset_index()
        
        size_summary.columns = ['尺寸', '总销售额', '总销量', '产品数量']
        size_summary = size_summary.sort_values('总销售额', ascending=False)
        
        return size_summary
    
    def analyze_daily_trends(self):
        """每日趋势分析"""
        if self.processed_data is None or 'date' not in self.processed_data.columns:
            return pd.DataFrame()
        
        df = self.processed_data
        
        daily_trends = df.groupby(df['date'].dt.date).agg({
            'product_amount': 'sum',
            'quantity': 'sum',
            'order_id': 'nunique',
            'shipping_fee': 'sum'
        }).reset_index()
        
        daily_trends.columns = ['日期', '销售额', '销量', '订单数', '运费']
        daily_trends['平均客单价'] = daily_trends['销售额'] / daily_trends['订单数']
        
        return daily_trends


# Streamlit应用主函数
def main():
    # 页面标题
    st.markdown('<h1 class="main-header">📊 店铺业绩分析系统</h1>', unsafe_allow_html=True)
    
    # 侧边栏
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/shop--v1.png", width=100)
        st.markdown("### 数据上传")
        
        # 文件上传
        uploaded_file = st.file_uploader("上传Excel文件", type=['xlsx', 'xls'])
        
        st.markdown("### 分析选项")
        analysis_type = st.multiselect(
            "选择分析类型",
            ["概览仪表板", "产品分析", "月度对比", "品类分析", "运费分析", "尺寸分析", "趋势分析"],
            default=["概览仪表板", "产品分析"]
        )
        
        top_n_products = st.slider("显示产品数量", 5, 50, 20)
        
        st.markdown("---")
        st.markdown("### 使用说明")
        st.info("""
        1. 上传包含店铺业绩数据的Excel文件
        2. 选择需要进行的分析类型
        3. 系统会自动分析并生成可视化报告
        4. 结果可以下载为Excel文件
        """)
        
        st.markdown("---")
        st.markdown("#### 关于")
        st.caption("店铺业绩分析系统 v1.0")
        st.caption("支持标准格式的电商店铺数据")
    
    # 主内容区域
    if uploaded_file is not None:
        try:
            # 读取数据
            with st.spinner("正在加载数据..."):
                df = pd.read_excel(uploaded_file)
                st.success(f"数据加载成功！共 {len(df)} 条记录")
            
            # 创建分析器
            analyzer = ShopPerformanceAnalyzer(df)
            
            # 数据预处理
            with st.spinner("正在处理数据..."):
                processed_df = analyzer.preprocess_data()
                st.success("数据预处理完成！")
            
            # 显示数据预览
            with st.expander("数据预览"):
                st.dataframe(processed_df.head(100))
                st.caption(f"数据形状: {processed_df.shape[0]} 行 × {processed_df.shape[1]} 列")
            
            # 概览仪表板
            if "概览仪表板" in analysis_type:
                st.markdown('<h2 class="sub-header">📈 业绩概览仪表板</h2>', unsafe_allow_html=True)
                
                # 获取汇总指标
                metrics = analyzer.get_summary_metrics()
                
                # 显示关键指标
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("总销售额", f"¥{metrics['总销售额']:,.0f}")
                with col2:
                    st.metric("总销量", f"{metrics['总销量']:,}")
                with col3:
                    st.metric("总订单数", f"{metrics['总订单数']:,}")
                with col4:
                    st.metric("平均客单价", f"¥{metrics['平均客单价']:,.1f}")
                
                col5, col6, col7, col8 = st.columns(4)
                with col5:
                    st.metric("总运费", f"¥{metrics['总运费']:,.0f}")
                with col6:
                    st.metric("运费占比", f"{metrics['运费占比']:.2f}%")
                with col7:
                    st.metric("产品数量", f"{metrics['产品数量']:,}")
                with col8:
                    st.metric("SKU数量", f"{metrics['SKU数量']:,}")
                
                # 销售额趋势图
                st.markdown("#### 销售额趋势")
                if 'date' in processed_df.columns:
                    daily_trends = analyzer.analyze_daily_trends()
                    
                    fig = px.line(daily_trends, x='日期', y='销售额', 
                                 title='每日销售额趋势',
                                 markers=True)
                    fig.update_layout(xaxis_title='日期', yaxis_title='销售额 (元)')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 销售额和销量双轴图
                    fig2 = go.Figure()
                    
                    fig2.add_trace(go.Scatter(
                        x=daily_trends['日期'], 
                        y=daily_trends['销售额'],
                        mode='lines+markers',
                        name='销售额',
                        yaxis='y',
                        line=dict(color='blue')
                    ))
                    
                    fig2.add_trace(go.Scatter(
                        x=daily_trends['日期'], 
                        y=daily_trends['销量'],
                        mode='lines+markers',
                        name='销量',
                        yaxis='y2',
                        line=dict(color='green')
                    ))
                    
                    fig2.update_layout(
                        title='销售额与销量趋势',
                        xaxis_title='日期',
                        yaxis=dict(title='销售额 (元)', side='left'),
                        yaxis2=dict(title='销量', side='right', overlaying='y'),
                        legend=dict(x=0.01, y=0.99)
                    )
                    
                    st.plotly_chart(fig2, use_container_width=True)
            
            # 产品分析
            if "产品分析" in analysis_type:
                st.markdown('<h2 class="sub-header">📦 产品表现分析</h2>', unsafe_allow_html=True)
                
                with st.spinner("正在分析产品表现..."):
                    product_summary = analyzer.analyze_products(top_n_products)
                    
                    if not product_summary.empty:
                        # 显示Top产品
                        st.dataframe(product_summary.head(top_n_products))
                        
                        # 产品销售额分布图
                        st.markdown("#### 产品销售额分布")
                        
                        fig = px.bar(product_summary.head(10), 
                                    x='产品名称', 
                                    y='总销售额',
                                    title='销售额Top 10产品',
                                    color='总销售额',
                                    color_continuous_scale='Viridis')
                        
                        fig.update_layout(xaxis_title='产品名称', 
                                         yaxis_title='销售额 (元)',
                                         xaxis_tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # 销售额占比饼图
                        st.markdown("#### 销售额占比")
                        
                        top_10 = product_summary.head(10).copy()
                        others_sales = product_summary['总销售额'].iloc[10:].sum()
                        
                        if others_sales > 0:
                            others_row = pd.DataFrame({
                                '产品名称': ['其他产品'],
                                '总销售额': [others_sales]
                            })
                            pie_data = pd.concat([top_10[['产品名称', '总销售额']], others_row])
                        else:
                            pie_data = top_10[['产品名称', '总销售额']]
                        
                        fig2 = px.pie(pie_data, 
                                     values='总销售额', 
                                     names='产品名称',
                                     title='产品销售额占比',
                                     hole=0.3)
                        
                        st.plotly_chart(fig2, use_container_width=True)
                        
                        # 下载产品分析数据
                        csv = product_summary.to_csv(index=False).encode('utf-8-sig')
                        st.download_button(
                            label="下载产品分析数据 (CSV)",
                            data=csv,
                            file_name="产品分析.csv",
                            mime="text/csv"
                        )
            
            # 月度对比分析
            if "月度对比" in analysis_type:
                st.markdown('<h2 class="sub-header">📊 月度对比分析</h2>', unsafe_allow_html=True)
                
                product_comparison, monthly_stats, current_data = analyzer.analyze_monthly_comparison()
                
                if product_comparison is not None:
                    # 显示月度统计对比
                    st.markdown("#### 月度业绩对比")
                    st.dataframe(monthly_stats)
                    
                    # 月度指标对比图
                    fig = go.Figure(data=[
                        go.Bar(name='本月', x=monthly_stats['指标'], y=monthly_stats['本月']),
                        go.Bar(name='上月', x=monthly_stats['指标'], y=monthly_stats['上月'])
                    ])
                    
                    fig.update_layout(
                        title='月度指标对比',
                        barmode='group',
                        xaxis_title='指标',
                        yaxis_title='数值'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 增长最快产品
                    st.markdown("#### 增长最快产品")
                    
                    growth_top = product_comparison[product_comparison['上月销售额'] > 0].nlargest(10, '销售额增长率')
                    
                    if not growth_top.empty:
                        fig2 = px.bar(growth_top, 
                                     x='产品名称', 
                                     y='销售额增长率',
                                     title='销售额增长率Top 10',
                                     color='销售额增长率',
                                     color_continuous_scale='RdYlGn')
                        
                        fig2.update_layout(xaxis_title='产品名称', 
                                          yaxis_title='增长率 (%)',
                                          xaxis_tickangle=-45)
                        
                        st.plotly_chart(fig2, use_container_width=True)
                        
                        # 显示增长产品详情
                        with st.expander("查看增长产品详情"):
                            st.dataframe(growth_top[['产品名称', '上月销售额', '本月销售额', '销售额增长率']])
                    
                    # 新产品和消失产品
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 🆕 新上市产品")
                        new_products = product_comparison[product_comparison['上月销售额'] == 0]
                        new_products_top = new_products.nlargest(10, '本月销售额')
                        
                        if not new_products_top.empty:
                            st.dataframe(new_products_top[['产品名称', '本月销售额']])
                    
                    with col2:
                        st.markdown("#### ❌ 本月未销售产品")
                        discontinued = product_comparison[product_comparison['本月销售额'] == 0]
                        discontinued_top = discontinued.nlargest(10, '上月销售额')
                        
                        if not discontinued_top.empty:
                            st.dataframe(discontinued_top[['产品名称', '上月销售额']])
            
            # 品类分析
            if "品类分析" in analysis_type:
                st.markdown('<h2 class="sub-header">📁 品类表现分析</h2>', unsafe_allow_html=True)
                
                category_summary, category_col = analyzer.analyze_categories()
                
                if not category_summary.empty:
                    st.info(f"正在使用 [{category_col}] 进行品类分析")
                    
                    # 显示品类汇总
                    st.dataframe(category_summary)
                    
                    # 品类销售额分布
                    st.markdown("#### 品类销售额分布")
                    
                    fig = px.bar(category_summary, 
                                x=category_col, 
                                y='product_amount',
                                title='各品类销售额',
                                color='product_amount',
                                color_continuous_scale='Blues')
                    
                    fig.update_layout(xaxis_title='品类', 
                                     yaxis_title='销售额 (元)',
                                     xaxis_tickangle=-45)
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 品类占比饼图
                    st.markdown("#### 品类销售额占比")
                    
                    fig2 = px.pie(category_summary, 
                                 values='product_amount', 
                                 names=category_col,
                                 title='品类销售额占比',
                                 hole=0.3)
                    
                    st.plotly_chart(fig2, use_container_width=True)
            
            # 运费分析
            if "运费分析" in analysis_type:
                st.markdown('<h2 class="sub-header">🚚 运费分析</h2>', unsafe_allow_html=True)
                
                shipping_stats, shipping_dist = analyzer.analyze_shipping()
                
                # 显示运费统计
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("总运费收入", f"¥{shipping_stats['总运费收入']:,.0f}")
                with col2:
                    st.metric("平均每单运费", f"¥{shipping_stats['平均每单运费']:.2f}")
                with col3:
                    st.metric("运费占比", f"{shipping_stats['运费占比']:.2f}%")
                
                # 运费分布
                st.markdown("#### 运费金额分布")
                
                if not shipping_dist.empty:
                    fig = px.bar(x=shipping_dist.index.astype(str), 
                                y=shipping_dist.values,
                                title='运费金额分布',
                                labels={'x': '运费区间', 'y': '订单数'})
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 显示分布详情
                    with st.expander("查看运费分布详情"):
                        dist_df = pd.DataFrame({
                            '运费区间': shipping_dist.index.astype(str),
                            '订单数': shipping_dist.values,
                            '占比': (shipping_dist.values / shipping_stats['总订单数'] * 100).round(2)
                        })
                        st.dataframe(dist_df)
            
            # 尺寸分析
            if "尺寸分析" in analysis_type:
                st.markdown('<h2 class="sub-header">📏 尺寸表现分析</h2>', unsafe_allow_html=True)
                
                size_summary = analyzer.analyze_size_performance()
                
                if not size_summary.empty:
                    # 显示尺寸汇总
                    st.dataframe(size_summary)
                    
                    # 尺寸销售额分布
                    st.markdown("#### 各尺寸销售额")
                    
                    fig = px.bar(size_summary, 
                                x='尺寸', 
                                y='总销售额',
                                title='各尺寸销售额',
                                color='总销售额',
                                color_continuous_scale='Purples')
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 尺寸销量分布
                    st.markdown("#### 各尺寸销量")
                    
                    fig2 = px.pie(size_summary, 
                                 values='总销量', 
                                 names='尺寸',
                                 title='各尺寸销量占比')
                    
                    st.plotly_chart(fig2, use_container_width=True)
            
            # 趋势分析
            if "趋势分析" in analysis_type:
                st.markdown('<h2 class="sub-header">📈 销售趋势分析</h2>', unsafe_allow_html=True)
                
                daily_trends = analyzer.analyze_daily_trends()
                
                if not daily_trends.empty:
                    # 多指标趋势图
                    st.markdown("#### 多指标趋势")
                    
                    fig = go.Figure()
                    
                    fig.add_trace(go.Scatter(
                        x=daily_trends['日期'], 
                        y=daily_trends['销售额'],
                        mode='lines+markers',
                        name='销售额',
                        yaxis='y'
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=daily_trends['日期'], 
                        y=daily_trends['订单数'],
                        mode='lines+markers',
                        name='订单数',
                        yaxis='y2'
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=daily_trends['日期'], 
                        y=daily_trends['平均客单价'],
                        mode='lines+markers',
                        name='平均客单价',
                        yaxis='y3'
                    ))
                    
                    fig.update_layout(
                        title='销售趋势分析',
                        xaxis_title='日期',
                        yaxis=dict(title='销售额 (元)', side='left'),
                        yaxis2=dict(title='订单数', side='right', overlaying='y'),
                        yaxis3=dict(title='平均客单价 (元)', side='right', overlaying='y', position=0.95),
                        legend=dict(x=0.01, y=0.99)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 周分析
                    st.markdown("#### 周度分析")
                    
                    if 'weekday' in processed_df.columns:
                        weekday_sales = processed_df.groupby('weekday').agg({
                            'product_amount': 'sum',
                            'quantity': 'sum',
                            'order_id': 'nunique'
                        }).reset_index()
                        
                        weekday_map = {0: '周一', 1: '周二', 2: '周三', 3: '周四', 4: '周五', 5: '周六', 6: '周日'}
                        weekday_sales['weekday_name'] = weekday_sales['weekday'].map(weekday_map)
                        
                        fig2 = px.bar(weekday_sales, 
                                     x='weekday_name', 
                                     y='product_amount',
                                     title='各工作日销售额',
                                     color='product_amount',
                                     color_continuous_scale='Greens')
                        
                        st.plotly_chart(fig2, use_container_width=True)
            
            # 数据导出
            st.markdown('<h2 class="sub-header">💾 数据导出</h2>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # 导出处理后的数据
                csv_data = processed_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="下载处理后的完整数据 (CSV)",
                    data=csv_data,
                    file_name="处理后的店铺数据.csv",
                    mime="text/csv"
                )
            
            with col2:
                # 生成Excel报告
                output = io.BytesIO()
                
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    processed_df.to_excel(writer, sheet_name='原始数据', index=False)
                    
                    if "产品分析" in analysis_type:
                        product_summary = analyzer.analyze_products(100)
                        if not product_summary.empty:
                            product_summary.to_excel(writer, sheet_name='产品分析', index=False)
                    
                    if "月度对比" in analysis_type:
                        product_comparison, monthly_stats, _ = analyzer.analyze_monthly_comparison()
                        if product_comparison is not None:
                            product_comparison.to_excel(writer, sheet_name='月度对比', index=False)
                            monthly_stats.to_excel(writer, sheet_name='月度统计', index=False)
                    
                    if "品类分析" in analysis_type:
                        category_summary, _ = analyzer.analyze_categories()
                        if not category_summary.empty:
                            category_summary.to_excel(writer, sheet_name='品类分析', index=False)
                    
                    if "趋势分析" in analysis_type:
                        daily_trends = analyzer.analyze_daily_trends()
                        if not daily_trends.empty:
                            daily_trends.to_excel(writer, sheet_name='每日趋势', index=False)
                
                output.seek(0)
                
                st.download_button(
                    label="下载完整分析报告 (Excel)",
                    data=output,
                    file_name="店铺业绩分析报告.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        except Exception as e:
            st.error(f"处理数据时发生错误: {str(e)}")
            st.exception(e)
    
    else:
        # 没有上传文件时的展示
        st.markdown("""
        ## 欢迎使用店铺业绩分析系统
        
        请按照以下步骤开始分析：
        
        1. **在左侧边栏上传您的Excel文件**
           - 支持.xlsx和.xls格式
           - 文件应包含店铺销售数据
        
        2. **选择分析类型**
           - 概览仪表板：关键指标概览
           - 产品分析：各产品销售表现
           - 月度对比：月度业绩对比
           - 品类分析：各品类销售情况
           - 运费分析：运费收入和占比
           - 尺寸分析：不同尺寸销售表现
           - 趋势分析：销售趋势变化
        
        3. **查看和下载分析结果**
           - 系统会自动生成可视化图表
           - 可以下载分析结果为CSV或Excel文件
        
        ### 数据格式要求
        
        您的Excel文件应包含以下列（列名可以不同，系统会自动适配）：
        - 订单编号、商品中文名称、商品数量、商品销售单价、商品总金额
        - 运费收入、日期、SKU
        - 品类相关列（如一级品类、二级品类等）
        
        ### 示例数据
        
        如果您没有数据文件，可以先下载示例文件进行测试：
        """)
        
        # 创建示例数据
        example_data = {
            '订单编号': [f'ORD{i:06d}' for i in range(1, 101)],
            '商品中文名称': np.random.choice(['运动鞋', 'T恤', '牛仔裤', '外套', '背包', '帽子'], 100),
            '商品数量': np.random.randint(1, 5, 100),
            '商品销售单价': np.random.uniform(50, 500, 100).round(2),
            '日期': pd.date_range('2024-01-01', periods=100, freq='D'),
            '运费收入': np.random.uniform(0, 30, 100).round(2),
            'SKU': [f'SKU{np.random.choice(["S", "M", "L", "XL"])}{i:03d}' for i in range(1, 101)],
            '一级品类': np.random.choice(['服装', '鞋类', '配件'], 100),
            '二级品类': np.random.choice(['上衣', '下装', '外套', '运动鞋', '休闲鞋'], 100)
        }
        
        example_df = pd.DataFrame(example_data)
        example_df['商品总金额'] = example_df['商品数量'] * example_df['商品销售单价']
        
        # 提供示例文件下载
        csv = example_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="下载示例数据 (CSV)",
            data=csv,
            file_name="示例店铺数据.csv",
            mime="text/csv"
        )


# 运行应用
if __name__ == "__main__":
    main()
