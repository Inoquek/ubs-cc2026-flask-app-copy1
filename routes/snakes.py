# routes/investigate.py
import logging
from collections import defaultdict, deque
from flask import request, jsonify, Response
from routes import app
import json
import xml.etree.ElementTree as ET
logger = logging.getLogger(__name__)
import xml.etree.ElementTree as ET
import re
from typing import Tuple, List, Dict

import copy

class SnakesAndLaddersParser:
    def __init__(self, svg_content: str):
        self.svg_content = svg_content
        self.root = ET.fromstring(svg_content)
        self.namespace = {'svg': 'http://www.w3.org/2000/svg'}
        
    def extract_grid_size(self) -> Tuple[int, int]:
        """Extract grid size (rows, cols) from the SVG pattern or polyline coordinates"""
        
        # # Method 1: Try to extract from pattern if available
        # pattern = self.root.find('.//svg:pattern[@id="grid"]', self.namespace)
        # if pattern is not None:
        #     width = pattern.get('width', '32')
        #     height = pattern.get('height', '32')
        #     # Get SVG viewBox to calculate grid dimensions
        #     viewbox = self.root.get('viewBox', '0 0 128 128')
        #     _, _, svg_width, svg_height = map(float, viewbox.split())
            
        #     grid_width = int(float(width))
        #     grid_height = int(float(height))
            
        #     cols = int(svg_width / grid_width)
        #     rows = int(svg_height / grid_height)
            
        #     return rows, cols
        
        # Method 2: Analyze polyline coordinates to determine grid bounds
        polylines = self.root.findall('.//svg:polyline', self.namespace)
        if polylines:
            max_x, max_y = 0, 0
            min_x, min_y = float('inf'), float('inf')
            
            for polyline in polylines:
                points = polyline.get('points', '')
                coords = self._parse_points(points)
                for x, y in coords:
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
            
            # Estimate grid size based on coordinate ranges
            # Assuming standard grid spacing
            grid_spacing = 16  # Common spacing in snakes and ladders
            cols = int((max_x - min_x) / grid_spacing) + 1
            rows = int((max_y - min_y) / grid_spacing) + 1
            
            return rows, cols
        
        # # Method 3: Default fallback - analyze viewBox
        # viewbox = self.root.get('viewBox', '0 0 128 128')
        # _, _, width, height = map(float, viewbox.split())
        
        # # Assume standard 8x8 or calculate based on typical cell size
        # estimated_cell_size = 16
        # cols = int(width / estimated_cell_size)
        # rows = int(height / estimated_cell_size)
        
        # return rows, cols
    
    def _parse_points(self, points_str: str) -> List[Tuple[float, float]]:
        """Parse SVG points string into list of (x, y) coordinates"""
        coords = []
        numbers = re.findall(r'-?\d+(?:\.\d+)?', points_str)
        for i in range(0, len(numbers), 2):
            if i + 1 < len(numbers):
                coords.append((float(numbers[i]), float(numbers[i + 1])))
        return coords
    
    def extract_edges(self) -> List[Dict]:
        """Extract edges (arrows) representing snakes and ladders"""
        edges = []
        
        # Find all polylines and lines that represent connections
        polylines = self.root.findall('.//svg:polyline', self.namespace)
        lines = self.root.findall('.//svg:line', self.namespace)
        
        rows, cols = self.extract_grid_size()
        
        # Process polylines (these are the main snake/ladder connections)
        for i, polyline in enumerate(polylines):
            points = polyline.get('points', '')
            stroke = polyline.get('stroke', 'unknown')
            
            if points:
                coords = self._parse_points(points)
                if len(coords) >= 2:
                    start_pos = self._coords_to_grid_position(coords[0], rows, cols)
                    end_pos = self._coords_to_grid_position(coords[-1], rows, cols)
                    
                    edge = {
                        'type': 'polyline',
                        'start_grid': start_pos,
                        'end_grid': end_pos,
                        'start_coords': coords[0],
                        'end_coords': coords[-1],
                        'color': stroke,
                        'all_points': coords
                    }
                    edges.append(edge)
        
        # Process lines
        for i, line in enumerate(lines):
            x1 = float(line.get('x1', 0))
            y1 = float(line.get('y1', 0))
            x2 = float(line.get('x2', 0))
            y2 = float(line.get('y2', 0))
            stroke = line.get('stroke', 'unknown')
            
            start_pos = self._coords_to_grid_position((x1, y1), rows, cols)
            end_pos = self._coords_to_grid_position((x2, y2), rows, cols)
            
            edge = {
                'type': 'line',
                'start_grid': start_pos,
                'end_grid': end_pos,
                'start_coords': (x1, y1),
                'end_coords': (x2, y2),
                'color': stroke
            }
            edges.append(edge)
        
        return edges
    
    def _coords_to_grid_position(self, coords: Tuple[float, float], rows: int, cols: int) -> Tuple[int, int]:
        """Convert SVG coordinates to grid position (row, col)"""
        x, y = coords
        
        # Get SVG dimensions
        viewbox = self.root.get('viewBox', '0 0 128 128')
        _, _, svg_width, svg_height = map(float, viewbox.split())
        
        # Calculate cell dimensions
        cell_width = svg_width / cols
        cell_height = svg_height / rows
        
        # Convert to grid position
        col = int(x / cell_width)
        row = int(y / cell_height)
        
        # Clamp to valid range
        row = max(0, min(rows - 1, row))
        col = max(0, min(cols - 1, col))
        
        return (row, col)
    
    def get_grid_cell_number(self, row: int, col: int, rows: int, cols: int) -> int:
        """Convert grid position to cell number (1-based, following snakes and ladders numbering)"""
        # Standard snakes and ladders numbering: bottom-left is 1, zigzag pattern
        if row % 2 == 0:  # Even rows go left to right
            return (rows - row - 1) * cols + col + 1
        else:  # Odd rows go right to left
            return (rows - row - 1) * cols + (cols - col)
    
    def analyze_svg(self) -> Dict:
        """Complete analysis of the SVG"""
        rows, cols = self.extract_grid_size()
        edges = self.extract_edges()
        
        # Convert edges to include cell numbers
        processed_edges = []
        for edge in edges:
            start_row, start_col = edge['start_grid']
            end_row, end_col = edge['end_grid']
            
            start_cell = self.get_grid_cell_number(start_row, start_col, rows, cols)
            end_cell = self.get_grid_cell_number(end_row, end_col, rows, cols)
            
            processed_edge = {
                'start_cell': start_cell,
                'end_cell': end_cell,
                'start_grid': (start_row, start_col),
                'end_grid': (end_row, end_col),
                'color': edge['color'],
                'type': edge['type']
            }
            processed_edges.append(processed_edge)
        
        return {
            'grid_size': (rows, cols),
            'total_cells': rows * cols,
            'edges': processed_edges,
            'num_connections': len(processed_edges)
        }

