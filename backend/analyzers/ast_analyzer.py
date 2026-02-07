"""
Advanced AST-based code analyzer with pattern detection
"""

import ast
import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
import hashlib
import json
from collections import defaultdict
import networkx as nx
import numpy as np

@dataclass
class SecurityPattern:
    """Represents a security pattern or vulnerability"""
    name: str
    severity: str  # critical, high, medium, low
    category: str
    description: str
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None
    
@dataclass 
class CodeBlock:
    """Represents a code block for analysis"""
    node: ast.AST
    start_line: int
    end_line: int
    code: str
    hash: str
    complexity: int = 0
    dependencies: Set[str] = field(default_factory=set)
    calls: Set[str] = field(default_factory=set)
    vulnerabilities: List[SecurityPattern] = field(default_factory=list)

class ASTSecurityAnalyzer:
    """Advanced AST-based security analyzer"""
    
    DANGEROUS_IMPORTS = {
        'os', 'subprocess', 'pickle', 'marshal', 'tempfile',
        'eval', 'exec', 'compile', '__import__'
    }
    
    DANGEROUS_FUNCTIONS = {
        'eval': 'critical',
        'exec': 'critical', 
        'compile': 'high',
        '__import__': 'high',
        'open': 'medium',
        'input': 'low',
        'raw_input': 'low',
        'os.system': 'critical',
        'subprocess.call': 'high',
        'subprocess.Popen': 'high',
        'pickle.loads': 'critical',
        'pickle.load': 'critical',
        'yaml.load': 'high',
        'requests.get': 'medium',
        'urllib.request.urlopen': 'medium'
    }
    
    def __init__(self):
        self.tree = None
        self.source_code = None
        self.blocks: List[CodeBlock] = []
        self.call_graph = nx.DiGraph()
        self.data_flow_graph = nx.DiGraph()
        self.control_flow_graph = nx.DiGraph()
        self.taint_sources: Set[str] = set()
        self.taint_sinks: Set[str] = set()
        
    async def analyze(self, source_code: str) -> Dict[str, Any]:
        """Main analysis entry point"""
        self.source_code = source_code
        
        try:
            self.tree = ast.parse(source_code)
        except SyntaxError as e:
            return {
                "success": False,
                "error": f"Syntax error: {str(e)}",
                "vulnerabilities": []
            }
            
        # Run all analysis phases in parallel
        results = await asyncio.gather(
            self._analyze_structure(),
            self._analyze_security_patterns(),
            self._analyze_complexity(),
            self._analyze_data_flow(),
            self._analyze_control_flow()
        )
        
        structure, patterns, complexity, data_flow, control_flow = results
        
        # Calculate entropy and other metrics
        entropy = self._calculate_entropy()
        
        # Build comprehensive report
        return {
            "success": True,
            "metrics": {
                "lines_of_code": len(source_code.split('\\n')),
                "complexity": complexity,
                "entropy": entropy,
                "num_functions": structure["functions"],
                "num_classes": structure["classes"]
            },
            "vulnerabilities": patterns,
            "data_flow": data_flow,
            "control_flow": control_flow,
            "call_graph": self._serialize_graph(self.call_graph),
            "blocks": [self._serialize_block(b) for b in self.blocks]
        }
        
    async def _analyze_structure(self) -> Dict[str, Any]:
        """Analyze code structure"""
        visitor = StructureVisitor()
        visitor.visit(self.tree)
        
        return {
            "functions": len(visitor.functions),
            "classes": len(visitor.classes),
            "imports": visitor.imports,
            "globals": visitor.globals
        }
        
    async def _analyze_security_patterns(self) -> List[Dict[str, Any]]:
        """Detect security vulnerabilities"""
        vulnerabilities = []
        visitor = SecurityPatternVisitor(self)
        visitor.visit(self.tree)
        
        for vuln in visitor.vulnerabilities:
            vulnerabilities.append({
                "type": vuln.name,
                "severity": vuln.severity,
                "category": vuln.category,
                "description": vuln.description,
                "line": vuln.line,
                "column": vuln.column,
                "cwe_id": vuln.cwe_id,
                "owasp": vuln.owasp_category
            })
            
        return vulnerabilities
        
    async def _analyze_complexity(self) -> Dict[str, Any]:
        """Calculate cyclomatic complexity"""
        visitor = ComplexityVisitor()
        visitor.visit(self.tree)
        
        return {
            "cyclomatic": visitor.complexity,
            "cognitive": visitor.cognitive_complexity,
            "nesting_depth": visitor.max_nesting,
            "halstead": self._calculate_halstead_metrics()
        }
        
    async def _analyze_data_flow(self) -> Dict[str, Any]:
        """Perform data flow analysis"""
        visitor = DataFlowVisitor(self)
        visitor.visit(self.tree)
        
        # Taint analysis
        tainted_paths = self._trace_taint_propagation()
        
        return {
            "taint_sources": list(self.taint_sources),
            "taint_sinks": list(self.taint_sinks),
            "tainted_paths": tainted_paths,
            "data_dependencies": self._serialize_graph(self.data_flow_graph)
        }
        
    async def _analyze_control_flow(self) -> Dict[str, Any]:
        """Build control flow graph"""
        visitor = ControlFlowVisitor(self)
        visitor.visit(self.tree)
        
        # Detect unreachable code
        unreachable = self._find_unreachable_code()
        
        # Detect infinite loops
        infinite_loops = self._detect_infinite_loops()
        
        return {
            "graph": self._serialize_graph(self.control_flow_graph),
            "unreachable_code": unreachable,
            "infinite_loops": infinite_loops,
            "entry_points": self._find_entry_points(),
            "exit_points": self._find_exit_points()
        }
        
    def _calculate_entropy(self) -> float:
        """Calculate Shannon entropy of the code"""
        if not self.source_code:
            return 0.0
            
        # Character frequency
        freq = defaultdict(int)
        for char in self.source_code:
            freq[char] += 1
            
        # Calculate entropy
        total = len(self.source_code)
        entropy = 0.0
        
        for count in freq.values():
            if count > 0:
                p = count / total
                entropy -= p * np.log2(p)
                
        return entropy
        
    def _calculate_halstead_metrics(self) -> Dict[str, float]:
        """Calculate Halstead complexity metrics"""
        visitor = HalsteadVisitor()
        visitor.visit(self.tree)
        
        n1 = len(visitor.operators)  # Unique operators
        n2 = len(visitor.operands)   # Unique operands
        N1 = visitor.total_operators  # Total operators
        N2 = visitor.total_operands   # Total operands
        
        # Halstead metrics
        n = n1 + n2  # Program vocabulary
        N = N1 + N2  # Program length
        
        if n > 0 and N > 0:
            volume = N * np.log2(n) if n > 0 else 0
            difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
            effort = volume * difficulty
            time = effort / 18  # Seconds to implement
            bugs = volume / 3000  # Estimated bugs
        else:
            volume = difficulty = effort = time = bugs = 0
            
        return {
            "vocabulary": n,
            "length": N,
            "volume": volume,
            "difficulty": difficulty,
            "effort": effort,
            "time": time,
            "bugs": bugs
        }
        
    def _trace_taint_propagation(self) -> List[List[str]]:
        """Trace taint propagation paths"""
        paths = []
        
        for source in self.taint_sources:
            for sink in self.taint_sinks:
                if nx.has_path(self.data_flow_graph, source, sink):
                    path = nx.shortest_path(self.data_flow_graph, source, sink)
                    paths.append(path)
                    
        return paths
        
    def _find_unreachable_code(self) -> List[int]:
        """Find unreachable code blocks"""
        if not self.control_flow_graph.nodes():
            return []
            
        entry_points = self._find_entry_points()
        reachable = set()
        
        for entry in entry_points:
            reachable.update(nx.descendants(self.control_flow_graph, entry))
            reachable.add(entry)
            
        all_nodes = set(self.control_flow_graph.nodes())
        unreachable = all_nodes - reachable
        
        # Convert to line numbers
        lines = []
        for node in unreachable:
            if hasattr(node, 'lineno'):
                lines.append(node.lineno)
                
        return sorted(lines)
        
    def _detect_infinite_loops(self) -> List[Dict[str, Any]]:
        """Detect potential infinite loops"""
        loops = []
        
        # Find strongly connected components (cycles)
        for cycle in nx.strongly_connected_components(self.control_flow_graph):
            if len(cycle) > 1:
                # Check if there's an exit condition
                has_exit = False
                for node in cycle:
                    for successor in self.control_flow_graph.successors(node):
                        if successor not in cycle:
                            has_exit = True
                            break
                            
                if not has_exit:
                    loops.append({
                        "nodes": list(cycle),
                        "type": "infinite_loop",
                        "confidence": "high"
                    })
                    
        return loops
        
    def _find_entry_points(self) -> List[Any]:
        """Find entry points in control flow graph"""
        return [n for n in self.control_flow_graph.nodes() 
                if self.control_flow_graph.in_degree(n) == 0]
                
    def _find_exit_points(self) -> List[Any]:
        """Find exit points in control flow graph"""
        return [n for n in self.control_flow_graph.nodes() 
                if self.control_flow_graph.out_degree(n) == 0]
                
    def _serialize_graph(self, graph: nx.DiGraph) -> Dict[str, Any]:
        """Serialize NetworkX graph to JSON-compatible format"""
        return {
            "nodes": [str(n) for n in graph.nodes()],
            "edges": [(str(u), str(v)) for u, v in graph.edges()],
            "num_nodes": graph.number_of_nodes(),
            "num_edges": graph.number_of_edges()
        }
        
    def _serialize_block(self, block: CodeBlock) -> Dict[str, Any]:
        """Serialize code block to JSON-compatible format"""
        return {
            "start_line": block.start_line,
            "end_line": block.end_line,
            "hash": block.hash,
            "complexity": block.complexity,
            "dependencies": list(block.dependencies),
            "calls": list(block.calls),
            "vulnerabilities": [
                {
                    "name": v.name,
                    "severity": v.severity,
                    "category": v.category
                } for v in block.vulnerabilities
            ]
        }


