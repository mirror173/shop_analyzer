"""
店铺业绩分析工具
用于分析店铺业绩构成，包括产品、尺寸、运费等数据的分析
支持对比不同月份的业绩变化
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class ShopAnalyzer:
    """店铺业绩分析器"""
    
    def __init__(self, excel_path=None, df=None):
        """
        初始化分析器
        
        Parameters:
        -----------
        excel_path : str, optional
            Excel文件路径
        df : pd.DataFrame, optional
            直接传入DataFrame（用于Web应用）
        """
        if df is not None:
            self.df = df
            self.excel_path = None
        elif excel_path is not None:
            self.excel_path = Path(excel_path)
            self.df = None
            self.load_data()
        else:
            raise ValueError("必须提供excel_path或df参数")
    
    def load_data(self):
        """加载Excel数据"""
        try:
            # 尝试读取第一个sheet
            self.df = pd.read_excel(self.excel_path, sheet_name=0)
            print(f"✓ 成功加载数据，共 {len(self.df)} 行")
            print(f"✓ 列名: {list(self.df.columns)}")
        except Exception as e:
            print(f"✗ 加载数据失败: {e}")
            sys.exit(1)
    
    def detect_columns(self):
        """自动检测列名（产品、尺寸、数量、金额、运费等）"""
        columns = self.df.columns.tolist()
        col_mapping = {}
        
        # 常见的中文列名映射
        keywords = {
            'product': ['产品', '品名', '商品', '货品', '名称', 'product', 'item'],
            'size': ['尺寸', '规格', 'size', '规格尺寸'],
            'quantity': ['数量', '件数', '销量', 'quantity', 'qty', '数量(件)'],
            'amount': ['金额', '销售额', '收入', 'amount', 'sales', '金额(元)', '销售额(元)'],
            'shipping': ['运费', '邮费', '快递费', 'shipping', '运费(元)'],
            'date': ['日期', '时间', 'date', '时间', '月份', 'month']
        }
        
        for col in columns:
            col_lower = str(col).lower()
            for key, words in keywords.items():
                if any(word in str(col) for word in words):
                    if key not in col_mapping:
                        col_mapping[key] = col
                    break
        
        return col_mapping
    
    def analyze_product_performance(self, group_by='product'):
        """
        分析产品业绩
        
        Parameters:
        -----------
        group_by : str
            分组字段，可以是 'product', 'product_size' 等
        """
        col_map = self.detect_columns()
        
        if not col_map:
            print("⚠ 无法自动识别列名，请手动指定列名")
            print(f"当前列名: {list(self.df.columns)}")
            return None
        
        # 确定分组字段
        if group_by == 'product':
            group_col = col_map.get('product')
        elif group_by == 'product_size':
            if 'product' in col_map and 'size' in col_map:
                self.df['产品_尺寸'] = self.df[col_map['product']].astype(str) + '_' + self.df[col_map['size']].astype(str)
                group_col = '产品_尺寸'
            else:
                group_col = col_map.get('product')
        else:
            group_col = group_by
        
        if not group_col:
            print("⚠ 无法找到分组列")
            return None
        
        # 确定统计字段
        amount_col = col_map.get('amount')
        quantity_col = col_map.get('quantity')
        shipping_col = col_map.get('shipping')
        
        # 构建统计字典
        agg_dict = {}
        if amount_col:
            agg_dict['销售额'] = amount_col
        if quantity_col:
            agg_dict['销量'] = quantity_col
        if shipping_col:
            agg_dict['运费'] = shipping_col
        
        if not agg_dict:
            print("⚠ 无法找到统计列（金额、数量、运费）")
            return None
        
        # 执行分组统计
        result = self.df.groupby(group_col).agg({
            col: 'sum' if col in self.df.select_dtypes(include=[np.number]).columns else 'sum'
            for col in agg_dict.values()
        }).round(2)
        
        # 重命名列
        rename_dict = {v: k for k, v in agg_dict.items()}
        result = result.rename(columns=rename_dict)
        
        # 计算占比
        if '销售额' in result.columns:
            result['销售额占比(%)'] = (result['销售额'] / result['销售额'].sum() * 100).round(2)
        if '销量' in result.columns:
            result['销量占比(%)'] = (result['销量'] / result['销量'].sum() * 100).round(2)
        
        # 排序
        if '销售额' in result.columns:
            result = result.sort_values('销售额', ascending=False)
        elif '销量' in result.columns:
            result = result.sort_values('销量', ascending=False)
        
        return result
    
    def compare_months(self, month1_df, month2_df, group_by='product'):
        """
        对比两个月份的业绩变化
        
        Parameters:
        -----------
        month1_df : pd.DataFrame
            第一个月的数据
        month2_df : pd.DataFrame
            第二个月的数据
        group_by : str
            分组字段
        """
        # 创建两个分析器实例
        analyzer1 = ShopAnalyzer.__new__(ShopAnalyzer)
        analyzer1.df = month1_df
        analyzer2 = ShopAnalyzer.__new__(ShopAnalyzer)
        analyzer2.df = month2_df
        
        # 分析两个月的业绩
        result1 = analyzer1.analyze_product_performance(group_by)
        result2 = analyzer2.analyze_product_performance(group_by)
        
        if result1 is None or result2 is None:
            return None
        
        # 合并数据
        comparison = pd.DataFrame()
        comparison['产品'] = result1.index
        
        # 合并销售额
        if '销售额' in result1.columns and '销售额' in result2.columns:
            comparison['上月销售额'] = result1['销售额']
            comparison['本月销售额'] = result2.reindex(result1.index, fill_value=0)['销售额']
            comparison['销售额变化'] = comparison['本月销售额'] - comparison['上月销售额']
            comparison['销售额变化率(%)'] = ((comparison['销售额变化'] / comparison['上月销售额'].replace(0, np.nan)) * 100).round(2)
        
        # 合并销量
        if '销量' in result1.columns and '销量' in result2.columns:
            comparison['上月销量'] = result1['销量']
            comparison['本月销量'] = result2.reindex(result1.index, fill_value=0)['销量']
            comparison['销量变化'] = comparison['本月销量'] - comparison['上月销量']
            comparison['销量变化率(%)'] = ((comparison['销量变化'] / comparison['上月销量'].replace(0, np.nan)) * 100).round(2)
        
        # 排序
        if '销售额变化' in comparison.columns:
            comparison = comparison.sort_values('销售额变化', ascending=False)
        elif '销量变化' in comparison.columns:
            comparison = comparison.sort_values('销量变化', ascending=False)
        
        return comparison
    
    def generate_report(self, output_path=None):
        """
        生成分析报告
        
        Parameters:
        -----------
        output_path : str
            输出文件路径，如果为None则打印到控制台
        """
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("店铺业绩分析报告")
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 60)
        report_lines.append("")
        
        # 产品业绩分析
        report_lines.append("【产品业绩分析】")
        report_lines.append("-" * 60)
        product_perf = self.analyze_product_performance('product')
        if product_perf is not None:
            report_lines.append(product_perf.to_string())
        report_lines.append("")
        
        # 产品+尺寸业绩分析
        report_lines.append("【产品+尺寸业绩分析】")
        report_lines.append("-" * 60)
        product_size_perf = self.analyze_product_performance('product_size')
        if product_size_perf is not None:
            report_lines.append(product_size_perf.head(20).to_string())
        report_lines.append("")
        
        report_text = "\n".join(report_lines)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"✓ 报告已保存到: {output_path}")
        else:
            print(report_text)
        
        return report_text
    
    def export_to_excel(self, output_path=None):
        """
        导出分析结果到Excel
        
        Parameters:
        -----------
        output_path : str
            输出Excel文件路径
        """
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if self.excel_path:
                output_path = self.excel_path.parent / f"分析结果_{timestamp}.xlsx"
            else:
                output_path = Path.cwd() / f"分析结果_{timestamp}.xlsx"
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 产品业绩
            product_perf = self.analyze_product_performance('product')
            if product_perf is not None:
                product_perf.to_excel(writer, sheet_name='产品业绩', index=True)
            
            # 产品+尺寸业绩
            product_size_perf = self.analyze_product_performance('product_size')
            if product_size_perf is not None:
                product_size_perf.to_excel(writer, sheet_name='产品尺寸业绩', index=True)
        
        print(f"✓ 分析结果已导出到: {output_path}")
        return output_path


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='店铺业绩分析工具')
    parser.add_argument('excel_path', help='Excel文件路径')
    parser.add_argument('--output', '-o', help='输出文件路径（Excel格式）')
    parser.add_argument('--report', '-r', help='生成文本报告路径')
    parser.add_argument('--compare', '-c', nargs=2, metavar=('FILE1', 'FILE2'), 
                       help='对比两个Excel文件的业绩变化')
    
    args = parser.parse_args()
    
    if args.compare:
        # 对比模式
        df1 = pd.read_excel(args.compare[0])
        df2 = pd.read_excel(args.compare[1])
        
        analyzer1 = ShopAnalyzer.__new__(ShopAnalyzer)
        analyzer1.df = df1
        analyzer2 = ShopAnalyzer.__new__(ShopAnalyzer)
        analyzer2.df = df2
        
        comparison = analyzer1.compare_months(df1, df2)
        
        if comparison is not None:
            print("\n【月度对比分析】")
            print("=" * 60)
            print(comparison.to_string(index=False))
            
            if args.output:
                comparison.to_excel(args.output, index=False)
                print(f"\n✓ 对比结果已保存到: {args.output}")
    else:
        # 单文件分析模式
        analyzer = ShopAnalyzer(args.excel_path)
        
        # 生成报告
        if args.report:
            analyzer.generate_report(args.report)
        else:
            analyzer.generate_report()
        
        # 导出Excel
        if args.output:
            analyzer.export_to_excel(args.output)
        else:
            analyzer.export_to_excel()


if __name__ == '__main__':
    main()

