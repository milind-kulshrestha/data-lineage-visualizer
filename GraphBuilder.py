import networkx as nx
from pyvis.network import Network
import json
import pandas as pd

class NodeFormatter:
    """Simple formatter that uses DataFrame column values directly"""
    
    @staticmethod
    def get_display_name(data, field_name):
        """Get display name from DataFrame data, return empty string if missing"""
        value = data.get(field_name, '')
        return str(value) if value and pd.notna(value) else ''
    
    @staticmethod
    def get_tooltip(data, node_type):
        """Generate tooltip using _definition pattern or show nothing"""
        definition_field = f"{node_type}_definition"
        
        if definition_field in data and pd.notna(data[definition_field]):
            return data[definition_field]
        
        return ''

# Simplified hierarchy configuration - just field mappings
BASE_HIERARCHY = {
    'levels': [
        {'name': 'model', 'id_field': 'model_name', 'display_field': 'model_name'},
        {'name': 'function', 'id_field': 'function_name', 'display_field': 'function_name'},
        {'name': 'dataset', 'id_field': 'dataset_name', 'display_field': 'dataset_name'},
        {'name': 'datapoint', 'id_field': 'datapoint_id', 'display_field': 'datapoint'},
        {'name': 'table', 'id_field': 'table_name', 'display_field': 'table_name'}
    ],
    'relationships': [
        {'parent': 'model', 'child': 'function', 'edge_type': 'model_to_function'},
        {'parent': 'function', 'child': 'dataset', 'edge_type': 'function_to_dataset'},
        {'parent': 'dataset', 'child': 'datapoint', 'edge_type': 'dataset_to_datapoint'},
        {'parent': 'datapoint', 'child': 'table', 'edge_type': 'datapoint_to_table'}
    ]
}

# Default hierarchy (same as base)
DEFAULT_HIERARCHY_CONFIG = BASE_HIERARCHY

# Extended hierarchy for Snowflake (inherits from base + adds new levels)
SNOWFLAKE_EXTENDED_HIERARCHY = {
    **BASE_HIERARCHY,
    'levels': BASE_HIERARCHY['levels'] + [
        {'name': 'column', 'id_field': 'column_name', 'display_field': 'column_name'},
        {'name': 'downstream_table', 'id_field': 'downstream_table', 'display_field': 'downstream_table'},
        {'name': 'downstream_column', 'id_field': 'downstream_column', 'display_field': 'downstream_column'}
    ],
    'relationships': BASE_HIERARCHY['relationships'] + [
        {'parent': 'table', 'child': 'column', 'edge_type': 'table_to_column'},
        {'parent': 'column', 'child': 'downstream_table', 'edge_type': 'column_to_downstream_table'},
        {'parent': 'downstream_table', 'child': 'downstream_column', 'edge_type': 'downstream_table_to_downstream_column'}
    ]
}

# 🎨 STREAMLINED STYLING - Only visual styles, no display logic
GRAPH_STYLES = {
    'model': {
        'color': {'background': '#1F4E79', 'border': '#0F3E69'}, 
        'size': 40, 
        'shape': 'ellipse', 
        'font': {'size': 20, 'color': 'white', 'bold': True}
    },
    'function': {
        'color': {'background': '#4A90A4', 'border': '#3A8094'}, 
        'size': 30, 
        'shape': 'box', 
        'font': {'size': 16, 'color': 'white', 'bold': True}
    },
    'dataset': {
        'color': {'background': '#87CEEB', 'border': '#77BEDB'}, 
        'size': 40, 
        'shape': 'diamond', 
        'font': {'size': 14, 'color': '#000080', 'bold': True}
    },
    'datapoint': {
        'color': {'background': '#B0E0E6', 'border': '#A0D0D6'}, 
        'size': 25, 
        'shape': 'ellipse', 
        'font': {'size': 11, 'color': '#000080'},
        'widthConstraint': {'maximum': 150}
    },
    'table': {
        'color': {'background': '#E6F3FF', 'border': '#D6E3EF'}, 
        'size': 30, 
        'shape': 'database', 
        'font': {'size': 12, 'color': '#000080', 'bold': True},
        'widthConstraint': {'maximum': 180}
    },
    'column': {
        'color': {'background': '#F0F8FF', 'border': '#E0E8EF'}, 
        'size': 20, 
        'shape': 'dot', 
        'font': {'size': 10, 'color': '#000080'},
        'widthConstraint': {'maximum': 120}
    },
    'downstream_table': {
        'color': {'background': '#FFE4E1', 'border': '#EED4D1'}, 
        'size': 30, 
        'shape': 'database', 
        'font': {'size': 12, 'color': '#8B0000', 'bold': True},
        'widthConstraint': {'maximum': 180}
    },
    'downstream_column': {
        'color': {'background': '#FFF0F5', 'border': '#EEE0E5'}, 
        'size': 20, 
        'shape': 'dot', 
        'font': {'size': 10, 'color': '#8B0000'},
        'widthConstraint': {'maximum': 120}
    }
}

