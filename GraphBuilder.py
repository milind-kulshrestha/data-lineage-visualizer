import networkx as nx
from pyvis.network import Network
import json
import pandas as pd

# Unified configuration for all graph elements
GRAPH_CONFIG = {
    'nodes': {
        'model': {
            'style': {
                'color': {'background': '#1F4E79', 'border': '#0F3E69'}, 
                'size': 40, 
                'shape': 'ellipse', 
                'font': {'size': 20, 'color': 'white', 'bold': True}
            },
            'display': lambda data: data['name'],
            'tooltip': lambda data: f"Model: {data['name']}"
        },
        'function': {
            'style': {
                'color': {'background': '#4A90A4', 'border': '#3A8094'}, 
                'size': 30, 
                'shape': 'box', 
                'font': {'size': 16, 'color': 'white', 'bold': True}
            },
            'display': lambda data: data['name'],
            'tooltip': lambda data: data.get('function_definition', ''),
        },
        'dataset': {
            'style': {
                'color': {'background': '#87CEEB', 'border': '#77BEDB'}, 
                'size': 40, 
                'shape': 'diamond', 
                'font': {'size': 14, 'color': '#000080', 'bold': True}
            },
            'display': lambda data: f"{data['name']} ({data.get('count', 0)} fields)",
            'tooltip': lambda data: data['name']
        },
        'datapoint': {
            'style': {
                'color': {'background': '#B0E0E6', 'border': '#A0D0D6'}, 
                'size': 25, 
                'shape': 'ellipse', 
                'font': {'size': 11, 'color': '#000080'},
                'widthConstraint': {'maximum': 150}
            },
            'display': lambda data: data['display_name'].replace('_', ' ').title() + (f" ({data['source_suffix']})" if data.get('source_suffix') else ''),
            'tooltip': lambda data: '\n'.join([f"{k.title().replace('_', ' ')}: {v}" for k, v in data.items() if k not in ['label', 'node_type', 'expandable', 'function_name', 'name', 'display_name', 'source_suffix', 'count'] and v is not None])
        },
        'table': {
            'style': {
                'color': {'background': '#E6F3FF', 'border': '#D6E3EF'}, 
                'size': 30, 
                'shape': 'database', 
                'font': {'size': 12, 'color': '#000080', 'bold': True},
                'widthConstraint': {'maximum': 180}
            },
            'display': lambda data: data['name'].split('.')[-1].replace('_VW', '').replace('_', ' ').title(),
            'tooltip': lambda data: f"Database: {data['name'].split('.')[0]}\nSchema: {data['name'].split('.')[1]}\nTable: {'.'.join(data['name'].split('.')[2:])}" if len(data['name'].split('.')) >= 3 else f"Table: {data['name']}"
        }
    },
    'edges': {
        'model_to_function': {
            'style': {'width': 3, 'color': '#1F4E79'},
            'display': lambda data: '',
            'show_label': False
        },
        'function_to_dataset': {
            'style': {'width': 2, 'color': '#666666'},
            'display': lambda data: '',
            'show_label': False
        },
        'dataset_to_datapoint': {
            'style': {'width': 2, 'color': '#666666'},
            'display': lambda data: '',
            'show_label': False
        },
        'datapoint_to_table': {
            'style': {'width': 2, 'color': '#666666'},
            'display': lambda data: data.get('method', ''),
            'font': {'size': 10, 'color': '#333333'},
            'show_label': True
        },
        'default': {
            'style': {'width': 2, 'color': '#666666'},
            'display': lambda data: '',
            'show_label': False
        }
    }
}

