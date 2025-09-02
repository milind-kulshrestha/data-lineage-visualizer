import pandas as pd
from GraphBuilder import build_model_graph_expandable_final

# Test data with same datapoint used by different functions
test_data = {
    'datapoint': ['revenue', 'revenue', 'expenses', 'expenses'],
    'dataset_name': ['financial_data', 'report_data', 'financial_data', 'cost_data'],
    'function_name': ['get_financials', 'get_reports', 'get_financials', 'get_costs'],
    'function_definition': ['get financial data', 'get report data', 'get financial data', 'get cost data'],
    'method': ['QRP', 'QRP', 'QRP', 'QRP'],
    'source_type': ['API', 'API', 'API', 'API'],
    'table_name': [
        'FINANCIAL.REVENUE_VW',
        'REPORTS.REVENUE_VW', 
        'FINANCIAL.EXPENSES_VW',
        'COSTS.EXPENSES_VW'
    ]
}

df_test = pd.DataFrame(test_data)
print("Test DataFrame:")
print(df_test)

# Build the graph
try:
    graph = build_model_graph_expandable_final('TestModel', df_test, "test_distinct_nodes.html")
    
    print(f"\nNodes created: {len(graph.G.nodes())}")
    print("\nNode IDs and their data:")
    for node_id, data in graph.G.nodes(data=True):
        if data.get('node_type') == 'datapoint':
            print(f"  {node_id}: display='{data.get('display_name')}', function_context='{data.get('function_context')}'")
    
    print(f"\nTotal datapoint nodes: {len([n for n, d in graph.G.nodes(data=True) if d.get('node_type') == 'datapoint'])}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()