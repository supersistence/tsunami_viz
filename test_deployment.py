#!/usr/bin/env python3
"""
Test script to verify the Tsunami Viz deployment is working correctly.
Run this after deployment to check all components.
"""

import requests
import time
import sys
from urllib.parse import urljoin

def test_app_health(base_url="http://localhost:8050", timeout=30):
    """Test if the application is responding correctly."""
    print(f"🧪 Testing application at {base_url}")
    
    try:
        # Test basic connectivity
        response = requests.get(base_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Application is responding")
            
            # Check if it's actually the Tsunami Viz app
            if "Wave Watch" in response.text or "Tsunami" in response.text:
                print("✅ Tsunami Viz app detected")
                return True
            else:
                print("❌ Response doesn't contain expected content")
                return False
                
        else:
            print(f"❌ HTTP {response.status_code}: {response.reason}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - app may not be running")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out - app may be slow to respond")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_ssl_redirect(domain):
    """Test if HTTP redirects to HTTPS properly."""
    http_url = f"http://{domain}"
    print(f"🔒 Testing SSL redirect for {http_url}")
    
    try:
        response = requests.get(http_url, timeout=10, allow_redirects=False)
        
        if response.status_code in [301, 302]:
            redirect_location = response.headers.get('Location', '')
            if redirect_location.startswith('https://'):
                print("✅ HTTP to HTTPS redirect working")
                return True
            else:
                print(f"❌ Redirect to {redirect_location} (should be HTTPS)")
                return False
        else:
            print(f"❌ No redirect (HTTP {response.status_code})")
            return False
            
    except Exception as e:
        print(f"❌ SSL redirect test failed: {e}")
        return False

def test_https_connection(domain):
    """Test HTTPS connection with SSL verification."""
    https_url = f"https://{domain}"
    print(f"🔒 Testing HTTPS connection to {https_url}")
    
    try:
        response = requests.get(https_url, timeout=10, verify=True)
        
        if response.status_code == 200:
            print("✅ HTTPS connection successful")
            print("✅ SSL certificate valid")
            return True
        else:
            print(f"❌ HTTP {response.status_code}: {response.reason}")
            return False
            
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL certificate error: {e}")
        return False
    except Exception as e:
        print(f"❌ HTTPS connection failed: {e}")
        return False

def main():
    """Run all deployment tests."""
    print("🚀 Tsunami Viz Deployment Test")
    print("=" * 40)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        domain = sys.argv[1]
        test_production = True
        print(f"Testing production deployment: {domain}")
    else:
        domain = None
        test_production = False
        print("Testing local deployment (use domain as argument for production test)")
    
    print()
    
    all_tests_passed = True
    
    # Test 1: Local application health
    if not test_app_health():
        all_tests_passed = False
    
    print()
    
    # Test 2 & 3: Production tests (if domain provided)
    if test_production and domain:
        if not test_ssl_redirect(domain):
            all_tests_passed = False
        
        print()
        
        if not test_https_connection(domain):
            all_tests_passed = False
    
    print()
    print("=" * 40)
    
    if all_tests_passed:
        print("🎉 All tests passed! Deployment is working correctly.")
        if test_production:
            print(f"🌐 Your app is live at: https://{domain}")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Check the output above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()