class ExpandableNetworkGraph:
    def __init__(self, width="100%", height="600px"):
        self.G = nx.DiGraph()
        self.hidden_nodes = {}
        self.net = Network(width=width, height=height, bgcolor="#ffffff", font_color="black", directed=True)

    def add_node(self, node_id, data_dict, node_type='regular', children=None, **properties):
        """Add node with config-based styling and display"""
        # Get display label from config
        display_label = self._get_display_label(node_type, data_dict)
        
        # Store all data in node
        node_data = {
            'label': display_label, 
            'node_type': node_type, 
            'expandable': bool(children),
            **data_dict,
            **properties
        }
        self.G.add_node(node_id, **node_data)
        
        if children:
            self.hidden_nodes[node_id] = children if isinstance(children, dict) else {f"{node_id}_child_{i}": child for i, child in enumerate(children)}
    
    def _get_display_label(self, node_type, data):
        """Get display label from config"""
        node_config = GRAPH_CONFIG['nodes'].get(node_type, {})
        display_func = node_config.get('display', lambda d: d.get('name', ''))
        return display_func(data)
    
    def add_edge(self, source, target, edge_type='default', **properties):
        """Add edge with configured styling"""
        edge_data = {'edge_type': edge_type, **properties}
        self.G.add_edge(source, target, **edge_data)
    
    def _get_edge_props(self, edge_type, edge_data):
        """Get edge properties from config"""
        edge_config = GRAPH_CONFIG['edges'].get(edge_type, GRAPH_CONFIG['edges']['default'])
        
        # Base style
        props = edge_config.get('style', {'width': 2, 'color': '#666666'}).copy()
        
        # Add label if configured
        if edge_config.get('show_label', False):
            display_func = edge_config.get('display', lambda d: '')
            label = display_func(edge_data)
            if label:
                props['label'] = label
                props['font'] = edge_config.get('font', {'size': 10, 'color': '#333333'})
        
        return props
    
    def _get_node_style(self, node_id):
        """Get complete node styling from config"""
        node_data = self.G.nodes[node_id]
        node_type = node_data.get('node_type', 'regular')
        
        # Get base style from config
        node_config = GRAPH_CONFIG['nodes'].get(node_type, {})
        style = node_config.get('style', {
            'color': {'background': '#F0F8FF', 'border': '#D0E8EF'}, 
            'size': 15, 'shape': 'ellipse'
        }).copy()
        
        # Get tooltip content from config
        tooltip_func = node_config.get('tooltip', lambda d: '')
        tooltip_data = {**node_data, 'name': node_id}
        tooltip = tooltip_func(tooltip_data)
        if tooltip:
            style['title'] = tooltip
        
        # Visual indicator for expandable nodes
        if node_data.get('expandable', False):
            style['borderWidth'] = style.get('borderWidth', 1) + 2
            style['borderWidthSelected'] = style.get('borderWidth', 3) + 1
        
        return style
    
    def build_initial_graph(self):
        visible_nodes = {node_id for node_id in self.G.nodes() 
                        if self.G.nodes[node_id].get('node_type') in ['model', 'function']}
        
        for node_id in visible_nodes:
            node_data = self.G.nodes[node_id]
            style = self._get_node_style(node_id)
            self.net.add_node(node_id, label=node_data.get('label', node_id), **style)
        
        for source, target in self.G.edges():
            if source in visible_nodes and target in visible_nodes:
                edge_data = self.G.edges[source, target]
                edge_type = edge_data.get('edge_type', 'default')
                edge_props = self._get_edge_props(edge_type, edge_data)
                self.net.add_edge(source, target, **edge_props)
    
    def generate_javascript_handlers(self):
        hidden_nodes_json = {}
        for parent, children in self.hidden_nodes.items():
            hidden_nodes_json[parent] = {}
            for child_id, child_info in children.items():
                if isinstance(child_info, dict):
                    hidden_nodes_json[parent][child_id] = child_info
                else:
                    hidden_nodes_json[parent][child_id] = {'label': str(child_info), 'node_type': 'table'}
        
        # Create edge data structure for JavaScript
        edge_data = {}
        for source, target, data in self.G.edges(data=True):
            if source not in edge_data:
                edge_data[source] = {}
            edge_data[source][target] = data
        
        return f"""
        <script type="text/javascript">
            const hiddenNodesData = {json.dumps(hidden_nodes_json)};
            const expandedNodes = new Set();
            const nodeStyles = {json.dumps({k: v['style'] for k, v in GRAPH_CONFIG['nodes'].items()})};
            window.graphData = {{edges: {json.dumps(edge_data)}}};
            
            network.on("click", function(params) {{
                if (params.nodes.length > 0) {{
                    const nodeId = params.nodes[0];
                    if (hiddenNodesData[nodeId]) {{
                        expandedNodes.has(nodeId) ? collapseNode(nodeId) : expandNode(nodeId);
                    }}
                }}
            }});
            
            function expandNode(parentId) {{
                if (expandedNodes.has(parentId)) return;
                
                const children = hiddenNodesData[parentId];
                const newNodes = [], newEdges = [];
                const existingNodes = new Set(nodes.getIds());
                
                // Get parent position for linear arrangement
                const parentPos = network.getPositions([parentId])[parentId];
                let childIndex = 0;
                const childrenCount = Object.keys(children).length;
                
                for (const [childId, childData] of Object.entries(children)) {{
                    if (!existingNodes.has(childId)) {{
                        const style = nodeStyles[childData.node_type] || {{}};
                        // Position children with better spacing based on node type
                        let xSpacing = 250; // Default spacing
                        let yOffset = 180;  // Default vertical offset
                        
                        if (childData.node_type === 'dataset') {{
                            xSpacing = 400;
                            yOffset = 220;
                        }} else if (childData.node_type === 'datapoint') {{
                            xSpacing = 180;
                            yOffset = 180;
                        }} else if (childData.node_type === 'table') {{
                            xSpacing = 200;
                            yOffset = 180;
                        }}
                        
                        // Special layout for datapoints to avoid overcrowding
                        let xPos, yPos;
                        if (childData.node_type === 'datapoint' && childrenCount > 6) {{
                            // Arrange in multiple rows for many datapoints
                            const itemsPerRow = Math.ceil(Math.sqrt(childrenCount));
                            const row = Math.floor(childIndex / itemsPerRow);
                            const col = childIndex % itemsPerRow;
                            xPos = parentPos.x + (col * xSpacing) - (itemsPerRow * xSpacing / 2);
                            yPos = parentPos.y + yOffset + (row * 80);
                        }} else {{
                            // Standard linear arrangement
                            xPos = parentPos.x + (childIndex * xSpacing) - (childrenCount * xSpacing / 2);
                            yPos = parentPos.y + yOffset;
                        }}
                        
                        newNodes.push({{
                            id: childId, 
                            label: childData.label, 
                            x: xPos,
                            y: yPos,
                            ...style
                        }});
                        childIndex++;
                    }}
                    // Default edge properties
                    const edgeProps = {{from: parentId, to: childId, width: 2, color: '#666666'}};
                    
                    // Add edge properties if they exist in the graph data
                    if (window.graphData && window.graphData.edges && window.graphData.edges[parentId] && window.graphData.edges[parentId][childId]) {{
                        const edgeData = window.graphData.edges[parentId][childId];
                        const edgeType = edgeData.edge_type || 'default';
                        
                        // Apply config-based edge styling (simplified for JavaScript)
                        if (edgeType === 'datapoint_to_table' && edgeData.method) {{
                            edgeProps.label = edgeData.method;
                            edgeProps.font = {{size: 10, color: '#333333'}};
                        }}
                    }}
                    newEdges.push(edgeProps);
                }}
                
                nodes.add(newNodes);
                edges.add(newEdges);
                expandedNodes.add(parentId);
                
                // Auto-expand nodes that should expand immediately (like tables under datapoints)
                setTimeout(() => {{
                    for (const [childId, childData] of Object.entries(children)) {{
                        if (childData.auto_expand && hiddenNodesData[childId] && !expandedNodes.has(childId)) {{
                            expandNode(childId);
                        }}
                    }}
                }}, 100); // Small delay to ensure nodes are rendered first
            }}
            
            function collapseNode(parentId) {{
                if (!expandedNodes.has(parentId)) return;
                
                const children = hiddenNodesData[parentId];
                const childIds = Object.keys(children);
                
                childIds.forEach(childId => expandedNodes.has(childId) && collapseNode(childId));
                nodes.remove(childIds);
                expandedNodes.delete(parentId);
                network.stabilize();
            }}
        </script>
        """
    
    def save_graph(self, filename="expandable_network.html"):
        self.build_initial_graph()
        self.net.set_options('''
        var options = {
          "layout": {
            "hierarchical": {
              "enabled": true,
              "direction": "UD",
              "sortMethod": "directed",
              "shakeTowards": "roots",
              "nodeSpacing": 200,
              "levelSeparation": 250
            }
          },
          "physics": {
            "enabled": false
          },
          "interaction": {
            "dragNodes": true,
            "dragView": true,
            "zoomView": true
          },
          "nodes": {
            "font": {
              "multi": true,
              "align": "center"
            }
          },
          "edges": {
            "font": {
              "size": 10,
              "color": "#333333",
              "strokeWidth": 1,
              "strokeColor": "#ffffff"
            },
            "labelHighlightBold": false
          }
        }
        ''')
        self.net.save_graph(filename)
        
        with open(filename, 'r') as file:
            html_content = file.read()
        
        js_injection = self.generate_javascript_handlers()
        
        if 'var network = new vis.Network' in html_content:
            pos = html_content.find('</script>', html_content.find('var network = new vis.Network')) + 9
            html_content = html_content[:pos] + js_injection + html_content[pos:]
        else:
            html_content = html_content.replace('</body>', f'{js_injection}</body>')
        
        with open(filename, 'w') as file:
            file.write(html_content)
        
        return filename

