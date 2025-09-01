# Data Lineage Visualizer

An interactive, configuration-driven network graph visualization tool for displaying data lineage relationships with expandable hierarchical views and fully customizable styling.

## Overview

This tool creates interactive HTML graphs that visualize data flow through models, functions, datasets, datapoints, and tables. The graph supports:
- **Configuration-driven styling and display** - All visual elements controlled through GRAPH_CONFIG
- **Hierarchical expandable nodes** with click-to-expand functionality  
- **Custom tooltips and properties** displayed on hover
- **Typed edges** with configurable labels and styling
- **Visual indicators** for expandable nodes (thick borders)
- **Responsive layout** with zoom and drag capabilities

## Quick Start

```python
from GraphBuilder import build_model_graph_expandable_final
import pandas as pd

# Load your data (see Data Format section)
df = pd.read_csv('your_data.csv')

# Generate graph
build_model_graph_expandable_final('YourModelName', df, "output.html")
```

## File Structure

```
├── GraphBuilder.py          # Main graph building logic with GRAPH_CONFIG
├── GraphBuilder_backup.py   # Backup of pre-refactor version
├── sample_data.py           # Example data structure and test runner
├── README.md               # This documentation
└── *.html                  # Generated graph files
```

## Data Format Requirements

Your DataFrame must contain the following columns:

### Required Columns
- `datapoint`: Field/column names in your data
- `function_name`: Function that processes the datapoint  
- `table_name`: Source table containing the datapoint
- `dataset_name`: Dataset categorization - used exactly as provided for grouping


## Configuration System

The graph appearance and behavior are controlled by the `GRAPH_CONFIG` dictionary at the top of `GraphBuilder.py`. This provides a single point of control for all visual and functional aspects.

### Configuration Structure
```python
GRAPH_CONFIG = {
    'nodes': {
        'node_type': {
            'style': {...},           # Visual styling (colors, shapes, sizes)
            'display': lambda data: ...,  # How labels are generated
            'tooltip': lambda data: ...   # Tooltip content
        }
    },
    'edges': {
        'edge_type': {
            'style': {...},           # Edge styling (width, color) 
            'display': lambda data: ...,  # Edge label content
            'show_label': bool,       # Whether to show labels
            'font': {...}            # Label font styling
        }
    }
}
```

### Node Types
- `model`: Root model nodes (dark blue, ellipse)
- `function`: Processing function nodes (medium blue, box) 
- `dataset`: Data grouping nodes (light blue, diamond)
- `datapoint`: Individual field nodes (pale blue, ellipse)
- `table`: Database table nodes (very light blue, database icon)

### Edge Types  
- `model_to_function`: Model to function connections
- `function_to_dataset`: Function to dataset grouping connections
- `dataset_to_datapoint`: Dataset to individual datapoints  
- `datapoint_to_table`: Datapoint to source table (shows method labels)

## Graph Hierarchy

The generated graph follows this hierarchy:
```
Model (root)
├── Function Nodes
│   ├── Dataset Nodes
│   │   ├── Datapoint Nodes  
│   │   │   └── Table Nodes (leaves)
```

## Visual Elements

### Tooltips
Tooltips appear automatically on hover for all nodes with content:
- **Function nodes**: Show function definition only (e.g., "get morningstar data")
- **Table nodes**: Show Database/Schema/Table breakdown 
- **Dataset nodes**: Show dataset name as-is
- **Model nodes**: Show "Model: [name]"
- **Datapoint nodes**: Show all relevant properties

### Expandable Indicators
- **Thick borders** (3px) indicate nodes that can be expanded
- **Click** any thick-bordered node to expand its children
- **Click again** to collapse

### Edge Labels
- **Method labels** appear on datapoint→table edges 
- Always visible with gray font

## Easy Customization

The new configuration system makes customization simple and centralized.

### Quick Styling Changes

**Change node colors:**
```python
# Make all function nodes red
GRAPH_CONFIG['nodes']['function']['style']['color']['background'] = '#FF0000'

# Make table nodes purple with gold border
GRAPH_CONFIG['nodes']['table']['style']['color'] = {'background': '#8A2BE2', 'border': '#FFD700'}
```

