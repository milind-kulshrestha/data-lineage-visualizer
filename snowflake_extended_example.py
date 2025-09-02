"""
Example: Extended Hierarchy for Snowflake Column-Level Lineage

This example demonstrates how to use the new extensible hierarchy system
to create detailed column-level lineage with downstream dependencies.
"""

import pandas as pd
from GraphBuilder import build_expandable_hierarchy_graph, SNOWFLAKE_EXTENDED_HIERARCHY

# Example data with extended hierarchy levels
extended_lineage_data = {
    # Existing levels (same as before)
    'datapoint': ['revenue', 'revenue', 'customer_count', 'customer_count'], 
    'dataset_name': ['financial_data', 'financial_data', 'customer_data', 'customer_data'],
    'function_name': ['get_financials', 'get_financials', 'get_customers', 'get_customers'],
    'function_definition': ['get financial data', 'get financial data', 'get customer data', 'get customer data'],
    'method': ['QRP', 'QRP', 'API', 'API'],
    'source_type': ['Database', 'Database', 'API', 'API'],
    'table_name': [
        'FINANCE.REVENUE_VW',
        'FINANCE.REVENUE_MONTHLY_VW', 
        'CUSTOMER.CUSTOMER_MASTER_VW',
        'CUSTOMER.CUSTOMER_SUMMARY_VW'
    ],
    
    # Extended levels for Snowflake column-level lineage
    'column_name': ['TOTAL_REVENUE', 'MONTHLY_REVENUE', 'CUSTOMER_ID', 'TOTAL_CUSTOMERS'],
    'downstream_table': [
        'REPORTS.MONTHLY_FINANCIAL_SUMMARY',
        'REPORTS.QUARTERLY_REVENUE', 
        'ANALYTICS.CUSTOMER_METRICS',
        'DASHBOARDS.CUSTOMER_OVERVIEW'
    ],
    'downstream_column': ['REVENUE_USD', 'Q_REVENUE', 'CUST_COUNT', 'ACTIVE_CUSTOMERS'],
    
    # Additional metadata for extended nodes
    'data_type': ['DECIMAL(18,2)', 'DECIMAL(18,2)', 'VARCHAR(50)', 'INTEGER'],
    'transformation': ['SUM(revenue)', 'SUM(monthly_rev)', 'COUNT(DISTINCT customer_id)', 'COUNT(*)']
}

df_extended = pd.DataFrame(extended_lineage_data)

def create_current_lineage():
    """Create lineage with current default hierarchy (5 levels)"""
    print("🔹 Creating current lineage (Model → Function → Dataset → Datapoint → Table)")
    
    graph = build_expandable_hierarchy_graph(
        root_name='AdvancedAnalyticsModel',
        df_sources=df_extended,
        output_file='current_lineage.html'
    )
    
    print(f"   Nodes created: {len(graph.G.nodes())}")
    print("   Generated: current_lineage.html")
    return graph

def create_extended_lineage():
    """Create lineage with extended hierarchy (8 levels) for Snowflake integration"""
    print("\n🚀 Creating extended lineage (Model → Function → Dataset → Datapoint → Table → Column → Downstream Table → Downstream Column)")
    
    graph = build_expandable_hierarchy_graph(
        root_name='AdvancedAnalyticsModel',
        df_sources=df_extended,
        hierarchy_config=SNOWFLAKE_EXTENDED_HIERARCHY,
        output_file='extended_snowflake_lineage.html'
    )
    
    print(f"   Nodes created: {len(graph.G.nodes())}")
    print("   Generated: extended_snowflake_lineage.html")
    return graph

def show_extensibility_example():
    """Show how easy it is to add new hierarchy levels"""
    print("\n💡 Extensibility Example:")
    print("   To add more levels (e.g., Transformations, Data Quality Rules):")
    print("   1. Add new columns to your DataFrame")
    print("   2. Extend the hierarchy configuration")
    print("   3. Add node styling to GRAPH_CONFIG")
    print("   4. Same function handles any number of levels!")
    
    custom_hierarchy = {
        'levels': SNOWFLAKE_EXTENDED_HIERARCHY['levels'] + [
            {'name': 'data_quality_rule', 'id_field': 'dq_rule_id', 'display_field': 'dq_rule_name'},
            {'name': 'business_glossary', 'id_field': 'term_id', 'display_field': 'business_term'}
        ],
        'relationships': SNOWFLAKE_EXTENDED_HIERARCHY['relationships'] + [
            {'parent': 'downstream_column', 'child': 'data_quality_rule', 'edge_type': 'column_to_dq_rule'},
            {'parent': 'data_quality_rule', 'child': 'business_glossary', 'edge_type': 'dq_rule_to_glossary'}
        ]
    }
    
    print(f"   Custom hierarchy now has {len(custom_hierarchy['levels'])} levels!")

if __name__ == "__main__":
    print("🎯 Extended Hierarchy Demonstration")
    print("=" * 50)
    
    # Show current data structure
    print(f"📊 Sample data shape: {df_extended.shape}")
    print(f"    Columns: {list(df_extended.columns)}")
    
    # Create both versions
    current_graph = create_current_lineage()
    extended_graph = create_extended_lineage()
    
    # Show extensibility
    show_extensibility_example()
    
    print("\n✅ Both lineage graphs created successfully!")
    print("\n🔍 Key Benefits:")
    print("   • Same code handles both simple and complex hierarchies")
    print("   • Zero code changes needed to add new levels")
    print("   • Perfect for Snowflake column-level lineage integration")
    print("   • Scales to enterprise-level data governance needs")
    print("   • Backward compatible with existing implementations")