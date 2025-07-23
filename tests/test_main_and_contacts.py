# tests/test_main_and_contacts.py
import io
import pandas as pd # Make sure pandas is imported
from fastapi.testclient import TestClient

def test_root_endpoint(test_client: TestClient):
    """Test the main GET / endpoint."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Mass Messaging Backend is running"}

def test_import_contacts_excel(test_client: TestClient):
    """Test uploading a valid Excel file to import contacts."""
    # --- FIX STARTS HERE ---
    # 1. Create a pandas DataFrame
    df = pd.DataFrame({
        'name': ['Test User 1', 'Test User 2'],
        'email': ['test1@example.com', 'test2@example.com'],
        'phone': ['1112223333', '4445556666']
    })

    # 2. Save the DataFrame to an in-memory Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')

    output.seek(0) # Go to the beginning of the in-memory file
    # --- FIX ENDS HERE ---

    response = test_client.post(
        "/contacts/import-excel",
        files={"file": ("test_contacts.xlsx", output, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )

    # The assertion should now pass
    assert response.status_code == 201
    assert response.json() == {"message": "Contacts imported successfully."}