import networkx as nx
from pyvis.network import Network
import json
import pandas as pd

# Configurable hierarchy definition - easily extensible for Snowflake and future sources
DEFAULT_HIERARCHY_CONFIG = {
    'levels': [
        {'name': 'model', 'id_field': 'model_name', 'display_field': 'model_name', 'group_by': None},
        {'name': 'function', 'id_field': 'function_name', 'display_field': 'function_name', 'group_by': 'function_name'},
        {'name': 'dataset', 'id_field': 'dataset_name', 'display_field': 'dataset_name', 'group_by': ['function_name', 'dataset_name']},
        {'name': 'datapoint', 'id_field': 'datapoint_id', 'display_field': 'datapoint', 'group_by': ['function_name', 'dataset_name', 'datapoint_id']},
        {'name': 'table', 'id_field': 'table_name', 'display_field': 'table_name', 'group_by': ['datapoint_id', 'table_name']}
    ],
    'relationships': [
        {'parent': 'model', 'child': 'function', 'edge_type': 'model_to_function'},
        {'parent': 'function', 'child': 'dataset', 'edge_type': 'function_to_dataset'},
        {'parent': 'dataset', 'child': 'datapoint', 'edge_type': 'dataset_to_datapoint'},
        {'parent': 'datapoint', 'child': 'table', 'edge_type': 'datapoint_to_table'}
    ]
}