# # Test examples for different grid sizes
# def test_different_grid_sizes():
#     """Test the parser with different grid configurations"""
    
#     # 4x4 grid (your original example)
#     svg_4x4 = '''<svg viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
#       <defs>
#         <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
#           <path d="M 0 0 L 32 0 32 32 0 32 0 0" fill="none" stroke="#ccc" stroke-width="1" />
#         </pattern>
#       </defs>
#       <rect width="100%" height="100%" fill="url(#grid)" />
#       <line x1="48" y1="16" x2="80" y2="48" stroke="BLUE" marker-end="url(#end)" />
#     </svg>'''
    
#     # 8x8 grid
#     svg_8x8 = '''<svg viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg">
#       <defs>
#         <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
#           <path d="M 0 0 L 32 0 32 32 0 32 0 0" fill="none" stroke="#ccc" stroke-width="1" />
#         </pattern>
#       </defs>
#       <rect width="100%" height="100%" fill="url(#grid)" />
#       <line x1="48" y1="32" x2="80" y2="64" stroke="RED" marker-end="url(#end)" />
#     </svg>'''
    
#     # 16x16 grid (smaller cells)
#     svg_16x16 = '''<svg viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
#       <defs>
#         <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
#           <path d="M 0 0 L 32 0 32 32 0 32 0 0" fill="none" stroke="#ccc" stroke-width="1" />
#         </pattern>
#       </defs>
#       <rect width="100%" height="100%" fill="url(#grid)" />
#       <line x1="48" y1="32" x2="80" y2="64" stroke="GREEN" marker-end="url(#end)" />
#     </svg>'''
    
