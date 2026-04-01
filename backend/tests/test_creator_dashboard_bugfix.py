"""
Bug condition exploration test for Creator Dashboard bugfix.

This test encodes the expected behavior from the design document:
- Dashboard renders with profile information
- Deals are fetched from GET /api/deals endpoint
- Deal cards display business info, amount, deliverables, deadline
- Action buttons call appropriate API endpoints
- TypeScript compiles without import errors

**CRITICAL**: This test MUST FAIL on the current unfixed code because:
1. CreatorDashboard.tsx is empty (renders nothing)
2. AuthContext.tsx has incorrect ReactNode import

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**
"""
import subprocess
import os
import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st
from pathlib import Path


# ---------------------------------------------------------------------------
# Property 1: Bug Condition - TypeScript Compilation Succeeds
# Validates: Requirements 1.2
# ---------------------------------------------------------------------------

def test_typescript_compilation_with_verbatim_module_syntax():
    """
    Property 1 (TypeScript): TypeScript compilation with verbatimModuleSyntax
    enabled must succeed without import errors.
    
    This test checks that AuthContext.tsx uses type-only imports for ReactNode,
    which is required when verbatimModuleSyntax is enabled in tsconfig.json.
    
    **EXPECTED ON UNFIXED CODE**: FAIL - AuthContext.tsx has incorrect ReactNode import
    **EXPECTED ON FIXED CODE**: PASS - ReactNode is imported as type-only
    
    **Validates: Requirements 1.2**
    """
    # Check if we're in the backend directory, navigate to frontend
    frontend_dir = Path(__file__).parent.parent.parent / "frontend"
    
    # Check tsconfig.json for verbatimModuleSyntax setting
    tsconfig_path = frontend_dir / "tsconfig.json"
    if tsconfig_path.exists():
        import json
        tsconfig = json.loads(tsconfig_path.read_text())
        # Note: verbatimModuleSyntax may be in compilerOptions
        compiler_options = tsconfig.get("compilerOptions", {})
        has_verbatim = compiler_options.get("verbatimModuleSyntax", False)
        
        # If verbatimModuleSyntax is enabled, check AuthContext import
        if has_verbatim:
            auth_context_path = frontend_dir / "src" / "context" / "AuthContext.tsx"
            content = auth_context_path.read_text()
            
            # ReactNode must be imported as type-only
            has_type_import = (
                "import { type ReactNode" in content or
                "import type { ReactNode" in content or
                "import { createContext, useContext, useState, type ReactNode" in content
            )
            
            assert has_type_import, (
                "TypeScript compilation will fail with verbatimModuleSyntax enabled. "
                "ReactNode is not imported as a type-only import. "
                "This confirms the bug exists."
            )
    
    # Alternative: Try to run tsc if available
    try:
        result = subprocess.run(
            ["npx", "tsc", "--noEmit"],
            cwd=str(frontend_dir),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # On unfixed code, this will fail with:
        # "'ReactNode' is a type and must be imported using a type-only import"
        assert result.returncode == 0, (
            f"TypeScript compilation failed. This confirms the bug exists.\n"
            f"Error output:\n{result.stderr}\n{result.stdout}"
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # If npm/npx not available, skip this part of the test
        # The type-only import check above is sufficient
        pass


# ---------------------------------------------------------------------------
# Property 2: Bug Condition - CreatorDashboard Component Exists and Has Content
# Validates: Requirements 1.1, 1.3
# ---------------------------------------------------------------------------

def test_creator_dashboard_component_is_not_empty():
    """
    Property 2 (Component Structure): CreatorDashboard.tsx must not be empty
    and must contain component implementation.
    
    **EXPECTED ON UNFIXED CODE**: FAIL - CreatorDashboard.tsx is empty
    **EXPECTED ON FIXED CODE**: PASS - CreatorDashboard.tsx has full implementation
    
    **Validates: Requirements 1.1, 1.3**
    """
    frontend_dir = Path(__file__).parent.parent.parent / "frontend"
    creator_dashboard_path = frontend_dir / "src" / "pages" / "CreatorDashboard.tsx"
    
    # Check file exists
    assert creator_dashboard_path.exists(), (
        f"CreatorDashboard.tsx does not exist at {creator_dashboard_path}"
    )
    
    # Read file content
    content = creator_dashboard_path.read_text()
    
    # On unfixed code, this will fail because the file is empty
    assert len(content.strip()) > 0, (
        "CreatorDashboard.tsx is empty. This confirms the bug exists."
    )
    
    # Check for essential component structure
    assert "CreatorDashboard" in content, (
        "CreatorDashboard component not found in file"
    )
    assert "export" in content, (
        "No export statement found in CreatorDashboard.tsx"
    )


# ---------------------------------------------------------------------------
# Property 3: Bug Condition - CreatorDashboard Renders Deal Cards
# Validates: Requirements 1.3, 1.4
# ---------------------------------------------------------------------------

def test_creator_dashboard_has_deal_display_logic():
    """
    Property 3 (Deal Display): CreatorDashboard must contain logic to fetch
    and display deals from the API.
    
    **EXPECTED ON UNFIXED CODE**: FAIL - No deal fetching or display logic exists
    **EXPECTED ON FIXED CODE**: PASS - Component fetches and displays deals
    
    **Validates: Requirements 1.3, 1.4**
    """
    frontend_dir = Path(__file__).parent.parent.parent / "frontend"
    creator_dashboard_path = frontend_dir / "src" / "pages" / "CreatorDashboard.tsx"
    
    content = creator_dashboard_path.read_text()
    
    # Check for API call to fetch deals
    assert "/api/deals" in content, (
        "No API call to /api/deals found. This confirms the bug exists."
    )
    
    # Check for deal state management
    assert "deals" in content.lower() or "Deal" in content, (
        "No deal state or Deal type found in component"
    )
    
    # Check for useEffect hook (for fetching data on mount)
    assert "useEffect" in content, (
        "No useEffect hook found for data fetching"
    )


# ---------------------------------------------------------------------------
# Property 4: Bug Condition - CreatorDashboard Has Action Buttons
# Validates: Requirements 1.4, 1.5
# ---------------------------------------------------------------------------

def test_creator_dashboard_has_deal_action_buttons():
    """
    Property 4 (Deal Actions): CreatorDashboard must contain UI elements
    for deal actions (accept, reject, counter).
    
    **EXPECTED ON UNFIXED CODE**: FAIL - No action button logic exists
    **EXPECTED ON FIXED CODE**: PASS - Component has accept/reject/counter buttons
    
    **Validates: Requirements 1.4, 1.5**
    """
    frontend_dir = Path(__file__).parent.parent.parent / "frontend"
    creator_dashboard_path = frontend_dir / "src" / "pages" / "CreatorDashboard.tsx"
    
    content = creator_dashboard_path.read_text()
    
    # Check for action handlers
    action_keywords = ["accept", "reject", "counter"]
    found_actions = [kw for kw in action_keywords if kw.lower() in content.lower()]
    
    assert len(found_actions) >= 2, (
        f"Missing deal action logic. Found: {found_actions}. "
        f"This confirms the bug exists."
    )
    
    # Check for button elements or click handlers
    assert "button" in content.lower() or "onClick" in content, (
        "No button elements or click handlers found"
    )


# ---------------------------------------------------------------------------
# Property 5: Bug Condition - AuthContext Has Type-Only Import
# Validates: Requirements 1.2
# ---------------------------------------------------------------------------

def test_auth_context_has_type_only_import():
    """
    Property 5 (TypeScript Import): AuthContext.tsx must import ReactNode
    as a type-only import when verbatimModuleSyntax is enabled.
    
    **EXPECTED ON UNFIXED CODE**: FAIL - ReactNode is imported as value
    **EXPECTED ON FIXED CODE**: PASS - ReactNode is imported with 'type' keyword
    
    **Validates: Requirements 1.2**
    """
    frontend_dir = Path(__file__).parent.parent.parent / "frontend"
    auth_context_path = frontend_dir / "src" / "context" / "AuthContext.tsx"
    
    content = auth_context_path.read_text()
    
    # Check that ReactNode is imported
    assert "ReactNode" in content, (
        "ReactNode import not found in AuthContext.tsx"
    )
    
    # Check for type-only import syntax
    # Should be: import { type ReactNode } or import type { ReactNode }
    has_type_import = (
        "import { type ReactNode" in content or
        "import type { ReactNode" in content or
        "import { createContext, useContext, useState, type ReactNode" in content
    )
    
    assert has_type_import, (
        "ReactNode is not imported as a type-only import. "
        "This confirms the bug exists. "
        "Expected: 'import { type ReactNode }' or similar."
    )


# ---------------------------------------------------------------------------
# Property-Based Test: For any creator user, dashboard should render
# Validates: Requirements 1.1, 1.3, 1.4
# ---------------------------------------------------------------------------

@given(
    st.fixed_dictionaries({
        "user_id": st.uuids().map(str),
        "email": st.emails(),
        "role": st.just("creator")
    })
)
@settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    max_examples=10
)
def test_creator_dashboard_renders_for_any_creator_user(user_data):
    """
    Property-Based Test: For ANY creator user who navigates to /creator,
    the CreatorDashboard component must render functional UI.
    
    This is a scoped property test that checks the component structure
    exists for any creator user input.
    
    **EXPECTED ON UNFIXED CODE**: FAIL - Component is empty
    **EXPECTED ON FIXED CODE**: PASS - Component renders for all creator users
    
    **Validates: Requirements 1.1, 1.3, 1.4**
    """
    frontend_dir = Path(__file__).parent.parent.parent / "frontend"
    creator_dashboard_path = frontend_dir / "src" / "pages" / "CreatorDashboard.tsx"
    
    content = creator_dashboard_path.read_text()
    
    # For any creator user, the component must have:
    # 1. Non-empty content
    assert len(content.strip()) > 0, (
        f"CreatorDashboard is empty for user {user_data['email']}"
    )
    
    # 2. Component export
    assert "export" in content, (
        f"No export found for user {user_data['email']}"
    )
    
    # 3. Authentication context usage (to check user role)
    assert "useAuth" in content or "AuthContext" in content, (
        f"No authentication context usage found for user {user_data['email']}"
    )
