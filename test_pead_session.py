"""
Test PEAD upload with session persistence verification.

This test simulates the production flow to ensure:
1. CSV uploads are processed correctly
2. Session data is persisted
3. Results are returned and rendered
"""
import os
import secrets

# Set required environment variables for testing
if not os.environ.get('SECRET_KEY'):
    os.environ['SECRET_KEY'] = secrets.token_hex(32)

from app import create_app
from flask import session

def test_pead_upload_with_session():
    """Test the complete PEAD upload flow with session verification."""
    app = create_app()
    
    with app.app_context():
        with app.test_client() as client:
            # Read the sample CSV
            with open('static/sample_pead_data.csv', 'rb') as f:
                csv_data = f.read()
            
            print("=" * 60)
            print("Testing PEAD CSV Upload Flow")
            print("=" * 60)
            
            # First, get the form page to obtain CSRF token
            get_response = client.get('/financial/pead-screener')
            
            # Extract CSRF token from response (simple approach for testing)
            # In production, this would be in the form
            
            # For testing, we'll disable CSRF
            app.config['WTF_CSRF_ENABLED'] = False
            
            # Simulate POST request with file upload
            from io import BytesIO
            response = client.post(
                '/financial/pead-screener',
                data={
                    'csv_file': (BytesIO(csv_data), 'test_data.csv'),
                    'ftse_index': 'BOTH',
                    'drift_window': '90'
                },
                content_type='multipart/form-data',
                follow_redirects=False
            )
            
            print(f"\nResponse Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            # Check if we got a successful response (200) or redirect (302)
            if response.status_code == 200:
                print("\n✓ SUCCESS: Got 200 response (results page)")
                
                # Check if results are in the response
                response_text = response.data.decode('utf-8')
                if 'Total Opportunities' in response_text:
                    print("✓ Results table found in response")
                else:
                    print("✗ WARNING: Results table not found in response")
                    
            elif response.status_code == 302:
                print(f"\n✗ REDIRECT: Got redirect to {response.location}")
                print("This indicates the upload did not progress to results")
                
                # Check flash messages
                with client.session_transaction() as sess:
                    flashes = sess.get('_flashes', [])
                    if flashes:
                        print(f"Flash messages: {flashes}")
            else:
                print(f"\n✗ ERROR: Unexpected status code {response.status_code}")
            
            # Check session state
            with client.session_transaction() as sess:
                batch_uuid = sess.get('pead_batch_uuid')
                ftse_index = sess.get('pead_ftse_index')
                is_permanent = sess.permanent
                
                print(f"\nSession State:")
                print(f"  - batch_uuid: {batch_uuid}")
                print(f"  - ftse_index: {ftse_index}")
                print(f"  - permanent: {is_permanent}")
                
                if batch_uuid:
                    print("✓ Session data persisted correctly")
                else:
                    print("✗ WARNING: Session data not persisted")
            
            print("\n" + "=" * 60)
            
            # Now test GET request to see if session is retrieved
            print("\nTesting GET request (session retrieval)...")
            response2 = client.get('/financial/pead-screener')
            
            print(f"Response Status: {response2.status_code}")
            
            if response2.status_code == 200:
                response_text = response2.data.decode('utf-8')
                if 'Total Opportunities' in response_text:
                    print("✓ Session retrieved and results displayed on GET")
                else:
                    print("✗ Session not retrieved or no results")
            
            print("=" * 60)

if __name__ == "__main__":
    test_pead_upload_with_session()