#     # 10x10 grid (different cell size)
#     svg_10x10 = '''<svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
#       <defs>
#         <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
#           <path d="M 0 0 L 40 0 40 40 0 40 0 0" fill="none" stroke="#ccc" stroke-width="1" />
#         </pattern>
#       </defs>
#       <rect width="100%" height="100%" fill="url(#grid)" />
#       <line x1="60" y1="40" x2="100" y2="80" stroke="PURPLE" marker-end="url(#end)" />
#     </svg>'''
    
#     test_cases = [
#         ("4x4 Grid", svg_4x4),
#         ("8x8 Grid", svg_8x8), 
#         ("16x16 Grid", svg_16x16),
#         ("10x10 Grid", svg_10x10)
#     ]
    
#     print("Testing different grid sizes:")
#     print("=" * 50)
    
#     for name, svg_content in test_cases:
#         print(f"\n{name}:")
#         try:
#             result = parse_snakes_and_ladders_svg(svg_content)
#             rows, cols = result['grid_size']
#             print(f"  Detected: {rows} rows × {cols} columns = {result['total_cells']} cells")
#             print(f"  Connections: {result['num_connections']}")
#             if result['edges']:
#                 edge = result['edges'][0]
#                 print(f"  Sample edge: Cell {edge['start_cell']} → Cell {edge['end_cell']}")
#         except Exception as e:
#             print(f"  Error: {e}")

# Enhanced function to handle any grid size automatically
def auto_detect_and_parse(svg_content: str, debug: bool = False):
    """
    Automatically detect grid size and parse any Snakes and Ladders SVG
    
    Args:
        svg_content: The SVG content as string
        debug: Whether to print debug information
    
    Returns:
        Dictionary with grid info and edges
    """
    parser = SnakesAndLaddersParser(svg_content)
    
    if debug:
        print("Analyzing SVG...")
        
        # Try to get viewBox info
        root = ET.fromstring(svg_content)
        viewbox = root.get('viewBox', 'Not found')
        print(f"ViewBox: {viewbox}")
        
        # Try to get pattern info
        pattern = root.find('.//{http://www.w3.org/2000/svg}pattern[@id="grid"]')
        if pattern is not None:
            width = pattern.get('width', 'Unknown')
            height = pattern.get('height', 'Unknown')
            print(f"Grid pattern: {width} × {height}")
        else:
            print("No grid pattern found, will use coordinate analysis")
    
    result = parser.analyze_svg()
    
    if debug:
        rows, cols = result['grid_size'] 
        print(f"Final result: {rows}×{cols} grid with {result['num_connections']} connections")
    
    return result

