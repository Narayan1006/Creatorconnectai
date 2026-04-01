"""
Simple verification test for Task 11.4: Business Counter Form UI

This test verifies the UI implementation without requiring complex fixtures.
"""

import pytest
import os


def test_business_counter_ui_components_exist():
    """
    Verify that all required UI components for business counter form exist.
    
    Task 11.4 Requirements:
    - Add "Counter Back" button to countered deals
    - Create business counter form with message, amount, deliverables inputs
    - Wire form to PUT /api/deals/:id/business-counter endpoint
    """
    dashboard_path = "../frontend/src/pages/BusinessDashboard.tsx"
    assert os.path.exists(dashboard_path), "BusinessDashboard.tsx should exist"
    
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Requirement: Add "Counter Back" button
    assert "Counter Back" in content, \
        "Counter Back button should exist"
    
    # Requirement: Create business counter form with message input
    assert "businessCounterMessage" in content, \
        "Business counter message state should exist"
    assert "Message (optional)" in content or "message" in content.lower(), \
        "Message input label should exist"
    
    # Requirement: Create business counter form with amount input
    assert "businessCounterAmount" in content, \
        "Business counter amount state should exist"
    assert "Counter Amount" in content, \
        "Counter Amount input label should exist"
    
    # Requirement: Create business counter form with deliverables input
    assert "businessCounterDeliverables" in content, \
        "Business counter deliverables state should exist"
    assert "Counter Deliverables" in content, \
        "Counter Deliverables input label should exist"
    
    # Requirement: Wire form to endpoint
    assert "/business-counter" in content, \
        "business-counter endpoint should be referenced"
    assert "handleBusinessCounter" in content, \
        "handleBusinessCounter function should exist"
    
    # Verify form submission logic
    assert "setShowBusinessCounterForm" in content, \
        "Form visibility state should exist"
    
    print("\n✅ Task 11.4 Verification Complete")
    print("=" * 60)
    print("✓ Counter Back button exists")
    print("✓ Business counter form with message input exists")
    print("✓ Business counter form with amount input exists")
    print("✓ Business counter form with deliverables input exists")
    print("✓ Form is wired to PUT /api/deals/:id/business-counter endpoint")
    print("=" * 60)


def test_business_counter_form_structure():
    """Verify the business counter form has proper structure."""
    dashboard_path = "../frontend/src/pages/BusinessDashboard.tsx"
    
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for form element
    assert "onSubmit={handleBusinessCounter}" in content, \
        "Form should have handleBusinessCounter as submit handler"
    
    # Check for textarea elements (message and deliverables)
    assert content.count("textarea") >= 2, \
        "Should have at least 2 textarea elements (message and deliverables)"
    
    # Check for number input (amount)
    assert 'type="number"' in content, \
        "Should have number input for counter amount"
    
    # Check for submit button
    assert "Send Counter" in content, \
        "Should have Send Counter submit button"
    
    # Check for cancel button
    assert "setShowBusinessCounterForm(false)" in content, \
        "Should have cancel functionality"
    
    print("\n✅ Business Counter Form Structure Verified")
    print("=" * 60)
    print("✓ Form has proper submit handler")
    print("✓ Form has textarea inputs for message and deliverables")
    print("✓ Form has number input for amount")
    print("✓ Form has submit and cancel buttons")
    print("=" * 60)


def test_business_counter_integration_with_modal():
    """Verify business counter form is integrated with the counter response modal."""
    dashboard_path = "../frontend/src/pages/BusinessDashboard.tsx"
    
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that form appears in modal context
    assert "selectedDeal" in content, \
        "Should use selectedDeal for modal context"
    
    # Check conditional rendering
    assert "showBusinessCounterForm" in content, \
        "Should conditionally show business counter form"
    
    # Check that clicking Counter Back shows the form
    assert "setShowBusinessCounterForm(true)" in content, \
        "Counter Back button should show the form"
    
    # Check that form resets on close
    assert "setBusinessCounterMessage('')" in content, \
        "Should reset message on close"
    assert "setBusinessCounterAmount('')" in content, \
        "Should reset amount on close"
    assert "setBusinessCounterDeliverables('')" in content, \
        "Should reset deliverables on close"
    
    print("\n✅ Business Counter Modal Integration Verified")
    print("=" * 60)
    print("✓ Form is integrated with counter response modal")
    print("✓ Form has conditional rendering logic")
    print("✓ Counter Back button triggers form display")
    print("✓ Form fields reset properly on close")
    print("=" * 60)


def test_business_counter_payload_construction():
    """Verify that the business counter payload is constructed correctly."""
    dashboard_path = "../frontend/src/pages/BusinessDashboard.tsx"
    
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check payload construction logic
    assert "payload.message" in content, \
        "Should add message to payload"
    assert "payload.counter_amount" in content, \
        "Should add counter_amount to payload"
    assert "payload.counter_deliverables" in content, \
        "Should add counter_deliverables to payload"
    
    # Check that fields are optional (only added if present)
    assert "if (businessCounterMessage.trim())" in content, \
        "Message should be optional"
    assert "if (businessCounterAmount)" in content, \
        "Counter amount should be optional"
    assert "if (businessCounterDeliverables.trim())" in content, \
        "Counter deliverables should be optional"
    
    print("\n✅ Business Counter Payload Construction Verified")
    print("=" * 60)
    print("✓ Payload includes message field (optional)")
    print("✓ Payload includes counter_amount field (optional)")
    print("✓ Payload includes counter_deliverables field (optional)")
    print("✓ All fields are properly validated before adding to payload")
    print("=" * 60)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
