// Interactive graph handlers for expandable network visualization
class GraphInteractionManager {
    constructor() {
        this.hiddenNodesData = {};
        this.expandedNodes = new Set();
        this.nodeStyles = {};
        this.graphData = {edges: {}};
    }

    initialize(hiddenNodes, nodeStyles, edgeData) {
        this.hiddenNodesData = hiddenNodes;
        this.nodeStyles = nodeStyles;
        this.graphData = {edges: edgeData};
        
        // Set up click handler
        network.on("click", (params) => {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                if (this.hiddenNodesData[nodeId]) {
                    this.expandedNodes.has(nodeId) ? this.collapseNode(nodeId) : this.expandNode(nodeId);
                }
            }
        });
    }

    expandNode(parentId) {
        if (this.expandedNodes.has(parentId)) return;
        
        const children = this.hiddenNodesData[parentId];
        const newNodes = [], newEdges = [];
        const existingNodes = new Set(nodes.getIds());
        
        // Get parent position for layout
        const parentPos = network.getPositions([parentId])[parentId];
        let childIndex = 0;
        const childrenCount = Object.keys(children).length;
        
        for (const [childId, childData] of Object.entries(children)) {
            if (!existingNodes.has(childId)) {
                const style = this.nodeStyles[childData.node_type] || {};
                const layout = this.getLayoutConfig(childData.node_type);
                
                // Calculate position
                const {xPos, yPos} = this.calculateChildPosition(
                    parentPos, childIndex, childrenCount, layout, childData.node_type
                );
                
                newNodes.push({
                    id: childId, 
                    label: childData.label, 
                    x: xPos,
                    y: yPos,
                    ...style
                });
                childIndex++;
            }
            
            // Create edge with styling
            const edgeProps = this.getEdgeProperties(parentId, childId);
            newEdges.push(edgeProps);
        }
        
        nodes.add(newNodes);
        edges.add(newEdges);
        this.expandedNodes.add(parentId);
        
        // Auto-expand nodes that should expand immediately
        setTimeout(() => {
            for (const [childId, childData] of Object.entries(children)) {
                if (childData.auto_expand && this.hiddenNodesData[childId] && !this.expandedNodes.has(childId)) {
                    this.expandNode(childId);
                }
            }
        }, 100);
    }

    collapseNode(parentId) {
        if (!this.expandedNodes.has(parentId)) return;
        
        const children = this.hiddenNodesData[parentId];
        const childIds = Object.keys(children);
        
        // Recursively collapse children first
        childIds.forEach(childId => {
            if (this.expandedNodes.has(childId)) {
                this.collapseNode(childId);
            }
        });
        
        nodes.remove(childIds);
        this.expandedNodes.delete(parentId);
        network.stabilize();
    }

    calculateChildPosition(parentPos, childIndex, childrenCount, layout, nodeType) {
        const {xSpacing, yOffset} = layout;
        
        // Special layout for datapoints to avoid overcrowding
        if (nodeType === 'datapoint' && childrenCount > 6) {
            const itemsPerRow = Math.ceil(Math.sqrt(childrenCount));
            const row = Math.floor(childIndex / itemsPerRow);
            const col = childIndex % itemsPerRow;
            return {
                xPos: parentPos.x + (col * xSpacing) - (itemsPerRow * xSpacing / 2),
                yPos: parentPos.y + yOffset + (row * 80)
            };
        } else {
            // Standard linear arrangement
            return {
                xPos: parentPos.x + (childIndex * xSpacing) - (childrenCount * xSpacing / 2),
                yPos: parentPos.y + yOffset
            };
        }
    }

    getLayoutConfig(nodeType) {
        const layoutConfigs = {
            'dataset': {xSpacing: 400, yOffset: 220},
            'datapoint': {xSpacing: 180, yOffset: 180},
            'table': {xSpacing: 200, yOffset: 180},
            'column': {xSpacing: 150, yOffset: 160},
            'downstream_table': {xSpacing: 220, yOffset: 200},
            'downstream_column': {xSpacing: 140, yOffset: 160},
            'default': {xSpacing: 250, yOffset: 180}
        };
        return layoutConfigs[nodeType] || layoutConfigs['default'];
    }

    getEdgeProperties(parentId, childId) {
        const edgeProps = {from: parentId, to: childId, width: 2, color: '#666666'};
        
        // Add edge properties if they exist in the graph data
        if (this.graphData.edges[parentId] && this.graphData.edges[parentId][childId]) {
            const edgeData = this.graphData.edges[parentId][childId];
            const edgeType = edgeData.edge_type || 'default';
            
            // Apply edge styling based on type
            if (edgeType === 'datapoint_to_table' && edgeData.method) {
                edgeProps.label = edgeData.method;
                edgeProps.font = {size: 10, color: '#333333'};
            }
        }
        
        return edgeProps;
    }
}

// Global instance
const graphManager = new GraphInteractionManager();

// Initialization function to be called from Python
function initializeGraphHandlers(hiddenNodes, nodeStyles, edgeData) {
    graphManager.initialize(hiddenNodes, nodeStyles, edgeData);
}
