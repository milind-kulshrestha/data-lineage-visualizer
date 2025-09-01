import networkx as nx
from pyvis.network import Network
import json
import pandas as pd

class ExpandableNetworkGraph:
    def __init__(self, width="100%", height="600px"):
        self.G = nx.DiGraph()
        self.hidden_nodes = {}
        self.net = Network(width=width, height=height, bgcolor="#ffffff", font_color="black", directed=True)
        self.styles = {
            'model': {'color': {'background': '#1F4E79', 'border': '#0F3E69'}, 'size': 40, 'shape': 'ellipse', 'font': {'size': 20, 'color': 'white', 'bold': True}},
            'function': {'color': {'background': '#4A90A4', 'border': '#3A8094'}, 'size': 30, 'shape': 'box', 'font': {'size': 16, 'color': 'white', 'bold': True}},
            'dataset': {'color': {'background': '#87CEEB', 'border': '#77BEDB'}, 'size': 40, 'shape': 'diamond', 'font': {'size': 14, 'color': '#000080', 'bold': True}},
            'datapoint': {'color': {'background': '#B0E0E6', 'border': '#A0D0D6'}, 'size': 25, 'shape': 'ellipse', 'font': {'size': 11, 'color': '#000080'}, 'widthConstraint': {'maximum': 150}},
            'table': {'color': {'background': '#E6F3FF', 'border': '#D6E3EF'}, 'size': 30, 'shape': 'database', 'font': {'size': 12, 'color': '#000080', 'bold': True}, 'widthConstraint': {'maximum': 180}},
        }

    def add_node(self, node_id, label, node_type='regular', children=None, **properties):
        self.G.add_node(node_id, label=label, node_type=node_type, expandable=bool(children), **properties)
        if children:
            self.hidden_nodes[node_id] = children if isinstance(children, dict) else {f"{node_id}_child_{i}": child for i, child in enumerate(children)}
    
    def add_edge(self, source, target, **properties):
        self.G.add_edge(source, target, **properties)
    
    def _get_node_style(self, node_id):
        node_data = self.G.nodes[node_id]
        node_type = node_data.get('node_type', 'regular')
        style = self.styles.get(node_type, {'color': {'background': '#F0F8FF', 'border': '#D0E8EF'}, 'size': 15, 'shape': 'ellipse'}).copy()
        
        # Add hover title with node properties only
        title_parts = []
        
        # For function nodes, show only function_definition
        if node_type == 'function' and 'function_definition' in node_data and node_data['function_definition']:
            title_parts.append(node_data['function_definition'])
        # For table nodes, show full breakdown (Database, Schema, Table)
        elif node_type == 'table':
            # Use node_id as it contains the full table name
            table_name = node_id
            # Parse the table name into components
            parts = table_name.split('.')
            if len(parts) >= 3:
                database = parts[0]
                schema = parts[1]
                table = '.'.join(parts[2:])  # In case table name has dots
                title_parts.append(f"Database: {database}")
                title_parts.append(f"Schema: {schema}")
                title_parts.append(f"Table: {table}")
            else:
                title_parts.append(f"Table: {table_name}")
        # For other nodes, show relevant properties
        else:
            for key, value in node_data.items():
                if key not in ['label', 'node_type', 'expandable', 'function_name'] and value is not None:
                    title_parts.append(f"{key.title().replace('_', ' ')}: {value}")
        
        if title_parts:
            style['title'] = "\\n".join(title_parts)
        
        # Use visual indicator for expandable nodes (border style)
        if node_data.get('expandable', False):
            style['borderWidth'] = 3
            style['borderWidthSelected'] = 4
        
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
                edge_props = {'width': 2, 'color': '#666666'}
                
                # Add method property to edge label if it exists
                if 'method' in edge_data:
                    edge_props['label'] = edge_data['method']
                    edge_props['font'] = {'size': 10, 'color': '#333333'}
                
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
            const nodeStyles = {json.dumps(self.styles)};
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
                    const edgeProps = {{from: parentId, to: childId, width: 2, color: '#666666'}};
                    // Add edge properties if they exist in the graph data
                    if (window.graphData && window.graphData.edges && window.graphData.edges[parentId] && window.graphData.edges[parentId][childId]) {{
                        const edgeData = window.graphData.edges[parentId][childId];
                        if (edgeData.method) {{
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
    graph.add_node(model_name, model_name, 'model')
    
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
        func_props = {'function_name': func_name}
        if func_name in functions_metadata and functions_metadata[func_name].get('function_definition'):
            func_props['function_definition'] = functions_metadata[func_name]['function_definition']
            
        graph.add_node(func_name, func_name, 'function', group_children, **func_props)
        graph.add_edge(model_name, func_name)
    
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
            graph.add_node(group_id, dataset_name, 'dataset', datapoint_children)
            graph.add_edge(func_name, group_id)
    
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
        
        display_label = dp_data['display_name'].replace('_', ' ').title()
        if '_' in dp_id and has_source_info:
            display_label = f"{display_label} ({dp_id.split('_', 1)[1]})"
        
        # Add additional properties to datapoint nodes
        node_props = {}
        if dp_data.get('dataset_name'):
            node_props['dataset_name'] = dp_data['dataset_name']
        if dp_data.get('function_def'):
            node_props['function_definition'] = dp_data['function_def']
            
        graph.add_node(dp_id, display_label, 'datapoint', table_children, **node_props)
    
    # Connect dataset groups to their datapoints
    for func_name, datapoints in functions_data.items():
        for dp_id in datapoints:
            # Find which dataset group this datapoint belongs to
            dp_data = datapoint_to_tables.get(dp_id, {})
            dataset_name = dp_data.get('dataset_name')
            if dataset_name:
                group_id = f"{func_name}_{dataset_name}"
                graph.add_edge(group_id, dp_id)
    
    # Connect datapoints directly to tables (no dataset layer)
    for dp_id, dp_data in datapoint_to_tables.items():
        for table in dp_data['tables']:
            if pd.notna(table):
                # Add method as edge property if available
                edge_props = {}
                if dp_data.get('method'):
                    edge_props['method'] = dp_data['method']
                graph.add_edge(dp_id, table, **edge_props)
                
                # Add table nodes (no children since tables are leaf nodes) - only if not already added
                if table not in graph.G.nodes:
                    table_parts = table.split('.')
                    if len(table_parts) >= 3:
                        clean_label = table_parts[-1].replace('_VW', '').replace('_', ' ').title()
                    else:
                        clean_label = table.replace('_VW', '').replace('_', ' ').title()
                    graph.add_node(table, clean_label, 'table', table_name=table)
    
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
        print("  • Drag to move nodes, scroll to zoom")
    except ImportError:
        print("Sample data not found. Create sample_data.py with df_sample to run demo.")
    except Exception as e:
        print(f"Error generating graph: {e}")

if __name__ == "__main__":
    main()