# 🔗 EDGE CONFIGURATIONS
EDGE_STYLES = {
    'model_to_function': {'width': 3, 'color': '#1F4E79'},
    'function_to_dataset': {'width': 2, 'color': '#666666'},
    'dataset_to_datapoint': {'width': 2, 'color': '#666666'},
    'datapoint_to_table': {'width': 2, 'color': '#666666', 'label_field': 'method'},
    'table_to_column': {'width': 1, 'color': '#999999'},
    'column_to_downstream_table': {'width': 2, 'color': '#CC6666', 'label_field': 'transformation'},
    'downstream_table_to_downstream_column': {'width': 1, 'color': '#AA5555'},
    'default': {'width': 2, 'color': '#666666'}
}

class ExpandableNetworkGraph:
    def __init__(self, width="100%", height="600px"):
        self.G = nx.DiGraph()
        self.hidden_nodes = {}
        self.net = Network(width=width, height=height, bgcolor="#ffffff", font_color="black", directed=True)

    def add_node(self, node_id, data_dict, node_type='regular', children=None, hierarchy_config=None, **properties):
        """Add node with streamlined display system"""
        # Get display label using new formatter
        display_label = self._format_node_label(node_type, data_dict, hierarchy_config)
        
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
    
    def _format_node_label(self, node_type, node_data, hierarchy_config=None):
        """Get node label directly from DataFrame data"""
        if hierarchy_config is None:
            hierarchy_config = DEFAULT_HIERARCHY_CONFIG
            
        # Find the level config for this node type
        level_config = next((level for level in hierarchy_config['levels'] if level['name'] == node_type), None)
        
        if not level_config:
            return ''
        
        # Get display name from the specified field
        display_field = level_config.get('display_field', level_config.get('id_field', ''))
        return NodeFormatter.get_display_name(node_data, display_field)
    
    def add_edge(self, source, target, edge_type='default', **properties):
        """Add edge with configured styling"""
        edge_data = {'edge_type': edge_type, **properties}
        self.G.add_edge(source, target, **edge_data)
    
    def _get_edge_props(self, edge_type, edge_data):
        """Get edge properties from streamlined config"""
        edge_config = EDGE_STYLES.get(edge_type, EDGE_STYLES['default'])
        
        # Base style
        props = {'width': edge_config.get('width', 2), 'color': edge_config.get('color', '#666666')}
        
        # Add label if configured
        label_field = edge_config.get('label_field')
        if label_field and label_field in edge_data:
            label = edge_data[label_field]
            if label:
                props['label'] = label
                props['font'] = {'size': 10, 'color': '#333333'}
        
        return props
    
    def _get_node_style(self, node_id, hierarchy_config=None):
        """Get complete node styling using simplified system"""
        node_data = self.G.nodes[node_id]
        node_type = node_data.get('node_type', 'regular')
        
        # Get base style from config
        style = GRAPH_STYLES.get(node_type, {
            'color': {'background': '#F0F8FF', 'border': '#D0E8EF'}, 
            'size': 15, 'shape': 'ellipse'
        }).copy()
        
        # Get tooltip using node type for customization
        tooltip = NodeFormatter.get_tooltip(node_data, node_type)
        if tooltip:
            style['title'] = tooltip
        
        # Visual indicator for expandable nodes
        if node_data.get('expandable', False):
            style['borderWidth'] = style.get('borderWidth', 1) + 2
            style['borderWidthSelected'] = style.get('borderWidth', 3) + 1
        
        return style
    
    def _get_value(self, source, field, default=None):
        """Simple value extractor with null safety"""
        if hasattr(source, 'get'):
            value = source.get(field, default)
            return value if pd.notna(value) else default
        elif hasattr(source, field):
            value = getattr(source, field, default)
            return value if pd.notna(value) else default
        return default
    
    
    
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
                    # Use hierarchy config to determine display name - no hardcoded overrides
                    display_name = row[display_field] if pd.notna(row[display_field]) else node_id
                    
                    current_level[node_id]['data'].update({
                        'name': node_id,
                        'display_name': display_name,
                        **{k: v for k, v in row.items() if pd.notna(v)}
                    })
                
                # Move to next level
                current_level = current_level[node_id]['children']
        
        return structure
    
    def _build_node_children(self, children_info, hierarchy_config=None):
        """Build children structure using DataFrame data directly"""
        children_dict = {}
        
        for child_id, child_info in children_info.items():
            child_type = child_info.get('node_type', 'unknown')
            child_data = child_info.get('data', {})
            child_children = child_info.get('children', {})
            
            # Get label directly from data
            label = self._format_node_label(child_type, child_data, hierarchy_config)
            
            children_dict[child_id] = {
                'label': label,
                'node_type': child_type,
                'expandable': bool(child_children),
                'auto_expand': child_info.get('auto_expand', child_type == 'table')
            }
            
            # Recursively handle nested children
            if child_children:
                self.hidden_nodes[child_id] = self._build_node_children(child_children, hierarchy_config)
        
        return children_dict

    def create_hierarchy_nodes(self, structure, hierarchy_config, parent_id=None, parent_type=None):
        """Recursively create nodes from hierarchy structure"""
        for node_id, node_info in structure.items():
            node_type = node_info['node_type']
            node_data = node_info['data']
            children = node_info['children']
            
            # Build children using streamlined method
            children_dict = self._build_node_children(children, hierarchy_config) if children else {}
            
            # Create the node directly
            self.add_node(node_id, node_data, node_type, children_dict, hierarchy_config)
            
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
    
    def build_initial_graph(self, hierarchy_config=None):
        visible_nodes = {node_id for node_id in self.G.nodes() 
                        if self.G.nodes[node_id].get('node_type') in ['model', 'function']}
        
        for node_id in visible_nodes:
            node_data = self.G.nodes[node_id]
            style = self._get_node_style(node_id, hierarchy_config)
            self.net.add_node(node_id, label=node_data.get('label', node_id), **style)
        
        for source, target in self.G.edges():
            if source in visible_nodes and target in visible_nodes:
                edge_data = self.G.edges[source, target]
                edge_type = edge_data.get('edge_type', 'default')
                edge_props = self._get_edge_props(edge_type, edge_data)
                self.net.add_edge(source, target, **edge_props)
    

    def generate_javascript_handlers(self):
        """Generate streamlined JavaScript injection using external handlers"""
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
        <script src="static/graph-handlers.js"></script>
        <script type="text/javascript">
            // Initialize graph handlers with data
            initializeGraphHandlers(
                {json.dumps(hidden_nodes_json)},
                {json.dumps(GRAPH_STYLES)},
                {json.dumps(edge_data)}
            );
        </script>
        """
    
    def save_graph(self, filename="expandable_network.html", hierarchy_config=None):
        self.build_initial_graph(hierarchy_config)
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
    graph.save_graph(output_file, hierarchy_config)
    return graph

def main():
    try:
        from sample_data import df_sample
        build_expandable_hierarchy_graph(
            root_name='UserAnalyticsModel', 
            df_sources=df_sample, 
            hierarchy_config=DEFAULT_HIERARCHY_CONFIG,
            output_file="sample_two_level.html"
        )
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