class StructureVisitor(ast.NodeVisitor):
    """Visitor for analyzing code structure"""
    
    def __init__(self):
        self.functions = []
        self.classes = []
        self.imports = []
        self.globals = []
        
    def visit_FunctionDef(self, node):
        self.functions.append(node.name)
        self.generic_visit(node)
        
    def visit_AsyncFunctionDef(self, node):
        self.functions.append(node.name)
        self.generic_visit(node)
        
    def visit_ClassDef(self, node):
        self.classes.append(node.name)
        self.generic_visit(node)
        
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.append(node.module)
        self.generic_visit(node)
        
    def visit_Global(self, node):
        self.globals.extend(node.names)
        self.generic_visit(node)


class SecurityPatternVisitor(ast.NodeVisitor):
    """Visitor for detecting security patterns"""
    
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.vulnerabilities = []
        
    def visit_Call(self, node):
        # Check for dangerous function calls
        func_name = self._get_func_name(node)
        
        if func_name in self.analyzer.DANGEROUS_FUNCTIONS:
            severity = self.analyzer.DANGEROUS_FUNCTIONS[func_name]
            self.vulnerabilities.append({
                "name": f"Dangerous function call: {func_name}",
                "severity": severity,
                "category": "security",
                "description": f"Potentially dangerous function {func_name} detected",
                "line": node.lineno,
                "column": node.col_offset,
                "cwe_id": "CWE-78" if 'os' in func_name or 'subprocess' in func_name else "CWE-95"
            })
            
        # Check for SQL injection patterns
        if func_name in ['execute', 'executemany', 'raw']:
            if self._has_string_formatting(node):
                self.vulnerabilities.append({
                    "name": "Potential SQL Injection",
                    "severity": "critical",
                    "category": "injection",
                    "description": "SQL query appears to use string formatting",
                    "line": node.lineno,
                    "column": node.col_offset,
                    "cwe_id": "CWE-89",
                    "owasp": "A03:2021"
                })
                
        self.generic_visit(node)
        
    def _get_func_name(self, node):
        """Extract function name from call node"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts = []
            current = node.func
            while current:
                if isinstance(current, ast.Attribute):
                    parts.append(current.attr)
                    current = current.value
                elif isinstance(current, ast.Name):
                    parts.append(current.id)
                    current = None
                else:
                    current = None
            return '.'.join(reversed(parts))
        return None
        
    def _has_string_formatting(self, node):
        """Check if node uses string formatting"""
        for arg in node.args:
            if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Mod):
                return True
            if isinstance(arg, ast.JoinedStr):  # f-string
                return True
        return False


class ComplexityVisitor(ast.NodeVisitor):
    """Calculate code complexity metrics"""
    
    def __init__(self):
        self.complexity = 1
        self.cognitive_complexity = 0
        self.nesting_level = 0
        self.max_nesting = 0
        
    def visit_If(self, node):
        self.complexity += 1
        self.cognitive_complexity += (1 + self.nesting_level)
        self._increase_nesting()
        self.generic_visit(node)
        self._decrease_nesting()
        
    def visit_While(self, node):
        self.complexity += 1
        self.cognitive_complexity += (1 + self.nesting_level)
        self._increase_nesting()
        self.generic_visit(node)
        self._decrease_nesting()
        
    def visit_For(self, node):
        self.complexity += 1
        self.cognitive_complexity += (1 + self.nesting_level)
        self._increase_nesting()
        self.generic_visit(node)
        self._decrease_nesting()
        
    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.cognitive_complexity += (1 + self.nesting_level)
        self.generic_visit(node)
        
    def visit_With(self, node):
        self.cognitive_complexity += 1
        self._increase_nesting()
        self.generic_visit(node)
        self._decrease_nesting()
        
    def _increase_nesting(self):
        self.nesting_level += 1
        self.max_nesting = max(self.max_nesting, self.nesting_level)
        
    def _decrease_nesting(self):
        self.nesting_level -= 1


class DataFlowVisitor(ast.NodeVisitor):
    """Analyze data flow and taint propagation"""
    
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.current_scope = {}
        self.taint_map = {}
        
    def visit_Assign(self, node):
        # Track variable assignments
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                
                # Check if value is from taint source
                if self._is_taint_source(node.value):
                    self.analyzer.taint_sources.add(var_name)
                    self.taint_map[var_name] = True
                    
                # Track data flow
                if hasattr(node.value, 'id'):
                    self.analyzer.data_flow_graph.add_edge(node.value.id, var_name)
                    
        self.generic_visit(node)
        
    def visit_Call(self, node):
        # Check for taint sinks
        func_name = self._get_func_name(node)
        
        if func_name in ['eval', 'exec', 'os.system', 'subprocess.call']:
            # Check if any argument is tainted
            for arg in node.args:
                if isinstance(arg, ast.Name) and arg.id in self.taint_map:
                    self.analyzer.taint_sinks.add(func_name)
                    
        self.generic_visit(node)
        
    def _is_taint_source(self, node):
        """Check if node is a taint source"""
        if isinstance(node, ast.Call):
            func_name = self._get_func_name(node)
            return func_name in ['input', 'raw_input', 'request.get', 'request.POST.get']
        return False
        
    def _get_func_name(self, node):
        """Extract function name from call node"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None


