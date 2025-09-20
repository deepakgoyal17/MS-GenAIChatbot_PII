#!/usr/bin/env python3
"""
Launcher script for PII Protection Chatbot
Choose between original and modular versions
"""

import os
import sys
import subprocess
import argparse

def check_requirements():
    """Check if required packages are installed"""
    required_packages = [
        'streamlit',
        'pandas',
        'openpyxl',
        'numpy',
        'scikit-learn'
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Install with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False

    return True

def check_api_key():
    """Check if Google API key is configured"""
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("GOOGLE-API-KEY")
    if not api_key:
        print("❌ GOOGLE-API-KEY not found in .env file")
        print("\n🔑 Add to .env file:")
        print("   GOOGLE-API-KEY=your_actual_api_key_here")
        return False

    return True

def run_app(version='modular'):
    """Run the specified version of the application"""

    print("🚀 Starting PII Protection Chatbot")
    print("=" * 50)

    # Check requirements
    if not check_requirements():
        sys.exit(1)

    # Check API key
    if not check_api_key():
        sys.exit(1)

    # Determine app file
    if version == 'modular':
        app_file = 'app_modular.py'
        print("🎛️  Running MODULAR version with feature flags")
    elif version == 'original':
        app_file = 'app.py'
        print("📚 Running ORIGINAL version (all features enabled)")
    else:
        print(f"❌ Unknown version: {version}")
        print("   Available versions: modular, original")
        sys.exit(1)

    # Check if app file exists
    if not os.path.exists(app_file):
        print(f"❌ App file not found: {app_file}")
        sys.exit(1)

    print(f"📁 App file: {app_file}")
    print(f"🌐 URL: http://localhost:8501")
    print("=" * 50)
    print("🔧 Configuration:")
    if version == 'modular':
        print("   • Use sidebar to enable/disable features")
        print("   • Choose from preset configurations")
        print("   • Real-time feature toggling")
    else:
        print("   • All features enabled by default")
        print("   • Fixed configuration")
    print("=" * 50)

    try:
        # Run Streamlit app
        cmd = [sys.executable, '-m', 'streamlit', 'run', app_file]
        subprocess.run(cmd, cwd=os.getcwd())
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Error running application: {e}")
        sys.exit(1)

def show_help():
    """Show help information"""
    print("PII Protection Chatbot Launcher")
    print("=" * 40)
    print()
    print("USAGE:")
    print("  python run.py [version]")
    print()
    print("VERSIONS:")
    print("  modular    - Feature-flag controlled version (recommended)")
    print("  original   - Original version with all features enabled")
    print()
    print("EXAMPLES:")
    print("  python run.py modular    # Run modular version")
    print("  python run.py original   # Run original version")
    print("  python run.py            # Run modular version (default)")
    print()
    print("FEATURES:")
    print("  • Modular: Enable/disable individual PII methods")
    print("  • Original: All methods enabled for comparison")
    print()
    print("CONFIGURATION:")
    print("  • Ensure .env file exists with GOOGLE-API-KEY")
    print("  • Install required packages: pip install -r requirements.txt")
    print("  • For modular version: Use sidebar to configure features")

def main():
    """Main launcher function"""
    parser = argparse.ArgumentParser(
        description='PII Protection Chatbot Launcher',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py modular    # Run modular version (recommended)
  python run.py original   # Run original version
  python run.py --help     # Show this help
        """
    )

    parser.add_argument(
        'version',
        nargs='?',
        default='modular',
        choices=['modular', 'original'],
        help='Version to run (default: modular)'
    )

    parser.add_argument(
        '--help-examples',
        action='store_true',
        help='Show detailed examples and configuration info'
    )

    args = parser.parse_args()

    if args.help_examples:
        show_help()
        return

    # Run the selected version
    run_app(args.version)

if __name__ == "__main__":
    main()