def build_model_graph_expandable_final(model_name, df_sources, output_file="model_lineage_expandable.html"):
    graph = ExpandableNetworkGraph(height="1200px", width="100%")
    graph.add_node(model_name, {'name': model_name}, 'model')
    
    if df_sources.empty:
        return graph
    
    has_source_info = 'source_instance' in df_sources.columns and not df_sources['source_instance'].isna().all()
    df_sources['datapoint_id'] = df_sources.apply(
        lambda row: f"{row['datapoint']}_{row['source_instance']}" if has_source_info and pd.notna(row['source_instance']) else row['datapoint'], 
        axis=1
    )
    
    # Create dataset groups using dataset_name column
    dataset_groups = {}
    datapoint_to_tables = {}
    
    for dp_id, group in df_sources.groupby("datapoint_id"):
        tables = group['table_name'].dropna().unique().tolist()
        # Get method information for this datapoint
        method_info = group['method'].dropna().iloc[0] if 'method' in group.columns and not group['method'].dropna().empty else None
        # Get additional properties
        dataset_name = group['dataset_name'].dropna().iloc[0] if 'dataset_name' in group.columns and not group['dataset_name'].dropna().empty else None
        function_def = group['function_def'].dropna().iloc[0] if 'function_def' in group.columns and not group['function_def'].dropna().empty else None
        
        datapoint_to_tables[dp_id] = {
            'tables': tables,
            'display_name': group['datapoint'].iloc[0],
            'method': method_info,
            'dataset_name': dataset_name,
            'function_def': function_def
        }
        
        # Group datapoints by their dataset_name (use as-is from df_sample)
        if dataset_name and pd.notna(dataset_name):
            if dataset_name not in dataset_groups:
                dataset_groups[dataset_name] = []
            dataset_groups[dataset_name].append(dp_id)
    
    functions_data = {}
    functions_metadata = {}
    for func_name, group in df_sources.groupby("function_name"):
        if pd.notna(func_name):
            dp_ids = group['datapoint_id'].unique()
            functions_data[func_name] = {dp_id: group[group['datapoint_id'] == dp_id]['datapoint'].iloc[0] for dp_id in dp_ids}
            # Store function metadata
            func_def = group['function_def'].dropna().iloc[0] if 'function_def' in group.columns and not group['function_def'].dropna().empty else None
            functions_metadata[func_name] = {'function_definition': func_def}
    
    
    # Create function nodes with dataset groups
    for func_name, datapoints in functions_data.items():
        # Group datapoints by their dataset_name
        func_dataset_groups = {}
        for dp_id, dp_name in datapoints.items():
            dp_data = datapoint_to_tables.get(dp_id, {})
            dataset_name = dp_data.get('dataset_name')
            if dataset_name:
                if dataset_name not in func_dataset_groups:
                    func_dataset_groups[dataset_name] = []
                source_info = f" ({dp_id.split('_', 1)[1]})" if '_' in dp_id and has_source_info else ""
                func_dataset_groups[dataset_name].append({'id': dp_id, 'label': dp_name + source_info})
        
        # Create children structure with dataset groups
        group_children = {}
        for dataset_name, datapoints_list in func_dataset_groups.items():
            # Use dataset name as-is from df_sample
            group_children[f"{func_name}_{dataset_name}"] = {
                'label': f"{dataset_name} ({len(datapoints_list)} fields)", 
                'node_type': 'dataset', 
                'expandable': True
            }
        
        # Add function metadata as node properties
        func_data = {'name': func_name, 'function_name': func_name}
        if func_name in functions_metadata and functions_metadata[func_name].get('function_definition'):
            func_data['function_definition'] = functions_metadata[func_name]['function_definition']
            
        graph.add_node(func_name, func_data, 'function', group_children)
        graph.add_edge(model_name, func_name, 'model_to_function')
    
    # Add dataset group nodes with their datapoints
    for func_name, datapoints in functions_data.items():
        func_dataset_groups = {}
        for dp_id, dp_name in datapoints.items():
            dp_data = datapoint_to_tables.get(dp_id, {})
            dataset_name = dp_data.get('dataset_name')
            if dataset_name:
                if dataset_name not in func_dataset_groups:
                    func_dataset_groups[dataset_name] = []
                source_info = f" ({dp_id.split('_', 1)[1]})" if '_' in dp_id and has_source_info else ""
                func_dataset_groups[dataset_name].append({'id': dp_id, 'label': dp_name + source_info})
        
        for dataset_name, datapoints_list in func_dataset_groups.items():
            group_id = f"{func_name}_{dataset_name}"
            datapoint_children = {}
            for dp_info in datapoints_list:
                dp_id = dp_info['id']
                datapoint_children[dp_id] = {'label': dp_info['label'], 'node_type': 'datapoint', 'expandable': True}
            
            # Use dataset name as-is from df_sample
            dataset_data = {'name': dataset_name, 'count': len(datapoints_list)}
            graph.add_node(group_id, dataset_data, 'dataset', datapoint_children)
            graph.add_edge(func_name, group_id, 'function_to_dataset')
    
    # Create datapoint nodes that connect directly to tables
    for dp_id, dp_data in datapoint_to_tables.items():
        table_children = {}
        for table in dp_data['tables']:
            if pd.notna(table):
                # Create cleaner table labels
                table_parts = table.split('.')
                if len(table_parts) >= 3:
                    clean_label = table_parts[-1].replace('_VW', '').replace('_', ' ').title()
                else:
                    clean_label = table.replace('_VW', '').replace('_', ' ').title()
                table_children[table] = {'label': clean_label, 'node_type': 'table', 'auto_expand': True}
        
        # Prepare datapoint data
        source_suffix = dp_id.split('_', 1)[1] if '_' in dp_id and has_source_info else None
        datapoint_data = {
            'name': dp_id,
            'display_name': dp_data['display_name'],
            'source_suffix': source_suffix
        }
        
        # Add additional properties to datapoint nodes
        if dp_data.get('dataset_name'):
            datapoint_data['dataset_name'] = dp_data['dataset_name']
        if dp_data.get('function_def'):
            datapoint_data['function_definition'] = dp_data['function_def']
            
        graph.add_node(dp_id, datapoint_data, 'datapoint', table_children)
    
    # Connect dataset groups to their datapoints
    for func_name, datapoints in functions_data.items():
        for dp_id in datapoints:
            # Find which dataset group this datapoint belongs to
            dp_data = datapoint_to_tables.get(dp_id, {})
            dataset_name = dp_data.get('dataset_name')
            if dataset_name:
                group_id = f"{func_name}_{dataset_name}"
                graph.add_edge(group_id, dp_id, 'dataset_to_datapoint')
    
    # Connect datapoints directly to tables (no dataset layer)
    for dp_id, dp_data in datapoint_to_tables.items():
        for table in dp_data['tables']:
            if pd.notna(table):
                # Add method as edge property if available
                edge_props = {}
                if dp_data.get('method'):
                    edge_props['method'] = dp_data['method']
                graph.add_edge(dp_id, table, 'datapoint_to_table', **edge_props)
                
                # Add table nodes (no children since tables are leaf nodes) - only if not already added
                if table not in graph.G.nodes:
                    table_data = {'name': table}
                    graph.add_node(table, table_data, 'table')
    
    graph.save_graph(output_file)
    
    return graph

def main():
    try:
        from sample_data import df_sample
        build_model_graph_expandable_final('UserAnalyticsModel', df_sample, "sample_two_level.html")
        print("Graph generated successfully: sample_two_level.html")
        print("\n🎮 Interaction Guide:")
        print("  • Click any node to expand its children")
        print("  • Shift+Click to expand ALL nodes at the same level")
        print("  • Click expanded nodes to collapse")
        print("  • Drag to move nodes, scroll to zoom-")
    except ImportError:
        print("Sample data not found. Create sample_data.py with df_sample to run demo.")
    except Exception as e:
        print(f"Error generating graph: {e}")

if __name__ == "__main__":
    main()