**Modify node shapes:**
```python
# Make dataset nodes star-shaped
GRAPH_CONFIG['nodes']['dataset']['style']['shape'] = 'star'
GRAPH_CONFIG['nodes']['dataset']['style']['size'] = 50
```

**Customize tooltips:**
```python
# Show only table name (no breakdown)
GRAPH_CONFIG['nodes']['table']['tooltip'] = lambda data: f"Table: {data['name'].split('.')[-1]}"

# Add custom info to function tooltips
GRAPH_CONFIG['nodes']['function']['tooltip'] = lambda data: f"{data.get('function_definition', '')}\nFunction: {data['name']}"

# Disable tooltips for a node type
GRAPH_CONFIG['nodes']['datapoint']['tooltip'] = lambda data: ''
```

### Edge Customization

**Add labels to more edges:**
```python
# Show labels on function→dataset edges
GRAPH_CONFIG['edges']['function_to_dataset']['show_label'] = True
GRAPH_CONFIG['edges']['function_to_dataset']['display'] = lambda data: 'contains'

# Style edge labels
GRAPH_CONFIG['edges']['function_to_dataset']['font'] = {'size': 12, 'color': '#0066CC'}
```

**Custom edge styling:**
```python
# Make model→function edges thicker and blue
GRAPH_CONFIG['edges']['model_to_function']['style'] = {'width': 5, 'color': '#0066CC'}

# Add dashed edges
GRAPH_CONFIG['edges']['dataset_to_datapoint']['style']['dashes'] = [5, 5]
```

### Adding New Node Types

```python
# Add a new 'schema' node type
GRAPH_CONFIG['nodes']['schema'] = {
    'style': {
        'color': {'background': '#FF6B6B', 'border': '#FF5252'}, 
        'size': 35,
        'shape': 'hexagon',
        'font': {'size': 14, 'color': 'white', 'bold': True}
    },
    'display': lambda data: f"📊 {data['name']}",
    'tooltip': lambda data: f"Schema: {data['name']}\nTables: {data.get('table_count', 0)}"
}
```

### Conditional Styling

```python
# Color-code tables based on security level
GRAPH_CONFIG['nodes']['table']['style']['color'] = lambda data: (
    {'background': '#FF4444', 'border': '#CC0000'} if 'SECURE' in data['name']
    else {'background': '#E6F3FF', 'border': '#D6E3EF'}
)

# Show different tooltips based on data
GRAPH_CONFIG['nodes']['function']['tooltip'] = lambda data: (
    f"🔒 {data.get('function_definition', '')}" if 'secure' in data.get('function_definition', '').lower()
    else data.get('function_definition', '')
)
```

### Display Label Customization

```python
# Add emoji icons to dataset labels
GRAPH_CONFIG['nodes']['dataset']['display'] = lambda data: f"📁 {data['name']} ({data.get('count', 0)} fields)"

# Shorten table names  
GRAPH_CONFIG['nodes']['table']['display'] = lambda data: data['name'].split('.')[-1]

# Add metadata to function labels
GRAPH_CONFIG['nodes']['function']['display'] = lambda data: f"{data['name']} ({data.get('datapoint_count', 0)} fields)"
```

### Performance Considerations

- **Large datasets**: Consider implementing data pagination or filtering
- **Many nodes**: Adjust `nodeSpacing` and `levelSeparation` for better layout
- **Complex hierarchies**: Limit initial expansion depth

## Dependencies

```python
pip install networkx pandas pyvis
```

## Architecture Notes

### Configuration-Driven Design
The codebase uses a **configuration-driven architecture** where all visual and behavioral aspects are controlled through the `GRAPH_CONFIG` dictionary. This approach provides:

- **Single source of truth** for all styling and display logic
- **Easy customization** without code changes
- **Consistent patterns** for extending functionality
- **Separation of concerns** between data processing and presentation

### Node Creation API
```python
# New API (post-refactor)
graph.add_node(node_id, data_dict, node_type, children)

# Where:
# - node_id: Unique identifier
# - data_dict: All node data (used by display/tooltip functions)
# - node_type: References GRAPH_CONFIG['nodes'][type]
# - children: Optional expandable content
```

### Edge Creation API  
```python
# New API with typed edges
graph.add_edge(source, target, edge_type, **properties)

# Where:
# - edge_type: References GRAPH_CONFIG['edges'][type]
# - properties: Additional edge data
```