# Example with your SVG content:
# svg_example = '''<svg viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
#   <defs>
#     <marker id="end" viewBox="0 0 8 8" refX="4" refY="4" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
#       <path d="M 0 0 L 8 4 L 0 8" />
#     </marker>
#     <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
#       <path d="M 0 0 L 32 0 32 32 0 32 0 0" fill="none" stroke="#ccc" stroke-width="1" />
#     </pattern>
#   </defs>
#   <rect width="100%" height="100%" fill="url(#grid)" />
#   <polyline points="16,112 112,112 112,80 16,80 16,48 112,48 112,16 16,16" fill="none" stroke="#aaa" stroke-dasharray="2" marker-end="url(#end)" />
#   <line x1="112" y1="48" x2="80" y2="16" stroke="BLUE" marker-end="url(#end)" />
#   <line x1="48" y1="16" x2="16" y2="48" stroke="YELLOW" marker-end="url(#end)" />
#   <line x1="48" y1="80" x2="80" y2="48" stroke="AQUA" marker-end="url(#end)" />
#   <line x1="80" y1="112" x2="112" y2="80" stroke="RED" marker-end="url(#end)" />
#   <line x1="16" y1="80" x2="48" y2="112" stroke="GREEN" marker-end="url(#end)" />
#   <line x1="48" y1="48" x2="80" y2="80" stroke="ORANGE" marker-end="url(#end)" />
# </svg>'''


# def calc(data):
#     m,n = data.get("grid_size")

#     edges = data.get("edges")
#     logger.info([m, n])
#     logger.info(edges)
    
#     k = m * n

#     visited = [[False for i in range(k)] for _ in range(2)]

#     pr = [[(-1,-1, -1) for i in range(k)] for _ in range(2)]

#     # connectivity_list = [[] for _ in range(n * m)]
#     connected = [-1 for _ in range(k)]
#     for edge in edges:
#         # connectivity_list[edge[0] - 1].append(edge[1] - 1)
#         connected[edge["start_cell"] - 1] = edge["end_cell"] - 1
#     bfs_queue = deque()
#     bfs_queue.append((0,0))
#     visited[0][0] = True 

#     logger.info("Starting BFS!")
#     while bfs_queue:
#         v, cur_type = bfs_queue.popleft()
#         logger.info([v, cur_type])
#         if v == k - 1:
#             break

#         if connected[v] != -1:

#             if not visited[cur_type][connected[v]]:
#                 visited[cur_type][connected[v]] = True
#                 pr[cur_type][connected[v]] = copy.deepcopy(pr[cur_type][v])
#                 bfs_queue.appendleft((connected[v], cur_type))

#             continue
        
#         for i in range(1, 7):
#             step = i if cur_type == 0 else int(2 ** i)
#             next = v + step
#             while next >= k or next < 0:
#                 if next >= k:
#                     next = (k - 1) - (next - (k - 1))
#                 else:
#                     next = -next
#             ntype = 1 if (i == 6 or (cur_type == 1 and i != 1)) else 0

#             logger.info([next, ntype, "ggg"])
#             if not visited[ntype][next]:
#                 visited[ntype][next] = True
#                 pr[ntype][next] = (v, i, cur_type)
#                 bfs_queue.append((next, ntype))

    
#     logger.info(visited[0][k - 1])
#     logger.info(visited[1][k - 1])
#     cur = k - 1
#     cur_type = 0 if visited[0][cur] else 1

#     logger.info("Finished bfs!")
#     path = []
#     path1 = [(cur, cur_type)]
#     idx = 0
#     while cur != 0 and idx <= 20:
#         prev_v, step, ntype = pr[cur_type][cur]
#         path.append(step)
#         cur = prev_v
#         cur_type = ntype
#         path1.append((cur,cur_type))
#         logger.info([cur, cur_type, "hmmmm"])
#         idx += 1
    
#     path = path[::-1]

#     logger.info(path1)
#     ans = []
#     for p in path:
#         ans.append(p)
#         ans.append(p)

#     ans[-2] = ((ans[-2] + 1) % 6) + 1

#     return ans

