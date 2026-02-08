"""Tests for code analyzers"""

import pytest
import asyncio
from analyzers.ast_analyzer import ASTSecurityAnalyzer
from analyzers.sast_analyzer import SastAnalyzer

@pytest.mark.asyncio
async def test_ast_analyzer():
    """Test AST analyzer with malicious code"""
    analyzer = ASTSecurityAnalyzer()
    
    code = """
import os
def backdoor():
    os.system("rm -rf /")
    eval(input())
"""
    
    result = await analyzer.analyze(code)
    
    assert result['success'] == True
    assert len(result['vulnerabilities']) > 0
    assert result['metrics']['lines_of_code'] > 0
    
@pytest.mark.asyncio
async def test_sast_analyzer():
    """Test SAST analyzer"""
    analyzer = SastAnalyzer()
    
    code = """
password = "hardcoded123"
exec(user_input)
"""
    
    result = await analyzer.analyze(code)
    
    assert 'findings' in result
    assert 'statistics' in result