class ControlFlowVisitor(ast.NodeVisitor):
    """Build control flow graph"""
    
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.current_block = None
        self.block_stack = []
        
    def visit_If(self, node):
        # Create branch in control flow
        parent = self.current_block
        
        # True branch
        true_block = f"if_true_{node.lineno}"
        self.analyzer.control_flow_graph.add_edge(parent, true_block)
        self.current_block = true_block
        for stmt in node.body:
            self.visit(stmt)
            
        # False branch
        if node.orelse:
            false_block = f"if_false_{node.lineno}"
            self.analyzer.control_flow_graph.add_edge(parent, false_block)
            self.current_block = false_block
            for stmt in node.orelse:
                self.visit(stmt)
                
        # Merge point
        merge_block = f"if_merge_{node.lineno}"
        self.analyzer.control_flow_graph.add_edge(true_block, merge_block)
        if node.orelse:
            self.analyzer.control_flow_graph.add_edge(false_block, merge_block)
        else:
            self.analyzer.control_flow_graph.add_edge(parent, merge_block)
            
        self.current_block = merge_block
        
    def visit_While(self, node):
        # Create loop in control flow
        loop_start = f"while_start_{node.lineno}"
        loop_body = f"while_body_{node.lineno}"
        loop_end = f"while_end_{node.lineno}"
        
        self.analyzer.control_flow_graph.add_edge(self.current_block, loop_start)
        self.analyzer.control_flow_graph.add_edge(loop_start, loop_body)
        self.analyzer.control_flow_graph.add_edge(loop_body, loop_start)  # Back edge
        self.analyzer.control_flow_graph.add_edge(loop_start, loop_end)
        
        self.current_block = loop_body
        for stmt in node.body:
            self.visit(stmt)
            
        self.current_block = loop_end
        
    def visit_For(self, node):
        # Similar to while loop
        loop_start = f"for_start_{node.lineno}"
        loop_body = f"for_body_{node.lineno}"
        loop_end = f"for_end_{node.lineno}"
        
        self.analyzer.control_flow_graph.add_edge(self.current_block, loop_start)
        self.analyzer.control_flow_graph.add_edge(loop_start, loop_body)
        self.analyzer.control_flow_graph.add_edge(loop_body, loop_start)  # Back edge
        self.analyzer.control_flow_graph.add_edge(loop_start, loop_end)
        
        self.current_block = loop_body
        for stmt in node.body:
            self.visit(stmt)
            
        self.current_block = loop_end


class HalsteadVisitor(ast.NodeVisitor):
    """Calculate Halstead metrics"""
    
    def __init__(self):
        self.operators = set()
        self.operands = set()
        self.total_operators = 0
        self.total_operands = 0
        
    def visit_BinOp(self, node):
        op_name = node.op.__class__.__name__
        self.operators.add(op_name)
        self.total_operators += 1
        self.generic_visit(node)
        
    def visit_UnaryOp(self, node):
        op_name = node.op.__class__.__name__
        self.operators.add(op_name)
        self.total_operators += 1
        self.generic_visit(node)
        
    def visit_Compare(self, node):
        for op in node.ops:
            op_name = op.__class__.__name__
            self.operators.add(op_name)
            self.total_operators += 1
        self.generic_visit(node)
        
    def visit_Name(self, node):
        self.operands.add(node.id)
        self.total_operands += 1
        self.generic_visit(node)
        
    def visit_Constant(self, node):
        self.operands.add(str(node.value))
        self.total_operands += 1
        self.generic_visit(node)