# Example extended hierarchy for Snowflake integration
SNOWFLAKE_EXTENDED_HIERARCHY = {
    'levels': [
        {'name': 'model', 'id_field': 'model_name', 'display_field': 'model_name', 'group_by': None},
        {'name': 'function', 'id_field': 'function_name', 'display_field': 'function_name', 'group_by': 'function_name'},
        {'name': 'dataset', 'id_field': 'dataset_name', 'display_field': 'dataset_name', 'group_by': ['function_name', 'dataset_name']},
        {'name': 'datapoint', 'id_field': 'datapoint_id', 'display_field': 'datapoint', 'group_by': ['function_name', 'dataset_name', 'datapoint_id']},
        {'name': 'table', 'id_field': 'table_name', 'display_field': 'table_name', 'group_by': ['datapoint_id', 'table_name']},
        {'name': 'column', 'id_field': 'column_name', 'display_field': 'column_name', 'group_by': ['table_name', 'column_name']},
        {'name': 'downstream_table', 'id_field': 'downstream_table', 'display_field': 'downstream_table', 'group_by': ['column_name', 'downstream_table']},
        {'name': 'downstream_column', 'id_field': 'downstream_column', 'display_field': 'downstream_column', 'group_by': ['downstream_table', 'downstream_column']}
    ],
    'relationships': [
        {'parent': 'model', 'child': 'function', 'edge_type': 'model_to_function'},
        {'parent': 'function', 'child': 'dataset', 'edge_type': 'function_to_dataset'},
        {'parent': 'dataset', 'child': 'datapoint', 'edge_type': 'dataset_to_datapoint'},
        {'parent': 'datapoint', 'child': 'table', 'edge_type': 'datapoint_to_table'},
        {'parent': 'table', 'child': 'column', 'edge_type': 'table_to_column'},
        {'parent': 'column', 'child': 'downstream_table', 'edge_type': 'column_to_downstream_table'},
        {'parent': 'downstream_table', 'child': 'downstream_column', 'edge_type': 'downstream_table_to_downstream_column'}
    ]
}

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
            'display': lambda data: data['display_name'].replace('_', ' ').title(),
            'tooltip': lambda data: '\n'.join([f"{k.title().replace('_', ' ')}: {v}" for k, v in data.items() if k not in ['label', 'node_type', 'expandable', 'function_name', 'name', 'display_name', 'function_context', 'count'] and v is not None])
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
        },
        'column': {
            'style': {
                'color': {'background': '#F0F8FF', 'border': '#E0E8EF'}, 
                'size': 20, 
                'shape': 'dot', 
                'font': {'size': 10, 'color': '#000080'},
                'widthConstraint': {'maximum': 120}
            },
            'display': lambda data: data['name'].replace('_', ' ').title(),
            'tooltip': lambda data: f"Column: {data['name']}\nType: {data.get('data_type', 'Unknown')}"
        },
        'downstream_table': {
            'style': {
                'color': {'background': '#FFE4E1', 'border': '#EED4D1'}, 
                'size': 30, 
                'shape': 'database', 
                'font': {'size': 12, 'color': '#8B0000', 'bold': True},
                'widthConstraint': {'maximum': 180}
            },
            'display': lambda data: data['name'].split('.')[-1].replace('_VW', '').replace('_', ' ').title(),
            'tooltip': lambda data: f"Downstream Table: {data['name']}"
        },
        'downstream_column': {
            'style': {
                'color': {'background': '#FFF0F5', 'border': '#EEE0E5'}, 
                'size': 20, 
                'shape': 'dot', 
                'font': {'size': 10, 'color': '#8B0000'},
                'widthConstraint': {'maximum': 120}
            },
            'display': lambda data: data['name'].replace('_', ' ').title(),
            'tooltip': lambda data: f"Downstream Column: {data['name']}"
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
        'table_to_column': {
            'style': {'width': 1, 'color': '#999999'},
            'display': lambda data: '',
            'show_label': False
        },
        'column_to_downstream_table': {
            'style': {'width': 2, 'color': '#CC6666'},
            'display': lambda data: data.get('transformation', ''),
            'font': {'size': 9, 'color': '#8B0000'},
            'show_label': True
        },
        'downstream_table_to_downstream_column': {
            'style': {'width': 1, 'color': '#AA5555'},
            'display': lambda data: '',
            'show_label': False
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
    
    def _extract_field(self, source, field_name, default=None):
        """Universal field extractor with null safety - works with DataFrames, Series, dicts, etc."""
        if hasattr(source, 'columns') and field_name in source.columns:
            # DataFrame/Series with columns
            values = source[field_name].dropna()
            return values.iloc[0] if not values.empty else default
        elif hasattr(source, 'get'):
            # Dict-like object
            value = source.get(field_name, default)
            return value if pd.notna(value) else default
        elif hasattr(source, 'index') and field_name in source.index:
            # Series with index
            value = source[field_name]
            return value if pd.notna(value) else default
        return default
    
    def _generate_node_label(self, node_id, node_type, node_data, children_count=0):
        """Universal label generator for all node types"""
        if node_type == 'dataset':
            return f"{node_data.get('display_name', node_id)} ({children_count} fields)"
        elif node_type in ['table', 'downstream_table']:
            return self._clean_table_label(node_data.get('display_name', node_id))
        else:
            return node_data.get('display_name', node_id)
    
    def _extract_metadata(self, node_type, base_data, source_group=None):
        """Extract metadata based on node type from source data"""
        metadata = {}
        
        if node_type == 'function' and source_group is not None:
            func_def = self._extract_field(source_group, 'function_definition')
            if func_def:
                metadata['function_definition'] = func_def
        
        elif node_type == 'datapoint' and source_group is not None:
            # Extract all relevant datapoint metadata
            for col in ['dataset_name', 'function_definition', 'method', 'source_type']:
                val = self._extract_field(source_group, col)
                if val:
                    metadata[col] = val
        
        return metadata
    
    def create_node_with_metadata(self, node_id, node_type, base_data, source_group=None, children=None):
        """Unified node creation with automatic metadata extraction"""
        # Extract metadata based on node type and source data
        metadata = self._extract_metadata(node_type, base_data, source_group)
        
        # Merge base data with extracted metadata
        node_data = {**base_data, **metadata}
        
        # Process children if provided - children should already be properly formatted
        self.add_node(node_id, node_data, node_type, children)
    
    
    def _clean_table_label(self, table_name):
        """Create clean table labels for display"""
        if pd.isna(table_name):
            return str(table_name)
        
        table_parts = str(table_name).split('.')
        if len(table_parts) >= 3:
            return table_parts[-1].replace('_VW', '').replace('_', ' ').title()
        else:
            return str(table_name).replace('_VW', '').replace('_', ' ').title()
    
    def build_hierarchy_structure(self, df_sources, hierarchy_config):
        """Generic hierarchy builder that creates separate instances for cleaner hierarchy"""
        structure = {}
        
        # Build nested structure by grouping according to hierarchy levels
        for _, row in df_sources.iterrows():
            current_level = structure
            path = []
            
            # Navigate through each level of the hierarchy
            for level_config in hierarchy_config['levels']:
                field_name = level_config['id_field']
                node_type = level_config['name']
                
                # Get the value for this level
                if field_name == 'model_name':
                    # Model is handled separately, skip in structure building
                    continue
                elif field_name in row.index and pd.notna(row[field_name]):
                    node_id = row[field_name]
                    
                    # Create function-specific dataset IDs to avoid sharing
                    # This ensures each function gets its own dataset instance
                    if node_type == 'dataset' and len(path) > 0:
                        # Prefix dataset with function name for uniqueness
                        function_name = path[0]  # First item in path is function name
                        node_id = f"{function_name}_{node_id}"
                else:
                    break  # Stop if we don't have data for this level
                
                path.append(node_id)
                
                # Create node if it doesn't exist
                if node_id not in current_level:
                    current_level[node_id] = {
                        'node_type': node_type,
                        'data': {},
                        'children': {},
                        'level_config': level_config
                    }
                
                # Update node data with row information
                display_field = level_config.get('display_field', field_name)
                if display_field in row.index:
                    # For renamed dataset nodes, keep original name for display
                    display_name = row[display_field] if pd.notna(row[display_field]) else node_id
                    if node_type == 'dataset' and '_' in node_id:
                        # Extract original dataset name for display (remove function prefix)
                        display_name = node_id.split('_', 1)[1]
                    
                    current_level[node_id]['data'].update({
                        'name': node_id,
                        'display_name': display_name,
                        **{k: v for k, v in row.items() if pd.notna(v)}
                    })
                
                # Move to next level
                current_level = current_level[node_id]['children']
        
        return structure
    
    def _build_node_children(self, children_info):
        """Universal children structure builder - handles any level of nesting"""
        children_dict = {}
        
        for child_id, child_info in children_info.items():
            child_type = child_info.get('node_type', 'unknown')
            child_data = child_info.get('data', {})
            child_children = child_info.get('children', {})
            child_count = len(child_children)
            
            # Use unified label generator
            label = self._generate_node_label(child_id, child_type, child_data, child_count)
            
            children_dict[child_id] = {
                'label': label,
                'node_type': child_type,
                'expandable': bool(child_children),
                'auto_expand': child_info.get('auto_expand', child_type == 'table')
            }
            
            # Recursively handle nested children
            if child_children:
                self.hidden_nodes[child_id] = self._build_node_children(child_children)
        
        return children_dict

    def create_hierarchy_nodes(self, structure, hierarchy_config, parent_id=None, parent_type=None):
        """Recursively create nodes from hierarchy structure"""
        for node_id, node_info in structure.items():
            node_type = node_info['node_type']
            node_data = node_info['data']
            children = node_info['children']
            
            # Build children using unified method
            children_dict = self._build_node_children(children) if children else {}
            
            # Create the node
            self.create_node_with_metadata(node_id, node_type, node_data, None, children_dict)
            
            # Create edge to parent if exists
            if parent_id and parent_type:
                edge_type = self._get_edge_type(parent_type, node_type, hierarchy_config)
                if edge_type:
                    self.add_edge(parent_id, node_id, edge_type)
            
            # Recursively create children
            if children:
                self.create_hierarchy_nodes(children, hierarchy_config, node_id, node_type)
    
    
    def _get_edge_type(self, parent_type, child_type, hierarchy_config):
        """Get edge type from hierarchy configuration"""
        for relationship in hierarchy_config.get('relationships', []):
            if relationship['parent'] == parent_type and relationship['child'] == child_type:
                return relationship['edge_type']
        return 'default'
    
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
    
    def _get_layout_config(self, node_type):
        """Get layout configuration for different node types"""
        layout_configs = {
            'dataset': {'xSpacing': 400, 'yOffset': 220},
            'datapoint': {'xSpacing': 180, 'yOffset': 180},
            'table': {'xSpacing': 200, 'yOffset': 180},
            'column': {'xSpacing': 150, 'yOffset': 160},
            'downstream_table': {'xSpacing': 220, 'yOffset': 200},
            'downstream_column': {'xSpacing': 140, 'yOffset': 160},
            'default': {'xSpacing': 250, 'yOffset': 180}
        }
        return layout_configs.get(node_type, layout_configs['default'])

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
                        // Get layout config for this node type (extensible for new types)
                        const layoutConfigs = {{
                            'dataset': {{xSpacing: 400, yOffset: 220}},
                            'datapoint': {{xSpacing: 180, yOffset: 180}},
                            'table': {{xSpacing: 200, yOffset: 180}},
                            'column': {{xSpacing: 150, yOffset: 160}},
                            'downstream_table': {{xSpacing: 220, yOffset: 200}},
                            'downstream_column': {{xSpacing: 140, yOffset: 160}},
                            'default': {{xSpacing: 250, yOffset: 180}}
                        }};
                        const layout = layoutConfigs[childData.node_type] || layoutConfigs['default'];
                        const xSpacing = layout.xSpacing;
                        const yOffset = layout.yOffset;
                        
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

def build_expandable_hierarchy_graph(root_name, df_sources, hierarchy_config=None, output_file="lineage_graph.html"):
    """
    Extensible hierarchy graph builder - works with any hierarchy configuration.
    
    Args:
        root_name: Name of the root node (e.g., model name)
        df_sources: DataFrame with lineage data
        hierarchy_config: Hierarchy configuration dict (uses DEFAULT_HIERARCHY_CONFIG if None)
        output_file: Output HTML file name
    
    Returns:
        ExpandableNetworkGraph instance
    """
    if hierarchy_config is None:
        hierarchy_config = DEFAULT_HIERARCHY_CONFIG
    
    graph = ExpandableNetworkGraph(height="1200px", width="100%")
    
    # Create root node
    graph.add_node(root_name, {'name': root_name}, 'model')
    
    if df_sources.empty:
        return graph
    
    # Prepare data for hierarchy building
    df_prepared = df_sources.copy()
    
    # Add model_name and ensure datapoint_id exists
    df_prepared['model_name'] = root_name
    if 'datapoint_id' not in df_prepared.columns:
        df_prepared['datapoint_id'] = df_prepared.apply(
            lambda row: f"{row['datapoint']}__{row['function_name']}" if pd.notna(row.get('function_name')) else row['datapoint'], 
            axis=1
        )
    
    # Build hierarchical structure
    structure = graph.build_hierarchy_structure(df_prepared, hierarchy_config)
    
    # Create all nodes and relationships
    graph.create_hierarchy_nodes(structure, hierarchy_config, root_name, 'model')
    
    # Save and return
    graph.save_graph(output_file)
    return graph


def build_model_graph_expandable_final(model_name, df_sources, output_file="model_lineage_expandable.html"):
    """
    Backward compatibility wrapper - uses the new extensible hierarchy system.
    
    This function maintains the same interface as before but now uses the configurable
    hierarchy system internally, making it future-proof and extensible.
    """
    return build_expandable_hierarchy_graph(
        root_name=model_name,
        df_sources=df_sources,
        hierarchy_config=DEFAULT_HIERARCHY_CONFIG,
        output_file=output_file
    )

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