def calc(data):
    """
    Fixed version of your BFS algorithm with corrections and improvements
    """
    m, n = data.get("grid_size")
    edges = data.get("edges")
    
    logger.info(f"Grid size: {m}x{n}")
    logger.info(f"Edges: {edges}")
    
    k = m * n
    
    # Two states for each cell: type 0 and type 1
    visited = [[False for _ in range(k)] for _ in range(2)]
    pr = [[(-1, -1, -1) for _ in range(k)] for _ in range(2)]
    
    # Build adjacency list for snakes/ladders
    connected = [-1 for _ in range(k)]
    for edge in edges:
        start = edge["start_cell"] - 1  # Convert to 0-based
        end = edge["end_cell"] - 1
        connected[start] = end
        logger.info(f"Connection: {start} -> {end}")
    
    # BFS initialization
    bfs_queue = deque()
    bfs_queue.append((0, 0))  # (position, type)
    visited[0][0] = True
    pr[0][0] = (0, 0, 0)  # Initialize starting position
    
    logger.info("Starting BFS!")
    
    while bfs_queue:
        v, current_type = bfs_queue.popleft()
        logger.info(f"Processing: position={v}, type={current_type}")
        
        # Check if we reached the end
        if v == k - 1:
            logger.info("Reached the end!")
            break
        
        # Handle snake/ladder connections (0-cost moves)
        if connected[v] != -1:
            next_pos = connected[v]
            if not visited[current_type][next_pos]:
                visited[current_type][next_pos] = True
                pr[current_type][next_pos] = pr[current_type][v]  # Same parent
                bfs_queue.appendleft((next_pos, current_type))  # Add to front (0-cost)
            continue
        
        # Try all dice rolls (1-6)
        for dice_roll in range(1, 7):
            # Calculate step based on type
            if current_type == 0:
                step = dice_roll
            else:  # type == 1
                step = 2 ** dice_roll  # Powers of 2
            
            next_pos = v + step
            
            # Handle bouncing off boundaries
            while next_pos >= k or next_pos < 0:
                if next_pos >= k:
                    # Bounce back from the end
                    next_pos = (k - 1) - (next_pos - (k - 1))
                else:
                    # Bounce back from the start (shouldn't happen with forward moves)
                    next_pos = -next_pos
            
            # Determine next type based on dice roll and current type
            if dice_roll == 6 or (current_type == 1 and dice_roll != 1):
                next_type = 1
            else:
                next_type = 0
            
            logger.info(f"  Trying: dice={dice_roll}, step={step}, next_pos={next_pos}, next_type={next_type}")
            
            # Add to queue if not visited
            if not visited[next_type][next_pos]:
                visited[next_type][next_pos] = True
                pr[next_type][next_pos] = (v, dice_roll, current_type)
                bfs_queue.append((next_pos, next_type))
    
    # Reconstruct path
    logger.info("Reconstructing path...")
    
    # Find which type reached the end
    end_pos = k - 1
    if visited[0][end_pos]:
        final_type = 0
    elif visited[1][end_pos]:
        final_type = 1
    else:
        logger.error("No path found to the end!")
        return []
    
    # Trace back the path
    path = []
    cur_pos = end_pos
    cur_type = final_type
    
    while cur_pos != 0 or cur_type != 0:
        prev_pos, dice_roll, prev_type = pr[cur_type][cur_pos]
        path.append(dice_roll)
        
        logger.info(f"Path step: dice={dice_roll}, from {prev_pos} to {cur_pos}")
        
        cur_pos = prev_pos
        cur_type = prev_type
    
    path = path[::-1]  # Reverse to get forward path
    
    # Generate answer format (appears to duplicate each move?)
    ans = []
    for dice_roll in path:
        ans.extend([dice_roll, dice_roll])
    
    # Modify second-to-last element
    if len(ans) >= 2:
        ans[-2] = ((ans[-2] + 1) % 6) + 1
    
    logger.info(f"Final answer: {ans}")
    return ans

@app.route("/slpu", methods = ["POST"])
def snakes():
    data = auto_detect_and_parse(request.get_data(as_text=True))

    logging.info("data sent for evaluation {}".format(data))

    result = calc(data)
    
    logging.info("investigate result: %s", result)
    string_numbers = map(str, result)  # Converts each number to a string
    concatenated_string = "".join(string_numbers)
    svg_data = f'<svg xmlns="http://www.w3.org/2000/svg"><text>{concatenated_string}</text></svg>'
    return Response(svg_data, mimetype="image/svg+xml")
